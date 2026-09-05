import zipfile
import json
import pytest
from pathlib import Path
from lxml import etree
from md_to_docx.pipeline import convert_markdown_to_docx
from md_to_docx.mermaid import ConvertError
from md_to_docx.template import Template

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}

def test_pipeline_missing_pandoc_raises_converterror(mocker, tmp_path):
    mocker.patch("shutil.which", return_value=None)
    in_file = tmp_path / "test.md"
    in_file.write_text("# Test Heading", encoding="utf-8")
    out_docx = tmp_path / "out.docx"
    with pytest.raises(ConvertError) as exc_info:
        convert_markdown_to_docx(in_file, out_docx)
    assert "pandoc" in str(exc_info.value).lower()
    assert "brew install pandoc" in str(exc_info.value)

def test_pipeline_golden_xpaths(tmp_path, mocker):
    sample_md = Path(__file__).parent / "fixtures" / "sample_input.md"
    stub_png = Path(__file__).parent / "fixtures" / "diagram-stub.png"
    ast_sample = Path(__file__).parent / "fixtures" / "pandoc_ast_sample.json"
    ast_data = json.loads(ast_sample.read_text(encoding="utf-8"))

    # Mock mermaid render to use stub
    def mock_mermaid(code, out_path, template):
        out_path.write_bytes(stub_png.read_bytes())
        return out_path

    # Mock pandoc AST parser to use ast_data fixture
    mocker.patch("md_to_docx.pipeline.run_pandoc_ast", return_value=ast_data)

    out_docx = tmp_path / "golden_output.docx"
    convert_markdown_to_docx(
        sample_md,
        out_docx,
        template="purple_book",
        render_mermaid_fn=mock_mermaid,
    )

    assert out_docx.exists()

    with zipfile.ZipFile(out_docx, "r") as z:
        file_list = z.namelist()
        
        # 6. word/media/ has at least one PNG
        media_pngs = [f for f in file_list if f.startswith("word/media/") and f.endswith(".png")]
        assert len(media_pngs) >= 1, "Must contain at least one PNG in word/media/"

        # 1. word/settings.xml has //w:settings/w:bidi
        settings_xml = z.read("word/settings.xml")
        settings_tree = etree.fromstring(settings_xml)
        assert len(settings_tree.xpath("//w:settings/w:bidi", namespaces=NS)) >= 1

        # 8. word/styles.xml has Normal style with w:rFonts/@w:cs="Vazirmatn"
        styles_xml = z.read("word/styles.xml")
        styles_tree = etree.fromstring(styles_xml)
        normal_cs = styles_tree.xpath(
            "//w:style[@w:styleId='Normal']//w:rFonts/@w:cs",
            namespaces=NS
        )
        assert "Vazirmatn" in normal_cs

        # word/document.xml checks
        doc_xml = z.read("word/document.xml")
        doc_tree = etree.fromstring(doc_xml)
        doc_text = "".join(doc_tree.xpath("//w:t/text()", namespaces=NS))

        # 2. At least one table with bidiVisual
        bidi_tables = doc_tree.xpath("//w:tbl[.//w:bidiVisual]", namespaces=NS)
        assert len(bidi_tables) >= 1

        # 3. At least one cell with w:shd fill 6B2FA0
        shd_cells = doc_tree.xpath("//w:tcPr/w:shd[@w:fill='6B2FA0']", namespaces=NS)
        assert len(shd_cells) >= 1

        # 4. Persian number preserved
        assert "۱.۴.۱" in doc_text

        # 5. DBA note present, warning present, NO ⚠️ emoji
        assert "نکتهٔ DBA" in doc_text
        assert "⚠️" not in doc_text

        # 7. Caption text present
        assert "شکل ۲-۱." in doc_text

        # 9. Numbered headings in w:tbl with badge, not raw pandoc heading
        badge_tables = doc_tree.xpath("//w:tbl[.//w:tcPr/w:shd[@w:fill='6B2FA0'] and .//w:t[contains(text(), '۱.۴.۱')]]", namespaces=NS)
        assert len(badge_tables) >= 1


def test_pipeline_special_characters_and_quotes(tmp_path, mocker):
    """F-14: Verifies titles with double quotes, special characters, and XML markup are rendered safely."""
    ast_dict = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [
            {
                "t": "Header",
                "c": [1, ["", [], []], [{"t": "Str", "c": 'عنوان با "کوتیشن" و <تگ>'}]],
            },
            {
                "t": "Para",
                "c": [{"t": "Str", "c": 'متن با کاراکترهای & و < و > و "کوتیشن"'}],
            },
        ],
    }
    mocker.patch("md_to_docx.pipeline.run_pandoc_ast", return_value=ast_dict)

    in_file = tmp_path / "special.md"
    in_file.write_text('# عنوان با "کوتیشن" و <تگ>\n\nمتن\n', encoding="utf-8")
    out_docx = tmp_path / "special.docx"

    convert_markdown_to_docx(in_file, out_docx)
    assert out_docx.exists()

    with zipfile.ZipFile(out_docx, "r") as z:
        doc_xml = z.read("word/document.xml")
        tree = etree.fromstring(doc_xml)
        doc_text = "".join(tree.xpath("//w:t/text()", namespaces=NS))
        assert "کوتیشن" in doc_text
        assert "<تگ>" in doc_text


def test_pipeline_unicode_paths_and_spaces(tmp_path, mocker):
    """F-14: Verifies pipeline handles directory paths with Persian Unicode characters and spaces."""
    ast_dict = {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [
            {"t": "Para", "c": [{"t": "Str", "c": "تست مسیر یونیکد"}]}
        ],
    }
    mocker.patch("md_to_docx.pipeline.run_pandoc_ast", return_value=ast_dict)

    unicode_dir = tmp_path / "پوشه آزمایشی با فاصله"
    unicode_dir.mkdir(parents=True)
    in_file = unicode_dir / "سند ورودی.md"
    in_file.write_text("# سلام", encoding="utf-8")
    out_docx = unicode_dir / "سند خروجی.docx"

    saved = convert_markdown_to_docx(in_file, out_docx)
    assert saved.exists()
    assert saved == out_docx.resolve()


def test_pipeline_missing_mermaid_cli_raises_informative_error(tmp_path, mocker):
    """F-01: Verifies that missing Mermaid CLI provides informative troubleshooting message."""
    from md_to_docx.mermaid import render_mermaid_to_png
    mocker.patch("md_to_docx.mermaid._find_mmdc_cmd", return_value=["non_existent_mmdc_executable_xyz"])
    tmpl = Template.load("purple_book")

    out_png = tmp_path / "diag.png"
    with pytest.raises(ConvertError) as exc_info:
        render_mermaid_to_png("graph TD\nA-->B", out_png, tmpl)
    err_str = str(exc_info.value)
    assert "executable not found" in err_str or "Mermaid CLI" in err_str
    assert "npm install" in err_str or "bootstrap" in err_str
