"""Font embedding into DOCX according to ECMA-376 Part 1 and Part 2 (V3-03)."""

from __future__ import annotations

import os
import re
import shutil
import struct
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple, TYPE_CHECKING
from xml.etree import ElementTree as ET

from md_to_docx.mermaid import ConvertError
from md_to_docx.template import Template

if TYPE_CHECKING:
    from md_to_docx.options import GeneratorOptions

REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

# Register standard namespaces so ET.tostring does not inject ns0: prefixes that break LibreOffice
ET.register_namespace("", CT_NS)
ET.register_namespace("", REL_NS)
ET.register_namespace("w", W_NS)
ET.register_namespace("r", R_NS)


def _serialize_element(root: ET.Element) -> bytes:
    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    xml_str = xml_bytes.decode("utf-8")
    xml_str = re.sub(r'</?ns0:', lambda m: m.group(0).replace('ns0:', ''), xml_str)
    xml_str = xml_str.replace('xmlns:ns0=', 'xmlns=')
    return xml_str.encode("utf-8")


def read_font_fstype(font_path: Path) -> Optional[int]:
    """Reads OS/2 fsType from TTF file according to OpenType / TrueType specification.

    Returns 16-bit uint fsType, or None if file format is invalid or OS/2 table is missing.
    """
    try:
        with font_path.open("rb") as f:
            data = f.read(12)
            if len(data) < 12:
                return None
            sfnt_version, num_tables = struct.unpack(">4sH", data[:6])
            if sfnt_version not in (b"\x00\x01\x00\x00", b"true", b"OTTO"):
                return None
            for _ in range(num_tables):
                rec = f.read(16)
                if len(rec) < 16:
                    break
                tag, checksum, offset, length = struct.unpack(">4sIII", rec)
                if tag == b"OS/2":
                    f.seek(offset)
                    os2_data = f.read(min(length, 10))
                    if len(os2_data) >= 10:
                        version, _, _, _, fs_type = struct.unpack(">HHHHH", os2_data[:10])
                        return fs_type
    except Exception:
        pass
    return None


