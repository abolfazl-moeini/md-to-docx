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


def test_pipeline_failure_during_pandoc_cleans_up_staging_and_leaves_no_artifacts(tmp_path, mocker):
    """R-02: Verifies that a failure during Pandoc parsing cleans up staging and leaves no docx or orphan media."""
    stub_png = Path(__file__).parent / "fixtures" / "diagram-stub.png"

    def mock_render(code, out_path, template):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(stub_png.read_bytes())
        return out_path

    in_file = tmp_path / "doc.md"
    in_file.write_text("# Doc\n\n```mermaid\ngraph TD\nA-->B\n```\n", encoding="utf-8")
    out_docx = tmp_path / "doc.docx"
    media_dir = tmp_path / "doc_media"

    mocker.patch("md_to_docx.pipeline.run_pandoc_ast", side_effect=ConvertError("Pandoc syntax error"))

    with pytest.raises(ConvertError) as exc_info:
        convert_markdown_to_docx(in_file, out_docx, render_mermaid_fn=mock_render)
    assert "Pandoc syntax error" in str(exc_info.value)

    # DOCX must not exist
    assert not out_docx.exists(), "Failed conversion must not leave output DOCX"
    # Media dir must not exist
    assert not media_dir.exists(), "Failed conversion must not leave orphan media"
    # Staging directories starting with .stage_doc_ must be cleaned up
    staging_dirs = list(tmp_path.glob(".stage_doc_*"))
    assert len(staging_dirs) == 0, "Staging directory must be deleted on failure"


def test_pipeline_failure_during_mermaid_cleans_up_staging_and_leaves_no_artifacts(tmp_path):
    """R-02: Verifies that a failure during Mermaid diagram compilation leaves no output or orphan media."""
    def failing_render(code, out_path, template):
        raise ConvertError("Puppeteer browser crash")

    in_file = tmp_path / "doc.md"
    in_file.write_text("# Doc\n\n```mermaid\ngraph TD\nA-->B\n```\n", encoding="utf-8")
    out_docx = tmp_path / "doc.docx"
    media_dir = tmp_path / "doc_media"

    with pytest.raises(ConvertError) as exc_info:
        convert_markdown_to_docx(in_file, out_docx, render_mermaid_fn=failing_render)
    assert "Puppeteer browser crash" in str(exc_info.value)

    assert not out_docx.exists()
    assert not media_dir.exists()
    staging_dirs = list(tmp_path.glob(".stage_doc_*"))
    assert len(staging_dirs) == 0


def test_pipeline_failure_preserves_existing_output_and_media(tmp_path, mocker):
    """R-02: Verifies that if previous valid output exists, a failed conversion does NOT overwrite or destroy it."""
    out_docx = tmp_path / "doc.docx"
    out_docx.write_bytes(b"EXISTING_DOCX_CONTENT")
    media_dir = tmp_path / "doc_media"
    media_dir.mkdir()
    existing_img = media_dir / "diagram_001.png"
    existing_img.write_bytes(b"EXISTING_PNG_CONTENT")

    in_file = tmp_path / "doc.md"
    in_file.write_text("# Doc\n\n```mermaid\ngraph TD\nA-->B\n```\n", encoding="utf-8")

    mocker.patch("md_to_docx.pipeline.run_pandoc_ast", side_effect=ConvertError("Pandoc crashed"))

    with pytest.raises(ConvertError):
        convert_markdown_to_docx(in_file, out_docx)

    # Existing content preserved intact
    assert out_docx.read_bytes() == b"EXISTING_DOCX_CONTENT"
    assert existing_img.read_bytes() == b"EXISTING_PNG_CONTENT"


def test_pipeline_reconvert_without_diagrams_cleans_stale_media(tmp_path):
    """R-02: Verifies that re-converting a document that no longer has diagrams removes old media dir."""
    out_docx = tmp_path / "doc.docx"
    media_dir = tmp_path / "doc_media"
    media_dir.mkdir()
    (media_dir / "old_diagram.png").write_bytes(b"OLD_PNG")

    in_file = tmp_path / "doc.md"
    in_file.write_text("# Simple Doc Without Any Mermaid Diagrams\n\nPlain text paragraph.\n", encoding="utf-8")

    convert_markdown_to_docx(in_file, out_docx)

    assert out_docx.exists()
    # Stale media dir should be removed
    assert not media_dir.exists(), "Stale auto-managed media directory must be cleaned up"


