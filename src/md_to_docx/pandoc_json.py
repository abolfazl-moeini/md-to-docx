"""Pandoc JSON AST adapter and AST-to-DOCX converter."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from docx import Document

from md_to_docx.headings import parse_heading
from md_to_docx.renderer import DocxRenderer


def emit_inlines(
    inlines: List[Dict[str, Any]],
    renderer: DocxRenderer,
    paragraph,
    bold: bool = False,
    italic: bool = False,
    font_size_pt: float = 11.0,
) -> None:
    """Writes formatted Pandoc inlines into an existing paragraph."""
    for inl in inlines:
        t = inl.get("t")
        c = inl.get("c")
        if t == "Str":
            renderer.append_text(paragraph, str(c), font_size_pt=font_size_pt, bold=bold, italic=italic)
        elif t in ("Space", "SoftBreak"):
            renderer.append_text(paragraph, " ", font_size_pt=font_size_pt, bold=bold, italic=italic)
        elif t == "LineBreak":
            renderer.append_text(paragraph, "\n", font_size_pt=font_size_pt, bold=bold, italic=italic)
        elif t == "Strong":
            emit_inlines(c or [], renderer, paragraph, bold=True, italic=italic, font_size_pt=font_size_pt)
        elif t == "Emph":
            emit_inlines(c or [], renderer, paragraph, bold=bold, italic=True, font_size_pt=font_size_pt)
        elif t == "Code":
            code = c[1] if isinstance(c, list) and len(c) > 1 else str(c)
            renderer.append_text(
                paragraph,
                code,
                font_size_pt=font_size_pt,
                bold=bold,
                italic=italic,
                font_name=renderer.template.fonts.get("code", "Courier New"),
                force_ltr=True,
            )
        elif t in ("Link", "Quoted", "Span"):
            inner = c[1] if isinstance(c, list) and len(c) > 1 and isinstance(c[1], list) else []
            emit_inlines(inner, renderer, paragraph, bold=bold, italic=italic, font_size_pt=font_size_pt)
        elif t == "Image":
            continue
        elif isinstance(c, str):
            renderer.append_text(paragraph, c, font_size_pt=font_size_pt, bold=bold, italic=italic)


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
        elif t in ("Emph", "Strong"):
            parts.append(inlines_to_text(c))
        elif t == "Code":
            # c is [attr, code_string]
            parts.append(c[1] if isinstance(c, list) and len(c) > 1 else str(c))
        elif t in ("Link", "Image", "Quoted", "Span"):
            # c is [attr, inlines, ...]
            if isinstance(c, list) and len(c) > 1 and isinstance(c[1], list):
                parts.append(inlines_to_text(c[1]))
            elif isinstance(c, list) and len(c) > 0 and isinstance(c[0], list):
                parts.append(inlines_to_text(c[0]))
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


def parse_pandoc_table(table_c: List[Any]) -> Tuple[List[str], List[List[str]]]:
    """
    Parses a Pandoc Table AST node into (headers, rows).
    Table AST format: [attr, caption, colspecs, thead, tbodies, tfoot]
    """
    thead = table_c[3]
    tbodies = table_c[4]

    headers: List[str] = []
    # thead is [attr, [rows]]
    if len(thead) > 1 and thead[1]:
        first_head_item = thead[1][0]
        if isinstance(first_head_item, list) and len(first_head_item) == 2 and isinstance(first_head_item[1], list):
            cells = first_head_item[1]
        elif isinstance(first_head_item, list) and len(first_head_item) > 1 and isinstance(first_head_item[0], list):
            # If thead[1] is a list of cells directly
            cells = thead[1] if isinstance(first_head_item[0], list) and len(first_head_item) >= 5 else [first_head_item]
        else:
            cells = thead[1]

        for cell in cells:
            cell_blocks = cell[4] if len(cell) > 4 else []
            headers.append(blocks_to_text(cell_blocks).strip())


    rows: List[List[str]] = []
    for tbody in tbodies:
        # tbody is [attr, row_head_cols, [intermediate_head_rows], [rows]]
        tbody_rows = tbody[3] if len(tbody) > 3 else []
        for row in tbody_rows:
            row_cells = row[1] if len(row) > 1 else []
            row_vals = []
            for cell in row_cells:
                cell_blocks = cell[4] if len(cell) > 4 else []
                row_vals.append(blocks_to_text(cell_blocks).strip())
            rows.append(row_vals)

    return headers, rows


def render_single_block(block: Dict[str, Any], renderer: DocxRenderer) -> None:
    t = block.get("t")
    c = block.get("c")

    if t == "Header":
        level = c[0]
        text = inlines_to_text(c[2])
        info = parse_heading(text, level=level)
        renderer.render_heading(info)

    elif t == "Figure":
        # Pandoc 3 standalone figure with caption: c = [attr, [short_cap, cap_blocks], content_blocks]
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
        # Check if this paragraph/plain block is solely an image (ignoring spaces)
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
            body_texts = [blocks_to_text([b]) for b in child_blocks]
            renderer.render_callout(cls, title, body_texts)

        else:
            for cb in child_blocks:
                render_single_block(cb, renderer)

    elif t == "Table":
        headers, rows = parse_pandoc_table(c)
        renderer.render_table(headers, rows)

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


def ast_to_docx(ast_dict: Dict[str, Any], renderer: DocxRenderer) -> Document:
    """Translates a full Pandoc AST dictionary into elements in a DOCX Document."""
    blocks = ast_dict.get("blocks", [])
    for block in blocks:
        render_single_block(block, renderer)
    return renderer.doc
