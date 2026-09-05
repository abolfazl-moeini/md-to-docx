import pytest
from pathlib import Path
from md_to_docx.template import Template, TemplateError, TemplateNotFoundError, TemplateValidationError

def test_load_template_by_name():
    tmpl = Template.load("purple_book")
    assert tmpl.name == "purple_book"
    assert tmpl.direction == "rtl"
    assert tmpl.fonts["body"] == "Vazirmatn"
    assert tmpl.fonts["heading"] == "Vazirmatn"
    assert tmpl.fonts["code"] == "Courier New"
    assert tmpl.colors["primary"] == "6B2FA0"
    assert tmpl.colors["primary_dark"] == "4A156D"
    assert tmpl.colors["warning_bg"] == "FBF7F4"
    assert tmpl.colors["warning_title"] == "8B6914"
    assert tmpl.callouts["note"]["icon"] == "◆"
    assert tmpl.callouts["warning"]["icon"] == ""
    assert tmpl.tables["bidi_visual"] is True
    assert tmpl.code_block["theme"] == "friendly"

def test_load_template_by_path(tmp_path):
    # Test loading from explicit directory
    tmpl_dir = Path("templates/purple_book").resolve()
    tmpl = Template.load(tmpl_dir)
    assert tmpl.name == "purple_book"

def test_template_not_found():
    with pytest.raises(TemplateNotFoundError) as exc_info:
        Template.load("non_existent_template_xyz")
    assert "non_existent_template_xyz" in str(exc_info.value)

def test_template_missing_schema_version(tmp_path):
    (tmp_path / "config.yaml").write_text(
        "name: bad_tmpl\n"
        "direction: rtl\n"
        "fonts: {body: Vazirmatn, heading: Vazirmatn, code: Courier New}\n"
        "colors: {primary: '6B2FA0', primary_dark: '4A156D', on_primary: 'FFF', quote_bg: 'EEE', warning_bg: 'FFF', warning_title: '888', body: '222', caption: '555'}\n"
        "headings: {}\n"
        "callouts: {}\n"
        "quotes: {}\n"
        "tables: {}\n",
        encoding="utf-8",
    )
    with pytest.raises(TemplateValidationError) as exc_info:
        Template.load(tmp_path)
    assert "schema_version" in str(exc_info.value)


def test_template_missing_field(tmp_path):
    bad_config = tmp_path / "config.yaml"
    bad_config.write_text("schema_version: 1\nname: bad_tmpl\ndirection: rtl\n", encoding="utf-8")
    with pytest.raises(TemplateValidationError) as exc_info:
        Template.load(tmp_path)
    assert "fonts" in str(exc_info.value)

def test_template_missing_fonts_body(tmp_path):
    bad_config = tmp_path / "config.yaml"
    bad_config.write_text(
        "schema_version: 1\n"
        "name: bad_tmpl\n"
        "direction: rtl\n"
        "colors: {primary: '6B2FA0', primary_dark: '4A156D', on_primary: 'FFF', quote_bg: 'EEE', warning_bg: 'FFF', warning_title: '888', body: '222', caption: '555'}\n"
        "headings: {}\n"
        "callouts: {}\n"
        "quotes: {}\n"
        "tables: {}\n"
        "fonts:\n"
        "  heading: Vazirmatn\n",
        encoding="utf-8"
    )
    with pytest.raises(TemplateValidationError) as exc_info:
        Template.load(tmp_path)
    assert "fonts.body" in str(exc_info.value)


def test_purple_book_vendors_vazirmatn_font():
    tmpl = Template.load("purple_book")
    font = tmpl.dir_path / "fonts" / "Vazirmatn-Regular.ttf"
    assert font.is_file()
    assert font.stat().st_size > 10_000


def test_template_mermaid_path_resolution(tmp_path):
    tmpl_dir = Path("templates/purple_book").resolve()
    tmpl = Template.load(tmpl_dir)
    assert tmpl.mermaid_theme_path is not None
    assert tmpl.mermaid_theme_path.is_file()
    assert tmpl.mermaid_theme_path.parent == tmpl.dir_path


