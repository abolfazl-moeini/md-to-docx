import pytest
from pathlib import Path
from docx import Document
from md_to_docx.template import Template
from md_to_docx.headings import HeadingInfo
from md_to_docx.renderer import DocxRenderer

@pytest.fixture
def template():
    return Template.load("purple_book")

@pytest.fixture
def renderer(template):
    doc = Document()
    return DocxRenderer(doc, template)

def test_normal_style_has_cs_font_and_bidi(renderer):
    xml = renderer.doc.styles["Normal"].element.xml
    assert 'w:cs="Vazirmatn"' in xml
    assert "<w:bidi" in xml
    assert 'w:szCs' in xml
    assert 'w:jc w:val="both"' in xml


def test_render_paragraph_rtl(renderer):
    p = renderer.render_paragraph("این یک متن نمونه به زبان فارسی است.")
    xml = p._p.xml
    assert "<w:bidi" in xml
    assert 'w:jc w:val="both"' in xml
    assert 'w:cs="Vazirmatn"' in xml

def test_render_heading_with_badge(renderer):
    info = HeadingInfo(level=2, number="۱.۴.۱", title="نقش Database Engine", raw_text="")
    tbl = renderer.render_heading(info)
    xml = tbl._tbl.xml
    # Must have bidiVisual
    assert "<w:bidiVisual" in xml
    # First cell has badge background 6B2FA0
    cell0_xml = tbl.cell(0, 0)._tc.xml
    assert 'w:fill="6B2FA0"' in cell0_xml
    assert "۱.۴.۱" in cell0_xml
    assert "<w:rtl" in cell0_xml
    # Second cell has title and bottom border
    cell1 = tbl.cell(0, 1)
    assert "نقش Database Engine" in cell1.paragraphs[0].text
    cell1_xml = cell1._tc.xml
    assert "Database Engine" in cell1_xml
    assert 'w:bottom' in cell1_xml

def test_render_heading_without_number(renderer):
    info = HeadingInfo(level=1, number=None, title="مقدمه", raw_text="")
    elem = renderer.render_heading(info)
    xml = elem._p.xml if hasattr(elem, "_p") else elem._tbl.xml
    assert "مقدمه" in xml
    assert "<w:pBdr" in xml
    assert "<w:bottom" in xml


def test_render_heading_badge_column_is_narrow(renderer):
    info = HeadingInfo(level=2, number="۱.۴.۱", title="نقش Database Engine", raw_text="")
    tbl = renderer.render_heading(info)
    from docx.oxml.ns import qn
    cols = tbl._tbl.findall(qn("w:tblGrid") + "/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}gridCol")
    # findall with path may fail; use xpath-like children
    grid = None
    for child in tbl._tbl:
        if child.tag == qn("w:tblGrid"):
            grid = child
            break
    assert grid is not None
    widths = [int(col.get(qn("w:w"))) for col in grid]
    assert len(widths) == 2
    assert widths[0] < widths[1]
    assert widths[0] <= 1200  # ~0.65in badge, not half-page

def test_render_note_callout(renderer):
    tbl = renderer.render_callout("note", "نکتهٔ DBA", ["متن داخل کادر نکته"])
    xml = tbl._tbl.xml
    assert "<w:bidiVisual" in xml
    # Header cell has primary_dark fill 4A156D and diamond icon
    hdr_cell = tbl.cell(0, 0)
    assert "◆" in hdr_cell.paragraphs[0].text
    assert "نکتهٔ DBA" in hdr_cell.paragraphs[0].text
    hdr_xml = hdr_cell._tc.xml
    assert 'w:fill="4A156D"' in hdr_xml
    # Body cell has F7F3FB fill
    body_xml = tbl.cell(1, 0)._tc.xml
    assert 'w:fill="F7F3FB"' in body_xml
    assert "متن داخل کادر نکته" in body_xml

def test_render_warning_callout(renderer):
    tbl = renderer.render_callout("warning", "هشدار", ["متن داخل کادر هشدار"])
    xml = tbl._tbl.xml
    hdr_xml = tbl.cell(0, 0)._tc.xml
    assert 'w:fill="FBF7F4"' in hdr_xml
    assert "هشدار" in hdr_xml
    assert "⚠️" not in hdr_xml  # NO emoji per specification
    assert 'w:color w:val="8B6914"' in hdr_xml

def test_render_quote(renderer):
    paragraphs = renderer.render_quote(["این یک نقل‌قول نمونه است."])
    assert len(paragraphs) == 1
    xml = paragraphs[0]._p.xml
    assert "<w:pBdr" in xml
    assert '<w:right w:val="single"' in xml
    assert 'w:color="6B2FA0"' in xml
    assert 'w:fill="ECE4F1"' in xml

def test_render_table(renderer):
    headers = ["مفهوم", "سطح معمول", "نمونه"]
    rows = [
        ["Login", "Instance", "DOMAIN\\Niloofar"],
        ["User", "Database", "Niloofar"],
    ]
    tbl = renderer.render_table(headers, rows)
    xml = tbl._tbl.xml
    assert "<w:bidiVisual" in xml
    # Header row cells have fill 6B2FA0 and white text
    for col_idx in range(3):
        cell_xml = tbl.cell(0, col_idx)._tc.xml
        assert 'w:fill="6B2FA0"' in cell_xml
        assert 'w:color w:val="FFFFFF"' in cell_xml

