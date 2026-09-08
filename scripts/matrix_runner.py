#!/usr/bin/env python3
"""
Matrix runner for Persian layout quality verification (Q03, Q15, Q16).
Executes the full cross-product of 61 fixtures × 4 templates = 244 pairs,
runs independent content/structural oracle verification, and generates
matrix.csv, run.json, issues.json, reviews.json, index.html, and summary.md.
"""

import argparse
import csv
import datetime
import hashlib
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

from md_to_docx import Template, convert_markdown_to_docx
from md_to_docx.mermaid import validate_rendered_diagram_image

FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "persian_layout"
MANIFEST_PATH = FIXTURE_ROOT / "manifest.yaml"

TEMPLATES = ["purple_book", "persian_book", "persian_compact", "persian_report"]
EXPECTED_IDS = (
    ["B00"]
    + [f"C{i:02d}" for i in range(1, 5)]
    + [f"R{i:02d}" for i in range(1, 41)]
    + [f"S{i:02d}" for i in range(1, 17)]
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def validate_corpus(manifest_data: Dict[str, Any]) -> List[str]:
    """F00: 61 unique IDs, 1+4+40+16, hashes, and files must all match before conversion."""
    errors: List[str] = []
    fixtures = manifest_data.get("fixtures") or []
    ids = [f.get("id") for f in fixtures]
    if len(fixtures) != 61:
        errors.append(f"Manifest must list 61 fixtures, found {len(fixtures)}")
    if len(ids) != len(set(ids)):
        errors.append("Manifest fixture IDs are not unique")
    missing_ids = [i for i in EXPECTED_IDS if i not in ids]
    extra_ids = [i for i in ids if i not in EXPECTED_IDS]
    if missing_ids:
        errors.append(f"Missing fixture IDs: {missing_ids}")
    if extra_ids:
        errors.append(f"Unexpected fixture IDs: {extra_ids}")
    book = ROOT / "SQL_Server_DBA_Book_Chapters_1_4_FIXED.md"
    if book.exists():
        book_sha = sha256_file(book)
        expected_book = manifest_data.get("source_book_sha256")
        if expected_book and book_sha != expected_book:
            errors.append("Source book SHA-256 does not match manifest source_book_sha256")
        b00 = next((f for f in fixtures if f.get("id") == "B00"), None)
        if b00 and b00.get("sha256") != book_sha:
            errors.append("B00 sha256 must equal the source book hash")
    else:
        errors.append(f"Source book missing: {book}")
    for fix in fixtures:
        rel = fix.get("rel_path")
        path = FIXTURE_ROOT / rel if rel else None
        if path is None or not path.is_file():
            errors.append(f"Fixture file missing for {fix.get('id')}: {rel}")
            continue
        actual = sha256_file(path)
        if actual != fix.get("sha256"):
            errors.append(f"SHA mismatch for {fix.get('id')}: manifest {fix.get('sha256')} file {actual}")
    return errors


def detect_environment() -> Dict[str, Any]:
    """Detects available conversion and review tooling in the execution environment (G02)."""
    # Pandoc
    pandoc_bin = shutil.which("pandoc")
    pandoc_ver = "absent"
    if pandoc_bin:
        try:
            out = subprocess.check_output([pandoc_bin, "--version"], text=True)
            pandoc_ver = out.splitlines()[0].strip()
        except Exception:
            pandoc_ver = f"present at {pandoc_bin}"

    # Mermaid CLI (mmdc)
    local_mmdc = ROOT / "node_modules" / ".bin" / "mmdc"
    mmdc_bin = shutil.which("mmdc")
    if local_mmdc.exists():
        mmdc_status = str(local_mmdc)
    elif mmdc_bin:
        mmdc_status = str(mmdc_bin)
    else:
        mmdc_status = "absent"

    # LibreOffice (soffice)
    soffice_bin = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice_bin and Path("/Applications/LibreOffice.app/Contents/MacOS/soffice").exists():
        soffice_bin = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    soffice_status = str(soffice_bin) if soffice_bin else "absent"

    # Microsoft Word
    word_status = "absent"
    if Path("/Applications/Microsoft Word.app").exists():
        word_status = "/Applications/Microsoft Word.app"
    elif shutil.which("winword"):
        word_status = str(shutil.which("winword"))

    # Manifest SHA256
    manifest_sha = None
    if MANIFEST_PATH.exists():
        manifest_sha = hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()

    # Template hashes
    template_hashes = {}
    for tmpl in TEMPLATES:
        t_dir = ROOT / "templates" / tmpl
        cfg_file = t_dir / "config.yaml"
        shell_file = t_dir / "shell.docx"
        template_hashes[tmpl] = {
            "config_sha256": hashlib.sha256(cfg_file.read_bytes()).hexdigest() if cfg_file.exists() else None,
            "shell_sha256": hashlib.sha256(shell_file.read_bytes()).hexdigest() if shell_file.exists() else None,
        }

    return {
        "pandoc": pandoc_ver,
        "mmdc": mmdc_status,
        "soffice": soffice_status,
        "word": word_status,
        "manifest_sha256": manifest_sha,
        "template_hashes": template_hashes,
    }


def extract_docx_text(docx_path: Path, include_headers_footers: bool = False) -> str:
    """
    Extracts text from body paragraphs, tables, and footnotes in DOCX (G09 & M4).
    Excludes headers and footers by default to ensure sensitive content is in document body.
    Paragraphs are separated by newline characters to preserve structure.
    """
    parts = []
    with zipfile.ZipFile(docx_path, "r") as z:
        target_files = ["word/document.xml"]
        if "word/footnotes.xml" in z.namelist():
            target_files.append("word/footnotes.xml")
        if include_headers_footers:
            for name in z.namelist():
                if (name.startswith("word/header") or name.startswith("word/footer")) and name.endswith(".xml"):
                    target_files.append(name)

        for name in target_files:
            if name in z.namelist():
                root = ET.fromstring(z.read(name))
                for p in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                    p_texts = [
                        t.text for t in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
                        if t.text
                    ]
                    if p_texts:
                        parts.append("".join(p_texts))
    return "\n".join(parts)


def run_structural_oracle(docx_path: Path) -> Tuple[bool, List[str]]:
    """Validates ZIP integrity, XML well-formedness, relationships, and media (G12 & M5)."""
    issues = []
    if not docx_path.exists():
        return False, ["DOCX output file does not exist"]
    if docx_path.stat().st_size == 0:
        return False, ["DOCX output file is 0 bytes"]

    try:
        with zipfile.ZipFile(docx_path, "r") as z:
            names = z.namelist()
            if "word/document.xml" not in names:
                issues.append("Missing word/document.xml in DOCX archive")
            if "[Content_Types].xml" not in names:
                issues.append("Missing [Content_Types].xml in DOCX archive")

            for xml_name in ["word/document.xml", "word/_rels/document.xml.rels", "[Content_Types].xml"]:
                if xml_name in names:
                    try:
                        ET.fromstring(z.read(xml_name))
                    except ET.ParseError as e:
                        issues.append(f"Malformed XML in {xml_name}: {e}")

            # Find media files corresponding specifically to Mermaid diagrams
            mermaid_targets = set()
            if "word/document.xml" in names and "word/_rels/document.xml.rels" in names:
                try:
                    doc_tree = ET.fromstring(z.read("word/document.xml"))
                    rels_tree = ET.fromstring(z.read("word/_rels/document.xml.rels"))
                    rid_to_target = {}
                    for rel in rels_tree.iter("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
                        rid = rel.get("Id")
                        tgt = rel.get("Target")
                        if rid and tgt:
                            norm_tgt = "word/" + tgt if not tgt.startswith("word/") else tgt
                            rid_to_target[rid] = norm_tgt

                    for drawing in doc_tree.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing"):
                        docPr = drawing.find(".//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr")
                        if docPr is not None:
                            name = docPr.get("name", "")
                            descr = docPr.get("descr", "")
                            if name == "Mermaid Diagram" or descr == "mermaid":
                                blip = drawing.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip")
                                if blip is not None:
                                    embed_id = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
                                    if embed_id and embed_id in rid_to_target:
                                        mermaid_targets.add(rid_to_target[embed_id])
                except Exception:
                    pass

            # Validate all media files
            media_files = [n for n in names if n.startswith("word/media/")]
            with tempfile.TemporaryDirectory() as tmp_media_dir:
                tmp_dir_path = Path(tmp_media_dir)
                for m_name in media_files:
                    data = z.read(m_name)
                    if len(data) == 0:
                        issues.append(f"Media file {m_name} is empty (0 bytes)")
                        continue

                    tmp_file = tmp_dir_path / Path(m_name).name
                    tmp_file.write_bytes(data)

                    # Validate valid image format
                    try:
                        from PIL import Image
                        with Image.open(tmp_file) as im:
                            im.verify()
                    except Exception as img_err:
                        issues.append(f"Media file {m_name} is not a valid image: {img_err}")
                        continue

                    # Only run blank/solid-color validation on Mermaid diagrams (G12 & M5)
                    is_mermaid = (m_name in mermaid_targets) or ("diagram_" in m_name)
                    if is_mermaid:
                        if not validate_rendered_diagram_image(tmp_file):
                            issues.append(f"Media file {m_name} is a flat blank/solid-color placeholder (E01 defect)")

    except zipfile.BadZipFile as e:
        issues.append(f"Corrupt ZIP file: {e}")

    return (len(issues) == 0), issues


def extract_docx_structural_counts(docx_path: Path) -> Dict[str, int]:
    """Extracts counts of headings, code_blocks, data_tables, callouts, images, and mermaid_blocks from DOCX (G10)."""
    counts = {
        "headings": 0,
        "code_blocks": 0,
        "tables": 0,
        "callouts": 0,
        "images": 0,
        "mermaid_blocks": 0,
    }
    if not docx_path.exists():
        return counts

    try:
        with zipfile.ZipFile(docx_path, "r") as z:
            if "word/document.xml" not in z.namelist():
                return counts
            xml_parts = [z.read("word/document.xml")]
            if "word/footnotes.xml" in z.namelist():
                xml_parts.append(z.read("word/footnotes.xml"))
            doc_root = ET.fromstring(xml_parts[0])
            extra_roots = [ET.fromstring(blob) for blob in xml_parts[1:]]

            # Count headings: paragraphs with outlineLvl
            for p in doc_root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                olvl = p.find(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}outlineLvl")
                if olvl is not None:
                    counts["headings"] += 1

            # Count tables by w:tblDescription (include footnote stories)
            tbl_roots = [doc_root, *extra_roots]
            for tbl_root in tbl_roots:
                for tbl in tbl_root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl"):
                    desc = tbl.find(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblDescription")
                    if desc is not None:
                        val = desc.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val")
                        if val == "data_table":
                            counts["tables"] += 1
                        elif val == "code_block":
                            counts["code_blocks"] += 1
                        elif val == "callout":
                            counts["callouts"] += 1
                        elif val == "heading_badge":
                            pass
                        else:
                            counts["tables"] += 1
                    else:
                        counts["tables"] += 1

            # Count images & mermaid blocks (body + footnotes)
            for img_root in tbl_roots:
                for drawing in img_root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing"):
                    docPr = drawing.find(".//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr")
                    if docPr is not None:
                        name = docPr.get("name", "")
                        descr = docPr.get("descr", "")
                        if name == "Mermaid Diagram" or descr == "mermaid":
                            counts["mermaid_blocks"] += 1
                        else:
                            counts["images"] += 1
    except Exception:
        pass

    return counts


def run_content_oracle(docx_path: Path, manifest_entry: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Checks sensitive strings and structural counts against manifest expectations (G09, G10, M2, M4).
    """
    issues = []
    try:
        doc_text = extract_docx_text(docx_path)
    except Exception as e:
        return False, [f"Failed to extract document text: {e}"]

    # 1. Sensitive strings check
    for s_str in manifest_entry.get("sensitive_strings", []):
        if s_str not in doc_text:
            issues.append(f"Missing sensitive string in document: '{s_str}'")

    # 2. Structural counts check (G10 & M2)
    exp_counts = manifest_entry.get("counts")
    if exp_counts and docx_path.exists():
        try:
            actual_counts = extract_docx_structural_counts(docx_path)
            for k in ("headings", "code_blocks", "tables", "callouts", "mermaid_blocks", "images"):
                if k in exp_counts and actual_counts[k] != exp_counts[k]:
                    label = "Data table" if k == "tables" else k.replace("_", " ").capitalize()
                    issues.append(f"{label} count mismatch: expected {exp_counts[k]}, found {actual_counts[k]}")
        except Exception as e:
            issues.append(f"Error checking structural counts: {e}")

    return (len(issues) == 0), issues


def _parse_warning_spec(item: str) -> Tuple[str, str]:
    """Split a warning into (code, identity). Identity is the @... token or trailing detail."""
    raw = (item or "").strip()
    if " @ " in raw:
        left, right = raw.split(" @ ", 1)
        ident = right.split(" at ")[0].strip()
        code = left.split(":", 1)[0].strip()
        return code.lower(), ident.lower()
    if ":" in raw:
        code, rest = raw.split(":", 1)
        return code.strip().lower(), rest.strip().lower()
    return raw.lower(), ""


def verify_warnings(actual_warnings: List[str], expected_warnings: Optional[List[str]]) -> List[str]:
    """Match expected warnings by code AND source identity (F07). Absent list means none allowed."""
    issues = []
    expected = list(expected_warnings or [])
    matched_indices = set()
    for exp in expected:
        exp_code, exp_ident = _parse_warning_spec(exp)
        match_found = False
        for idx, act in enumerate(actual_warnings):
            if idx in matched_indices:
                continue
            act_lower = act.lower()
            act_code, act_ident = _parse_warning_spec(act)
            code_ok = bool(exp_code) and (
                exp_code == act_code
                or exp_code in act_lower
                or (
                    "caption_without_image" in exp_code
                    and ("caption without" in act_lower or "standalone caption" in act_lower)
                )
            )
            if not code_ok:
                continue
            if exp_ident:
                if exp_ident not in act_lower and exp_ident not in act_ident:
                    continue
            matched_indices.add(idx)
            match_found = True
            break
        if not match_found:
            issues.append(f"Missing expected warning: '{exp}'")

    for idx, act in enumerate(actual_warnings):
        if idx not in matched_indices:
            issues.append(f"Unexpected warning: '{act}'")

    return issues


def check_mermaid_label_sidecars(md_text: str, media_dir: Path) -> List[str]:
    """Require a same-process SVG sidecar and source labels for every Mermaid fence (V2)."""
    from md_to_docx.mermaid import (
        extract_mermaid_blocks,
        extract_mermaid_source_labels,
        validate_mermaid_svg_labels,
    )

    issues: List[str] = []
    blocks = extract_mermaid_blocks(md_text)
    for idx, block in enumerate(blocks):
        expected_svg = Path(media_dir) / f"diagram_{idx + 1:03d}.svg"
        if not expected_svg.is_file() or expected_svg.stat().st_size == 0:
            issues.append(
                f"Missing Mermaid SVG sidecar for diagram {idx + 1}: expected {expected_svg.name}"
            )
            continue
        expected_labels = extract_mermaid_source_labels(block.code)
        ok_lab, missing = validate_mermaid_svg_labels(expected_svg, expected_labels)
        if not ok_lab:
            issues.append(f"Mermaid SVG {expected_svg.name} missing labels: {missing}")
    return issues


def execute_matrix_pair(
    fixture: Dict[str, Any],
    template_name: str,
    output_base_dir: Path,
    render_pages: bool = False,
) -> Dict[str, Any]:
    f_id = fixture["id"]
    in_path = FIXTURE_ROOT / fixture["rel_path"]
    pair_dir = output_base_dir / f_id / template_name
    pair_dir.mkdir(parents=True, exist_ok=True)
    out_docx = pair_dir / "output.docx"
    media_dir = pair_dir / "media"

    record = {
        "fixture_id": f_id,
        "template": template_name,
        "input_path": str(in_path),
        "output_path": str(out_docx),
        "status": "pending",
        "conversion_time_sec": 0.0,
        "file_size_bytes": 0,
        "structural_pass": False,
        "content_pass": False,
        "warnings_pass": False,
        "issues": [],
        "warnings": []
    }

    t0 = time.time()
    try:
        convert_markdown_to_docx(
            input_path=in_path,
            output_path=out_docx,
            template=template_name,
            media_dir=media_dir,
            overwrite=True,
            warnings=record["warnings"],
        )
        record["conversion_time_sec"] = round(time.time() - t0, 3)
        record["file_size_bytes"] = out_docx.stat().st_size

        # Run oracles
        struct_ok, struct_issues = run_structural_oracle(out_docx)
        record["structural_pass"] = struct_ok
        record["issues"].extend(struct_issues)

        content_ok, content_issues = run_content_oracle(out_docx, fixture)
        record["content_pass"] = content_ok
        record["issues"].extend(content_issues)

        from package_oracle import run_package_oracle
        from semantic_oracle import run_semantic_oracle
        pkg_ok, pkg_issues = run_package_oracle(out_docx)
        record["package_pass"] = pkg_ok
        record["issues"].extend(pkg_issues)
        md_text = in_path.read_text(encoding="utf-8")
        sem_ok, sem_issues = run_semantic_oracle(md_text, out_docx, base_dir=in_path.parent)
        record["semantic_pass"] = sem_ok
        record["issues"].extend(sem_issues)

        mermaid_label_issues = check_mermaid_label_sidecars(md_text, media_dir)
        record["mermaid_label_pass"] = (len(mermaid_label_issues) == 0)
        record["issues"].extend(mermaid_label_issues)

        # Extract actual structural counts (G10)
        actual_counts = extract_docx_structural_counts(out_docx)
        record["counts"] = actual_counts

        # Check warnings against expected_warnings (G11)
        expected_w = fixture.get("expected_warnings")
        record["expected_warnings"] = expected_w or []
        warn_issues = verify_warnings(record["warnings"], expected_w)
        record["warnings_pass"] = (len(warn_issues) == 0)
        record["issues"].extend(warn_issues)
        record["unexpected_warnings"] = [
            iss.split("Unexpected warning: '", 1)[1].rstrip("'")
            for iss in warn_issues if iss.startswith("Unexpected warning: '")
        ]

        # Render pages (V3)
        if render_pages:
            from scripts.page_render import find_soffice, render_docx_pages
            soffice = find_soffice()
            if not soffice:
                record["render_status"] = "blocked"
                record["issues"].append("Page rendering blocked: LibreOffice soffice not found in PATH or environment")
            else:
                render_out = pair_dir / "render"
                render_res = render_docx_pages(out_docx, render_out)
                record["render_executable_found"] = render_res.get("executable_found", False)
                record["render_ran"] = render_res.get("render_ran", False)
                record["render_pdf"] = render_res.get("pdf")
                record["render_pages"] = render_res.get("pages", [])
                record["render_page_count"] = len(render_res.get("pages", []))
                if render_res.get("error"):
                    record["render_status"] = "fail"
                    record["issues"].append(f"Page render error: {render_res['error']}")
                elif render_res.get("render_ran") and render_res.get("pages"):
                    record["render_status"] = "done"
                else:
                    record["render_status"] = "fail"
                    record["issues"].append("Page render produced no pages")
        else:
            record["render_status"] = "not_run"

        conversion_ok = out_docx.exists() and out_docx.stat().st_size > 0
        record["conversion_success"] = conversion_ok
        record["review_status"] = "pending"
        if (
            conversion_ok
            and struct_ok
            and content_ok
            and record["warnings_pass"]
            and record.get("package_pass", True)
            and record.get("semantic_pass", True)
            and record.get("mermaid_label_pass", True)
        ):
            if render_pages and record["render_status"] == "blocked":
                record["status"] = "blocked"
            elif render_pages and record["render_status"] == "fail":
                record["status"] = "fail"
            else:
                record["status"] = "pass"
        else:
            record["status"] = "fail"

    except Exception as e:
        record["conversion_time_sec"] = round(time.time() - t0, 3)
        record["status"] = "error"
        record["issues"].append(f"Conversion exception: {str(e)}")

    report_json = pair_dir / "report.json"
    with open(report_json, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    return record


def _issue_severity(status: str, message: str) -> str:
    msg = (message or "").lower()
    if status == "error" or status == "blocked":
        return "severe"
    blocking_tokens = (
        "missing paragraph",
        "missing heading",
        "missing code",
        "table cell mismatch",
        "missing relationship",
        "missing table",
        "count mismatch",
        "sha mismatch",
        "corrupt zip",
        "malformed",
    )
    if any(tok in msg for tok in blocking_tokens):
        return "blocking"
    return "warning"


def generate_matrix_reports(results: List[Dict[str, Any]], out_dir: Path, run_id: str, elapsed: float):
    env_info = detect_environment()
    used_templates = []
    for r in results:
        if r["template"] not in used_templates:
            used_templates.append(r["template"])
    soffice_present = env_info["soffice"] != "absent"
    word_present = env_info["word"] != "absent"
    render_ran = any(r.get("render_status") == "done" for r in results)
    soffice_note = (
        "executable present"
        if soffice_present
        else "absent"
    )
    if soffice_present and not render_ran:
        soffice_note += "; render not executed this run"
    word_note = "executable present" if word_present else "absent"
    snapshot = {
        "renderer_py_sha256": sha256_file(ROOT / "src" / "md_to_docx" / "renderer.py"),
        "pandoc_json_py_sha256": sha256_file(ROOT / "src" / "md_to_docx" / "pandoc_json.py"),
        "mermaid_py_sha256": sha256_file(ROOT / "src" / "md_to_docx" / "mermaid.py"),
        "matrix_runner_py_sha256": sha256_file(ROOT / "scripts" / "matrix_runner.py"),
        "manifest_sha256": env_info.get("manifest_sha256"),
    }

    # 1. matrix.csv (G10 & G11: Structural counts and warning accounting columns)
    csv_path = out_dir / "matrix.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "fixture_id", "template", "status", "time_sec", "size_bytes",
            "structural_pass", "content_pass", "warnings_pass",
            "headings", "code_blocks", "data_tables", "callouts", "images", "mermaid_blocks",
            "expected_warnings_count", "actual_warnings_count", "unexpected_warnings_count",
            "issues_count", "issues"
        ])
        for r in results:
            c = r.get("counts", {})
            writer.writerow([
                r["fixture_id"],
                r["template"],
                r["status"],
                r["conversion_time_sec"],
                r["file_size_bytes"],
                r["structural_pass"],
                r["content_pass"],
                r.get("warnings_pass", True),
                c.get("headings", 0),
                c.get("code_blocks", 0),
                c.get("tables", 0),
                c.get("callouts", 0),
                c.get("images", 0),
                c.get("mermaid_blocks", 0),
                len(r.get("expected_warnings", [])),
                len(r.get("warnings", [])),
                len(r.get("unexpected_warnings", [])),
                len(r["issues"]),
                "; ".join(r["issues"])
            ])

    # 2. run.json (G02)
    run_meta = {
        "run_id": run_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "total_pairs": len(results),
        "total_elapsed_sec": round(elapsed, 2),
        "conversions_passed": sum(1 for r in results if r["status"] == "pass"),
        "conversions_failed": sum(1 for r in results if r["status"] == "fail"),
        "conversions_error": sum(1 for r in results if r["status"] == "error"),
        "structural_oracles_passed": sum(1 for r in results if r.get("structural_pass")),
        "content_oracles_passed": sum(1 for r in results if r.get("content_pass")),
        "visual_pages_reviewed": 0,
        "environment": env_info,
        "templates": used_templates,
        "python_version": sys.version,
        "code_snapshot": snapshot,
        "render_executed": render_ran,
        "soffice_status": soffice_note,
        "word_status": word_note,
    }
    with open(out_dir / "run.json", "w", encoding="utf-8") as f:
        json.dump(run_meta, f, ensure_ascii=False, indent=2)

    # 3. issues.json
    all_issues = []
    for r in results:
        for iss in r["issues"]:
            all_issues.append({
                "fixture_id": r["fixture_id"],
                "template": r["template"],
                "severity": _issue_severity(r["status"], iss),
                "message": iss
            })
    with open(out_dir / "issues.json", "w", encoding="utf-8") as f:
        json.dump(all_issues, f, ensure_ascii=False, indent=2)

    # 4. reviews.json (G01: Honest reporting, pending when visual review not performed)
    reviews = []
    has_soffice = env_info["soffice"] != "absent"
    for r in results:
        reviews.append({
            "fixture_id": r["fixture_id"],
            "template": r["template"],
            "status": "pending",
            "reviewed_by": "none",
            "pages_reviewed": 0,
            "notes": (
                "Visual page review pending: LibreOffice executable is absent."
                if not has_soffice
                else "Visual page review pending: soffice was detected but page render/review was not executed."
            ),
            "timestamp": datetime.datetime.now().isoformat(),
        })
    with open(out_dir / "reviews.json", "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)

    # 5. summary.md (G01 & G02: 3 distinct metrics + environment limitations)
    summary_md = f"""# گزارش جامع اجرای ماتریس تبدیل فارسی (Matrix Summary)

- **شناسه اجرا:** `{run_id}`
- **زمان ثبت:** {run_meta['timestamp']}
- **کل موارد (Pairs):** {len(results)}
- **تبدیل‌های موفق (Conversions Passed):** {run_meta['conversions_passed']}
- **اوراکل‌های ساختاری و محتوایی (Oracles Passed):** {sum(1 for r in results if r.get('structural_pass') and r.get('content_pass'))}
- **صفحات مرورشدهٔ بصری (Visual Page Reviews):** 0 (pending)
- **قالب‌های این اجرا:** {', '.join(f'`{t}`' for t in used_templates)}
- **ناموفق (Fail):** {run_meta['conversions_failed']}
- **خطای اجرایی (Error):** {run_meta['conversions_error']}
- **مدت زمان کل:** {round(elapsed, 2)} ثانیه

## وضعیت ابزارها و محدودیت‌های محیط اجرا (Environment & Limitations)

- **Pandoc:** {env_info['pandoc']}
- **Mermaid CLI (mmdc):** {env_info['mmdc']}
- **LibreOffice (soffice):** `{env_info['soffice']}` — {soffice_note}
- **Microsoft Word:** `{env_info['word']}` — {word_note}; visual review is a separate human/AI step
- **Manifest SHA256:** `{env_info['manifest_sha256']}`

## وضعیت قالب‌ها

| نام قالب | اندازه صفحه | کل تبدیل‌ها | موفق | ناموفق |
| :--- | :--- | :--- | :--- | :--- |
| `purple_book` | A4 | {sum(1 for r in results if r['template'] == 'purple_book')} | {sum(1 for r in results if r['template'] == 'purple_book' and r['status'] == 'pass')} | {sum(1 for r in results if r['template'] == 'purple_book' and r['status'] != 'pass')} |
| `persian_book` | A4 | {sum(1 for r in results if r['template'] == 'persian_book')} | {sum(1 for r in results if r['template'] == 'persian_book' and r['status'] == 'pass')} | {sum(1 for r in results if r['template'] == 'persian_book' and r['status'] != 'pass')} |
| `persian_compact` | A5 | {sum(1 for r in results if r['template'] == 'persian_compact')} | {sum(1 for r in results if r['template'] == 'persian_compact' and r['status'] == 'pass')} | {sum(1 for r in results if r['template'] == 'persian_compact' and r['status'] != 'pass')} |
| `persian_report` | Letter | {sum(1 for r in results if r['template'] == 'persian_report')} | {sum(1 for r in results if r['template'] == 'persian_report' and r['status'] == 'pass')} | {sum(1 for r in results if r['template'] == 'persian_report' and r['status'] != 'pass')} |
"""
    with open(out_dir / "summary.md", "w", encoding="utf-8") as f:
        f.write(summary_md)

    # 6. index.html
    html_content = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>گزارش ماتریس Persian Layout - {run_id}</title>
    <style>
        body {{ font-family: Tahoma, sans-serif; background: #f8f9fa; padding: 20px; color: #212529; }}
        h1, h2 {{ color: #17324d; }}
        .summary {{ display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }}
        .card {{ background: #fff; padding: 15px 25px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); }}
        .badge-pass {{ background: #28a745; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: bold; }}
        .badge-fail {{ background: #dc3545; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: bold; }}
        .badge-error {{ background: #ffc107; color: #000; padding: 3px 8px; border-radius: 4px; font-weight: bold; }}
        .badge-pending {{ background: #6c757d; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.08); }}
        th, td {{ padding: 10px 14px; border-bottom: 1px solid #dee2e6; text-align: right; }}
        th {{ background: #17324d; color: #fff; }}
        tr:hover {{ background: #f1f3f5; }}
    </style>
</head>
<body>
    <h1>داشبورد نتایج ماتریس تبدیل فارسی ({len(results)} ترکیب)</h1>
    <div class="summary">
        <div class="card"><strong>شناسه اجرا:</strong> {run_id}</div>
        <div class="card"><strong>کل موارد:</strong> {len(results)}</div>
        <div class="card"><strong>تبدیل موفق:</strong> <span style="color:#28a745">{run_meta['conversions_passed']}</span></div>
        <div class="card"><strong>اوراکل پاس‌شده:</strong> <span style="color:#28a745">{sum(1 for r in results if r.get('structural_pass') and r.get('content_pass'))}</span></div>
        <div class="card"><strong>مرور بصری صفحات:</strong> <span class="badge-pending">0 (pending)</span></div>
        <div class="card"><strong>مدت زمان:</strong> {round(elapsed, 1)}s</div>
    </div>
    <table>
        <thead>
            <tr>
                <th>شناسه فیچر</th>
                <th>قالب</th>
                <th>وضعیت</th>
                <th>زمان (ثانیه)</th>
                <th>حجم فایل</th>
                <th>ساختار DOCX</th>
                <th>صحت محتوا</th>
                <th>هشدارها</th>
                <th>خطاها / هشدارها</th>
            </tr>
        </thead>
        <tbody>
"""
    for r in results:
        b_class = "badge-pass" if r["status"] == "pass" else ("badge-fail" if r["status"] == "fail" else "badge-error")
        issues_str = "<br>".join(html.escape(str(i)) for i in r["issues"]) if r["issues"] else "-"
        html_content += f"""            <tr>
                <td><strong>{html.escape(str(r['fixture_id']))}</strong></td>
                <td>{html.escape(str(r['template']))}</td>
                <td><span class="{b_class}">{html.escape(str(r['status']))}</span></td>
                <td>{r['conversion_time_sec']}s</td>
                <td>{r['file_size_bytes']:,} B</td>
                <td>{'✓' if r['structural_pass'] else '✗'}</td>
                <td>{'✓' if r['content_pass'] else '✗'}</td>
                <td>{'✓' if r.get('warnings_pass') else '✗'}</td>
                <td style="color:#dc3545; font-size:12px;">{issues_str}</td>
            </tr>\n"""
    html_content += """        </tbody>
    </table>
</body>
</html>
"""
    with open(out_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(html_content)


def main():
    parser = argparse.ArgumentParser(description="Persian Layout Quality Matrix Runner")
    parser.add_argument("--run-id", default=None, help="Custom run identifier")
    parser.add_argument("--fixtures", default=None, help="Comma-separated fixture IDs (e.g. S01,S02,R01)")
    parser.add_argument("--templates", default=None, help="Comma-separated template names")
    parser.add_argument("--output-dir", default=None, help="Base output directory")
    parser.add_argument(
        "--overwrite-run",
        action="store_true",
        help="Allow writing into a non-empty output directory (default: refuse collision)",
    )
    parser.add_argument(
        "--render-pages",
        action="store_true",
        default=False,
        help="Render DOCX pages to PDF and PNG via LibreOffice (default: off)",
    )
    args = parser.parse_args()

    run_id = args.run_id or datetime.datetime.now().strftime("run_%Y%m%d_%H%M%S")
    out_dir = Path(args.output_dir) if args.output_dir else ROOT / "artifacts" / "persian-layout" / run_id
    if out_dir.exists() and any(out_dir.iterdir()) and not args.overwrite_run:
        print(f"Output directory already exists and is not empty: {out_dir}", file=sys.stderr)
        print("Pass --overwrite-run to reuse it, or choose a new --run-id / --output-dir.", file=sys.stderr)
        sys.exit(2)
    out_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MD2DOCX_MERMAID_HEALTH_FILE", str(out_dir / "runtime-health.json"))

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest_data = yaml.safe_load(f)

    corpus_errors = validate_corpus(manifest_data)
    if corpus_errors:
        print("Corpus validation failed:", file=sys.stderr)
        for err in corpus_errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(2)

    all_fixtures = manifest_data["fixtures"]
    known_ids = {f["id"] for f in all_fixtures}
    if args.fixtures:
        filter_ids = [x.strip() for x in args.fixtures.split(",") if x.strip()]
        unknown = [i for i in filter_ids if i not in known_ids]
        if unknown:
            print(f"Unknown fixture ID(s): {', '.join(unknown)}", file=sys.stderr)
            sys.exit(2)
        if not filter_ids:
            print("No fixture IDs given after --fixtures", file=sys.stderr)
            sys.exit(2)
        all_fixtures = [f for f in all_fixtures if f["id"] in set(filter_ids)]

    active_templates = TEMPLATES
    if args.templates:
        filter_tmpls = [x.strip() for x in args.templates.split(",") if x.strip()]
        unknown_t = [t for t in filter_tmpls if t not in TEMPLATES]
        if unknown_t:
            print(f"Unknown template(s): {', '.join(unknown_t)}", file=sys.stderr)
            sys.exit(2)
        active_templates = [t for t in TEMPLATES if t in set(filter_tmpls)]

    total_pairs = len(all_fixtures) * len(active_templates)
    if total_pairs == 0:
        print("No conversion pairs selected.", file=sys.stderr)
        sys.exit(2)
    print(f"Starting Matrix Runner: {total_pairs} pairs ({len(all_fixtures)} fixtures × {len(active_templates)} templates)")
    print(f"Artifacts output directory: {out_dir}")

    results = []
    t_start = time.time()

    pair_idx = 0
    for fix in all_fixtures:
        for tmpl in active_templates:
            pair_idx += 1
            print(f"[{pair_idx}/{total_pairs}] Running {fix['id']} with {tmpl}...", end=" ", flush=True)
            res = execute_matrix_pair(fix, tmpl, out_dir, render_pages=args.render_pages)
            print(f"{res['status'].upper()} ({res['conversion_time_sec']}s)")
            results.append(res)

    t_elapsed = time.time() - t_start
    print(f"\nCompleted {len(results)} pairs in {t_elapsed:.2f} seconds.")
    print("Writing matrix reports (CSV, JSON, Markdown, HTML)...")
    generate_matrix_reports(results, out_dir, run_id, t_elapsed)
    print(f"Reports saved to {out_dir}")
    failed = sum(1 for r in results if r["status"] in ("fail", "error", "blocked"))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
