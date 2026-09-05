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


def test_ast_to_docx_blockquote_preserves_inline_formatting():
    ast_dict = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [
            {
                "t": "BlockQuote",
                "c": [
                    {
                        "t": "Para",
                        "c": [
                            {"t": "Str", "c": "Login "},
                            {"t": "Strong", "c": [{"t": "Str", "c": "معمولاً"}]},
                            {"t": "Str", "c": " هویت Instance است."},
                        ],
                    }
                ],
            }
        ],
    }
    doc = Document()
    tmpl = Template.load("purple_book")
    renderer = DocxRenderer(doc, tmpl)
    ast_to_docx(ast_dict, renderer)
    quotes = [p for p in doc.paragraphs if p.text.strip()]
    assert quotes
    xml = quotes[0]._p.xml
    assert "معمولاً" in xml
    assert "<w:b" in xml
    assert 'w:fill="ECE4F1"' in xml


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


def test_ast_to_docx_rich_callouts_preserve_formatting():
    """F-05: Verifies that callout Divs retain multi-paragraph, bold, italic, list, and code formatting."""
    ast_dict = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [
            {
                "t": "Div",
                "c": [
                    ["", ["note"], [["title", "نکتهٔ کلیدی"]]],
                    [
                        {
                            "t": "Para",
                            "c": [
                                {"t": "Str", "c": "این "},
                                {"t": "Strong", "c": [{"t": "Str", "c": "متن بولد"}]},
                                {"t": "Str", "c": " و "},
                                {"t": "Emph", "c": [{"t": "Str", "c": "متن ایتالیک"}]},
                                {"t": "Str", "c": " است."},
                            ],
                        },
                        {
                            "t": "BulletList",
                            "c": [
                                [{"t": "Plain", "c": [{"t": "Str", "c": "مورد اول لیست"}]}],
                                [{"t": "Plain", "c": [{"t": "Str", "c": "مورد دوم لیست"}]}],
                            ],
                        },
                        {
                            "t": "CodeBlock",
                            "c": [["", ["json"], []], '{"active": true}'],
                        },
                    ],
                ],
            }
        ],
    }
    doc = Document()
    tmpl = Template.load("purple_book")
    renderer = DocxRenderer(doc, tmpl)
    ast_to_docx(ast_dict, renderer)

    # A callout table is produced
    assert len(doc.tables) == 1
    callout_tbl = doc.tables[0]
    cell_body = callout_tbl.cell(1, 0)
    body_xml = cell_body._tc.xml

    # Formatting must be preserved in OOXML
    assert "متن بولد" in cell_body.text
    assert "متن ایتالیک" in cell_body.text
    assert "<w:b" in body_xml
    assert "<w:i" in body_xml
    assert "مورد اول لیست" in cell_body.text
    assert "مورد دوم لیست" in cell_body.text
    assert '{"active": true}' in cell_body.text


def test_ast_to_docx_strikeout_superscript_subscript_underline():
    """F-06: Verifies inline formatting nodes: Strikeout, Superscript, Subscript, Underline, SmallCaps."""
    ast_dict = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [
            {
                "t": "Para",
                "c": [
                    {"t": "Strikeout", "c": [{"t": "Str", "c": "خط‌خورده"}]},
                    {"t": "Space"},
                    {"t": "Superscript", "c": [{"t": "Str", "c": "بالانویس"}]},
                    {"t": "Space"},
                    {"t": "Subscript", "c": [{"t": "Str", "c": "زیرنویس"}]},
                    {"t": "Space"},
                    {"t": "Underline", "c": [{"t": "Str", "c": "زیرخط"}]},
                    {"t": "Space"},
                    {"t": "SmallCaps", "c": [{"t": "Str", "c": "caps"}]},
                ],
            }
        ],
    }
    doc = Document()
    tmpl = Template.load("purple_book")
    renderer = DocxRenderer(doc, tmpl)
    ast_to_docx(ast_dict, renderer)

    p_xml = doc.paragraphs[0]._p.xml
    assert "<w:strike" in p_xml
    assert 'w:val="superscript"' in p_xml
    assert 'w:val="subscript"' in p_xml
    assert "<w:u" in p_xml
    assert "<w:smallCaps" in p_xml


