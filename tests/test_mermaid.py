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
