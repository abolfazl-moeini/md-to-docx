import pytest
from pathlib import Path
from click.testing import CliRunner
from md_to_docx.cli import main

@pytest.fixture
def runner():
    return CliRunner()

def test_cli_help(runner):
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "convert" in result.output
    assert "templates" in result.output

def test_cli_templates_list(runner):
    result = runner.invoke(main, ["templates", "list"])
    assert result.exit_code == 0
    assert "purple_book" in result.output

def test_cli_convert_nonexistent_input(runner):
    result = runner.invoke(main, ["convert", "non_existent_file_xyz.md", "-o", "out.docx"])
    assert result.exit_code != 0
    assert "non_existent_file_xyz.md" in result.output or "does not exist" in result.output.lower()

def test_cli_convert_nonexistent_template(runner, tmp_path):
    dummy_in = tmp_path / "in.md"
    dummy_in.write_text("# سلام", encoding="utf-8")
    result = runner.invoke(main, ["convert", str(dummy_in), "-o", str(tmp_path / "out.docx"), "--template", "nonexistent_tmpl"])
    assert result.exit_code != 0
    assert "nonexistent_tmpl" in result.output

def test_cli_convert_success(runner, tmp_path, mocker):
    dummy_in = tmp_path / "in.md"
    dummy_in.write_text("# ۱.۱ عنوان", encoding="utf-8")
    out_file = tmp_path / "out.docx"

    mocker.patch("md_to_docx.cli.convert_markdown_to_docx", return_value=out_file)

    result = runner.invoke(main, ["convert", str(dummy_in), "-o", str(out_file), "--template", "purple_book"])
    assert result.exit_code == 0
    assert "Success" in result.output or str(out_file) in result.output

