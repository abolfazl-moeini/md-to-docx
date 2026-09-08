"""DOCX package/relationship oracle (F04 / P0-B)."""

from __future__ import annotations

import os
import zipfile
from pathlib import Path
from typing import Dict, List, Set, Tuple
from xml.etree import ElementTree as ET

REL_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"
CT_NS = "{http://schemas.openxmlformats.org/package/2006/content-types}"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

EXPECTED_CONTENT_TYPES = {
    "word/document.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
    "word/footnotes.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml",
    "word/styles.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml",
    "word/numbering.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml",
    "word/settings.xml": "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml",
}


def _resolve_target(owner_dir: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    joined = os.path.normpath(os.path.join(owner_dir, target))
    return joined.replace("\\", "/")


def run_package_oracle(docx_path: Path) -> Tuple[bool, List[str]]:
    issues: List[str] = []
    path = Path(docx_path)
    if not path.exists():
        return False, ["DOCX does not exist"]
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            if len(names) != len(set(names)):
                issues.append("Duplicate ZIP member names in DOCX package")
            name_set = set(names)
            if "word/document.xml" not in name_set:
                issues.append("Missing word/document.xml")
            if "[Content_Types].xml" not in name_set:
                issues.append("Missing [Content_Types].xml")

            # 1. Parse [Content_Types].xml
            overrides: Dict[str, str] = {}
            defaults: Dict[str, str] = {}
            if "[Content_Types].xml" in name_set:
                try:
                    ct_root = ET.fromstring(z.read("[Content_Types].xml"))
                except ET.ParseError as e:
                    issues.append(f"Malformed [Content_Types].xml: {e}")
                    ct_root = None
                if ct_root is not None:
                    for el in ct_root:
                        if el.tag == f"{CT_NS}Default":
                            defaults[el.get("Extension", "").lower()] = el.get("ContentType") or ""
                        elif el.tag == f"{CT_NS}Override":
                            part_name = el.get("PartName", "").lstrip("/")
                            ct = el.get("ContentType") or ""
                            overrides[part_name] = ct
                            if part_name not in name_set:
                                issues.append(f"Override specifies non-existent part '{part_name}'")

            # Validate key parts have correct content types
            for key_part, expected_ct in EXPECTED_CONTENT_TYPES.items():
                if key_part in name_set:
                    actual_ct = overrides.get(key_part)
                    if actual_ct != expected_ct:
                        issues.append(
                            f"Invalid ContentType for {key_part}: expected '{expected_ct}', got '{actual_ct}'"
                        )

            # Validate that every part in the package has a ContentType (except metadata)
            for part in names:
                if part == "[Content_Types].xml" or part.endswith(".rels"):
                    continue
                ext = Path(part).suffix.lstrip(".").lower()
                part_ct = overrides.get(part) or defaults.get(ext)
                if not part_ct:
                    issues.append(f"Missing content type for part '{part}'")

            # 2. Parse all relationship (.rels) files
            part_rels_map: Dict[str, Dict[str, Tuple[str, str, str]]] = {}
            referenced_parts: Set[str] = set()
            rel_files = [n for n in names if n.endswith(".rels")]

            for rel_name in rel_files:
                try:
                    rel_root = ET.fromstring(z.read(rel_name))
                except ET.ParseError as e:
                    issues.append(f"Malformed relationship XML {rel_name}: {e}")
                    continue

                owner_dir = os.path.dirname(rel_name)
                if owner_dir.endswith("_rels"):
                    owner_dir = os.path.dirname(owner_dir)

                # Determine owner part name
                base_name = os.path.basename(rel_name)
                if base_name == ".rels":
                    owner_part = "/"  # Package level
                else:
                    stem = base_name[:-5]  # remove .rels
                    owner_part = os.path.normpath(os.path.join(owner_dir, stem)).replace("\\", "/")

                rels_for_part: Dict[str, Tuple[str, str, str]] = {}
                seen_rids: Set[str] = set()

                for rel in rel_root:
                    rid = rel.get("Id")
                    tgt = rel.get("Target") or ""
                    mode = rel.get("TargetMode")
                    rel_type = rel.get("Type") or ""

                    if not rid:
                        continue
                    if rid in seen_rids:
                        issues.append(f"Duplicate relationship Id '{rid}' in {rel_name}")
                    seen_rids.add(rid)

                    rels_for_part[rid] = (tgt, mode or "Internal", rel_type)

                    if not tgt or mode == "External":
                        continue

                    resolved = _resolve_target(owner_dir, tgt)
                    referenced_parts.add(resolved)
                    if resolved not in name_set:
                        issues.append(
                            f"Missing relationship target '{tgt}' (resolved '{resolved}') from {rel_name}"
                        )

                part_rels_map[owner_part] = rels_for_part

            # 3. Check that all XML parts only reference defined rId / r:embed / r:link
            for part in names:
                if not part.endswith(".xml") or part == "[Content_Types].xml":
                    continue
                try:
                    part_root = ET.fromstring(z.read(part))
                except ET.ParseError as e:
                    issues.append(f"Malformed XML in {part}: {e}")
                    continue

                owner_rels = part_rels_map.get(part, {})
                defined_rids = set(owner_rels.keys())

                for el in part_root.iter():
                    for attr_key, attr_val in el.attrib.items():
                        if attr_key.endswith("}id") or attr_key.endswith("}embed") or attr_key.endswith("}link"):
                            if attr_key.startswith(f"{R}") or attr_key.startswith("r:"):
                                if attr_val not in defined_rids:
                                    issues.append(
                                        f"Part '{part}' references undefined relationship Id '{attr_val}'"
                                    )

            # 4. Check document.xml structure (body, sectPr, tc ending with w:p)
            if "word/document.xml" in name_set:
                try:
                    doc_root = ET.fromstring(z.read("word/document.xml"))
                    body = doc_root.find(f"{W}body")
                    if body is None:
                        issues.append("word/document.xml has no w:body")
                    else:
                        children = list(body)
                        if not children or children[-1].tag != f"{W}sectPr":
                            issues.append("w:body last child must be w:sectPr")
                        for tc in body.iter(f"{W}tc"):
                            kids = [el for el in list(tc) if el.tag != f"{W}tcPr"]
                            if kids and kids[-1].tag != f"{W}p":
                                issues.append("Table cell does not end with w:p")
                except ET.ParseError:
                    pass

            # 5. Check orphan media
            for media in [n for n in names if n.startswith("word/media/")]:
                if media not in referenced_parts:
                    issues.append(f"Orphan media part '{media}' is not referenced by any relationship")

    except zipfile.BadZipFile as e:
        return False, [f"Corrupt ZIP: {e}"]
    return (len(issues) == 0), issues
