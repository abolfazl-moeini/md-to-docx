"""OOXML helpers for RTL, Complex Script (CS) fonts, bidiVisual tables, and borders."""

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from docx.table import Table, _Cell
from docx.document import Document

NSMAP = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def set_paragraph_bidi(paragraph: Paragraph, bidi: bool = True) -> None:
    """Sets or clears <w:bidi/> on paragraph properties."""
    pPr = paragraph._p.get_or_add_pPr()
    existing = pPr.find(qn("w:bidi"))
    if bidi:
        if existing is None:
            pPr.append(OxmlElement("w:bidi"))
    else:
        if existing is not None:
            pPr.remove(existing)


def set_paragraph_align(paragraph: Paragraph, align: str = "both") -> None:
    """
    Sets paragraph justification/alignment: 'both' (justify), 'start', 'center', 'end'.
    Note: 'start' in RTL aligns visually to the right without the bidi flipping bug.
    """
    pPr = paragraph._p.get_or_add_pPr()
    existing_jc = pPr.find(qn("w:jc"))
    if existing_jc is not None:
        pPr.remove(existing_jc)
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), align)
    pPr.append(jc)


def set_run_cs_font(
    run: Run,
    font_name: str = "Vazirmatn",
    size_pt: float = 11.0,
    bold: bool = False,
    italic: bool = False,
    color_hex: str | None = None,
    bidi_lang: str = "fa-IR",
    latin_lang: str = "en-US",
    cs_font_name: str | None = None,
    strike: bool = False,
    superscript: bool = False,
    subscript: bool = False,
    underline: bool = False,
    small_caps: bool = False,
) -> None:
    """Sets Complex Script and Latin font families, sizes, formatting, and bidi language."""
    rPr = run._r.get_or_add_rPr()

    # Font names
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), font_name)
    rFonts.set(qn("w:hAnsi"), font_name)
    rFonts.set(qn("w:cs"), cs_font_name or font_name)

    # Sizes in half-points (1 pt = 2 half-points)
    sz_val = str(int(round(size_pt * 2)))
    for tag in ("w:sz", "w:szCs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            rPr.append(el)
        el.set(qn("w:val"), sz_val)

    # Bold
    if bold:
        for tag in ("w:b", "w:bCs"):
            if rPr.find(qn(tag)) is None:
                rPr.append(OxmlElement(tag))

    # Italic
    if italic:
        for tag in ("w:i", "w:iCs"):
            if rPr.find(qn(tag)) is None:
                rPr.append(OxmlElement(tag))

    # Strikeout
    if strike:
        if rPr.find(qn("w:strike")) is None:
            rPr.append(OxmlElement("w:strike"))

    # Superscript / Subscript
    if superscript:
        vert = rPr.find(qn("w:vertAlign"))
        if vert is None:
            vert = OxmlElement("w:vertAlign")
            rPr.append(vert)
        vert.set(qn("w:val"), "superscript")
    elif subscript:
        vert = rPr.find(qn("w:vertAlign"))
        if vert is None:
            vert = OxmlElement("w:vertAlign")
            rPr.append(vert)
        vert.set(qn("w:val"), "subscript")

    # Underline
    if underline:
        u = rPr.find(qn("w:u"))
        if u is None:
            u = OxmlElement("w:u")
            rPr.append(u)
        u.set(qn("w:val"), "single")

    # Small Caps
    if small_caps:
        if rPr.find(qn("w:smallCaps")) is None:
            rPr.append(OxmlElement("w:smallCaps"))

    # Color
    if color_hex:
        clean_color = color_hex.lstrip("#")
        color_el = rPr.find(qn("w:color"))
        if color_el is None:
            color_el = OxmlElement("w:color")
            rPr.append(color_el)
        color_el.set(qn("w:val"), clean_color)

    # Lang
    lang = rPr.find(qn("w:lang"))
    if lang is None:
        lang = OxmlElement("w:lang")
        rPr.append(lang)
    lang.set(qn("w:val"), latin_lang)
    lang.set(qn("w:bidi"), bidi_lang)


def set_run_rtl(run: Run, rtl: bool = True) -> None:
    """Sets <w:rtl/> on a run. Use ONLY for pure RTL runs (like the heading number badge)."""
    rPr = run._r.get_or_add_rPr()
    existing = rPr.find(qn("w:rtl"))
    if rtl:
        if existing is None:
            rPr.append(OxmlElement("w:rtl"))
    else:
        if existing is not None:
            rPr.remove(existing)


def set_table_bidi_visual(table: Table) -> None:
    """Sets <w:bidiVisual/> on table properties so column 0 is visually on the right."""
    tblPr = table._tbl.tblPr
    if tblPr.find(qn("w:bidiVisual")) is None:
        tblPr.append(OxmlElement("w:bidiVisual"))


def set_cell_shading(cell: _Cell, color_hex: str) -> None:
    """Sets background shading fill on a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    existing = tcPr.find(qn("w:shd"))
    if existing is not None:
        tcPr.remove(existing)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex.lstrip("#"))
    tcPr.append(shd)


def set_cell_margins(
    cell: _Cell,
    top_pt: float = 4.0,
    bottom_pt: float = 4.0,
    left_pt: float = 6.0,
    right_pt: float = 6.0,
) -> None:
    """Sets cell internal margins (padding) in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    existing = tcPr.find(qn("w:tcMar"))
    if existing is not None:
        tcPr.remove(existing)
    tcMar = OxmlElement("w:tcMar")
    for side, pt in [("w:top", top_pt), ("w:bottom", bottom_pt), ("w:left", left_pt), ("w:right", right_pt)]:
        el = OxmlElement(side)
        el.set(qn("w:w"), str(int(round(pt * 20))))
        el.set(qn("w:type"), "dxa")
        tcMar.append(el)
    tcPr.append(tcMar)


def set_cell_borders(
    cell: _Cell,
    top: dict | None = None,
    bottom: dict | None = None,
    left: dict | None = None,
    right: dict | None = None,
) -> None:
    """Sets specific borders on a cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    existing = tcPr.find(qn("w:tcBorders"))
    if existing is not None:
        tcPr.remove(existing)
    tcBorders = OxmlElement("w:tcBorders")
    
    borders = {"w:top": top, "w:bottom": bottom, "w:left": left, "w:right": right}
    for tag, border_spec in borders.items():
        el = OxmlElement(tag)
        if border_spec:
            el.set(qn("w:val"), border_spec.get("val", "single"))
            el.set(qn("w:sz"), str(border_spec.get("sz", 4)))
            el.set(qn("w:space"), str(border_spec.get("space", 0)))
            el.set(qn("w:color"), border_spec.get("color", "auto").lstrip("#"))
        else:
            el.set(qn("w:val"), "none")
        tcBorders.append(el)
    tcPr.append(tcBorders)


def set_paragraph_shading(paragraph: Paragraph, color_hex: str) -> None:
    """Sets paragraph background shading."""
    pPr = paragraph._p.get_or_add_pPr()
    existing = pPr.find(qn("w:shd"))
    if existing is not None:
        pPr.remove(existing)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex.lstrip("#"))
    pPr.append(shd)


def set_paragraph_bottom_border(
    paragraph: Paragraph,
    color_hex: str = "6B2FA0",
    sz: int = 14,
    space: int = 4,
) -> None:
    """Sets a bottom paragraph border (used for unnumbered headings)."""
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = pPr.find(qn("w:pBdr"))
    if pBdr is None:
        pBdr = OxmlElement("w:pBdr")
        pPr.append(pBdr)
    bottom = pBdr.find(qn("w:bottom"))
    if bottom is None:
        bottom = OxmlElement("w:bottom")
        pBdr.append(bottom)
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(sz))
    bottom.set(qn("w:space"), str(space))
    bottom.set(qn("w:color"), color_hex.lstrip("#"))


def set_table_column_widths(table: Table, widths_dxa: list[int]) -> None:
    """Sets tblW, tblGrid, and cell tcW so Word honors column widths."""
    total = int(sum(widths_dxa))
    tbl = table._tbl
    tblPr = tbl.tblPr
    tbl_w = tblPr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tblPr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(total))
    tbl_w.set(qn("w:type"), "dxa")

    layout = tblPr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tblPr.append(layout)
    layout.set(qn("w:type"), "fixed")

    grid = tbl.find(qn("w:tblGrid"))
    if grid is None:
        grid = OxmlElement("w:tblGrid")
        tblPr.addnext(grid)
    else:
        for child in list(grid):
            grid.remove(child)
    for width in widths_dxa:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(int(width)))
        grid.append(col)

    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            if idx >= len(widths_dxa):
                break
            tcPr = cell._tc.get_or_add_tcPr()
            tc_w = tcPr.find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tcPr.insert(0, tc_w)
            tc_w.set(qn("w:w"), str(int(widths_dxa[idx])))
            tc_w.set(qn("w:type"), "dxa")


def set_paragraph_quote_border(
    paragraph: Paragraph,
    color_hex: str = "6B2FA0",
    sz: int = 24,
    space: int = 15,
) -> None:
    """Sets thick physical right border on a paragraph for blockquote callout."""
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = pPr.find(qn("w:pBdr"))
    if pBdr is None:
        pBdr = OxmlElement("w:pBdr")
        pPr.append(pBdr)
    right = pBdr.find(qn("w:right"))
    if right is None:
        right = OxmlElement("w:right")
        pBdr.append(right)
    right.set(qn("w:val"), "single")
    right.set(qn("w:sz"), str(sz))
    right.set(qn("w:space"), str(space))
    right.set(qn("w:color"), color_hex.lstrip("#"))


def set_doc_bidi(doc: Document) -> None:
    """Sets document-level and section-level bidi flags."""
    # Section bidi
    for section in doc.sections:
        sectPr = section._sectPr
        if sectPr.find(qn("w:bidi")) is None:
            sectPr.append(OxmlElement("w:bidi"))

    # Document settings bidi
    settings_el = doc.settings.element
    if settings_el.find(qn("w:bidi")) is None:
        settings_el.append(OxmlElement("w:bidi"))
