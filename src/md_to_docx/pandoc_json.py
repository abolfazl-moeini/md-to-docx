"""Pandoc JSON AST adapter and AST-to-DOCX converter."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_BREAK
from docx.table import _Cell

from md_to_docx.headings import parse_heading
from md_to_docx.renderer import DocxRenderer
from md_to_docx.mermaid import ConvertError
from md_to_docx.bidi import contains_persian
from md_to_docx.oxml import (
    set_paragraph_bidi,
    set_paragraph_align,
    set_run_cs_font,
    set_paragraph_bottom_border,
)


def emit_inlines(
    inlines: List[Dict[str, Any]],
    renderer: DocxRenderer,
    paragraph,
    bold: bool = False,
    italic: bool = False,
    font_size_pt: float = 11.0,
    strike: bool = False,
    superscript: bool = False,
    subscript: bool = False,
    underline: bool = False,
    small_caps: bool = False,
) -> None:
    """Writes formatted Pandoc inlines into an existing paragraph."""
    for inl in inlines:
        t = inl.get("t")
        c = inl.get("c")
        if t == "Str":
            renderer.append_text(
                paragraph,
                str(c),
                font_size_pt=font_size_pt,
                bold=bold,
                italic=italic,
                strike=strike,
                superscript=superscript,
                subscript=subscript,
                underline=underline,
                small_caps=small_caps,
            )
        elif t in ("Space", "SoftBreak"):
            renderer.append_text(
                paragraph,
                " ",
                font_size_pt=font_size_pt,
                bold=bold,
                italic=italic,
                strike=strike,
                superscript=superscript,
                subscript=subscript,
                underline=underline,
                small_caps=small_caps,
            )
        elif t == "LineBreak":
            r = paragraph.add_run()
            r.add_break()
        elif t == "Strong":
            emit_inlines(
                c or [],
                renderer,
                paragraph,
                bold=True,
                italic=italic,
                font_size_pt=font_size_pt,
                strike=strike,
                superscript=superscript,
                subscript=subscript,
                underline=underline,
                small_caps=small_caps,
            )
        elif t == "Emph":
            emit_inlines(
                c or [],
                renderer,
                paragraph,
                bold=bold,
                italic=True,
                font_size_pt=font_size_pt,
                strike=strike,
                superscript=superscript,
                subscript=subscript,
                underline=underline,
                small_caps=small_caps,
            )
        elif t == "Strikeout":
            emit_inlines(
                c or [],
                renderer,
                paragraph,
                bold=bold,
                italic=italic,
                font_size_pt=font_size_pt,
                strike=True,
                superscript=superscript,
                subscript=subscript,
                underline=underline,
                small_caps=small_caps,
            )
        elif t == "Superscript":
            emit_inlines(
                c or [],
                renderer,
                paragraph,
                bold=bold,
                italic=italic,
                font_size_pt=font_size_pt,
                strike=strike,
                superscript=True,
                subscript=False,
                underline=underline,
                small_caps=small_caps,
            )
        elif t == "Subscript":
            emit_inlines(
                c or [],
                renderer,
                paragraph,
                bold=bold,
                italic=italic,
                font_size_pt=font_size_pt,
                strike=strike,
                superscript=False,
                subscript=True,
                underline=underline,
                small_caps=small_caps,
            )
        elif t == "Underline":
            emit_inlines(
                c or [],
                renderer,
                paragraph,
                bold=bold,
                italic=italic,
                font_size_pt=font_size_pt,
                strike=strike,
                superscript=superscript,
                subscript=subscript,
                underline=True,
                small_caps=small_caps,
            )
        elif t == "SmallCaps":
            emit_inlines(
                c or [],
                renderer,
                paragraph,
                bold=bold,
                italic=italic,
                font_size_pt=font_size_pt,
                strike=strike,
                superscript=superscript,
                subscript=subscript,
                underline=underline,
                small_caps=True,
            )
        elif t == "Code":
            code = c[1] if isinstance(c, list) and len(c) > 1 else str(c)
            renderer.append_text(
                paragraph,
                code,
                font_size_pt=font_size_pt,
                bold=bold,
                italic=italic,
                strike=strike,
                superscript=superscript,
                subscript=subscript,
                underline=underline,
                small_caps=small_caps,
                font_name=renderer.template.fonts.get("code", "Courier New"),
                force_ltr=True,
            )
        elif t in ("Link", "Quoted", "Span"):
            inner = c[1] if isinstance(c, list) and len(c) > 1 and isinstance(c[1], list) else []
            emit_inlines(
                inner,
                renderer,
                paragraph,
                bold=bold,
                italic=italic,
                font_size_pt=font_size_pt,
                strike=strike,
                superscript=superscript,
                subscript=subscript,
                underline=underline,
                small_caps=small_caps,
            )
        elif t == "RawInline":
            raw_text = c[1] if isinstance(c, list) and len(c) > 1 else str(c)
            stripped = str(raw_text).strip()
            if stripped in ("\\pagebreak", "\\newpage"):
                r = paragraph.add_run()
                r.add_break(WD_BREAK.PAGE)
            else:
                renderer.append_text(paragraph, str(raw_text), font_size_pt=font_size_pt, bold=bold, italic=italic)
        elif t == "Note":
            note_text = f" [{blocks_to_text(c)}]" if isinstance(c, list) else f" [{c}]"
            renderer.append_text(paragraph, note_text, font_size_pt=font_size_pt * 0.85, superscript=True)
        elif t == "Math":
            math_text = c[1] if isinstance(c, list) and len(c) > 1 else str(c)
            renderer.append_text(paragraph, math_text, font_size_pt=font_size_pt, italic=True)
        elif t == "Image":
            continue
        elif isinstance(c, str):
            renderer.append_text(paragraph, c, font_size_pt=font_size_pt, bold=bold, italic=italic)
        else:
            raise ConvertError(f"Unsupported Pandoc AST inline type: '{t}'")


def emit_paragraph_inlines(inlines: List[Dict[str, Any]], renderer: DocxRenderer, font_size_pt: float = 11.0):
    text = inlines_to_text(inlines)
    p = renderer.begin_paragraph(text, align="both")
    emit_inlines(inlines, renderer, p, font_size_pt=font_size_pt)
    return p


def inlines_to_text(inlines: List[Dict[str, Any]]) -> str:
    """Converts Pandoc AST inline nodes into a plain string."""
    parts = []
    for inl in inlines:
        t = inl.get("t")
        c = inl.get("c")
        if t == "Str":
            parts.append(str(c))
        elif t in ("Space", "SoftBreak"):
            parts.append(" ")
        elif t == "LineBreak":
            parts.append("\n")
        elif t in ("Emph", "Strong", "Strikeout", "Superscript", "Subscript", "Underline", "SmallCaps"):
            parts.append(inlines_to_text(c or []))
        elif t == "Code":
            parts.append(c[1] if isinstance(c, list) and len(c) > 1 else str(c))
        elif t in ("Link", "Image", "Quoted", "Span"):
            if isinstance(c, list) and len(c) > 1 and isinstance(c[1], list):
                parts.append(inlines_to_text(c[1]))
            elif isinstance(c, list) and len(c) > 0 and isinstance(c[0], list):
                parts.append(inlines_to_text(c[0]))
        elif t == "RawInline":
            parts.append(c[1] if isinstance(c, list) and len(c) > 1 else str(c))
        elif t == "Note":
            parts.append(blocks_to_text(c) if isinstance(c, list) else str(c))
        elif t == "Math":
            parts.append(c[1] if isinstance(c, list) and len(c) > 1 else str(c))
        elif isinstance(c, str):
            parts.append(c)
    return "".join(parts)


def blocks_to_text(blocks: List[Dict[str, Any]]) -> str:
    """Extracts plain text from a list of AST block nodes."""
    lines = []
    for b in blocks:
        t = b.get("t")
        c = b.get("c")
        if t in ("Para", "Plain"):
            lines.append(inlines_to_text(c))
        elif t == "Header":
            lines.append(inlines_to_text(c[2]))
        elif t == "BlockQuote":
            lines.append(blocks_to_text(c))
        elif t == "CodeBlock":
            lines.append(c[1] if isinstance(c, list) and len(c) > 1 else str(c))
    return "\n".join(lines)


def extract_table_caption(table_c: List[Any]) -> Optional[str]:
    """Extracts table caption text from a Pandoc 3 Table node."""
    if len(table_c) > 1 and table_c[1] and isinstance(table_c[1], list):
        caption_blocks = table_c[1][1] if len(table_c[1]) > 1 else []
        if caption_blocks:
            return blocks_to_text(caption_blocks).strip() or None
    return None


def parse_pandoc_table(table_c: List[Any]) -> Tuple[List[str], List[List[str]]]:
    """
    Parses a Pandoc Table AST node into (headers, rows).
    Table AST format: [attr, caption, colspecs, thead, tbodies, tfoot]
    Supports multiple tbodies and multiple rows per tbody.
    """
    thead = table_c[3] if len(table_c) > 3 else []
    tbodies = table_c[4] if len(table_c) > 4 else []

    headers: List[str] = []
    if len(thead) > 1 and thead[1]:
        first_head_item = thead[1][0]
        if isinstance(first_head_item, list) and len(first_head_item) == 2 and isinstance(first_head_item[1], list):
            cells = first_head_item[1]
        elif isinstance(first_head_item, list) and len(first_head_item) > 1 and isinstance(first_head_item[0], list):
            cells = thead[1] if isinstance(first_head_item[0], list) and len(first_head_item) >= 5 else [first_head_item]
        else:
            cells = thead[1]

        for cell in cells:
            cell_blocks = cell[4] if len(cell) > 4 else []
            headers.append(blocks_to_text(cell_blocks).strip())

    rows: List[List[str]] = []
    for tbody in tbodies:
        tbody_rows = tbody[3] if len(tbody) > 3 else []
        for row in tbody_rows:
            row_cells = row[1] if len(row) > 1 else []
            row_vals = []
            for cell in row_cells:
                cell_blocks = cell[4] if len(cell) > 4 else []
                row_vals.append(blocks_to_text(cell_blocks).strip())
            rows.append(row_vals)

    return headers, rows


def render_block_into_cell(block: Dict[str, Any], cell: _Cell, renderer: DocxRenderer, is_first: bool = False) -> None:
    """Renders child AST blocks into a table cell (e.g. inside a callout box)."""
    t = block.get("t")
    c = block.get("c")

    if t in ("Para", "Plain"):
        p = cell.paragraphs[0] if (is_first and len(cell.paragraphs) > 0 and cell.paragraphs[0].text == "") else cell.add_paragraph()
        text = inlines_to_text(c)
        is_rtl = contains_persian(text) if renderer.template.direction == "rtl" else False
        set_paragraph_bidi(p, bidi=is_rtl)
        set_paragraph_align(p, "both")
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(4)
        emit_inlines(c, renderer, p, font_size_pt=10.5)

    elif t == "CodeBlock":
        code_str = c[1] if isinstance(c, list) and len(c) > 1 else str(c)
        code_font = renderer.template.fonts.get("code", "Courier New")
        for line in code_str.splitlines() or [""]:
            p = cell.paragraphs[0] if (is_first and len(cell.paragraphs) > 0 and cell.paragraphs[0].text == "") else cell.add_paragraph()
            is_first = False
            set_paragraph_bidi(p, bidi=False)
            set_paragraph_align(p, "start")
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(1)
            renderer.append_text(p, line, font_size_pt=9.5, font_name=code_font, force_ltr=True)

    elif t == "BulletList":
        for item_blocks in c:
            p = cell.paragraphs[0] if (is_first and len(cell.paragraphs) > 0 and cell.paragraphs[0].text == "") else cell.add_paragraph()
            is_first = False
            item_text = blocks_to_text(item_blocks)
            is_rtl = contains_persian(item_text) if renderer.template.direction == "rtl" else False
            set_paragraph_bidi(p, bidi=is_rtl)
            set_paragraph_align(p, "start")
            p.paragraph_format.space_after = Pt(2)
            r_mark = p.add_run("- ")
            set_run_cs_font(r_mark, font_name=renderer.template.fonts.get("body", "Vazirmatn"), size_pt=10.5)
            if item_blocks and item_blocks[0].get("t") in ("Para", "Plain"):
                emit_inlines(item_blocks[0].get("c", []), renderer, p, font_size_pt=10.5)
            else:
                renderer.append_text(p, item_text, font_size_pt=10.5)

    elif t == "OrderedList":
        attr = c[0] if c else [1]
        items = c[1] if len(c) > 1 else []
        start = attr[0] if isinstance(attr, list) and attr else 1
        try:
            start = int(start)
        except (TypeError, ValueError):
            start = 1
        for offset, item_blocks in enumerate(items):
            p = cell.paragraphs[0] if (is_first and len(cell.paragraphs) > 0 and cell.paragraphs[0].text == "") else cell.add_paragraph()
            is_first = False
            item_text = blocks_to_text(item_blocks)
            is_rtl = contains_persian(item_text) if renderer.template.direction == "rtl" else False
            set_paragraph_bidi(p, bidi=is_rtl)
            set_paragraph_align(p, "start")
            p.paragraph_format.space_after = Pt(2)
            r_mark = p.add_run(f"{start + offset}. ")
            set_run_cs_font(r_mark, font_name=renderer.template.fonts.get("body", "Vazirmatn"), size_pt=10.5)
            if item_blocks and item_blocks[0].get("t") in ("Para", "Plain"):
                emit_inlines(item_blocks[0].get("c", []), renderer, p, font_size_pt=10.5)
            else:
                renderer.append_text(p, item_text, font_size_pt=10.5)

    elif t == "Table":
        headers, rows = parse_pandoc_table(c)
        caption = extract_table_caption(c)
        renderer.render_table(headers, rows, caption=caption, container=cell)

    elif t == "BlockQuote":
        quote_texts = [blocks_to_text([b]) for b in c]
        for q in quote_texts:
            p = cell.paragraphs[0] if (is_first and len(cell.paragraphs) > 0 and cell.paragraphs[0].text == "") else cell.add_paragraph()
            is_first = False
            renderer.append_text(p, q, italic=True, font_size_pt=10.5)

    elif t == "DefinitionList":
        def_items = []
        for item in c:
            term = inlines_to_text(item[0])
            defs = [blocks_to_text(d) for d in item[1]]
            def_items.append((term, defs))
        for term, def_texts in def_items:
            p_term = cell.paragraphs[0] if (is_first and len(cell.paragraphs) > 0 and cell.paragraphs[0].text == "") else cell.add_paragraph()
            is_first = False
            is_rtl = contains_persian(term) if renderer.template.direction == "rtl" else False
            set_paragraph_bidi(p_term, bidi=is_rtl)
            set_paragraph_align(p_term, "start")
            p_term.paragraph_format.space_before = Pt(4)
            p_term.paragraph_format.space_after = Pt(2)
            renderer.append_text(p_term, term, bold=True, font_size_pt=10.5)
            for dtext in def_texts:
                p_def = cell.add_paragraph()
                is_rtl_d = contains_persian(dtext) if renderer.template.direction == "rtl" else False
                set_paragraph_bidi(p_def, bidi=is_rtl_d)
                set_paragraph_align(p_def, "both")
                p_def.paragraph_format.left_indent = Inches(0.2)
                p_def.paragraph_format.space_after = Pt(3)
                renderer.append_text(p_def, dtext, font_size_pt=10.0)

    elif t == "HorizontalRule":
        p = cell.paragraphs[0] if (is_first and len(cell.paragraphs) > 0 and cell.paragraphs[0].text == "") else cell.add_paragraph()
        is_first = False
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        border_color = renderer._resolve_color("caption")
        set_paragraph_bottom_border(p, color_hex=border_color, sz=6, space=1)

    elif t == "Div":
        child_blocks = c[1] if isinstance(c, list) and len(c) > 1 and isinstance(c[1], list) else []
        for cb in child_blocks:
            render_block_into_cell(cb, cell, renderer, is_first=is_first)
            is_first = False

    else:
        p = cell.paragraphs[0] if (is_first and len(cell.paragraphs) > 0 and cell.paragraphs[0].text == "") else cell.add_paragraph()
        renderer.append_text(p, blocks_to_text([block]), font_size_pt=10.5)


def render_single_block(block: Dict[str, Any], renderer: DocxRenderer) -> None:
    t = block.get("t")
    c = block.get("c")

    if t == "Header":
        level = c[0]
        text = inlines_to_text(c[2])
        info = parse_heading(text, level=level)
        renderer.render_heading(info)

    elif t == "Figure":
        caption_text = None
        if len(c) > 1 and len(c[1]) > 1 and c[1][1]:
            caption_text = blocks_to_text(c[1][1])

        img_src = None
        img_alt = None
        content_blocks = c[2] if len(c) > 2 else []
        for cb in content_blocks:
            inlines = cb.get("c", []) if isinstance(cb, dict) else []
            for inl in inlines:
                if isinstance(inl, dict) and inl.get("t") == "Image":
                    img_src = inl["c"][2][0]
                    img_alt = inlines_to_text(inl["c"][1])
                    break
            if img_src:
                break

        if img_src:
            final_caption = caption_text or img_alt or None
            renderer.render_image(Path(img_src), caption=final_caption)

    elif t in ("Para", "Plain"):
        images = [inl for inl in c if isinstance(inl, dict) and inl.get("t") == "Image"]
        non_spaces = [
            inl for inl in c
            if isinstance(inl, dict) and inl.get("t") not in ("Image", "Space", "SoftBreak", "LineBreak")
        ]
        if len(images) == 1 and len(non_spaces) == 0:
            img_src = images[0]["c"][2][0]
            alt = inlines_to_text(images[0]["c"][1])
            renderer.render_image(Path(img_src), caption=alt or None)
        else:
            emit_paragraph_inlines(c, renderer)

    elif t == "BlockQuote":
        quote_texts = [blocks_to_text([b]) for b in c]
        renderer.render_quote(quote_texts)

    elif t == "Div":
        attr, child_blocks = c
        id_, classes, kvs = attr
        kv_dict = {k: v for k, v in kvs}

        if "mermaid-figure" in classes:
            caption = kv_dict.get("caption")
            img_path = None
            for cb in child_blocks:
                if cb.get("t") in ("Para", "Plain"):
                    for inl in cb.get("c", []):
                        if isinstance(inl, dict) and inl.get("t") == "Image":
                            img_path = inl["c"][2][0]
            if img_path:
                renderer.render_image(Path(img_path), caption=caption)

        elif any(cls in renderer.template.callouts for cls in classes):
            cls = next(c for c in classes if c in renderer.template.callouts)
            default_title = renderer.template.callouts.get(cls, {}).get("default_title", cls)
            title = kv_dict.get("title", default_title)
            # F-05: Preserve child AST blocks and rich formatting inside callout
            renderer.render_callout(cls, title, child_blocks, block_renderer=render_block_into_cell)

        else:
            for cb in child_blocks:
                render_single_block(cb, renderer)

    elif t == "Table":
        headers, rows = parse_pandoc_table(c)
        caption = extract_table_caption(c)
        renderer.render_table(headers, rows, caption=caption)

    elif t == "CodeBlock":
        attr = c[0] if isinstance(c, list) and len(c) > 0 else []
        code_str = c[1] if isinstance(c, list) and len(c) > 1 else str(c)
        classes = attr[1] if isinstance(attr, list) and len(attr) > 1 and isinstance(attr[1], list) else []
        lang = classes[0] if classes else None
        renderer.render_code_block(code_str, language=lang)

    elif t == "BulletList":
        for item_blocks in c:
            renderer.render_list_item(blocks_to_text(item_blocks), marker="-")

    elif t == "OrderedList":
        attr = c[0] if c else [1]
        items = c[1] if len(c) > 1 else []
        start = attr[0] if isinstance(attr, list) and attr else 1
        try:
            start = int(start)
        except (TypeError, ValueError):
            start = 1
        for offset, item_blocks in enumerate(items):
            renderer.render_list_item(blocks_to_text(item_blocks), marker=f"{start + offset}.")

    elif t == "DefinitionList":
        def_items = []
        for item in c:
            term = inlines_to_text(item[0])
            defs = [blocks_to_text(d) for d in item[1]]
            def_items.append((term, defs))
        renderer.render_definition_list(def_items)

    elif t == "HorizontalRule":
        renderer.render_horizontal_rule()

    elif t == "RawBlock":
        raw_text = c[1] if isinstance(c, list) and len(c) > 1 else str(c)
        stripped = raw_text.strip()
        if stripped in ("\\pagebreak", "\\newpage", "<!-- pagebreak -->", "<!-- newpage -->") or (
            "<w:br" in stripped and 'type="page"' in stripped
        ):
            renderer.render_page_break()
        else:
            p = renderer.begin_paragraph(raw_text)
            renderer.append_text(p, raw_text)

    else:
        # F-06: Explicit error for unknown/unsupported AST blocks rather than silent omission
        raise ConvertError(f"Unsupported Pandoc AST block type: '{t}'")


def ast_to_docx(ast_dict: Dict[str, Any], renderer: DocxRenderer) -> Document:
    """Translates a full Pandoc AST dictionary into elements in a DOCX Document."""
    blocks = ast_dict.get("blocks", [])
    for block in blocks:
        render_single_block(block, renderer)
    return renderer.doc
