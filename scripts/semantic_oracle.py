"""Independent Markdown AST vs DOCX semantic oracle (F03 / P0-A)."""

from __future__ import annotations

import hashlib
import os
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

from md_to_docx.pipeline import run_pandoc_ast
from md_to_docx.admonitions import preprocess_admonitions
from md_to_docx.pandoc_json import inlines_to_text, format_ordered_marker


def _visible_inlines(inlines: Any) -> List[Dict[str, Any]]:
    """Drop Note/Math/Image so body text is not concatenated with footnote, TeX or image source."""
    kept: List[Dict[str, Any]] = []
    if not isinstance(inlines, list):
        return kept
    for inl in inlines:
        if not isinstance(inl, dict):
            continue
        t = inl.get("t")
        if t in ("Note", "Math", "Image"):
            continue
        c = inl.get("c")
        if t in ("Emph", "Strong", "Strikeout", "Superscript", "Subscript", "Underline", "SmallCaps") and isinstance(c, list):
            kept.extend(_visible_inlines(c))
        elif t in ("Link", "Span", "Quoted") and isinstance(c, list) and len(c) > 1 and isinstance(c[1], list):
            kept.append({"t": t, "c": [c[0], _visible_inlines(c[1]), *c[2:]]})
        else:
            kept.append(inl)
    return kept


def _inlines_to_text_oracle(inlines: Any, is_rtl: bool = True) -> str:
    parts = []
    if not isinstance(inlines, list):
        return ""
    for inl in inlines:
        if not isinstance(inl, dict):
            if isinstance(inl, str):
                parts.append(inl)
            continue
        t = inl.get("t")
        c = inl.get("c")
        if t == "Str":
            parts.append(str(c))
        elif t in ("Space", "SoftBreak"):
            parts.append(" ")
        elif t == "LineBreak":
            parts.append("\n")
        elif t in ("Emph", "Strong", "Strikeout", "Superscript", "Subscript", "Underline", "SmallCaps"):
            parts.append(_inlines_to_text_oracle(c or [], is_rtl))
        elif t == "Code":
            parts.append(c[1] if isinstance(c, list) and len(c) > 1 else str(c))
        elif t == "Quoted":
            qtype = c[0].get("t") if isinstance(c, list) and c and isinstance(c[0], dict) else "DoubleQuote"
            inner = c[1] if isinstance(c, list) and len(c) > 1 and isinstance(c[1], list) else []
            if is_rtl:
                left, right = ("«", "»") if qtype != "SingleQuote" else ("‹", "›")
            else:
                left, right = ("\u201c", "\u201d") if qtype != "SingleQuote" else ("\u2018", "\u2019")
            parts.append(f"{left}{_inlines_to_text_oracle(inner, is_rtl)}{right}")
        elif t in ("Link", "Span"):
            if isinstance(c, list) and len(c) > 1 and isinstance(c[1], list):
                parts.append(_inlines_to_text_oracle(c[1], is_rtl))
            elif isinstance(c, list) and len(c) > 0 and isinstance(c[0], list):
                parts.append(_inlines_to_text_oracle(c[0], is_rtl))
        elif t == "Image":
            pass
        elif t == "RawInline":
            parts.append(c[1] if isinstance(c, list) and len(c) > 1 else str(c))
        elif t == "Math":
            parts.append(c[1] if isinstance(c, list) and len(c) > 1 else str(c))
        elif isinstance(c, str):
            parts.append(c)
    return "".join(parts)


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"


class SemanticStory:
    def __init__(self, name: str = "body"):
        self.name = name
        self.paragraphs: List[str] = []
        self.headings: List[Dict[str, Any]] = []
        self.tables: List[List[List[str]]] = []
        self.codes: List[str] = []
        self.links: List[Dict[str, str]] = []
        self.images: List[Dict[str, str]] = []
        self.math: List[Dict[str, str]] = []