def test_render_image_with_caption(renderer, tmp_path):
    stub_img = Path(__file__).parent / "fixtures" / "diagram-stub.png"
    p_img, p_cap = renderer.render_image(stub_img, caption="شکل ۲-۱. معماری داخلی")
    assert p_img is not None
    assert p_cap is not None
    cap_xml = p_cap._p.xml
    assert "شکل ۲-۱. معماری داخلی" in cap_xml
    assert 'w:jc w:val="center"' in cap_xml
    assert 'w:color w:val="5A5A5A"' in cap_xml


def test_render_code_block_box_styling(renderer):
    code = "def calculate_total(price: float, tax: float) -> float:\n    return price * (1 + tax)"
    tbl = renderer.render_code_block(code, language="python")
    assert tbl is not None
    xml = tbl._tbl.xml
    # Code block must be LTR (no bidiVisual)
    assert "<w:bidiVisual" not in xml

    # Table level width in dxa and center alignment
    tblPr_xml = tbl._tbl.tblPr.xml
    assert 'w:tblW w:type="dxa"' in tblPr_xml
    assert 'w:jc w:val="center"' in tblPr_xml

    # Shading on cell
    cell_xml = tbl.cell(0, 0)._tc.xml
    assert 'w:fill="F6F8FA"' in cell_xml
    # Borders on cell
    assert '<w:tcBorders' in cell_xml
    assert 'w:color="D0D7DE"' in cell_xml
    # Cell margins (padding)
    assert '<w:tcMar>' in cell_xml

    # Check paragraph and runs
    paragraphs = tbl.cell(0, 0).paragraphs
    assert len(paragraphs) == 2  # 2 lines of code
    for p in paragraphs:
        p_xml = p._p.xml
        assert '<w:bidi' not in p_xml
        assert 'w:jc w:val="left"' in p_xml

    # Check monospaced font
    assert 'w:ascii="Courier New"' in cell_xml
    # Check syntax highlighting token colors (e.g. def / return keyword color)
    assert 'w:color w:val="007020"' in cell_xml  # Python keyword color in friendly theme


def test_render_code_block_diverse_languages(renderer):
    # SQL
    sql_tbl = renderer.render_code_block("SELECT id, name FROM users WHERE active = 1;", language="sql")
    sql_xml = sql_tbl._tbl.xml
    assert "users" in sql_xml
    assert 'w:color' in sql_xml

    # JSON
    json_tbl = renderer.render_code_block('{"status": "ok", "code": 200}', language="json")
    json_xml = json_tbl._tbl.xml
    assert "status" in json_xml
    assert 'w:color' in json_xml

    # TypeScript
    ts_tbl = renderer.render_code_block("interface User { id: number; name: string; }", language="typescript")
    ts_xml = ts_tbl._tbl.xml
    assert "User" in ts_xml
    assert 'w:color' in ts_xml


def test_render_code_block_empty_and_indented_lines(renderer):
    code = "def foo():\n    x = 10\n\n    return x\n"
    tbl = renderer.render_code_block(code, language="python")
    paragraphs = tbl.cell(0, 0).paragraphs
    # Exactly 4 lines (the 5th trailing newline stripped)
    assert len(paragraphs) == 4
    # 2nd line should preserve 4-space indentation
    p2 = paragraphs[1]
    assert p2.text == "    x = 10"
    # 3rd line is empty
    p3 = paragraphs[2]
    assert p3.text == ""


def test_render_code_block_edge_cases(renderer):
    # 1. No language specified
    tbl_no_lang = renderer.render_code_block("plain text line 1\nplain text line 2")
    assert tbl_no_lang is not None
    assert len(tbl_no_lang.cell(0, 0).paragraphs) == 2

    # 2. Unknown language
    tbl_unknown = renderer.render_code_block("echo 'test'", language="unknown_custom_lang_xyz")
    assert tbl_unknown is not None
    assert "echo" in tbl_unknown.cell(0, 0).text

    # 3. Empty code block
    tbl_empty = renderer.render_code_block("")
    assert tbl_empty is not None
    assert len(tbl_empty.cell(0, 0).paragraphs) >= 1

    # 4. XML special characters & quotes
    code_special = "if (a < 5 && b > 10) { print(\"<a>&nbsp;</a>\"); }"
    tbl_special = renderer.render_code_block(code_special, language="typescript")
    xml = tbl_special._tbl.xml
    assert "&lt;" in xml or "<" in tbl_special.cell(0, 0).text
    assert "&amp;" in xml or "&" in tbl_special.cell(0, 0).text

    # 5. Persian comments within code block
    code_persian = "-- این یک کامنت فارسی در کلاینت است\nSELECT * FROM Orders;"
    tbl_persian = renderer.render_code_block(code_persian, language="sql")
    assert "کامنت فارسی" in tbl_persian.cell(0, 0).text
    assert 'w:cs="Vazirmatn"' in tbl_persian._tbl.xml


