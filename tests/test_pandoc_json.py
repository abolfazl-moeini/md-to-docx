import json
import pytest
from pathlib import Path
from docx import Document
from md_to_docx.template import Template
from md_to_docx.renderer import DocxRenderer
from md_to_docx.pandoc_json import inlines_to_text, ast_to_docx, parse_pandoc_table

def test_inlines_to_text():
    inlines = [
        {"t": "Str", "c": "یک"},
        {"t": "Space"},
        {"t": "Str", "c": "آزمایش"},
        {"t": "Space"},
        {"t": "Code", "c": [["", [], []], "code_snippet"]},
        {"t": "Space"},
        {"t": "Strong", "c": [{"t": "Str", "c": "مهم"}]},
    ]
    text = inlines_to_text(inlines)
    assert text == "یک آزمایش code_snippet مهم"

def test_parse_pandoc_table():
    ast_path = Path(__file__).parent / "fixtures" / "pandoc_ast_sample.json"
    ast_data = json.loads(ast_path.read_text(encoding="utf-8"))
    table_block = next(b for b in ast_data["blocks"] if b["t"] == "Table")
    headers, rows = parse_pandoc_table(table_block["c"])
    assert headers == ["مفهوم", "سطح معمول", "نمونه"]
    assert len(rows) == 2
    assert rows[0] == ["Login", "Instance", "DOMAIN\\Niloofar"]
    assert rows[1] == ["User", "Database", "Niloofar"]

def test_ast_to_docx_with_sample_ast(tmp_path):
    ast_path = Path(__file__).parent / "fixtures" / "pandoc_ast_sample.json"
    ast_data = json.loads(ast_path.read_text(encoding="utf-8"))

    doc = Document()
    tmpl = Template.load("purple_book")
    renderer = DocxRenderer(doc, tmpl)

    ast_to_docx(ast_data, renderer)

    out_docx = tmp_path / "test_out.docx"
    doc.save(str(out_docx))
    assert out_docx.exists()
    assert out_docx.stat().st_size > 0

    # Inspect rendered docx tables and paragraphs
    assert len(doc.tables) >= 4  # 2 headings badges + 2 callouts + 1 data table
    # Check that Persian number was rendered in document
    full_text = " ".join([p.text for p in doc.paragraphs] + [c.paragraphs[0].text for t in doc.tables for row in t.rows for c in row.cells])
    assert "۱.۵" in full_text
    assert "۱.۴.۱" in full_text
    assert "نکتهٔ DBA" in full_text
    assert "هشدار" in full_text


def test_ast_to_docx_preserves_inline_formatting():
    ast_dict = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [
            {
                "t": "Para",
                "c": [
                    {"t": "Str", "c": "This has "},
                    {"t": "Strong", "c": [{"t": "Str", "c": "bold"}]},
                    {"t": "Space"},
                    {"t": "Emph", "c": [{"t": "Str", "c": "italic"}]},
                    {"t": "Space"},
                    {"t": "Code", "c": [["", [], []], "x = 1"]},
                ],
            }
        ],
    }
    doc = Document()
    tmpl = Template.load("purple_book")
    renderer = DocxRenderer(doc, tmpl)
    ast_to_docx(ast_dict, renderer)
    xml = doc.paragraphs[0]._p.xml
    assert "bold" in xml
    assert "italic" in xml
    assert "x = 1" in xml
    assert "<w:b" in xml
    assert "<w:i" in xml


def test_ast_to_docx_ordered_and_bullet_lists():
    ast_dict = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [
            {
                "t": "OrderedList",
                "c": [
                    [1, {"t": "Decimal"}, {"t": "Period"}],
                    [
                        [{"t": "Plain", "c": [{"t": "Str", "c": "first item"}]}],
                        [{"t": "Plain", "c": [{"t": "Str", "c": "second item"}]}],
                    ],
                ],
            },
            {
                "t": "BulletList",
                "c": [
                    [{"t": "Plain", "c": [{"t": "Str", "c": "bullet one"}]}],
                    [{"t": "Plain", "c": [{"t": "Str", "c": "bullet two"}]}],
                ],
            },
        ],
    }
    doc = Document()
    tmpl = Template.load("purple_book")
    renderer = DocxRenderer(doc, tmpl)
    ast_to_docx(ast_dict, renderer)
    texts = [p.text for p in doc.paragraphs if p.text.strip()]
    assert any("first item" in t for t in texts)
    assert any("second item" in t for t in texts)
    assert any(t.strip().startswith("1.") for t in texts)
    assert any(t.strip().startswith("2.") for t in texts)
    assert any("bullet one" in t for t in texts)
    assert "•" not in "".join(texts)


def test_ast_to_docx_code_block():
    ast_dict = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [
            {
                "t": "CodeBlock",
                "c": [
                    ["", ["sql"], []],
                    "SELECT TOP 10 id FROM orders;"
                ]
            }
        ]
    }
    doc = Document()
    tmpl = Template.load("purple_book")
    renderer = DocxRenderer(doc, tmpl)
    ast_to_docx(ast_dict, renderer)

    assert len(doc.tables) == 1
    cell = doc.tables[0].cell(0, 0)
    assert "SELECT" in cell.text
    assert "orders" in cell.text
    # Cell has background shading
    assert 'w:fill="F6F8FA"' in cell._tc.xml

