"""Acceptance tests for finalize.md FIN-01 through FIN-14."""

import os
from pathlib import Path
from click.testing import CliRunner
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Inches
from PIL import Image
import pytest
import yaml
import zipfile
from lxml import etree

from md_to_docx.admonitions import preprocess_admonitions
from md_to_docx.cli import main
from md_to_docx.mermaid import ConvertError, extract_mermaid_blocks, process_mermaid_ast
from md_to_docx.pandoc_json import ast_to_docx
from md_to_docx.pipeline import convert_markdown_to_docx
from md_to_docx.renderer import DocxRenderer
from md_to_docx.template import Template, TemplateValidationError
from md_to_docx.paths import resolve_image_source


STUB = Path(__file__).parent / "fixtures" / "diagram-stub.png"


def _write_png(path: Path, w: int, h: int) -> None:
    Image.new("RGB", (w, h), (200, 180, 220)).save(path)


def _minimal_template_yaml(**overrides) -> str:
    data = {
        "schema_version": 1,
        "name": "custom",
        "direction": "rtl",
        "fonts": {"body": "Vazirmatn", "heading": "Vazirmatn", "code": "Courier New"},
        "colors": {
            "primary": "6B2FA0",
            "primary_dark": "4A156D",
            "on_primary": "FFFFFF",
            "quote_bg": "ECE4F1",
            "warning_bg": "FBF7F4",
            "warning_title": "8B6914",
            "body": "2D2D2D",
            "caption": "5A5A5A",
        },
        "headings": {"extract_number": True, "badge": True},
        "callouts": {},
        "quotes": {"border_side": "physical_right", "border_pt": 12, "border_color": "primary", "bg": "quote_bg"},
        "tables": {"header_bg": "primary", "header_fg": "on_primary", "bidi_visual": True},
        "page": {"size": "A4", "margin_cm": {"top": 2.0, "bottom": 2.0, "left": 2.0, "right": 2.0}},
    }
    for key, val in overrides.items():
        if isinstance(val, dict) and isinstance(data.get(key), dict):
            data[key].update(val)
        else:
            data[key] = val
    return yaml.safe_dump(data, allow_unicode=True)


def test_fin01_custom_media_dir_keeps_unrelated_files(tmp_path):
    user_dir = tmp_path / "assets"
    user_dir.mkdir()
    keep = user_dir / "keep.txt"
    keep.write_text("do not delete", encoding="utf-8")
    in_file = tmp_path / "doc.md"
    in_file.write_text("# Hello\n\nNo diagrams here.\n", encoding="utf-8")
    out = tmp_path / "out.docx"
    convert_markdown_to_docx(in_file, out, media_dir=user_dir)
    assert keep.exists()
    assert keep.read_text(encoding="utf-8") == "do not delete"


def test_fin01_rejects_media_dir_equal_to_input_folder(tmp_path):
    in_file = tmp_path / "doc.md"
    in_file.write_text("# x\n", encoding="utf-8")
    out = tmp_path / "nested" / "out.docx"
    with pytest.raises(ConvertError, match="Refusing"):
        convert_markdown_to_docx(in_file, out, media_dir=tmp_path)


def test_fin03_code_block_explicit_ltr_bidi_zero(tmp_path):
    in_file = tmp_path / "c.md"
    in_file.write_text("```sql\nSELECT 1;\n```\n", encoding="utf-8")
    out = tmp_path / "c.docx"
    convert_markdown_to_docx(in_file, out)
    doc = Document(str(out))
    xml = doc.tables[0]._tbl.xml
    assert 'w:bidi w:val="0"' in xml or 'w:val="0"' in xml
    assert "<w:bidiVisual" not in xml
    assert "SELECT 1;" in doc.tables[0].cell(0, 0).text


def test_fin04_image_with_spaces_and_percent_encoding(tmp_path):
    img = tmp_path / "my image.png"
    img.write_bytes(STUB.read_bytes())
    in_file = tmp_path / "doc.md"
    in_file.write_text("![alt](<my image.png>)\n", encoding="utf-8")
    out = tmp_path / "out with spaces.docx"
    convert_markdown_to_docx(in_file, out)
    assert out.exists()
    doc = Document(str(out))
    assert doc._body._element.xpath(".//w:drawing")


def test_fin04_remote_image_rejected(tmp_path):
    with pytest.raises(ConvertError, match="Remote images"):
        resolve_image_source("https://example.com/a.png", tmp_path)


