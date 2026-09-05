import pytest
from pathlib import Path
from md_to_docx.template import Template, TemplateError, TemplateNotFoundError, TemplateValidationError

def test_load_template_by_name():
    tmpl = Template.load("purple_book")
    assert tmpl.name == "purple_book"
    assert tmpl.direction == "rtl"
    assert tmpl.fonts["body"] == "Vazirmatn"
    assert tmpl.fonts["heading"] == "Vazirmatn"
    assert tmpl.fonts["latin"] == "Segoe UI"
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


def test_template_missing_font_file(tmp_path):
    (tmp_path / "config.yaml").write_text(
        "schema_version: 1\nname: bad\ndirection: rtl\n"
        "fonts: {body: Vazirmatn, heading: Vazirmatn, code: Courier New}\n"
        "colors: {primary: '6B2FA0', primary_dark: '4A156D', on_primary: 'FFF', quote_bg: 'EEE', warning_bg: 'FFF', warning_title: '888', body: '222', caption: '555'}\n"
        "headings: {}\ncallouts: {}\nquotes: {}\ntables: {}\n"
        "font_files:\n  Vazirmatn: fonts/missing.ttf\n",
        encoding="utf-8",
    )
    with pytest.raises(TemplateValidationError) as exc_info:
        Template.load(tmp_path)
    err = str(exc_info.value)
    assert "fonts/missing.ttf" in err
    assert "font_files.Vazirmatn" in err


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


def test_packaged_template_mirrors_project_template():
    """Packaged wheel copy must stay in sync with the repo-root templates/ theme."""
    import filecmp
    from md_to_docx.template import PACKAGE_DIR, PROJECT_ROOT

    project = PROJECT_ROOT / "templates" / "purple_book"
    packaged = PACKAGE_DIR / "templates" / "purple_book"
    assert project.is_dir()
    assert packaged.is_dir()
    for rel in (
        "config.yaml",
        "mermaid.css",
        "mermaid.json",
        "puppeteer.json",
        "fonts/Vazirmatn-Regular.ttf",
        "fonts/OFL.txt",
    ):
        left = project / rel
        right = packaged / rel
        assert left.is_file(), f"missing project template file: {rel}"
        assert right.is_file(), f"missing packaged template file: {rel}"
        assert filecmp.cmp(left, right, shallow=False), f"template drift: {rel}"


def test_template_load_prefers_project_templates_over_package(tmp_path, monkeypatch):
    """A checkout templates/ directory must win over the packaged copy."""
    import md_to_docx.template as tmpl_mod
    from md_to_docx.template import PROJECT_ROOT

    override = tmp_path / "templates" / "purple_book"
    override.mkdir(parents=True)
    src = PROJECT_ROOT / "templates" / "purple_book" / "config.yaml"
    text = src.read_text(encoding="utf-8").replace("name: purple_book", "name: purple_book_checkout")
    (override / "config.yaml").write_text(text, encoding="utf-8")
    for rel in ("mermaid.css", "mermaid.json", "puppeteer.json"):
        (override / rel).write_text((PROJECT_ROOT / "templates" / "purple_book" / rel).read_text(encoding="utf-8"), encoding="utf-8")
    fonts = override / "fonts"
    fonts.mkdir()
    (fonts / "Vazirmatn-Regular.ttf").write_bytes(
        (PROJECT_ROOT / "templates" / "purple_book" / "fonts" / "Vazirmatn-Regular.ttf").read_bytes()
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(tmpl_mod, "PROJECT_ROOT", tmp_path)
    tmpl = Template.load("purple_book")
    assert tmpl.name == "purple_book_checkout"
    assert tmpl.dir_path == override.resolve()


def test_template_load_from_installed_package_dir(monkeypatch, tmp_path):
    """R3-06 / Packaging: Template.load must find templates from PACKAGE_DIR / 'templates' without PROJECT_ROOT."""
    import md_to_docx.template as tmpl_mod
    monkeypatch.setattr(tmpl_mod, "PROJECT_ROOT", tmp_path / "nowhere")
    monkeypatch.chdir(tmp_path)

    tmpl = Template.load("purple_book")
    assert tmpl.name == "purple_book"
    assert (tmpl.dir_path / "config.yaml").exists()
    assert (tmpl.dir_path / "fonts" / "Vazirmatn-Regular.ttf").exists()