def test_pipeline_concurrency_same_stem(tmp_path):
    """R-04: Verifies concurrent conversions with identical output stem run safely without corruption."""
    from concurrent.futures import ThreadPoolExecutor
    stub_png = Path(__file__).parent / "fixtures" / "diagram-stub.png"

    def mock_render(code, out_path, template):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(stub_png.read_bytes())
        return out_path

    md_file = tmp_path / "shared.md"
    md_file.write_text(
        "# Concurrent Test\n\n```mermaid\ngraph TD\nA-->B\n```\nشکل ۱. تست\n",
        encoding="utf-8",
    )
    out_docx = tmp_path / "shared.docx"

    def run_conv(iteration: int):
        return convert_markdown_to_docx(md_file, out_docx, render_mermaid_fn=mock_render)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(run_conv, i) for i in range(4)]
        results = [f.result() for f in futures]

    assert all(r == out_docx.resolve() for r in results)
    assert out_docx.exists()
    assert zipfile.is_zipfile(out_docx)

    media_dir = tmp_path / "shared_media"
    assert media_dir.exists()
    pngs = list(media_dir.glob("*.png"))
    assert len(pngs) >= 1
    # Check NO nested subdirectories created inside media_dir
    subdirs = [p for p in media_dir.iterdir() if p.is_dir()]
    assert len(subdirs) == 0, f"No nested subdirectories should exist in media_dir, found {subdirs}"


def test_pipeline_crash_during_pandoc_cleans_up_staging(tmp_path, mocker):
    """R3-05: Verifies that if Pandoc crashes, staging directories are removed and no artifacts leak."""
    mocker.patch("md_to_docx.pipeline.run_pandoc_ast", side_effect=RuntimeError("Simulated Pandoc Crash"))
    in_file = tmp_path / "test.md"
    in_file.write_text("# Test Title\nSome content.", encoding="utf-8")
    out_docx = tmp_path / "out.docx"

    with pytest.raises(RuntimeError) as exc_info:
        convert_markdown_to_docx(in_file, out_docx)
    assert "Simulated Pandoc Crash" in str(exc_info.value)

    assert not out_docx.exists()
    staged = [p for p in tmp_path.iterdir() if p.name.startswith(".stage_")]
    assert len(staged) == 0, f"Staging directories must be cleaned up on failure: {staged}"


def test_pipeline_crash_during_ast_cleans_up_staging(tmp_path, mocker):
    """R3-05: Verifies that if AST translation crashes, staging directories are removed."""
    mocker.patch("md_to_docx.pipeline.ast_to_docx", side_effect=ValueError("Simulated AST translation failure"))
    in_file = tmp_path / "test.md"
    in_file.write_text("# Test Title\nSome content.", encoding="utf-8")
    out_docx = tmp_path / "out.docx"

    with pytest.raises(ValueError) as exc_info:
        convert_markdown_to_docx(in_file, out_docx)
    assert "Simulated AST translation failure" in str(exc_info.value)

    assert not out_docx.exists()
    staged = [p for p in tmp_path.iterdir() if p.name.startswith(".stage_")]
    assert len(staged) == 0, f"Staging directories must be cleaned up on failure: {staged}"


def test_pipeline_crash_during_publish_rolls_back_existing_files(tmp_path, mocker):
    """R3-05: Verifies transactional rollback if publishing media fails after docx replace."""
    out_docx = tmp_path / "doc.docx"
    out_docx.write_bytes(b"ORIGINAL_DOCX_V1")

    media_dir = tmp_path / "doc_media"
    media_dir.mkdir()
    orig_img = media_dir / "diagram_001.png"
    orig_img.write_bytes(b"ORIGINAL_PNG_V1")

    stub_png = Path(__file__).parent / "fixtures" / "diagram-stub.png"

    def mock_render(code, out_path, template):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(stub_png.read_bytes())
        return out_path

    in_file = tmp_path / "doc.md"
    in_file.write_text("# New Title\n```mermaid\ngraph TD\nA-->B\n```\nشکل ۱. تست\n", encoding="utf-8")

    import os
    import shutil
    real_replace = os.replace
    real_copytree = shutil.copytree

    def selective_media_fail(src, dst, *args, **kwargs):
        if "_media" in str(src) and ".stage_" in str(src):
            raise OSError("Simulated disk error moving media directory")
        return real_replace(src, dst, *args, **kwargs)

    def selective_copytree_fail(src, dst, *args, **kwargs):
        if "_media" in str(src) and ".stage_" in str(src):
            raise OSError("Simulated disk error copying media directory")
        return real_copytree(src, dst, *args, **kwargs)

    mocker.patch("md_to_docx.pipeline.os.replace", side_effect=selective_media_fail)
    mocker.patch("md_to_docx.pipeline.shutil.move", side_effect=selective_media_fail)
    mocker.patch("md_to_docx.pipeline.shutil.copytree", side_effect=selective_copytree_fail)

    with pytest.raises(OSError) as exc_info:
        convert_markdown_to_docx(in_file, out_docx, render_mermaid_fn=mock_render)
    assert "Simulated disk error" in str(exc_info.value)

    # Rollback assertion: original docx and media must be preserved intact!
    assert out_docx.exists()
    assert out_docx.read_bytes() == b"ORIGINAL_DOCX_V1", "Original docx must be rolled back on publish failure"
    assert orig_img.exists()
    assert orig_img.read_bytes() == b"ORIGINAL_PNG_V1", "Original media must be rolled back on publish failure"

    # No leftover staging or backup files
    staged = [p for p in tmp_path.iterdir() if p.name.startswith((".stage_", ".backup_", ".trash_"))]
    assert len(staged) == 0, f"No temporary or backup files should remain: {staged}"