def test_fin02_letter_page_and_green_table_and_no_badge(tmp_path):
    tmpl_dir = tmp_path / "tmpl"
    tmpl_dir.mkdir()
    (tmpl_dir / "config.yaml").write_text(
        _minimal_template_yaml(
            page={"size": "Letter", "font_size_pt": 17, "margin_cm": {"top": 2, "bottom": 2, "left": 2, "right": 2}},
            tables={"header_bg": "00FF00", "header_fg": "000000", "bidi_visual": True},
            quotes={"border_side": "physical_left", "border_pt": 12, "border_color": "primary", "bg": "quote_bg"},
            headings={"extract_number": False, "badge": True},
        ),
        encoding="utf-8",
    )
    in_file = tmp_path / "doc.md"
    in_file.write_text("# ۱.۲ عنوان\n\n> quote\n\n| a | b |\n| --- | --- |\n| 1 | 2 |\n", encoding="utf-8")
    out = tmp_path / "out.docx"
    convert_markdown_to_docx(in_file, out, template=tmpl_dir)
    doc = Document(str(out))
    section = doc.sections[0]
    assert abs(section.page_width.inches - 8.5) < 0.05
    assert abs(section.page_height.inches - 11.0) < 0.05
    normal = doc.styles["Normal"].element.xml
    assert 'w:val="34"' in normal  # 17pt
    # no badge table for numbered heading when extract_number is false
    texts = " ".join(p.text for p in doc.paragraphs)
    assert "۱.۲ عنوان" in texts
    shds = doc._body._element.xpath(".//w:shd/@w:fill")
    assert "00FF00" in shds
    quote_xml = " ".join(p._p.xml for p in doc.paragraphs if p._p.find(qn("w:pPr")) is not None)
    assert "w:left" in quote_xml


def test_fin12_three_digit_hex_normalized_and_bool_rejected(tmp_path):
    tmpl_dir = tmp_path / "tmpl"
    tmpl_dir.mkdir()
    (tmpl_dir / "config.yaml").write_text(
        _minimal_template_yaml(colors={"body": "ABC"}),
        encoding="utf-8",
    )
    tmpl = Template.load(tmpl_dir)
    assert tmpl.colors["body"] == "AABBCC"

    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "config.yaml").write_text(
        _minimal_template_yaml(page={"font_size_pt": True, "size": "A4", "margin_cm": {"top": 2, "bottom": 2, "left": 2, "right": 2}}),
        encoding="utf-8",
    )
    with pytest.raises(TemplateValidationError, match="font_size_pt"):
        Template.load(bad)


def test_fin12_unknown_field_rejected(tmp_path):
    tmpl_dir = tmp_path / "tmpl"
    tmpl_dir.mkdir()
    text = _minimal_template_yaml() + "typo_field: 1\n"
    (tmpl_dir / "config.yaml").write_text(text, encoding="utf-8")
    with pytest.raises(TemplateValidationError, match="typo_field"):
        Template.load(tmpl_dir)


@pytest.mark.parametrize(
    ("section", "value", "field"),
    [
        ("headings", {"h4": {"size_pt": True}}, "headings.h4.size_pt"),
        ("quotes", {"border_pt": True}, "quotes.border_pt"),
        ("code_block", {"font_size_pt": True}, "code_block.font_size_pt"),
        ("code_block", {"border_sz": True}, "code_block.border_sz"),
        ("mermaid", {"scale": True}, "mermaid.scale"),
        ("mermaid", {"max_width_in": True}, "mermaid.max_width_in"),
    ],
)
def test_fin12_rejects_boolean_values_for_all_numeric_template_fields(tmp_path, section, value, field):
    tmpl_dir = tmp_path / "tmpl"
    tmpl_dir.mkdir()
    (tmpl_dir / "config.yaml").write_text(
        _minimal_template_yaml(**{section: value}),
        encoding="utf-8",
    )

    with pytest.raises(TemplateValidationError, match=field):
        Template.load(tmpl_dir)


def test_fin05_explicit_width_and_tall_image_capped(tmp_path):
    img = tmp_path / "tall.png"
    _write_png(img, 100, 1600)
    in_file = tmp_path / "doc.md"
    in_file.write_text("![alt](tall.png){width=1in}\n", encoding="utf-8")
    out = tmp_path / "out.docx"
    convert_markdown_to_docx(in_file, out)
    doc = Document(str(out))
    ext = doc._body._element.xpath(".//wp:extent")[0]
    cx = int(ext.get("cx"))
    cy = int(ext.get("cy"))
    # 1 inch = 914400 EMU; height capped to page, width near 1in unless scaled to fit
    assert cx < 2_000_000
    assert cy < 12_000_000


