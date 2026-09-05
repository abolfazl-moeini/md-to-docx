import pytest
from pathlib import Path
from md_to_docx.mermaid import (
    extract_mermaid_blocks,
    process_mermaid_blocks,
    render_mermaid_to_png,
    ConvertError,
    CAPTION_RE,
)
from md_to_docx.template import Template

def test_caption_regex_matching():
    assert CAPTION_RE.match("شکل ۲-۱. معماری داخلی") is not None
    assert CAPTION_RE.match("Figure 1. Architecture") is not None
    assert CAPTION_RE.match("Fig. 2: Overview") is not None
    assert CAPTION_RE.match("متن عادی بدون کپشن") is None

def test_extract_mermaid_blocks_with_caption():
    text = """# عنوان

```mermaid
graph TD
    A --> B
```
شکل ۲-۱. دیاگرام نمونه

پاراگراف بعدی.
"""
    blocks = extract_mermaid_blocks(text)
    assert len(blocks) == 1
    assert "A --> B" in blocks[0].code
    assert blocks[0].caption == "شکل ۲-۱. دیاگرام نمونه"

def test_extract_mermaid_blocks_without_caption():
    text = """```mermaid
graph TD
    A --> B
```

پاراگراف عادی بدون کپشن شکل.
"""
    blocks = extract_mermaid_blocks(text)
    assert len(blocks) == 1
    assert blocks[0].caption is None

def test_process_mermaid_blocks_with_mock(tmp_path):
    tmpl = Template.load("purple_book")
    stub_png = Path(__file__).parent / "fixtures" / "diagram-stub.png"

    def mock_render(code, out_path, template):
        out_path.write_bytes(stub_png.read_bytes())
        return out_path

    md_input = """```mermaid
graph TD
    Client --> Server
```
شکل ۱. جریان داده
"""
    result = process_mermaid_blocks(md_input, output_dir=tmp_path, template=tmpl, render_fn=mock_render)
    assert "mermaid-figure" in result
    assert "شکل ۱. جریان داده" in result
    assert "```mermaid" not in result

def test_render_mermaid_failure_raises_converterror(mocker, tmp_path):
    tmpl = Template.load("purple_book")
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 1
    mock_run.return_value.stderr = "Syntax error in diagram"

    out_file = tmp_path / "diag.png"
    with pytest.raises(ConvertError) as exc_info:
        render_mermaid_to_png("graph TD\n A --->", out_file, tmpl)
    assert "Syntax error in diagram" in str(exc_info.value)

def test_render_mermaid_empty_output_raises_converterror(mocker, tmp_path):
    tmpl = Template.load("purple_book")
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stderr = ""

    out_file = tmp_path / "empty.png"
    out_file.write_bytes(b"")  # 0 bytes

    with pytest.raises(ConvertError) as exc_info:
        render_mermaid_to_png("graph TD\n A --> B", out_file, tmpl)
    assert "empty or missing" in str(exc_info.value)


def test_extract_unclosed_mermaid_fence_raises_syntax_error():
    from md_to_docx.mermaid import MermaidSyntaxError
    md_text = "# عنوان\n\n```mermaid\ngraph TD\n    A --> B\n"
    with pytest.raises(MermaidSyntaxError) as exc_info:
        extract_mermaid_blocks(md_text)
    assert "Unclosed mermaid code block" in str(exc_info.value)
    assert exc_info.value.line_number == 3


def test_extract_nested_mermaid_fence_raises_syntax_error():
    from md_to_docx.mermaid import MermaidSyntaxError
    md_text = "```mermaid\ngraph TD\n```mermaid\n    A --> B\n```\n"
    with pytest.raises(MermaidSyntaxError) as exc_info:
        extract_mermaid_blocks(md_text)
    assert "Nested mermaid fence" in str(exc_info.value)
    assert exc_info.value.line_number == 3


def test_extract_multiple_consecutive_mermaid_blocks():
    md_text = """```mermaid
graph TD
    A --> B
```
شکل ۱. اول

```mermaid
graph LR
    C --> D
```
شکل ۲. دوم
"""
    blocks = extract_mermaid_blocks(md_text)
    assert len(blocks) == 2
    assert blocks[0].caption == "شکل ۱. اول"
    assert blocks[1].caption == "شکل ۲. دوم"


def test_puppeteer_runtime_config_always_includes_no_sandbox(tmp_path):
    from md_to_docx.mermaid import _get_puppeteer_config_path
    import json
    tmpl = Template.load("purple_book")
    cfg_path = _get_puppeteer_config_path(tmpl, tmp_path)
    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert "--no-sandbox" in data.get("args", [])
    assert "--disable-setuid-sandbox" in data.get("args", [])


def test_puppeteer_runtime_config_sets_explicit_executable_path(tmp_path):
    from md_to_docx.mermaid import _get_puppeteer_config_path
    import json
    tmpl = Template.load("purple_book")
    browser = tmp_path / "Google Chrome for Testing"
    browser.write_text("", encoding="utf-8")
    cfg_path = _get_puppeteer_config_path(tmpl, tmp_path, browser_bin=str(browser))
    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert data["executablePath"] == str(browser)
    assert "--no-sandbox" in data["args"]