def _walk_inlines_story(
    inlines: Any,
    story: SemanticStory,
    footnote_stories: List[SemanticStory],
) -> None:
    if not isinstance(inlines, list):
        return
    for inl in inlines:
        if not isinstance(inl, dict):
            continue
        t = inl.get("t")
        c = inl.get("c")
        if t == "Link" and isinstance(c, list) and len(c) > 2:
            target = c[2][0] if isinstance(c[2], (list, tuple)) and c[2] else ""
            txt = _inlines_to_text_oracle(_visible_inlines(c[1] if isinstance(c[1], list) else []))
            if target:
                story.links.append({"target": str(target), "text": txt.strip()})
            if isinstance(c[1], list):
                _walk_inlines_story(c[1], story, footnote_stories)
        elif t == "Image" and isinstance(c, list) and len(c) > 2:
            src = c[2][0] if isinstance(c[2], (list, tuple)) and c[2] else ""
            if src:
                story.images.append({"src": str(src)})
        elif t == "Math" and isinstance(c, list) and len(c) > 1:
            tex = c[1] if isinstance(c[1], str) else ""
            story.math.append({"tex": tex})
        elif t == "Note" and isinstance(c, list):
            fn_story = SemanticStory(name=f"footnote_{len(footnote_stories) + 1}")
            for child in c:
                if isinstance(child, dict):
                    _walk_expect_block(child, fn_story, footnote_stories)
            footnote_stories.append(fn_story)
        elif t in ("Emph", "Strong", "Strikeout", "Superscript", "Subscript", "Underline", "SmallCaps") and isinstance(c, list):
            _walk_inlines_story(c, story, footnote_stories)
        elif t in ("Span", "Quoted", "Cite") and isinstance(c, list) and len(c) > 1 and isinstance(c[1], list):
            _walk_inlines_story(c[1], story, footnote_stories)