def test_ast_to_docx_table_multiple_tbodies_and_caption():
    """F-06: Verifies multi-tbody table structure and caption."""
    ast_dict = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [
            {
                "t": "Table",
                "c": [
                    ["", [], []],
                    # Caption
                    [None, [{"t": "Plain", "c": [{"t": "Str", "c": "جدول ۱. مقایسه کارایی"}]}]],
                    [],
                    # thead
                    ["", [[["", [], []], [[None, [{"t": "Plain", "c": [{"t": "Str", "c": "نام"}]}], 1, 1, [{"t": "Plain", "c": [{"t": "Str", "c": "نام"}]}]]]]]],
                    # tbodies (2 tbodies)
                    [
                        ["", 0, [], [[["", [], []], [[None, [], 1, 1, [{"t": "Plain", "c": [{"t": "Str", "c": "سطر اول"}]}]]]]]],
                        ["", 0, [], [[["", [], []], [[None, [], 1, 1, [{"t": "Plain", "c": [{"t": "Str", "c": "سطر دوم"}]}]]]]]],
                    ],
                    [],
                ],
            }
        ],
    }
    doc = Document()
    tmpl = Template.load("purple_book")
    renderer = DocxRenderer(doc, tmpl)
    ast_to_docx(ast_dict, renderer)

    assert len(doc.tables) == 1
    tbl = doc.tables[0]
    assert len(tbl.rows) == 3  # 1 header + 2 data rows
    assert tbl.cell(1, 0).text == "سطر اول"
    assert tbl.cell(2, 0).text == "سطر دوم"
    # Caption rendered
    assert any("جدول ۱. مقایسه کارایی" in p.text for p in doc.paragraphs)


def test_ast_to_docx_definition_list():
    """F-06: Verifies DefinitionList rendering."""
    ast_dict = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [
            {
                "t": "DefinitionList",
                "c": [
                    [
                        [{"t": "Str", "c": "Redis"}],
                        [[{"t": "Para", "c": [{"t": "Str", "c": "In-memory data store."}]}]]
                    ]
                ]
            }
        ]
    }
    doc = Document()
    tmpl = Template.load("purple_book")
    renderer = DocxRenderer(doc, tmpl)
    ast_to_docx(ast_dict, renderer)

    full_text = " ".join(p.text for p in doc.paragraphs)
    assert "Redis" in full_text
    assert "In-memory data store." in full_text


def test_ast_to_docx_unknown_block_raises_convert_error():
    """F-06: Verifies explicit error for unknown AST blocks."""
    from md_to_docx.mermaid import ConvertError
    ast_dict = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [{"t": "CustomUnsupportedBlockXYZ", "c": []}]
    }
    doc = Document()
    tmpl = Template.load("purple_book")
    renderer = DocxRenderer(doc, tmpl)
    with pytest.raises(ConvertError) as exc_info:
        ast_to_docx(ast_dict, renderer)
    assert "Unsupported Pandoc AST block type" in str(exc_info.value)


def test_ast_to_docx_callout_with_nested_table():
    """F-05: Verifies that a table inside a callout is rendered inside the cell, not at root."""
    ast_dict = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [
            {
                "t": "Div",
                "c": [
                    ["", ["note"], [["title", "نکته مهم"]]],
                    [
                        {
                            "t": "Table",
                            "c": [
                                ["", [], []],
                                [None, []],
                                [],
                                ["", [[["", [], []], [[None, [], 1, 1, [{"t": "Plain", "c": [{"t": "Str", "c": "سربرگ"}]}]]]]]],
                                [["", 0, [], [[["", [], []], [[None, [], 1, 1, [{"t": "Plain", "c": [{"t": "Str", "c": "داده"}]}]]]]]]],
                                [],
                            ],
                        }
                    ],
                ],
            }
        ],
    }
    doc = Document()
    tmpl = Template.load("purple_book")
    renderer = DocxRenderer(doc, tmpl)
    ast_to_docx(ast_dict, renderer)

    # Document should only contain 1 top-level table (the callout table)
    assert len(doc.tables) == 1
    callout_tbl = doc.tables[0]
    cell_body = callout_tbl.cell(1, 0)
    # The cell must contain the nested table
    assert len(cell_body.tables) == 1
    nested_tbl = cell_body.tables[0]
    assert "سربرگ" in nested_tbl.cell(0, 0).text
    assert "داده" in nested_tbl.cell(1, 0).text


def test_ast_to_docx_line_break_emits_w_br():
    """Verifies that Pandoc LineBreak emits <w:br/> rather than \\n in <w:t>."""
    ast_dict = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [
            {
                "t": "Para",
                "c": [
                    {"t": "Str", "c": "خط اول"},
                    {"t": "LineBreak"},
                    {"t": "Str", "c": "خط دوم"},
                ],
            }
        ],
    }
    doc = Document()
    tmpl = Template.load("purple_book")
    renderer = DocxRenderer(doc, tmpl)
    ast_to_docx(ast_dict, renderer)

    p_xml = doc.paragraphs[0]._p.xml
    assert "<w:br" in p_xml
    assert "\n" not in "".join(doc.paragraphs[0]._p.xpath(".//w:t/text()"))


def test_ast_to_docx_raw_block_pagebreak():
    """F-12: Verifies that raw \\pagebreak directives produce actual page breaks."""
    ast_dict = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [
            {"t": "Para", "c": [{"t": "Str", "c": "صفحه اول"}]},
            {"t": "RawBlock", "c": ["tex", "\\pagebreak"]},
            {"t": "Para", "c": [{"t": "Str", "c": "صفحه دوم"}]},
        ],
    }
    doc = Document()
    tmpl = Template.load("purple_book")
    renderer = DocxRenderer(doc, tmpl)
    ast_to_docx(ast_dict, renderer)

    full_xml = doc._body._element.xml
    assert 'w:type="page"' in full_xml