def test_find_browser_prefers_puppeteer_chrome_for_testing(tmp_path, monkeypatch):
    from md_to_docx import mermaid as mermaid_mod

    cache = tmp_path / "puppeteer"
    older = (
        cache / "chrome" / "mac_arm-121.0.6167.85" / "chrome-mac-arm64"
        / "Google Chrome for Testing.app" / "Contents" / "MacOS" / "Google Chrome for Testing"
    )
    newer = (
        cache / "chrome" / "mac_arm-152.0.7977.75" / "chrome-mac-arm64"
        / "Google Chrome for Testing.app" / "Contents" / "MacOS" / "Google Chrome for Testing"
    )
    helper = (
        cache / "chrome" / "mac_arm-152.0.7977.75" / "chrome-mac-arm64"
        / "Google Chrome for Testing.app" / "Contents" / "Frameworks" / "F.framework"
        / "Helpers" / "Google Chrome for Testing Helper.app" / "Contents" / "MacOS"
        / "Google Chrome for Testing"
    )
    system_chrome = tmp_path / "Applications" / "Google Chrome.app" / "Contents" / "MacOS" / "Google Chrome"
    for path in (older, newer, helper, system_chrome):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\n", encoding="utf-8")
        path.chmod(0o755)

    monkeypatch.setattr(mermaid_mod, "_puppeteer_cache_dirs", lambda: [cache])
    monkeypatch.setattr(mermaid_mod, "_system_browser_candidates", lambda: [str(system_chrome)])
    monkeypatch.setattr(mermaid_mod.shutil, "which", lambda _name: None)
    monkeypatch.delenv("PUPPETEER_EXECUTABLE_PATH", raising=False)

    found = mermaid_mod._find_browser_executable()
    assert found == str(newer.resolve())
    assert "Helpers" not in found
    assert "Google Chrome.app" not in found


def test_render_mermaid_does_not_pollute_output_dir(mocker, tmp_path):
    tmpl = Template.load("purple_book")
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stderr = ""
    mock_run.return_value.stdout = ""

    out_file = tmp_path / "diagram_001.png"
    out_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
    render_mermaid_to_png("graph TD\nA-->B", out_file, tmpl)

    leftover = {p.name for p in tmp_path.iterdir()}
    assert leftover == {"diagram_001.png"}


def test_mermaid_artifact_persistence_after_context_exit(tmp_path):
    """Verifies that generated diagram images remain accessible on disk after processing."""
    from md_to_docx.pipeline import convert_markdown_to_docx
    tmpl = Template.load("purple_book")
    stub_png = Path(__file__).parent / "fixtures" / "diagram-stub.png"

    def mock_render(code, out_path, template):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(stub_png.read_bytes())
        return out_path

    md_file = tmp_path / "doc.md"
    md_file.write_text(
        "# تست دیاگرام\n\n```mermaid\ngraph TD\n    A --> B\n```\nشکل ۱. نمونه\n",
        encoding="utf-8",
    )
    docx_file = tmp_path / "doc.docx"

    convert_markdown_to_docx(md_file, docx_file, template=tmpl, render_mermaid_fn=mock_render)

    # DOCX exists
    assert docx_file.exists()

    # Stable media dir exists and contains diagram
    media_dir = tmp_path / "doc_media"
    assert media_dir.exists(), "Persistent media_dir must exist beside output docx"
    diagrams = list(media_dir.glob("*.png"))
    assert len(diagrams) >= 1, "Diagram PNG must persist on disk"
    assert diagrams[0].stat().st_size > 0, "Persisted diagram must not be empty"


@pytest.mark.mermaid
@pytest.mark.integration
def test_real_persian_mermaid_rendering_integration(tmp_path):
    """R3-01: End-to-end integration test executing real mmdc with Persian text, asserting on PNG and DOCX."""
    import zipfile
    from lxml import etree
    from md_to_docx.mermaid import probe_mermaid_renderer, render_mermaid_to_png
    from md_to_docx.pipeline import convert_markdown_to_docx

    can_render, reason = probe_mermaid_renderer()
    if not can_render:
        pytest.skip(f"Mermaid renderer not operational: {reason}")

    tmpl = Template.load("purple_book")

    # 1. Direct render of Persian Mermaid diagram to PNG
    png_out = tmp_path / "persian_diag.png"
    persian_mmd = """graph TD
    Client["درخواست کاربر"] --> Engine["پردازش در موتور داده"]
    Engine --> DB["ثبت نهایی در دیتابیس"]
"""
    rendered_path = render_mermaid_to_png(persian_mmd, png_out, tmpl)
    assert rendered_path == png_out
    assert png_out.exists(), "Rendered PNG must exist on disk"
    content = png_out.read_bytes()
    assert content.startswith(b"\x89PNG\r\n\x1a\n"), "File must have valid PNG signature"
    assert len(content) > 2000, f"Persian diagram PNG must be substantial, got {len(content)} bytes"

    # 2. Pipeline integration: Markdown with Persian Mermaid converted to DOCX
    md_file = tmp_path / "persian_mermaid.md"
    md_file.write_text(
        "# معماری سیستم\n\n"
        "```mermaid\n"
        + persian_mmd
        + "```\n"
        "شکل ۱. نمودار معماری پردازش فارسی\n",
        encoding="utf-8",
    )
    docx_file = tmp_path / "persian_mermaid.docx"
    saved_path = convert_markdown_to_docx(md_file, docx_file, template=tmpl)
    assert saved_path == docx_file.resolve()
    assert docx_file.exists()
    assert docx_file.stat().st_size > 20_000

    # 3. Verify DOCX zip package contains the rendered diagram and caption
    with zipfile.ZipFile(docx_file, "r") as z:
        media_files = [n for n in z.namelist() if n.startswith("word/media/")]
        assert len(media_files) >= 1, "DOCX package must contain diagram image in word/media/"
        doc_xml = z.read("word/document.xml")
        tree = etree.fromstring(doc_xml)
        all_text = "".join(tree.xpath("//w:t/text()", namespaces={"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}))
        assert "شکل ۱. نمودار معماری پردازش فارسی" in all_text