def _walk_expect_block(
    block: Dict[str, Any],
    story: SemanticStory,
    footnote_stories: List[SemanticStory],
) -> None:
    t = block.get("t")
    c = block.get("c")
    if t is None:
        raise ValueError(f"Malformed AST block: missing 't' in {block}")

    if t == "Header":
        level = c[0] if isinstance(c, list) and c else 1
        inlines = c[2] if isinstance(c, list) and len(c) > 2 else []
        text = _inlines_to_text_oracle(inlines).strip()
        story.headings.append({"level": level, "text": text})
        story.paragraphs.append(text)
        _walk_inlines_story(inlines, story, footnote_stories)
    elif t in ("Para", "Plain"):
        inls = c or []
        kinds = [i.get("t") for i in inls if isinstance(i, dict)]
        image_only = bool(kinds) and all(k in ("Image", "Space", "SoftBreak") for k in kinds)
        if not image_only:
            text = _inlines_to_text_oracle(_visible_inlines(inls)).strip()
            if text:
                story.paragraphs.append(text)
        _walk_inlines_story(inls, story, footnote_stories)
    elif t == "CodeBlock":
        attr = c[0] if isinstance(c, list) and c else []
        classes = attr[1] if isinstance(attr, list) and len(attr) > 1 else []
        code = c[1] if isinstance(c, list) and len(c) > 1 else ""
        if "mermaid" in (classes or []):
            story.images.append({"src": "mermaid"})
        else:
            story.codes.append(code.replace("\r\n", "\n").rstrip("\n"))
    elif t == "Table" and isinstance(c, list):
        grid: List[List[str]] = []
        thead = c[3] if len(c) > 3 else []
        tbodies = c[4] if len(c) > 4 else []
        head_rows = thead[1] if isinstance(thead, list) and len(thead) > 1 else []
        body_rows = []
        if isinstance(tbodies, list):
            for body in tbodies:
                if isinstance(body, list) and len(body) > 2 and isinstance(body[2], list):
                    body_rows.extend(body[2])
                if isinstance(body, list) and len(body) > 3 and isinstance(body[3], list):
                    body_rows.extend(body[3])
        for row in list(head_rows) + list(body_rows):
            cells = []
            if isinstance(row, list) and len(row) > 1 and isinstance(row[1], list):
                for cell in row[1]:
                    if isinstance(cell, list) and len(cell) > 4 and isinstance(cell[4], list):
                        cell_bits = []
                        for b in cell[4]:
                            if not isinstance(b, dict):
                                continue
                            temp_s = SemanticStory()
                            _walk_expect_block(b, temp_s, footnote_stories)
                            cell_bits.extend(temp_s.paragraphs)
                            story.images.extend(temp_s.images)
                            story.codes.extend(temp_s.codes)
                            story.links.extend(temp_s.links)
                            story.math.extend(temp_s.math)
                        cells.append(" ".join(x for x in cell_bits if x).strip())
            if cells:
                grid.append(cells)
        if grid:
            story.tables.append(grid)
    elif t == "Div" and isinstance(c, list) and len(c) > 1:
        for child in c[1] if isinstance(c[1], list) else []:
            if isinstance(child, dict):
                _walk_expect_block(child, story, footnote_stories)
    elif t == "BlockQuote" and isinstance(c, list):
        for child in c:
            if isinstance(child, dict):
                _walk_expect_block(child, story, footnote_stories)
    elif t == "BulletList" and isinstance(c, list):
        for item in c:
            if isinstance(item, list):
                for blk_idx, child in enumerate(item):
                    if isinstance(child, dict):
                        if blk_idx == 0 and child.get("t") in ("Para", "Plain"):
                            inls = child.get("c") or []
                            text = _inlines_to_text_oracle(_visible_inlines(inls)).strip()
                            if text:
                                story.paragraphs.append(f"- {text}")
                            _walk_inlines_story(inls, story, footnote_stories)
                        else:
                            _walk_expect_block(child, story, footnote_stories)
    elif t == "OrderedList" and isinstance(c, list) and len(c) > 1:
        attr = c[0] if c else [1, {"t": "Decimal"}, {"t": "Period"}]
        items = c[1] if len(c) > 1 else []
        start = attr[0] if isinstance(attr, list) and attr else 1
        try:
            start = int(start)
        except (TypeError, ValueError):
            start = 1
        style = attr[1].get("t", "Decimal") if len(attr) > 1 and isinstance(attr[1], dict) else "Decimal"
        delim = attr[2].get("t", "Period") if len(attr) > 2 and isinstance(attr[2], dict) else "Period"
        for item_idx, item in enumerate(items):
            if isinstance(item, list):
                num = start + item_idx
                sample_text = _inlines_to_text_oracle(item[0].get("c", []) if item and isinstance(item[0], dict) else [])
                is_rtl = any("\u0600" <= ch <= "\u06ff" for ch in sample_text)
                marker = format_ordered_marker(num, style, delim, is_rtl)
                for blk_idx, child in enumerate(item):
                    if isinstance(child, dict):
                        if blk_idx == 0 and child.get("t") in ("Para", "Plain"):
                            inls = child.get("c") or []
                            text = _inlines_to_text_oracle(_visible_inlines(inls)).strip()
                            if text:
                                story.paragraphs.append(f"{marker} {text}")
                            _walk_inlines_story(inls, story, footnote_stories)
                        else:
                            _walk_expect_block(child, story, footnote_stories)
    elif t == "DefinitionList" and isinstance(c, list):
        for item in c:
            if isinstance(item, list) and len(item) > 1:
                _walk_inlines_story(item[0], story, footnote_stories)
                term = _inlines_to_text_oracle(item[0] if isinstance(item[0], list) else []).strip()
                if term:
                    story.paragraphs.append(term)
                for def_blocks in item[1]:
                    if isinstance(def_blocks, list):
                        for child in def_blocks:
                            if isinstance(child, dict):
                                _walk_expect_block(child, story, footnote_stories)
    elif t == "Figure" and isinstance(c, list) and len(c) > 2 and isinstance(c[2], list):
        for child in c[2]:
            if isinstance(child, dict):
                _walk_expect_block(child, story, footnote_stories)
    elif t == "RawBlock":
        raw_text = c[1] if isinstance(c, list) and len(c) > 1 else str(c)
        stripped = raw_text.strip()
        if stripped.startswith("<!--") and stripped.endswith("-->"):
            pass
        elif stripped in ("\\pagebreak", "\\newpage", "<!-- pagebreak -->", "<!-- newpage -->", "<hr>", "<hr/>", "<hr />"):
            pass
        elif "<w:br" in stripped and 'type="page"' in stripped:
            pass
        else:
            if stripped:
                story.paragraphs.append(raw_text.strip())
    elif t in ("HorizontalRule", "Null"):
        pass
    else:
        raise ValueError(f"Unrecognized AST block type '{t}'")