def validate_font_embedding(
    template: Template,
    font_family: Optional[str] = None,
) -> Tuple[bool, Optional[str], Optional[Path], Optional[Path]]:
    """Validates presence of regular and bold font files, fsType permissions, and license for a font family."""
    effective_family = font_family or template.fonts.get("body", "Vazirmatn")
    fonts_dir = template.dir_path / "fonts" if template.dir_path else None

    # Resolve regular font
    reg_rel = template.font_files.get(f"{effective_family}-Regular") or template.font_files.get(effective_family)
    reg_path: Optional[Path] = (template.dir_path / reg_rel) if (template.dir_path and reg_rel) else None
    if not reg_path or not reg_path.is_file():
        cand = (fonts_dir / f"{effective_family}-Regular.ttf") if fonts_dir else None
        if cand and cand.is_file():
            reg_path = cand
        elif fonts_dir and (fonts_dir / "Vazirmatn-Regular.ttf").is_file() and effective_family == "Vazirmatn":
            reg_path = fonts_dir / "Vazirmatn-Regular.ttf"

    if not reg_path or not reg_path.is_file():
        return False, f"Regular font file missing for '{effective_family}'", None, None

    # Resolve bold font: never fall back to Vazirmatn-Bold for custom fonts (finilize.v3.md V3-02 / V3-03)
    bold_rel = template.font_files.get(f"{effective_family}-Bold") or (
        template.font_files.get("Vazirmatn-Bold") if effective_family == "Vazirmatn" else None
    )
    bold_path: Optional[Path] = (template.dir_path / bold_rel) if (template.dir_path and bold_rel) else None
    if not bold_path or not bold_path.is_file():
        cand = (fonts_dir / f"{effective_family}-Bold.ttf") if fonts_dir else None
        if cand and cand.is_file():
            bold_path = cand
        elif fonts_dir and (fonts_dir / "Vazirmatn-Bold.ttf").is_file() and effective_family == "Vazirmatn":
            bold_path = fonts_dir / "Vazirmatn-Bold.ttf"

    if not bold_path or not bold_path.is_file():
        return False, f"Bold font file missing for '{effective_family}'", None, None

    # Check OS/2 fsType for embedding permissions
    reg_fstype = read_font_fstype(reg_path)
    if reg_fstype is None:
        return False, f"Regular font '{reg_path.name}' is invalid or missing OS/2 table", None, None
    if (reg_fstype & 0x0202) != 0:
        return False, f"Regular font '{reg_path.name}' has restricted licensing (fsType 0x{reg_fstype:04x}) and cannot be embedded", None, None
    if (reg_fstype & 0x0004) != 0 and (reg_fstype & 0x0008) == 0:
        return False, f"Regular font '{reg_path.name}' has Preview/Print-only licensing (fsType 0x{reg_fstype:04x}) and cannot be embedded for editing", None, None

    bold_fstype = read_font_fstype(bold_path)
    if bold_fstype is None:
        return False, f"Bold font '{bold_path.name}' is invalid or missing OS/2 table", None, None
    if (bold_fstype & 0x0202) != 0:
        return False, f"Bold font '{bold_path.name}' has restricted licensing (fsType 0x{bold_fstype:04x}) and cannot be embedded", None, None
    if (bold_fstype & 0x0004) != 0 and (bold_fstype & 0x0008) == 0:
        return False, f"Bold font '{bold_path.name}' has Preview/Print-only licensing (fsType 0x{bold_fstype:04x}) and cannot be embedded for editing", None, None

    # Validate license file
    lic_file: Optional[Path] = None
    search_dirs: List[Path] = []
    if reg_path and reg_path.parent and reg_path.parent not in search_dirs:
        search_dirs.append(reg_path.parent)
    if fonts_dir and fonts_dir not in search_dirs:
        search_dirs.append(fonts_dir)
    if template.dir_path and template.dir_path not in search_dirs:
        search_dirs.append(template.dir_path)

    for d in search_dirs:
        for name in ("OFL.txt", "LICENSE", "LICENSE.txt", "OFL.md"):
            p = d / name
            if p.is_file():
                lic_file = p
                break
        if lic_file:
            break

    if not lic_file or not lic_file.is_file():
        return False, f"Font license (OFL.txt) missing for '{effective_family}'", None, None

    try:
        lic_text = lic_file.read_text(encoding="utf-8", errors="ignore").lower()
    except Exception as e:
        return False, f"Failed to read font license file: {e}", None, None

    if not ("open font license" in lic_text or "sil open font" in lic_text or "apache" in lic_text or "mit license" in lic_text or "gpl" in lic_text or "public domain" in lic_text):
        return False, f"Font license in '{lic_file}' does not grant embedding rights", None, None

    return True, None, reg_path, bold_path


def resolve_primary_font_families(
    template: Template,
    font_family: Optional[str] = None,
    heading_font: Optional[str] = None,
    options: Optional[GeneratorOptions] = None,
) -> List[str]:
    """Resolves primary font families that must be embedded according to finilize.v3.md Section 4.1.

    At least effective body and heading font families are embedded.
    If they are identical, duplicates are eliminated.
    """
    body_fam = (options.font_family if options else None) or font_family or template.fonts.get("body", "Vazirmatn")
    if options and options.heading_font:
        head_fam = options.heading_font
    elif heading_font:
        head_fam = heading_font
    elif (options and options.font_family) or font_family:
        head_fam = (options.font_family if options else None) or font_family
    elif template.fonts.get("heading"):
        head_fam = template.fonts.get("heading")
    else:
        head_fam = body_fam

    families: List[str] = [body_fam]
    if head_fam != body_fam:
        families.append(head_fam)
    return families


def obfuscate_font_data(font_bytes: bytes, guid_str: str) -> bytes:
    """Obfuscates TrueType font bytes using ECMA-376-2 Section 8.5.3.1 XOR algorithm."""
    guid_digits = re.sub(r"[^0-9a-fA-F]", "", guid_str)
    if len(guid_digits) != 32:
        raise ValueError(f"Invalid fontKey GUID format: '{guid_str}'")
    key = bytes.fromhex(guid_digits)[::-1]
    data = bytearray(font_bytes)
    for i in range(16):
        if i < len(data):
            data[i] ^= key[i]
        if i + 16 < len(data):
            data[i + 16] ^= key[i]
    return bytes(data)