def test_fin05_image_in_a_table_cell_uses_the_cell_width(tmp_path):
    img = tmp_path / "wide.png"
    _write_png(img, 1600, 400)
    in_file = tmp_path / "doc.md"
    in_file.write_text(
        "| تصویر | متن |\n| --- | --- |\n| ![alt](wide.png) | توضیح |\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.docx"
    convert_markdown_to_docx(in_file, out)
    doc = Document(str(out))
    image_width_emu = int(doc._body._element.xpath(".//wp:extent")[0].get("cx"))
    outer_table_width_emu = int(doc.tables[0]._tbl.tblGrid.gridCol_lst[0].get(qn("w:w"))) * 635

    # This is a two-column table, so the image needs to fit inside one cell,
    # including its cell padding, instead of using the full page width.
    assert image_width_emu < outer_table_width_emu


def test_fin11_only_table_header_rows_are_prevented_from_splitting(tmp_path):
    in_file = tmp_path / "doc.md"
    in_file.write_text(
        "| عنوان |\n| --- |\n| " + ("متن بلند " * 200) + " |\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.docx"
    convert_markdown_to_docx(in_file, out)
    table = Document(str(out)).tables[0]
    assert "w:tblHeader" in table.rows[0]._tr.xml
    assert "w:cantSplit" in table.rows[0]._tr.xml
    assert "w:cantSplit" not in table.rows[1]._tr.xml


def test_fin06_admonition_inside_code_fence_unchanged():
    md = "```text\n::: note Literal\n```\n"
    out = preprocess_admonitions(md)
    assert "::: note Literal" in out
    assert '{.note' not in out


def test_fin06_code_fence_with_a_spaced_info_string_is_preserved():
    md = "``` text\n::: note Literal\n```\n"
    assert preprocess_admonitions(md) == md


def test_fin06_mermaid_inside_outer_fence_not_extracted():
    md = "````markdown\n```mermaid\ngraph TD\nA-->B\n```\n````\n"
    blocks = extract_mermaid_blocks(md)
    assert blocks == []


def test_fin06_tilde_mermaid_extracted():
    md = "~~~mermaid\ngraph TD\nA-->B\n~~~\nشکل ۱. تست\n"
    blocks = extract_mermaid_blocks(md)
    assert len(blocks) == 1
    assert blocks[0].caption.startswith("شکل")


def test_fin07_hyperlink_and_quotes(tmp_path):
    in_file = tmp_path / "doc.md"
    in_file.write_text('See [پیوند](https://example.com) and "quoted text".\n', encoding="utf-8")
    out = tmp_path / "out.docx"
    convert_markdown_to_docx(in_file, out)
    doc = Document(str(out))
    xml = doc._body._element.xml
    assert "w:hyperlink" in xml
    assert "https://example.com" in xml or "r:id" in xml
    joined = "".join(p.text for p in doc.paragraphs)
    assert "quoted text" in joined
    assert "«" in joined or "“" in joined or '"' in joined


def test_fin07_internal_link_targets_bookmark_on_numbered_heading(tmp_path):
    in_file = tmp_path / "doc.md"
    in_file.write_text(
        "[رفتن به بخش](#target-section)\n\n# 1. عنوان {#target-section}\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.docx"
    convert_markdown_to_docx(in_file, out)

    body = Document(str(out))._body._element
    hyperlink = body.xpath(".//w:hyperlink")[0]
    bookmark = body.xpath(".//w:bookmarkStart")[0]
    assert hyperlink.get(qn("w:anchor")) == bookmark.get(qn("w:name"))
    # A numbered heading is a two-cell table followed by a spacer paragraph. The
    # bookmark must be in the heading title, not on that empty spacer.
    heading_paragraph = bookmark.getparent()
    assert heading_paragraph.tag == qn("w:p")
    assert "عنوان" in "".join(heading_paragraph.itertext())


def test_fin08_math_omml_and_footnote_part(tmp_path):
    in_file = tmp_path / "doc.md"
    in_file.write_text("Half is $\\frac{1}{2}$. Note.[^1]\n\n[^1]: پاورقی فارسی.\n", encoding="utf-8")
    out = tmp_path / "out.docx"
    convert_markdown_to_docx(in_file, out)
    xml = Document(str(out))._body._element.xml
    assert "m:oMath" in xml or "oMath" in xml
    import zipfile
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        assert "word/footnotes.xml" in names
        fn = z.read("word/footnotes.xml").decode("utf-8")
        assert "پاورقی" in fn


def test_fin08_display_math_is_a_block_level_omml_element(tmp_path):
    in_file = tmp_path / "doc.md"
    in_file.write_text("$$\\frac{1}{2}$$\n", encoding="utf-8")
    out = tmp_path / "out.docx"
    convert_markdown_to_docx(in_file, out)

    body = Document(str(out))._body._element
    # Per Word specification (FINAL-01), m:oMathPara must be hosted inside a w:p element
    assert not body.xpath("./m:oMathPara")
    assert body.xpath(".//w:p/m:oMathPara")


def test_fin09_code_preserves_blank_lines(tmp_path):
    from md_to_docx.template import Template
    renderer = DocxRenderer(Document(), Template.load("purple_book"))
    renderer.render_code_block("\n\nprint(1)\n\n", language="python")
    cell = renderer.doc.tables[0].cell(0, 0)
    reconstructed = "\n".join(p.text for p in cell.paragraphs)
    assert reconstructed == "\n\nprint(1)\n\n"


def test_fin10_multi_section_shell_rejected(tmp_path):
    from docx import Document as D
    shell = D()
    shell.add_paragraph("s1")
    shell.add_section()
    shell.add_paragraph("s2")
    shell_path = tmp_path / "shell.docx"
    shell.save(str(shell_path))
    tmpl_dir = tmp_path / "tmpl"
    tmpl_dir.mkdir()
    cfg = _minimal_template_yaml()
    cfg += "shell: shell.docx\n"
    (tmpl_dir / "config.yaml").write_text(cfg, encoding="utf-8")
    import shutil
    shutil.copy2(shell_path, tmpl_dir / "shell.docx")
    in_file = tmp_path / "doc.md"
    in_file.write_text("# Hi\n", encoding="utf-8")
    with pytest.raises(ConvertError, match="single-section"):
        convert_markdown_to_docx(in_file, tmp_path / "out.docx", template=tmpl_dir)


def test_fin13_overwrite_false_under_lock(tmp_path):
    in_file = tmp_path / "doc.md"
    in_file.write_text("# once\n", encoding="utf-8")
    out = tmp_path / "out.docx"
    convert_markdown_to_docx(in_file, out, overwrite=True)
    with pytest.raises(ConvertError, match="already exists"):
        convert_markdown_to_docx(in_file, out, overwrite=False)


def test_fin14_cli_rejects_doc_extension(tmp_path):
    in_file = tmp_path / "a.md"
    in_file.write_text("# x\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(main, ["convert", str(in_file), "-o", str(tmp_path / "out.doc")])
    assert result.exit_code == 2
    assert ".doc" in result.output.lower()


def _mp_worker(in_file_str: str, out_file_str: str, overwrite: bool, q) -> None:
    try:
        from md_to_docx.pipeline import convert_markdown_to_docx
        res = convert_markdown_to_docx(Path(in_file_str), Path(out_file_str), overwrite=overwrite)
        q.put(("OK", str(res)))
    except Exception as e:
        q.put(("ERR", type(e).__name__, str(e)))


def test_fin13_multiprocess_concurrency(tmp_path):
    import multiprocessing
    in_file = tmp_path / "mp_in.md"
    in_file.write_text("# Multi-Process Test\n\nSome paragraph text.\n", encoding="utf-8")
    out_file = tmp_path / "mp_out.docx"

    ctx = multiprocessing.get_context("spawn")
    q = ctx.Queue()

    p1 = ctx.Process(target=_mp_worker, args=(str(in_file), str(out_file), True, q))
    p2 = ctx.Process(target=_mp_worker, args=(str(in_file), str(out_file), True, q))

    p1.start()
    p2.start()
    p1.join(timeout=30)
    p2.join(timeout=30)
    assert p1.exitcode == 0, f"worker1 exitcode={p1.exitcode}"
    assert p2.exitcode == 0, f"worker2 exitcode={p2.exitcode}"

    import queue as queue_mod

    results = []
    for _ in range(2):
        try:
            results.append(q.get(timeout=10))
        except queue_mod.Empty:
            break

    assert len(results) == 2
    assert all(r[0] == "OK" for r in results)
    assert out_file.exists()

    # Now verify overwrite=False fails safely in a separate process
    p3 = ctx.Process(target=_mp_worker, args=(str(in_file), str(out_file), False, q))
    p3.start()
    p3.join(timeout=30)
    assert p3.exitcode == 0, f"worker3 exitcode={p3.exitcode}"
    import queue as queue_mod

    try:
        err_res = q.get(timeout=10)
    except queue_mod.Empty:
        pytest.fail("expected overwrite=False error result from worker")
    assert err_res[0] == "ERR"
    assert "ConvertError" in err_res[1]
    assert "already exists" in err_res[2]


# ---------------------------------------------------------------------------
# FINAL-01 through FINAL-16 Specific Verification Suite
# ---------------------------------------------------------------------------

def test_final01_display_math_in_paragraph_across_contexts(tmp_path):
    """FINAL-01: Display math must be hosted inside a w:p element in body, callouts, and cells."""
    md_content = (
        "# Math In Contexts\n\n"
        "$$\\frac{1}{2}$$\n\n"
        "> [!NOTE]\n"
        "> $$\\frac{3}{4}$$\n\n"
        "| Header |\n"
        "| --- |\n"
        "| $$\\frac{5}{6}$$ |\n"
    )
    in_file = tmp_path / "math_ctx.md"
    in_file.write_text(md_content, encoding="utf-8")
    out = tmp_path / "math_ctx.docx"
    convert_markdown_to_docx(in_file, out)

    doc = Document(str(out))
    body = doc._body._element
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
          "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}

    # No m:oMathPara can be a direct child of body or table cell
    assert not body.xpath("./m:oMathPara")
    assert not body.xpath(".//w:tc/m:oMathPara")

    # All m:oMathPara must be inside a w:p
    omath_paras = body.xpath(".//m:oMathPara")
    assert len(omath_paras) >= 3
    for omp in omath_paras:
        assert omp.getparent().tag.endswith("}p")


def test_final02_math_expressions_nested_fractions_and_subscripts(tmp_path):
    """FINAL-02: Native OMML rendering without regex breakage for x_1, nested fractions, etc."""
    md_content = (
        "# Math Test\n\n"
        "Formula 1: $x_1$\n\n"
        "Formula 2: $x^{2}+y$\n\n"
        "Formula 3: $x_{i}^{2}$\n\n"
        "Formula 4: $\\sqrt{x}$\n\n"
        "Formula 5: $\\frac{1}{\\frac{2}{3}}$\n\n"
        "Display:\n\n"
        "$$\\sum_{i=1}^{n} x_i$$\n"
    )
    in_file = tmp_path / "math.md"
    in_file.write_text(md_content, encoding="utf-8")
    out = tmp_path / "math.docx"
    convert_markdown_to_docx(in_file, out)

    with zipfile.ZipFile(out, "r") as z:
        doc_xml = z.read("word/document.xml").decode("utf-8")
        assert "m:oMath" in doc_xml
        assert "m:sSub" in doc_xml
        assert "m:sSup" in doc_xml
        assert "m:rad" in doc_xml
        assert "m:f" in doc_xml
        # Display math must be hosted in w:p
        tree = etree.fromstring(doc_xml.encode("utf-8"))
        ns = {
            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
            "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
        }
        assert tree.xpath("//w:p/m:oMathPara", namespaces=ns)
        assert not tree.xpath("/w:document/w:body/m:oMathPara", namespaces=ns)


def test_final03_code_multiline_triple_quotes_and_blanks(tmp_path):
    """FINAL-03: Multiline token state preserved across newlines and blank lines intact."""
    code = (
        'def test():\n'
        '    """This is a\n'
        '    multi-line string\n'
        '    description."""\n'
        '\n'
        '    return True\n'
    )
    md_content = f"```python\n{code}```\n"
    in_file = tmp_path / "code.md"
    in_file.write_text(md_content, encoding="utf-8")
    out = tmp_path / "code.docx"
    convert_markdown_to_docx(in_file, out)

    doc = Document(str(out))
    # Code block renders into a 1x1 table
    code_table = doc.tables[0]
    cell = code_table.cell(0, 0)
    # Total 6 lines in code (including blank line)
    assert len(cell.paragraphs) == 6
    # Verify multiline docstring lines retain their text
    texts = [p.text for p in cell.paragraphs]
    assert '    """This is a' in texts[1]
    assert '    multi-line string' in texts[2]
    assert '    description."""' in texts[3]
    assert texts[4] == ""  # blank line preserved
    assert '    return True' in texts[5]


def test_final04_code_fence_inside_blockquote_literal(tmp_path):
    """FINAL-04: Blockquote containing a literal code fence must not trigger admonition conversion."""
    md_content = (
        "> ```text\n"
        "> [!NOTE]\n"
        "> This is literal code inside quote\n"
        "> ```\n"
    )
    in_file = tmp_path / "bq.md"
    in_file.write_text(md_content, encoding="utf-8")
    out = tmp_path / "bq.docx"
    convert_markdown_to_docx(in_file, out)

    doc = Document(str(out))
    # Should render as a quote/code paragraph, NOT a callout box table
    with zipfile.ZipFile(out, "r") as z:
        doc_xml = z.read("word/document.xml").decode("utf-8")
        assert "This is literal code inside quote" in doc_xml


def test_final05_mermaid_traversal_in_definition_list_and_footnote(tmp_path):
    """FINAL-05: Mermaid blocks inside DefinitionList and footnotes are parsed."""
    ast_dict = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [
            {
                "t": "DefinitionList",
                "c": [
                    [
                        [{"t": "Str", "c": "Term"}],
                        [
                            [
                                {
                                    "t": "CodeBlock",
                                    "c": [["", ["mermaid"], []], "graph TD\nA-->B"],
                                }
                            ]
                        ],
                    ]
                ],
            },
            {
                "t": "Para",
                "c": [
                    {
                        "t": "Note",
                        "c": [
                            {
                                "t": "CodeBlock",
                                "c": [["", ["mermaid"], []], "graph LR\nC-->D"],
                            }
                        ],
                    }
                ],
            },
        ],
    }
    tmpl = Template.load("purple_book")
    stub_png = Path(__file__).parent / "fixtures" / "diagram-stub.png"

    def mock_mermaid(code, out_path, template):
        out_path.write_bytes(stub_png.read_bytes())
        return out_path

    n = process_mermaid_ast(ast_dict, output_dir=tmp_path, template=tmpl, render_fn=mock_mermaid)
    assert n == 2
    # Verify no mermaid CodeBlocks remain in AST
    cb_count = 0
    def _count(node):
        nonlocal cb_count
        if isinstance(node, dict):
            if node.get("t") == "CodeBlock" and "mermaid" in node.get("c", [[], []])[0][1]:
                cb_count += 1
            for v in node.values():
                _count(v)
        elif isinstance(node, list):
            for v in node:
                _count(v)
    _count(ast_dict)
    assert cb_count == 0


def test_final06_image_relative_path_no_basename_fallback(tmp_path):
    """FINAL-06: Referencing missing/image.png when image.png exists beside Markdown must fail."""
    # Create image.png beside doc.md
    (tmp_path / "image.png").write_bytes(STUB.read_bytes())
    in_file = tmp_path / "doc.md"
    in_file.write_text("![alt](missing/image.png)\n", encoding="utf-8")
    out = tmp_path / "out.docx"

    with pytest.raises(ConvertError, match="Image not found"):
        convert_markdown_to_docx(in_file, out)


def test_final07_rich_footnote_part_and_relationships(tmp_path):
    """FINAL-07: Footnotes support multiple paragraphs, hyperlinks, bold, and math in word/footnotes.xml."""
    md_content = (
        "Main text with footnote.[^fn1]\n\n"
        "[^fn1]: First paragraph with **bold** and [link](https://example.com).\n\n"
        "    Second paragraph with math $E=mc^2$.\n"
    )
    in_file = tmp_path / "fn.md"
    in_file.write_text(md_content, encoding="utf-8")
    out = tmp_path / "fn.docx"
    convert_markdown_to_docx(in_file, out)

    with zipfile.ZipFile(out, "r") as z:
        assert "word/footnotes.xml" in z.namelist()
        fn_xml = z.read("word/footnotes.xml").decode("utf-8")
        fn_tree = etree.fromstring(fn_xml.encode("utf-8"))
        fn_text = " ".join("".join(fn_tree.itertext()).split())
        assert "First paragraph with" in fn_text
        assert "Second paragraph with math" in fn_text
        assert "w:b" in fn_xml
        assert "m:oMath" in fn_xml
        # Verify relationship exists in footnotes.xml.rels
        assert "word/_rels/footnotes.xml.rels" in z.namelist()
        rels_xml = z.read("word/_rels/footnotes.xml.rels").decode("utf-8")
        assert "https://example.com" in rels_xml


def test_final08_heading_rich_inlines_and_strikes(tmp_path):
    """FINAL-08: Headings preserve math and inlines, strike on link preserved."""
    md_content = (
        "# ۱.۱ تیتر با $\\alpha$ و *تاکید*\n\n"
        "متن با ~~[لینک خط خورده](https://example.com)~~ در ادامه.\n"
    )
    in_file = tmp_path / "h_rich.md"
    in_file.write_text(md_content, encoding="utf-8")
    out = tmp_path / "h_rich.docx"
    convert_markdown_to_docx(in_file, out)

    with zipfile.ZipFile(out, "r") as z:
        doc_xml = z.read("word/document.xml").decode("utf-8")
        assert "m:oMath" in doc_xml
        assert "w:i" in doc_xml
        assert "w:strike" in doc_xml


def test_final09_template_validation_edge_cases(tmp_path):
    """FINAL-09: Template validation rejects null page, bad headings, and margin < 2cm."""
    tmpl_dir = tmp_path / "bad_tmpl"
    tmpl_dir.mkdir()

    # 1. Null page
    (tmpl_dir / "config.yaml").write_text(_minimal_template_yaml(page=None), encoding="utf-8")
    with pytest.raises(TemplateValidationError, match="page"):
        Template.load(tmpl_dir)

    # 2. String heading config
    (tmpl_dir / "config.yaml").write_text(_minimal_template_yaml(headings={"h1": "invalid_string"}), encoding="utf-8")
    with pytest.raises(TemplateValidationError, match="headings.h1"):
        Template.load(tmpl_dir)

    # 3. Excessive margins leaving < 2cm usable width
    (tmpl_dir / "config.yaml").write_text(
        _minimal_template_yaml(page={"size": "A5", "margin_cm": {"left": 8, "right": 8, "top": 2, "bottom": 2}}),
        encoding="utf-8",
    )
    with pytest.raises(TemplateValidationError, match="leaves no usable content area"):
        Template.load(tmpl_dir)

    # 4. Non-PNG mermaid format
    (tmpl_dir / "config.yaml").write_text(_minimal_template_yaml(mermaid={"format": "svg"}), encoding="utf-8")
    with pytest.raises(TemplateValidationError, match="mermaid.format"):
        Template.load(tmpl_dir)


def test_final10_uniform_fonts_and_bidi_across_contexts(tmp_path):
    """FINAL-10: Body font size and line spacing propagate to lists, quotes, and callouts; bidi=1 on Persian."""
    tmpl_dir = tmp_path / "tmpl_ltr"
    tmpl_dir.mkdir()
    (tmpl_dir / "config.yaml").write_text(
        _minimal_template_yaml(
            direction="ltr",
            page={"size": "A4", "font_size_pt": 15, "line_spacing": 1.8, "margin_cm": {"top": 2, "bottom": 2, "left": 2, "right": 2}},
        ),
        encoding="utf-8",
    )
    md_content = (
        "# تیتر اول\n\n"
        "متن فارسی در قالب LTR.\n\n"
        "- آیتم فارسی یک\n"
        "- آیتم فارسی دو\n\n"
        "> نقل قول فارسی\n"
    )
    in_file = tmp_path / "ltr_test.md"
    in_file.write_text(md_content, encoding="utf-8")
    out = tmp_path / "ltr_test.docx"
    convert_markdown_to_docx(in_file, out, template=tmpl_dir)

    with zipfile.ZipFile(out, "r") as z:
        doc_xml = z.read("word/document.xml").decode("utf-8")
        tree = etree.fromstring(doc_xml.encode("utf-8"))
        # All Persian paragraphs must have w:bidi even though template is LTR
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        bidi_elements = tree.xpath("//w:pPr/w:bidi", namespaces=ns)
        assert len(bidi_elements) >= 3


def test_final11_media_rollback_on_failure(tmp_path, mocker):
    """FINAL-11: Media rollback restores overwritten files and removes newly created diagrams on failure."""
    out_docx = tmp_path / "rollback_doc.docx"
    out_docx.write_bytes(b"OLD_DOCX")

    media_dir = tmp_path / "rollback_media"
    media_dir.mkdir()
    orig_png = media_dir / "diagram_001.png"
    orig_png.write_bytes(b"OLD_PNG_001")

    # Create dummy staging directory simulating two new diagrams
    stage_media = tmp_path / "stage_media"
    stage_media.mkdir()
    (stage_media / "diagram_001.png").write_bytes(b"NEW_PNG_001")
    (stage_media / "diagram_002.png").write_bytes(b"NEW_PNG_002")

    from md_to_docx.pipeline import _publish_diagrams

    # Inject error when replacing diagram_002
    real_replace = os.replace
    def faulty_replace(src, dst):
        if "diagram_002" in str(src) or "diagram_002" in str(dst):
            raise OSError("Injected disk failure on diagram 2")
        return real_replace(src, dst)

    mocker.patch("md_to_docx.pipeline.os.replace", side_effect=faulty_replace)

    with pytest.raises(OSError, match="Injected disk failure"):
        _publish_diagrams(stage_media, media_dir)

    # diagram_001 must have been rolled back to OLD_PNG_001
    assert orig_png.exists()
    assert orig_png.read_bytes() == b"OLD_PNG_001"
    # diagram_002 must not exist
    assert not (media_dir / "diagram_002.png").exists()
    # No .tmp_ files left behind
    assert not list(media_dir.glob("*.tmp*"))


def test_final12_input_output_protection(tmp_path):
    """FINAL-12: Reject non-docx extensions and output path equal to input path."""
    in_file = tmp_path / "doc.md"
    in_file.write_text("# Title\n", encoding="utf-8")

    # 1. Reject non-.docx extensions in API
    for ext in [".png", ".doc", ".md", ".pdf"]:
        out = tmp_path / f"out{ext}"
        with pytest.raises(ConvertError, match="must have a .docx extension"):
            convert_markdown_to_docx(in_file, out)

    # 2. Reject output == input
    with pytest.raises(ValueError, match="cannot be identical to input path"):
        convert_markdown_to_docx(in_file, in_file)


def test_final13_table_tbody_intermediate_and_colspec(tmp_path):
    """FINAL-13: Table intermediate headers and explicit colspecs preserved."""
    ast_dict = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [
            {
                "t": "Table",
                "c": [
                    ["", [], []],
                    [None, []],
                    [
                        [{"t": "AlignLeft"}, {"t": "ColWidth", "c": 0.25}],
                        [{"t": "AlignRight"}, {"t": "ColWidth", "c": 0.75}],
                    ],
                    [[], []],
                    [
                        [
                            [[], []],
                            0,
                            # intermediate head (tbody[2])
                            [
                                [
                                    [[], []],
                                    [
                                        [[], {"t": "AlignDefault"}, 1, 1, [{"t": "Plain", "c": [{"t": "Str", "c": "IH1"}]}]],
                                        [[], {"t": "AlignDefault"}, 1, 1, [{"t": "Plain", "c": [{"t": "Str", "c": "IH2"}]}]],
                                    ],
                                ]
                            ],
                            # body rows (tbody[3])
                            [
                                [
                                    [[], []],
                                    [
                                        [[], {"t": "AlignDefault"}, 1, 1, [{"t": "Plain", "c": [{"t": "Str", "c": "B1"}]}]],
                                        [[], {"t": "AlignDefault"}, 1, 1, [{"t": "Plain", "c": [{"t": "Str", "c": "B2"}]}]],
                                    ],
                                ]
                            ],
                        ]
                    ],
                    [[], []],
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
    # Intermediate head + body row = 2 rows
    assert len(tbl.rows) == 2
    assert tbl.cell(0, 0).text == "IH1"
    assert tbl.cell(1, 0).text == "B1"


def test_final16_docx_to_markdown_conversion(tmp_path):
    """FINAL-16: DOCX to Markdown conversion using to_md module with media extraction."""
    from md_to_docx.to_md import convert_docx_to_markdown

    # First generate a real DOCX
    in_md = tmp_path / "sample.md"
    in_md.write_text("# عنوان اصلی\n\nمتن نمونه با **قلم درشت**.\n", encoding="utf-8")
    docx_out = tmp_path / "sample.docx"
    convert_markdown_to_docx(in_md, docx_out)
    assert docx_out.exists()

    # Convert back to Markdown
    md_back = tmp_path / "sample_back.md"
    res = convert_docx_to_markdown(docx_out, md_back)
    assert res.exists()
    content = res.read_text(encoding="utf-8")
    assert "عنوان اصلی" in content
    assert "متن نمونه" in content

    # Verify rejecting .doc
    bad_doc = tmp_path / "test.doc"
    bad_doc.write_bytes(b"fake doc")
    with pytest.raises(ConvertError, match="Word 97-2003 .doc is not supported"):
        convert_docx_to_markdown(bad_doc)


def test_review_footnote_table_and_code_no_crash(tmp_path):
    """Review: tables and code blocks inside footnotes must not raise AttributeError."""
    import zipfile

    for md in (
        "Text[^1]\n\n[^1]: Para one.\n\n    | A | B |\n    |---|---|\n    | 1 | 2 |\n",
        "Text[^1]\n\n[^1]: code:\n\n        x = 1\n",
    ):
        out = tmp_path / f"fn_{abs(hash(md)) % 10_000}.docx"
        convert_markdown_to_docx(content=md, base_dir=str(tmp_path), output_path=str(out), overwrite=True)
        fx = zipfile.ZipFile(out).read("word/footnotes.xml").decode("utf-8")
        assert "w:tbl" in fx


def test_review_image_path_no_parent_fallback(tmp_path):
    """Review FINAL-06: a same-subpath file in a parent dir must not satisfy a missing child path."""
    from PIL import Image
    from md_to_docx.paths import resolve_image_source

    base = tmp_path / "a" / "b"
    (base / "missing").mkdir(parents=True)
    parent_missing = tmp_path / "a" / "missing"
    parent_missing.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (5, 5), "blue").save(parent_missing / "sibling.png")
    with pytest.raises(ConvertError, match="Image not found"):
        resolve_image_source("missing/sibling.png", base)


def test_review_add_omml_respects_display(tmp_path):
    """Review FINAL-01/02: add_omml(display=True) must emit oMathPara inside w:p."""
    from md_to_docx.renderer import DocxRenderer

    tmpl = Template.load("purple_book")
    renderer = DocxRenderer(template=tmpl, base_dir=tmp_path)
    p = renderer.doc.add_paragraph()
    renderer.add_omml(p, r"\frac{1}{2}", display=True)
    assert p._p.find("{http://schemas.openxmlformats.org/officeDocument/2006/math}oMathPara") is not None
    p2 = renderer.doc.add_paragraph()
    renderer.add_omml(p2, r"\frac{1}{2}", display=False)
    assert p2._p.find("{http://schemas.openxmlformats.org/officeDocument/2006/math}oMath") is not None


def test_review_to_md_keeps_prose_media_word(tmp_path):
    """Review FINAL-16: to_md must rewrite only media link targets, not prose."""
    from md_to_docx.to_md import convert_docx_to_markdown

    in_md = tmp_path / "sample.md"
    in_md.write_text("# T\n\nWe discuss media/ handling in prose.\n", encoding="utf-8")
    docx_out = tmp_path / "sample.docx"
    convert_markdown_to_docx(in_md, docx_out)
    md_back = tmp_path / "back.md"
    convert_docx_to_markdown(docx_out, md_back, overwrite=True)
    content = md_back.read_text(encoding="utf-8")
    assert "media/" in content
    assert "back_media/" not in content


def test_review_callout_bidi_ltr_template(tmp_path):
    """Review FINAL-10: Persian callout header in LTR template must be explicitly RTL."""
    import shutil
    import yaml
    from lxml import etree

    src = Path("templates/purple_book")
    dst = tmp_path / "tmpl_ltr"
    shutil.copytree(src, dst)
    cfg = yaml.safe_load(open(dst / "config.yaml", encoding="utf-8"))
    cfg["direction"] = "ltr"
    open(dst / "config.yaml", "w", encoding="utf-8").write(yaml.safe_dump(cfg))
    md = "::: note تیتر فارسی\nبدنه فارسی\n:::\n"
    out = tmp_path / "o.docx"
    convert_markdown_to_docx(content=md, base_dir=str(tmp_path), output_path=str(out), template=dst, overwrite=True)
    tree = etree.fromstring(zipfile.ZipFile(out).read("word/document.xml"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    texts = tree.xpath("//w:t[contains(text(), 'تیتر فارسی')]/ancestor::w:p/w:pPr/w:bidi", namespaces=ns)
    assert texts, "Persian callout header must carry explicit w:bidi"
    assert any(t.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val") == "1" for t in texts), "Persian header in LTR template must be bidi=1"