def expected_from_markdown(markdown: str) -> Dict[str, Any]:
    if not isinstance(markdown, str):
        raise ValueError("Markdown input must be a string")
    admon_md = preprocess_admonitions(markdown)
    ast = run_pandoc_ast(admon_md)
    if not isinstance(ast, dict) or "blocks" not in ast:
        raise ValueError("Invalid pandoc AST output")

    body_story = SemanticStory(name="body")
    footnote_stories: List[SemanticStory] = []

    meta = ast.get("meta") or {}
    toc_node = meta.get("toc") if isinstance(meta, dict) else None
    toc_val = ""
    if isinstance(toc_node, dict):
        t_meta = toc_node.get("t")
        c_meta = toc_node.get("c")
        if t_meta == "MetaString":
            toc_val = str(c_meta or "").strip().lower()
        elif t_meta == "MetaBool":
            toc_val = "true" if c_meta else "false"
        elif t_meta == "MetaInlines" and isinstance(c_meta, list):
            toc_val = _inlines_to_text_oracle(c_meta).strip().lower()
    elif isinstance(toc_node, bool):
        toc_val = "true" if toc_node else "false"
    elif isinstance(toc_node, (int, str)):
        toc_val = str(toc_node).strip().lower()

    if toc_val in ("true", "yes", "1"):
        body_story.paragraphs.append("جدول محتوا — فیلد را در Word به‌روز کنید")

    for b in ast.get("blocks") or []:
        if isinstance(b, dict):
            _walk_expect_block(b, body_story, footnote_stories)

    return {
        "body": {
            "paragraphs": body_story.paragraphs,
            "headings": body_story.headings,
            "tables": body_story.tables,
            "codes": body_story.codes,
            "links": body_story.links,
            "images": body_story.images,
            "math": body_story.math,
        },
        "footnotes": [
            {
                "paragraphs": fn.paragraphs,
                "links": fn.links,
                "images": fn.images,
                "math": fn.math,
            }
            for fn in footnote_stories
        ],
        # Backward-compatibility flat aliases for existing callers:
        "paragraphs": body_story.paragraphs,
        "headings": [h["text"] for h in body_story.headings],
        "tables": body_story.tables,
        "codes": body_story.codes,
        "links": [l["target"] for l in body_story.links],
        "images": [img["src"] for img in body_story.images],
    }


def _p_text(p: ET.Element) -> str:
    bits: List[str] = []
    for el in p.iter():
        tag = el.tag
        if tag == f"{W}t":
            bits.append(el.text or "")
        elif tag == f"{W}tab":
            bits.append("\t")
        elif tag == f"{W}br":
            bits.append("\n")
        elif tag == f"{W}cr":
            bits.append("\n")
    return "".join(bits)


