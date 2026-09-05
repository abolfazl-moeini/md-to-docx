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


def test_cli_convert_directory_as_input_fails(runner, tmp_path):
    sub_dir = tmp_path / "sub_dir"
    sub_dir.mkdir()
    result = runner.invoke(main, ["convert", str(sub_dir)])
    assert result.exit_code == 2
    assert "not a regular file" in result.output or "directory" in result.output.lower()


def test_cli_convert_output_equals_input_fails(runner, tmp_path):
    in_file = tmp_path / "doc.md"
    in_file.write_text("# Test", encoding="utf-8")
    result = runner.invoke(main, ["convert", str(in_file), "-o", str(in_file)])
    assert result.exit_code == 2
    assert "cannot be identical" in result.output


def test_cli_convert_output_already_exists_without_overwrite_fails(runner, tmp_path):
    in_file = tmp_path / "in.md"
    in_file.write_text("# Test", encoding="utf-8")
    out_file = tmp_path / "out.docx"
    out_file.write_text("dummy", encoding="utf-8")

    result = runner.invoke(main, ["convert", str(in_file), "-o", str(out_file)])
    assert result.exit_code == 2
    assert "already exists" in result.output


def test_cli_convert_output_already_exists_with_overwrite_succeeds(runner, tmp_path, mocker):
    in_file = tmp_path / "in.md"
    in_file.write_text("# Test", encoding="utf-8")
    out_file = tmp_path / "out.docx"
    out_file.write_text("dummy", encoding="utf-8")

    mocker.patch("md_to_docx.cli.convert_markdown_to_docx", return_value=out_file)

    result = runner.invoke(main, ["convert", str(in_file), "-o", str(out_file), "--overwrite"])
    assert result.exit_code == 0
    assert "Success" in result.output


def test_cli_templates_validate_valid(runner):
    result = runner.invoke(main, ["templates", "validate", "purple_book"])
    assert result.exit_code == 0
    assert "is valid" in result.output


def test_cli_templates_validate_invalid(runner, tmp_path):
    bad_cfg = tmp_path / "config.yaml"
    bad_cfg.write_text("schema_version: 1\nname: bad\n", encoding="utf-8")
    result = runner.invoke(main, ["templates", "validate", str(tmp_path)])
    assert result.exit_code == 1
    assert "Validation failed" in result.output


def test_cli_convert_permission_error_handling(runner, tmp_path, mocker):
    in_file = tmp_path / "in.md"
    in_file.write_text("# Test", encoding="utf-8")
    out_file = tmp_path / "out.docx"

    mocker.patch("md_to_docx.cli.convert_markdown_to_docx", side_effect=PermissionError("Permission denied"))

    result = runner.invoke(main, ["convert", str(in_file), "-o", str(out_file)])
    assert result.exit_code == 1
    assert "Permission Error" in result.output


def test_cli_convert_output_is_directory_fails(runner, tmp_path):
    in_file = tmp_path / "in.md"
    in_file.write_text("# Test", encoding="utf-8")
    out_dir = tmp_path / "existing_dir"
    out_dir.mkdir()

    result = runner.invoke(main, ["convert", str(in_file), "-o", str(out_dir)])
    assert result.exit_code == 2
    assert "is a directory" in result.output