def embed_fonts_in_docx(
    docx_path: Path,
    template: Template,
    font_family: Optional[str] = None,
    heading_font: Optional[str] = None,
    options: Optional[GeneratorOptions] = None,
) -> str:
    """Embeds regular and bold fonts for body and heading families into the given DOCX package.

    Follows ECMA-376-1 / ECMA-376-2:
    - Obfuscates TTF files using fontKey GUID.
    - Saves font files to word/fonts/font{N}.odttf.
    - Merges with word/fontTable.xml with embedRegular and embedBold.
    - Merges with word/_rels/fontTable.xml.rels.
    - Updates word/_rels/document.xml.rels with relationship to fontTable.xml.
    - Updates [Content_Types].xml with odttf Default and fontTable Override.
    - Updates word/settings.xml with w:embedTrueTypeFonts and strips saveSubsetFonts.
    """
    families = resolve_primary_font_families(
        template,
        font_family=font_family,
        heading_font=heading_font,
        options=options,
    )

    faces_to_embed: List[Tuple[str, Path, Path]] = []
    for fam in families:
        valid, err_msg, reg_path, bold_path = validate_font_embedding(template, fam)
        if not valid or not reg_path or not bold_path:
            raise ConvertError(f"Font embedding failed for '{fam}': {err_msg}")
        faces_to_embed.append((fam, reg_path, bold_path))

    tmp_docx = docx_path.with_name(f".tmp_embed_{uuid.uuid4().hex[:8]}.docx")
    try:
        with zipfile.ZipFile(docx_path, "r") as zin, zipfile.ZipFile(tmp_docx, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            has_settings = False
            existing_font_table_bytes: Optional[bytes] = None
            existing_ft_rels_bytes: Optional[bytes] = None

            for item in zin.infolist():
                if item.filename == "word/_rels/document.xml.rels":
                    rels_data = zin.read(item.filename)
                    root = ET.fromstring(rels_data)
                    has_ft = any(
                        r.get("Type") == "http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable"
                        for r in root
                    )
                    if not has_ft:
                        existing_ids = {r.get("Id") for r in root}
                        rid_idx = 1
                        while f"rIdFontTable{rid_idx}" in existing_ids:
                            rid_idx += 1
                        ft_rid = f"rIdFontTable{rid_idx}"
                        ft_rel = ET.Element(
                            f"{{{REL_NS}}}Relationship",
                            {
                                "Id": ft_rid,
                                "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable",
                                "Target": "fontTable.xml",
                            },
                        )
                        root.append(ft_rel)
                    new_rels = _serialize_element(root)
                    zout.writestr(item, new_rels)

                elif item.filename == "[Content_Types].xml":
                    ct_data = zin.read(item.filename)
                    root = ET.fromstring(ct_data)
                    has_odttf = any(
                        d.get("Extension", "").lower() == "odttf"
                        for d in root.findall(f"{{{CT_NS}}}Default")
                    )
                    if not has_odttf:
                        d_el = ET.Element(
                            f"{{{CT_NS}}}Default",
                            {
                                "Extension": "odttf",
                                "ContentType": "application/vnd.openxmlformats-officedocument.obfuscatedFont",
                            },
                        )
                        root.append(d_el)
                    has_ft_ct = any(
                        o.get("PartName", "").lstrip("/") == "word/fontTable.xml"
                        for o in root.findall(f"{{{CT_NS}}}Override")
                    )
                    if not has_ft_ct:
                        o_el = ET.Element(
                            f"{{{CT_NS}}}Override",
                            {
                                "PartName": "/word/fontTable.xml",
                                "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml",
                            },
                        )
                        root.append(o_el)
                    new_ct = _serialize_element(root)
                    zout.writestr(item, new_ct)

                elif item.filename == "word/settings.xml":
                    has_settings = True
                    settings_data = zin.read(item.filename)
                    root = ET.fromstring(settings_data)
                    # Set w:embedTrueTypeFonts
                    embed_el = root.find(f"{{{W_NS}}}embedTrueTypeFonts")
                    if embed_el is None:
                        root.append(ET.Element(f"{{{W_NS}}}embedTrueTypeFonts"))
                    # Remove or set saveSubsetFonts to 0
                    subset_el = root.find(f"{{{W_NS}}}saveSubsetFonts")
                    if subset_el is not None:
                        root.remove(subset_el)
                    new_settings = _serialize_element(root)
                    zout.writestr(item, new_settings)

                elif item.filename == "word/fontTable.xml":
                    existing_font_table_bytes = zin.read(item.filename)
                    continue

                elif item.filename == "word/_rels/fontTable.xml.rels":
                    existing_ft_rels_bytes = zin.read(item.filename)
                    continue

                elif item.filename.startswith("word/fonts/") and item.filename.endswith(".odttf"):
                    continue

                else:
                    zout.writestr(item, zin.read(item.filename))

            # If settings.xml was missing, create it
            if not has_settings:
                settings_xml = (
                    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                    f'<w:settings xmlns:w="{W_NS}">\n'
                    f'  <w:embedTrueTypeFonts/>\n'
                    f'</w:settings>'
                )
                zout.writestr("word/settings.xml", settings_xml.encode("utf-8"))

            # Build or merge word/_rels/fontTable.xml.rels
            if existing_ft_rels_bytes:
                try:
                    ft_rels_root = ET.fromstring(existing_ft_rels_bytes)
                except Exception:
                    ft_rels_root = ET.Element(f"{{{REL_NS}}}Relationships")
            else:
                ft_rels_root = ET.Element(f"{{{REL_NS}}}Relationships")

            # Build or merge word/fontTable.xml
            if existing_font_table_bytes:
                try:
                    ft_root = ET.fromstring(existing_font_table_bytes)
                except Exception:
                    ft_root = ET.Element(f"{{{W_NS}}}fonts", {f"xmlns:r": R_NS})
            else:
                ft_root = ET.Element(f"{{{W_NS}}}fonts", {f"xmlns:r": R_NS})

            # Process each family
            font_idx = 1
            for fam_name, reg_path, bold_path in faces_to_embed:
                reg_guid = "{" + str(uuid.uuid4()).upper() + "}"
                bold_guid = "{" + str(uuid.uuid4()).upper() + "}"

                reg_obfuscated = obfuscate_font_data(reg_path.read_bytes(), reg_guid)
                bold_obfuscated = obfuscate_font_data(bold_path.read_bytes(), bold_guid)

                reg_part_name = f"fonts/font{font_idx}.odttf"
                bold_part_name = f"fonts/font{font_idx + 1}.odttf"
                reg_rid = f"rIdFont{font_idx}"
                bold_rid = f"rIdFont{font_idx + 1}"
                font_idx += 2

                # Write obfuscated parts
                zout.writestr(f"word/{reg_part_name}", reg_obfuscated)
                zout.writestr(f"word/{bold_part_name}", bold_obfuscated)

                # Add relationships to fontTable.xml.rels
                existing_rids = {r.get("Id"): r for r in ft_rels_root}
                if reg_rid in existing_rids:
                    ft_rels_root.remove(existing_rids[reg_rid])
                ft_rels_root.append(
                    ET.Element(
                        f"{{{REL_NS}}}Relationship",
                        {
                            "Id": reg_rid,
                            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font",
                            "Target": reg_part_name,
                        },
                    )
                )

                if bold_rid in existing_rids:
                    ft_rels_root.remove(existing_rids[bold_rid])
                ft_rels_root.append(
                    ET.Element(
                        f"{{{REL_NS}}}Relationship",
                        {
                            "Id": bold_rid,
                            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font",
                            "Target": bold_part_name,
                        },
                    )
                )

                # Find or create font element for fam_name
                target_font_el = None
                for font_el in ft_root.findall(f"{{{W_NS}}}font"):
                    if font_el.get(f"{{{W_NS}}}name") == fam_name:
                        target_font_el = font_el
                        break
                if target_font_el is None:
                    target_font_el = ET.Element(f"{{{W_NS}}}font", {f"{{{W_NS}}}name": fam_name})
                    ft_root.append(target_font_el)

                # Update embedRegular and embedBold
                reg_el = target_font_el.find(f"{{{W_NS}}}embedRegular")
                if reg_el is None:
                    reg_el = ET.Element(f"{{{W_NS}}}embedRegular", {f"{{{R_NS}}}id": reg_rid, f"{{{W_NS}}}fontKey": reg_guid})
                    target_font_el.append(reg_el)
                else:
                    reg_el.set(f"{{{R_NS}}}id", reg_rid)
                    reg_el.set(f"{{{W_NS}}}fontKey", reg_guid)

                bold_el = target_font_el.find(f"{{{W_NS}}}embedBold")
                if bold_el is None:
                    bold_el = ET.Element(f"{{{W_NS}}}embedBold", {f"{{{R_NS}}}id": bold_rid, f"{{{W_NS}}}fontKey": bold_guid})
                    target_font_el.append(bold_el)
                else:
                    bold_el.set(f"{{{R_NS}}}id", bold_rid)
                    bold_el.set(f"{{{W_NS}}}fontKey", bold_guid)

            zout.writestr("word/_rels/fontTable.xml.rels", _serialize_element(ft_rels_root))
            zout.writestr("word/fontTable.xml", _serialize_element(ft_root))

        os.replace(tmp_docx, docx_path)
        return "embedded"
    finally:
        if tmp_docx.exists():
            try:
                tmp_docx.unlink()
            except OSError:
                pass


def strip_embedded_fonts(docx_path: Path) -> None:
    """Removes font embedding parts, relationships, and settings from a DOCX package if present (finilize.v3.md Section 4.1)."""
    tmp_docx = docx_path.with_name(f".tmp_strip_{uuid.uuid4().hex[:8]}.docx")
    try:
        with zipfile.ZipFile(docx_path, "r") as zin:
            names = zin.namelist()
            has_embed = (
                any(n.startswith("word/fonts/") for n in names)
                or "word/fontTable.xml" in names
                or "word/settings.xml" in names
            )
            if not has_embed:
                return

            with zipfile.ZipFile(tmp_docx, "w", compression=zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    if item.filename.startswith("word/fonts/") and item.filename.endswith(".odttf"):
                        continue

                    if item.filename == "[Content_Types].xml":
                        try:
                            root = ET.fromstring(zin.read(item.filename))
                            for d in list(root.findall(f"{{{CT_NS}}}Default")):
                                if d.get("Extension", "").lower() == "odttf":
                                    root.remove(d)
                            zout.writestr(item, _serialize_element(root))
                        except Exception:
                            zout.writestr(item, zin.read(item.filename))

                    elif item.filename == "word/settings.xml":
                        try:
                            root = ET.fromstring(zin.read(item.filename))
                            for el in list(root):
                                if el.tag in (f"{{{W_NS}}}embedTrueTypeFonts", f"{{{W_NS}}}saveSubsetFonts"):
                                    root.remove(el)
                            zout.writestr(item, _serialize_element(root))
                        except Exception:
                            zout.writestr(item, zin.read(item.filename))

                    elif item.filename == "word/fontTable.xml":
                        try:
                            root = ET.fromstring(zin.read(item.filename))
                            for font_el in root.findall(f"{{{W_NS}}}font"):
                                for el in list(font_el):
                                    if el.tag in (
                                        f"{{{W_NS}}}embedRegular",
                                        f"{{{W_NS}}}embedBold",
                                        f"{{{W_NS}}}embedItalic",
                                        f"{{{W_NS}}}embedBoldItalic",
                                    ):
                                        font_el.remove(el)
                            zout.writestr(item, ET.tostring(root, encoding="utf-8", xml_declaration=True))
                        except Exception:
                            zout.writestr(item, zin.read(item.filename))

                    elif item.filename == "word/_rels/fontTable.xml.rels":
                        try:
                            root = ET.fromstring(zin.read(item.filename))
                            for rel in list(root):
                                if "relationships/font" in (rel.get("Type") or ""):
                                    root.remove(rel)
                            zout.writestr(item, ET.tostring(root, encoding="utf-8", xml_declaration=True))
                        except Exception:
                            zout.writestr(item, zin.read(item.filename))

                    else:
                        zout.writestr(item, zin.read(item.filename))

        os.replace(tmp_docx, docx_path)
    finally:
        if tmp_docx.exists():
            try:
                tmp_docx.unlink()
            except OSError:
                pass