def _collect_tbl_story(
    tbl: ET.Element,
    story: SemanticStory,
    rels: Dict[str, str],
) -> None:
    desc = tbl.find(f".//{W}tblDescription")
    val = desc.get(f"{W}val") if desc is not None else None
    if val == "code_block":
        code_lines = [_p_text(p) for p in tbl.iter(f"{W}p")]
        story.codes.append("\n".join(code_lines).rstrip("\n"))
        return
    if val == "callout":
        rows = tbl.findall(f"{W}tr")
        body_rows = rows[1:] if len(rows) > 1 else rows
        for r in body_rows:
            for tc in r.findall(f"{W}tc"):
                for child in list(tc):
                    if child.tag == f"{W}p":
                        txt = _p_text(child).strip()
                        if txt:
                            story.paragraphs.append(txt)
                        for h in child.iter(f"{W}hyperlink"):
                            anchor = h.get(f"{W}anchor")
                            rid = h.get(f"{R}id")
                            if anchor:
                                story.links.append({"target": "#" + anchor, "text": _p_text(h).strip()})
                            elif rid and rid in rels:
                                story.links.append({"target": rels[rid], "text": _p_text(h).strip()})
                        for d in child.iter(f"{W}drawing"):
                            for blip in d.iter(f"{A}blip"):
                                embed = blip.get(f"{R}embed") or blip.get(f"{R}link")
                                if embed and embed in rels:
                                    story.images.append({"src": rels[embed]})
                        for _m in child.iter(f"{M}oMath"):
                            story.math.append({"tex": ""})
                    elif child.tag == f"{W}tbl":
                        _collect_tbl_story(child, story, rels)
        return
    if val == "heading_badge":
        t = " ".join(_p_text(p).strip() for p in tbl.iter(f"{W}p") if _p_text(p).strip()).strip()
        if t:
            level = 1
            for p in tbl.iter(f"{W}p"):
                olvl = p.find(f".//{W}outlineLvl")
                if olvl is not None:
                    try:
                        level = int(olvl.get(f"{W}val", "0")) + 1
                        break
                    except ValueError:
                        pass
            story.paragraphs.append(t)
            story.headings.append({"level": level, "text": t})
        return

    grid = []
    for tr in tbl.findall(f"{W}tr"):
        row = []
        for tc in tr.findall(f"{W}tc"):
            row.append(" ".join(_p_text(p).strip() for p in tc.findall(f"{W}p") if _p_text(p).strip()))
            for nested in tc.findall(f"{W}tbl"):
                nested_desc = nested.find(f".//{W}tblDescription")
                nested_val = nested_desc.get(f"{W}val") if nested_desc is not None else None
                if nested_val == "code_block":
                    _collect_tbl_story(nested, story, rels)
            for h in tc.iter(f"{W}hyperlink"):
                anchor = h.get(f"{W}anchor")
                rid = h.get(f"{R}id")
                if anchor:
                    story.links.append({"target": "#" + anchor, "text": _p_text(h).strip()})
                elif rid and rid in rels:
                    story.links.append({"target": rels[rid], "text": _p_text(h).strip()})
            for d in tc.iter(f"{W}drawing"):
                for blip in d.iter(f"{A}blip"):
                    embed = blip.get(f"{R}embed") or blip.get(f"{R}link")
                    if embed and embed in rels:
                        story.images.append({"src": rels[embed]})
            for _m in tc.iter(f"{M}oMath"):
                story.math.append({"tex": ""})
        if row:
            grid.append(row)
    if grid:
        story.tables.append(grid)