def test_template_invalid_direction(tmp_path):
    (tmp_path / "config.yaml").write_text(
        "schema_version: 1\nname: bad\ndirection: upside_down\n"
        "fonts: {body: Vazirmatn, heading: Vazirmatn, code: Courier New}\n"
        "colors: {primary: '6B2FA0', primary_dark: '4A156D', on_primary: 'FFF', quote_bg: 'EEE', warning_bg: 'FFF', warning_title: '888', body: '222', caption: '555'}\n"
        "headings: {}\ncallouts: {}\nquotes: {}\ntables: {}\n",
        encoding="utf-8",
    )
    with pytest.raises(TemplateValidationError) as exc_info:
        Template.load(tmp_path)
    assert "direction" in str(exc_info.value)


def test_template_invalid_hex_color(tmp_path):
    (tmp_path / "config.yaml").write_text(
        "schema_version: 1\nname: bad\ndirection: rtl\n"
        "fonts: {body: Vazirmatn, heading: Vazirmatn, code: Courier New}\n"
        "colors: {primary: 'INVALID_HEX', primary_dark: '4A156D', on_primary: 'FFF', quote_bg: 'EEE', warning_bg: 'FFF', warning_title: '888', body: '222', caption: '555'}\n"
        "headings: {}\ncallouts: {}\nquotes: {}\ntables: {}\n",
        encoding="utf-8",
    )
    with pytest.raises(TemplateValidationError) as exc_info:
        Template.load(tmp_path)
    assert "colors.primary" in str(exc_info.value)


def test_template_invalid_margins(tmp_path):
    (tmp_path / "config.yaml").write_text(
        "schema_version: 1\nname: bad\ndirection: rtl\n"
        "fonts: {body: Vazirmatn, heading: Vazirmatn, code: Courier New}\n"
        "colors: {primary: '6B2FA0', primary_dark: '4A156D', on_primary: 'FFF', quote_bg: 'EEE', warning_bg: 'FFF', warning_title: '888', body: '222', caption: '555'}\n"
        "headings: {}\ncallouts: {}\nquotes: {}\ntables: {}\n"
        "page:\n  margin_cm: {top: -2.0, bottom: 2.0, left: 2.0, right: 2.0}\n",
        encoding="utf-8",
    )
    with pytest.raises(TemplateValidationError) as exc_info:
        Template.load(tmp_path)
    assert "page.margin_cm.top" in str(exc_info.value)


def test_template_missing_referenced_file(tmp_path):
    (tmp_path / "config.yaml").write_text(
        "schema_version: 1\nname: bad\ndirection: rtl\n"
        "fonts: {body: Vazirmatn, heading: Vazirmatn, code: Courier New}\n"
        "colors: {primary: '6B2FA0', primary_dark: '4A156D', on_primary: 'FFF', quote_bg: 'EEE', warning_bg: 'FFF', warning_title: '888', body: '222', caption: '555'}\n"
        "headings: {}\ncallouts: {}\nquotes: {}\ntables: {}\n"
        "mermaid:\n  theme_file: non_existent_theme.json\n",
        encoding="utf-8",
    )
    with pytest.raises(TemplateValidationError) as exc_info:
        Template.load(tmp_path)
    assert "non_existent_theme.json" in str(exc_info.value)


def test_template_missing_referenced_custom_shell(tmp_path):
    (tmp_path / "config.yaml").write_text(
        "schema_version: 1\nname: bad\ndirection: rtl\n"
        "fonts: {body: Vazirmatn, heading: Vazirmatn, code: Courier New}\n"
        "colors: {primary: '6B2FA0', primary_dark: '4A156D', on_primary: 'FFF', quote_bg: 'EEE', warning_bg: 'FFF', warning_title: '888', body: '222', caption: '555'}\n"
        "headings: {}\ncallouts: {}\nquotes: {}\ntables: {}\n"
        "shell: missing_shell.docx\n",
        encoding="utf-8",
    )
    with pytest.raises(TemplateValidationError) as exc_info:
        Template.load(tmp_path)
    assert "missing_shell.docx" in str(exc_info.value)