def actual_from_docx(docx_path: Path) -> Dict[str, Any]:
    with zipfile.ZipFile(docx_path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
        rels = {}
        if "word/_rels/document.xml.rels" in z.namelist():
            rel_root = ET.fromstring(z.read("word/_rels/document.xml.rels"))
            for rel in rel_root:
                rid = rel.get("Id")
                tgt = rel.get("Target")
                if rid and tgt:
                    rels[rid] = tgt
        footnote_xml = z.read("word/footnotes.xml") if "word/footnotes.xml" in z.namelist() else None
        fn_rels = {}
        if "word/_rels/footnotes.xml.rels" in z.namelist():
            fn_rel_root = ET.fromstring(z.read("word/_rels/footnotes.xml.rels"))
            for rel in fn_rel_root:
                rid = rel.get("Id")
                tgt = rel.get("Target")
                if rid and tgt:
                    fn_rels[rid] = tgt

    body = root.find(f"{W}body")
    body_story = SemanticStory(name="body")

    if body is not None:
        for child in list(body):
            tag = child.tag
            if tag == f"{W}sectPr":
                continue
            if tag == f"{W}p":
                txt = _p_text(child).strip()
                if txt:
                    body_story.paragraphs.append(txt)
                olvl = child.find(f".//{W}outlineLvl")
                if olvl is not None and txt:
                    try:
                        lvl = int(olvl.get(f"{W}val", "0")) + 1
                    except ValueError:
                        lvl = 1
                    body_story.headings.append({"level": lvl, "text": txt})
                for h in child.iter(f"{W}hyperlink"):
                    anchor = h.get(f"{W}anchor")
                    rid = h.get(f"{R}id")
                    if anchor:
                        body_story.links.append({"target": "#" + anchor, "text": _p_text(h).strip()})
                    elif rid and rid in rels:
                        body_story.links.append({"target": rels[rid], "text": _p_text(h).strip()})
                for d in child.iter(f"{W}drawing"):
                    for blip in d.iter(f"{A}blip"):
                        embed = blip.get(f"{R}embed") or blip.get(f"{R}link")
                        if embed and embed in rels:
                            body_story.images.append({"src": rels[embed]})
                for _m in child.iter(f"{M}oMath"):
                    body_story.math.append({"tex": ""})
            elif tag == f"{W}tbl":
                _collect_tbl_story(child, body_story, rels)

    actual_footnotes: List[Dict[str, Any]] = []
    if footnote_xml is not None:
        fn_root = ET.fromstring(footnote_xml)
        for fn in fn_root.findall(f"{W}footnote"):
            fn_type = fn.get(f"{W}type")
            fn_id = fn.get(f"{W}id", "0")
            if fn_type in ("separator", "continuationSeparator"):
                continue
            try:
                if int(fn_id) <= 0:
                    continue
            except ValueError:
                pass
            fn_paras = [_p_text(p).strip() for p in fn.findall(f"{W}p") if _p_text(p).strip()]
            fn_links = []
            for h in fn.iter(f"{W}hyperlink"):
                anchor = h.get(f"{W}anchor")
                rid = h.get(f"{R}id")
                if anchor:
                    fn_links.append({"target": "#" + anchor, "text": _p_text(h).strip()})
                elif rid and rid in fn_rels:
                    fn_links.append({"target": fn_rels[rid], "text": _p_text(h).strip()})
            fn_images = []
            for d in fn.iter(f"{W}drawing"):
                for blip in d.iter(f"{A}blip"):
                    embed = blip.get(f"{R}embed") or blip.get(f"{R}link")
                    if embed and embed in fn_rels:
                        fn_images.append({"src": fn_rels[embed]})
            fn_math = []
            for _m in fn.iter(f"{M}oMath"):
                fn_math.append({"tex": ""})
            actual_footnotes.append({
                "paragraphs": fn_paras,
                "links": fn_links,
                "images": fn_images,
                "math": fn_math,
            })

    return {
        "body": {
            "paragraphs": body_story.paragraphs,
            "headings": body_story.headings,
            "tables": body_story.tables,
            "codes": body_story.codes,
            "links": body_story.links,
            "images": body_story.images,
            "math": body_story.math,
        },
        "footnotes": actual_footnotes,
        # Backward-compatibility flat aliases:
        "paragraphs": body_story.paragraphs,
        "headings": [h["text"] for h in body_story.headings],
        "tables": body_story.tables,
        "codes": body_story.codes,
        "links": [l["target"] for l in body_story.links],
        "images": [img["src"] for img in body_story.images],
    }


def _matches_internal_anchor(exp_anchor: str, act_anchor: str) -> bool:
    if exp_anchor == act_anchor:
        return True
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", exp_anchor)
    if not cleaned or not cleaned[0].isalpha():
        cleaned = f"md_{cleaned}"
    digest = hashlib.sha1(exp_anchor.encode("utf-8")).hexdigest()[:8]
    expected_safe = f"{cleaned[:31]}_{digest}"
    return act_anchor in (exp_anchor, cleaned, expected_safe) or act_anchor.startswith(cleaned[:31])


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _resolve_expected_image_path(src: str, base_dir: Optional[Path]) -> Optional[Path]:
    if not src or src == "mermaid":
        return None
    path = Path(src)
    if path.is_file():
        return path
    if base_dir is not None:
        cand = (base_dir / src).resolve()
        if cand.is_file():
            return cand
    return None


def _docx_media_bytes(docx_path: Path, rel_target: str) -> Optional[bytes]:
    if not rel_target:
        return None
    part = rel_target.lstrip("/")
    if not part.startswith("word/"):
        part = os.path.normpath(os.path.join("word", part)).replace("\\", "/")
    try:
        with zipfile.ZipFile(docx_path) as z:
            if part in z.namelist():
                return z.read(part)
    except zipfile.BadZipFile:
        return None
    return None


def run_semantic_oracle(
    markdown: str,
    docx_path: Path,
    base_dir: Optional[Path] = None,
) -> Tuple[bool, List[str]]:
    issues: List[str] = []
    try:
        expected = expected_from_markdown(markdown)
        actual = actual_from_docx(Path(docx_path))
    except Exception as e:
        return False, [f"Semantic oracle parse error: {e}"]

    # 1. Body Paragraphs (Sequential & Occurrence-aware)
    exp_paras = expected["body"]["paragraphs"]
    act_paras = actual["body"]["paragraphs"]
    if len(exp_paras) != len(act_paras):
        issues.append(f"Body paragraph count mismatch: expected {len(exp_paras)}, found {len(act_paras)}")
    for idx, (exp_p, act_p) in enumerate(zip(exp_paras, act_paras)):
        if exp_p != act_p:
            issues.append(f"Body paragraph sequence mismatch at index {idx}: expected '{exp_p[:80]}', got '{act_p[:80]}'")
            break

    # 2. Code blocks (Sequential, exact line & indentation aware)
    exp_codes = expected["body"]["codes"]
    act_codes = actual["body"]["codes"]
    if len(exp_codes) != len(act_codes):
        issues.append(f"Code block count mismatch: expected {len(exp_codes)}, found {len(act_codes)}")
    for idx, (exp_c, act_c) in enumerate(zip(exp_codes, act_codes)):
        exp_norm = exp_c.replace("\r\n", "\n").rstrip()
        act_norm = act_c.replace("\r\n", "\n").rstrip()
        if exp_norm != act_norm:
            exp_lines = exp_norm.split("\n")
            act_lines = act_norm.split("\n")
            if len(exp_lines) != len(act_lines):
                issues.append(f"Code block {idx} line count mismatch: expected {len(exp_lines)}, got {len(act_lines)}")
            else:
                for l_idx, (el, al) in enumerate(zip(exp_lines, act_lines)):
                    if el != al:
                        issues.append(f"Code block {idx} line {l_idx} mismatch: expected '{el[:80]}', got '{al[:80]}'")
                        break

    # 3. Tables (Sequential, grid dimensions & cell coordinate match)
    exp_tables = expected["body"]["tables"]
    act_tables = actual["body"]["tables"]
    if len(exp_tables) != len(act_tables):
        issues.append(f"Table count mismatch: expected {len(exp_tables)}, found {len(act_tables)}")
    for t_idx, (exp_t, act_t) in enumerate(zip(exp_tables, act_tables)):
        if len(exp_t) != len(act_t):
            issues.append(f"Table {t_idx} row count mismatch: expected {len(exp_t)}, found {len(act_t)}")
            continue
        for r_idx, (exp_r, act_r) in enumerate(zip(exp_t, act_t)):
            if len(exp_r) != len(act_r):
                issues.append(f"Table {t_idx} row {r_idx} column count mismatch: expected {len(exp_r)}, found {len(act_r)}")
                continue
            for c_idx, (exp_c, act_c) in enumerate(zip(exp_r, act_r)):
                if exp_c.strip() != act_c.strip():
                    issues.append(f"Table {t_idx} cell [{r_idx},{c_idx}] mismatch: expected '{exp_c}', got '{act_c}'")

    # 4. Headings (Sequential, text match)
    exp_headings = expected["body"]["headings"]
    act_headings = actual["body"]["headings"]
    if len(exp_headings) != len(act_headings):
        issues.append(f"Heading count mismatch: expected {len(exp_headings)}, found {len(act_headings)}")
    for h_idx, (exp_h, act_h) in enumerate(zip(exp_headings, act_headings)):
        if exp_h["text"].strip() != act_h["text"].strip():
            issues.append(f"Heading text mismatch at index {h_idx}: expected '{exp_h['text']}', got '{act_h['text']}'")
        if exp_h.get("level") != act_h.get("level"):
            issues.append(
                f"Heading level mismatch at index {h_idx}: expected {exp_h.get('level')}, got {act_h.get('level')}"
            )

    # 5. Hyperlinks (Sequential, target destination match)
    exp_links = expected["body"]["links"]
    act_links = actual["body"]["links"]
    if len(exp_links) != len(act_links):
        issues.append(f"Hyperlink count mismatch: expected {len(exp_links)}, found {len(act_links)}")
    for l_idx, (exp_l, act_l) in enumerate(zip(exp_links, act_links)):
        exp_tgt = exp_l["target"]
        act_tgt = act_l["target"]
        if exp_tgt.startswith("#") or act_tgt.startswith("#"):
            exp_a = exp_tgt.lstrip("#")
            act_a = act_tgt.lstrip("#")
            if not _matches_internal_anchor(exp_a, act_a):
                issues.append(f"Internal link mismatch at index {l_idx}: expected '{exp_tgt}', got '{act_tgt}'")
        elif exp_tgt != act_tgt:
            issues.append(f"External link mismatch at index {l_idx}: expected '{exp_tgt}', got '{act_tgt}'")

    # 6. Images (Occurrence + source hash when the Markdown asset is resolvable)
    exp_images = expected["body"]["images"]
    act_images = actual["body"]["images"]
    if len(exp_images) != len(act_images):
        issues.append(f"Image count mismatch: expected {len(exp_images)}, found {len(act_images)}")
    for img_idx, (exp_img, act_img) in enumerate(zip(exp_images, act_images)):
        act_src = act_img.get("src", "")
        if not act_src:
            issues.append(f"Image {img_idx} has empty target/relationship in DOCX")
            continue
        exp_src = exp_img.get("src", "")
        if exp_src == "mermaid":
            continue
        src_path = _resolve_expected_image_path(exp_src, base_dir)
        if src_path is None:
            continue
        actual_bytes = _docx_media_bytes(Path(docx_path), act_src)
        if actual_bytes is None:
            issues.append(f"Image {img_idx} target '{act_src}' is missing from the DOCX package")
            continue
        if _sha256_bytes(src_path.read_bytes()) != _sha256_bytes(actual_bytes):
            issues.append(
                f"Image {img_idx} hash mismatch: expected source '{exp_src}' does not match embedded '{act_src}'"
            )

    # 7. Math (Formula occurrence count match)
    exp_math = expected["body"]["math"]
    act_math = actual["body"]["math"]
    if len(exp_math) != len(act_math):
        issues.append(f"Math formula count mismatch: expected {len(exp_math)}, found {len(act_math)}")

    # 8. Footnotes Story (Story boundary & content separation)
    exp_fns = expected["footnotes"]
    act_fns = actual["footnotes"]
    if len(exp_fns) != len(act_fns):
        issues.append(f"Footnote count mismatch: expected {len(exp_fns)}, found {len(act_fns)}")
    for f_idx, (exp_fn, act_fn) in enumerate(zip(exp_fns, act_fns)):
        if exp_fn["paragraphs"] != act_fn["paragraphs"]:
            issues.append(f"Footnote {f_idx} content mismatch: expected {exp_fn['paragraphs']}, got {act_fn['paragraphs']}")
        exp_fn_links = exp_fn.get("links", [])
        act_fn_links = act_fn.get("links", [])
        if len(exp_fn_links) != len(act_fn_links):
            issues.append(f"Footnote {f_idx} link count mismatch: expected {len(exp_fn_links)}, found {len(act_fn_links)}")
        exp_fn_imgs = exp_fn.get("images", [])
        act_fn_imgs = act_fn.get("images", [])
        if len(exp_fn_imgs) != len(act_fn_imgs):
            issues.append(f"Footnote {f_idx} image count mismatch: expected {len(exp_fn_imgs)}, found {len(act_fn_imgs)}")
        exp_fn_math = exp_fn.get("math", [])
        act_fn_math = act_fn.get("math", [])
        if len(exp_fn_math) != len(act_fn_math):
            issues.append(f"Footnote {f_idx} math count mismatch: expected {len(exp_fn_math)}, found {len(act_fn_math)}")

    return (len(issues) == 0), issues
