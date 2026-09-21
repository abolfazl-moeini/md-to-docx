"""
Unit and regression tests for Persian layout quality requirements (Q04-Q14).
"""

from pathlib import Path
import pytest
from md_to_docx import convert_markdown_to_docx, Template
from md_to_docx.pipeline import run_pandoc_ast
from md_to_docx.pandoc_json import ast_to_docx
from md_to_docx.headings import parse_heading

ROOT = Path(__file__).resolve().parent.parent


def test_custom_style_mapping_six_roles(tmp_path):
    md = """---
lang: fa-IR
dir: rtl
---

::: {custom-style="Chapter Overview"}
مرور فصل اول کتاب.
:::

::: {custom-style="DBA Note"}
نکتهٔ DBA: همیشه از کانال‌های امن استفاده کنید.
:::

::: {custom-style="Important Note"}
توجه مهم: از بک‌آپ اطمینان حاصل کنید.
:::

::: {custom-style="Warning"}
هشدار: دسترسی sa را محدود کنید.
:::

::: {custom-style="Lab Note"}
یادداشت تمرین: در آزمایشگاه تست کنید.
:::

::: {custom-style="Screenshot Recommendation"}
پیشنهاد تصویر: از تنظیمات سرور اسکرین‌شات بگیرید.
:::
"""
    out_docx = tmp_path / "custom_styles.docx"
    convert_markdown_to_docx(content=md, output_path=out_docx, template="purple_book", overwrite=True)
    assert out_docx.exists()

    # Verify that all 6 custom styles rendered into tables
    import docx
    doc = docx.Document(str(out_docx))
    assert len(doc.tables) == 6
    for tbl in doc.tables:
        # All custom-styles without title should render single-row tables (no orphaned empty header)
        assert len(tbl.rows) == 1


def test_unknown_custom_style_preserves_content_and_warns(tmp_path):
    md = """---
lang: fa-IR
dir: rtl
---

::: {custom-style="Completely Unknown Style"}
متن درون استایل ناشناخته که نباید از بین برود.
:::
"""
    out_docx = tmp_path / "unknown_style.docx"
    warnings: list[str] = []
    convert_markdown_to_docx(
        content=md,
        output_path=out_docx,
        template="purple_book",
        overwrite=True,
        warnings=warnings,
    )
    assert out_docx.exists()

    import docx
    doc = docx.Document(str(out_docx))
    # Content must be preserved in document paragraphs
    all_text = " ".join(p.text for p in doc.paragraphs)
    assert "متن درون استایل ناشناخته" in all_text
    assert any("Unknown custom-style" in w and "Completely Unknown Style" in w for w in warnings)


def test_custom_style_mapping_via_template_config(tmp_path):
    """G04 & B2 Test A: Custom styles mapped in template config.yaml must resolve without python edits."""
    import shutil
    import yaml
    import docx
    from md_to_docx import Template

    # Create temporary template derived from purple_book
    pb_dir = ROOT / "templates" / "purple_book"
    custom_tmpl_dir = tmp_path / "custom_tmpl"
    shutil.copytree(pb_dir, custom_tmpl_dir)

    cfg_path = custom_tmpl_dir / "config.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    cfg["name"] = "custom_tmpl"
    cfg["custom_styles"] = {
        "Field Note": "note",
    }
    with open(cfg_path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True)

    loaded_tmpl = Template.load(str(custom_tmpl_dir))
    assert loaded_tmpl.custom_styles.get("field note") == "note"

    md = """---
lang: fa-IR
dir: rtl
---

::: {custom-style="Field Note"}
متن یادداشت فیلد که باید به نقش note نگاشت شود.
:::
"""
    out_docx = tmp_path / "field_note.docx"
    convert_markdown_to_docx(content=md, output_path=out_docx, template=loaded_tmpl, overwrite=True)
    assert out_docx.exists()

    doc = docx.Document(str(out_docx))
    # It must be rendered into a callout table, not plain paragraph
    assert len(doc.tables) == 1
    assert "متن یادداشت فیلد" in doc.tables[0].cell(0, 0).text


def test_custom_style_strict_mode_raises_error(tmp_path):
    """G04 & B2 Test C: In strict mode, unknown custom styles must raise an error instead of passing silently."""
    import shutil
    import yaml
    from md_to_docx import Template, ConvertError

    pb_dir = ROOT / "templates" / "purple_book"
    custom_tmpl_dir = tmp_path / "strict_tmpl"
    shutil.copytree(pb_dir, custom_tmpl_dir)

    cfg_path = custom_tmpl_dir / "config.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    cfg["name"] = "strict_tmpl"
    cfg["custom_styles"] = {
        "strict": True,
        "mappings": {
            "Known Style": "note"
        }
    }
    with open(cfg_path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True)

    loaded_tmpl = Template.load(str(custom_tmpl_dir))
    assert loaded_tmpl.custom_styles_strict is True

    md = """---
lang: fa-IR
dir: rtl
---

::: {custom-style="Completely Unknown Style In Strict Mode"}
متن استایل ناشناخته در حالت استریکت.
:::
"""
    out_docx = tmp_path / "strict_fail.docx"
    with pytest.raises(Exception) as exc_info:
        convert_markdown_to_docx(content=md, output_path=out_docx, template=loaded_tmpl, overwrite=True)
    assert "Unknown custom-style" in str(exc_info.value) or "strict" in str(exc_info.value).lower()


def test_heading_id_not_leaked_in_title(tmp_path):
    md = """---
lang: fa-IR
dir: rtl
---

# فصل اول: معماری پایه {#chapter-1}

متن پاراگراف اول.
"""
    out_docx = tmp_path / "heading_id.docx"
    convert_markdown_to_docx(content=md, output_path=out_docx, template="purple_book", overwrite=True)

    import docx
    doc = docx.Document(str(out_docx))
    all_text = " ".join(p.text for p in doc.paragraphs)
    assert "{#chapter-1}" not in all_text
    assert "#chapter-1" not in all_text
    assert "فصل اول: معماری پایه" in all_text


def test_standalone_caption_warning_and_styling(tmp_path):
    md = """---
lang: fa-IR
dir: rtl
---

پاراگراف عادی قبل از کپشن.

شکل ۱-۱. نمای مفهومی Windows Server و Database Engine

در شکل ۱-۱، توضیحات تکمیلی داده شده است که نباید کپشن شمرده شود.
"""
    out_docx = tmp_path / "captions.docx"
    convert_markdown_to_docx(content=md, output_path=out_docx, template="purple_book", overwrite=True)

    import docx
    doc = docx.Document(str(out_docx))
    # Check that standalone caption paragraph is styled as centered
    found_caption = False
    for p in doc.paragraphs:
        if "شکل ۱-۱. نمای مفهومی" in p.text:
            found_caption = True
            # Check paragraph alignment is center
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            assert p.alignment == WD_ALIGN_PARAGRAPH.CENTER
    assert found_caption


def test_callout_with_title_has_keep_next_on_header(tmp_path):
    md = """---
lang: fa-IR
dir: rtl
---

::: note
عنوان اعلان در متن
:::
"""
    out_docx = tmp_path / "callout_header.docx"
    convert_markdown_to_docx(content=md, output_path=out_docx, template="purple_book", overwrite=True)

    import docx
    from docx.oxml.ns import qn
    doc = docx.Document(str(out_docx))
    tbl = doc.tables[0]
    assert len(tbl.rows) == 2
    hdr_p = tbl.cell(0, 0).paragraphs[0]
    # keep_with_next must be True on header row paragraph
    assert hdr_p.paragraph_format.keep_with_next is True
    hdr_trPr = tbl.rows[0]._tr.get_or_add_trPr()
    assert hdr_trPr.find(qn("w:cantSplit")) is not None


def test_heading_badge_table_has_cantsplit(tmp_path):
    md = """---
lang: fa-IR
dir: rtl
---

# ۱.۱۰.۲ عنوان بخش تست با شماره چندبخشی بلند
"""
    out_docx = tmp_path / "heading_badge.docx"
    convert_markdown_to_docx(content=md, output_path=out_docx, template="purple_book", overwrite=True)

    import docx
    from docx.oxml.ns import qn
    doc = docx.Document(str(out_docx))
    tbl = doc.tables[0]
    trPr = tbl.rows[0]._tr.get_or_add_trPr()
    assert trPr.find(qn("w:cantSplit")) is not None


def test_all_four_templates_convert_successfully(tmp_path):
    md = """---
lang: fa-IR
dir: rtl
---

# تیتر اصلی سند آزمایشی

متن فارسی به همراه عبارت انگلیسی **SQL Server Database Engine** و مسیر `D:\\SQLData`.

::: {custom-style="DBA Note"}
نکتهٔ DBA: همیشه از سرویس‌های استاندارد استفاده کنید.
:::

| شماره | نام سرویس | وضعیت |
| :--- | :--- | :--- |
| ۱ | Database Engine | فعال |
| ۲ | SQL Agent | فعال |
"""
    for tmpl_name in ["purple_book", "persian_book", "persian_compact", "persian_report"]:
        out_docx = tmp_path / f"test_{tmpl_name}.docx"
        res = convert_markdown_to_docx(content=md, output_path=out_docx, template=tmpl_name, overwrite=True)
        assert out_docx.exists()
        assert out_docx.stat().st_size > 1000


def test_bordered_placeholder_diagram_rejected(tmp_path):
    """E01: validate_rendered_diagram_image must reject solid rectangles with borders."""
    from PIL import Image, ImageDraw
    from md_to_docx.mermaid import validate_rendered_diagram_image

    # Solid purple 900x450
    solid_path = tmp_path / "solid.png"
    im_solid = Image.new("RGB", (900, 450), "#6B2FA0")
    im_solid.save(solid_path)
    assert not validate_rendered_diagram_image(solid_path)

    # Bordered purple placeholder 900x450 (1px border)
    bordered_path = tmp_path / "bordered.png"
    draw = ImageDraw.Draw(im_solid)
    draw.rectangle([0, 0, 899, 449], outline="#000000", width=2)
    im_solid.save(bordered_path)
    assert not validate_rendered_diagram_image(bordered_path)


def test_callout_full_width_grid_formatting(tmp_path):
    """E06: Callout tables must explicitly set tblW, tblGrid, and cell tcW to span 100% width."""
    md = """---
lang: fa-IR
dir: rtl
---

::: {custom-style="Chapter Overview"}
متن مرور فصل با پهنای کامل صفحه بدون فشرده‌شدن به یک سمت.
:::
"""
    out_docx = tmp_path / "callout_grid.docx"
    convert_markdown_to_docx(content=md, output_path=out_docx, template="purple_book", overwrite=True)

    import docx
    from docx.oxml.ns import qn
    doc = docx.Document(str(out_docx))
    tbl = doc.tables[0]
    tblPr = tbl._tbl.tblPr
    tbl_w = tblPr.find(qn("w:tblW"))
    assert tbl_w is not None
    assert tbl_w.get(qn("w:type")) == "dxa"
    assert int(tbl_w.get(qn("w:w"))) > 5000  # at least printable width in dxa

    grid = tbl._tbl.find(qn("w:tblGrid"))
    assert grid is not None
    assert len(grid.findall(qn("w:gridCol"))) == 1


def test_h1_page_break_before_in_persian_book_and_compact(tmp_path):
    """Section 5: H1 in persian_book and persian_compact must start on a fresh page."""
    md = """---
lang: fa-IR
dir: rtl
---

# فصل اول: مقدمه

متن فصل اول.

# فصل دوم: معماری

متن فصل دوم.
"""
    for tmpl in ["persian_book", "persian_compact"]:
        out_docx = tmp_path / f"h1_break_{tmpl}.docx"
        convert_markdown_to_docx(content=md, output_path=out_docx, template=tmpl, overwrite=True)

        import docx
        doc = docx.Document(str(out_docx))
        h1_paras = [p for p in doc.paragraphs if p.text.startswith("فصل دوم")]
        assert len(h1_paras) == 1
        assert h1_paras[0].paragraph_format.page_break_before is True


def test_dynamic_page_fields_in_template_shells():
    """Section 5 & Q13: Templates must use native dynamic Word PAGE fields, not hardcoded strings."""
    import docx
    from docx.oxml.ns import qn

    for tmpl in ["persian_book", "persian_compact", "persian_report"]:
        shell_path = ROOT / "templates" / tmpl / "shell.docx"
        assert shell_path.exists(), f"Shell missing for {tmpl}"
        doc = docx.Document(str(shell_path))
        section = doc.sections[0]
        footer = section.footer
        fp = footer.paragraphs[0]
        # Check for w:fldSimple with w:instr=" PAGE " and a cached result run (Word-safe)
        fld = fp._p.find(qn("w:fldSimple"))
        assert fld is not None, f"Dynamic PAGE field missing in {tmpl} shell footer"
        assert fld.get(qn("w:instr")).strip() == "PAGE"
        assert fld.find(qn("w:r")) is not None, f"PAGE field in {tmpl} has no result run"


def test_dynamic_page_fields_in_conversion_output(tmp_path):
    """G05 Test C: Verify native dynamic Word PAGE field appears in the actual conversion output DOCX."""
    import docx
    from docx.oxml.ns import qn

    md = """---
lang: fa-IR
dir: rtl
---

# تیتر آزمایش

متن پاراگراف آزمایشی.
"""
    for tmpl in ["persian_book", "persian_compact", "persian_report"]:
        out_docx = tmp_path / f"test_page_{tmpl}.docx"
        convert_markdown_to_docx(content=md, output_path=out_docx, template=tmpl, overwrite=True)
        doc = docx.Document(str(out_docx))
        section = doc.sections[0]
        footer = section.footer
        fp = footer.paragraphs[0]
        fld = fp._p.find(qn("w:fldSimple"))
        assert fld is not None, f"Dynamic PAGE field missing in {tmpl} conversion output footer"
        assert fld.get(qn("w:instr")).strip() == "PAGE"
        assert fld.find(qn("w:r")) is not None, f"PAGE field in {tmpl} output has no result run"


def test_persian_report_identity_and_distinct_shells(tmp_path):
    """G05 & B4: persian_report must have its own distinct shell with header logo and unique hash."""
    import hashlib
    import zipfile
    from xml.etree import ElementTree as ET

    # Test A: Shell hashes must be distinct between persian_compact and persian_report
    compact_shell = ROOT / "templates" / "persian_compact" / "shell.docx"
    report_shell = ROOT / "templates" / "persian_report" / "shell.docx"
    compact_hash = hashlib.md5(compact_shell.read_bytes()).hexdigest()
    report_hash = hashlib.md5(report_shell.read_bytes()).hexdigest()
    assert compact_hash != report_hash, "persian_compact and persian_report shells must not have identical MD5 hashes"

    # Test B: Conversion output of persian_report must have header with image relationship
    md = "# گزارش تست\n\nمتن گزارش.\n"
    out_docx = tmp_path / "report_out.docx"
    convert_markdown_to_docx(content=md, output_path=out_docx, template="persian_report", overwrite=True)

    with zipfile.ZipFile(out_docx) as z:
        names = z.namelist()
        header_names = [n for n in names if n.startswith("word/header") and n.endswith(".xml")]
        assert len(header_names) > 0, "persian_report output must contain word/header*.xml"
        # Verify header rels contains image relationship
        hdr_rels = [n for n in names if n.startswith("word/_rels/header") and n.endswith(".xml.rels")]
        assert len(hdr_rels) > 0, "persian_report output must contain header relationship XML"
        rels_tree = ET.fromstring(z.read(hdr_rels[0]))
        image_rels = [
            elem for elem in rels_tree
            if "image" in elem.get("Type", "")
        ]
        assert len(image_rels) > 0, "persian_report header rels must contain an image relationship for logo"


def test_template_headers_footers_contain_no_book_specific_text(tmp_path):
    """G03 & B1: Headers and footers of template outputs must not contain hardcoded book titles."""
    import zipfile
    from xml.etree import ElementTree as ET

    md = """---
lang: fa-IR
dir: rtl
---

# یک سند کاملاً عمومی و بی‌ارتباط

متن سند آزمایشی برای تست هدر و فوتر.
"""
    forbidden_terms = [
        "کتاب راهنمای جامع مدیریت پایگاه داده",
        "SQL Server",
        "Database Engine",
    ]
    for tmpl in ["purple_book", "persian_book", "persian_compact", "persian_report"]:
        out_docx = tmp_path / f"test_hdr_{tmpl}.docx"
        convert_markdown_to_docx(content=md, output_path=out_docx, template=tmpl, overwrite=True)
        with zipfile.ZipFile(out_docx) as z:
            for name in z.namelist():
                if ("header" in name or "footer" in name) and name.endswith(".xml"):
                    tree = ET.fromstring(z.read(name))
                    texts = [t.text for t in tree.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t") if t.text]
                    full_hdr_footer_text = " ".join(texts)
                    for term in forbidden_terms:
                        assert term not in full_hdr_footer_text, (
                            f"Found forbidden term '{term}' in {name} of {tmpl} output: '{full_hdr_footer_text}'"
                        )


def test_manifest_sensitive_strings_completeness():
    """Section 4 & 11: All 61 fixtures must have meaningful sensitive strings in manifest.yaml."""
    import yaml
    manifest_path = ROOT / "tests" / "fixtures" / "persian_layout" / "manifest.yaml"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    fixtures = manifest["fixtures"]
    assert len(fixtures) == 61
    for fix in fixtures:
        fid = fix["id"]
        s_strings = fix.get("sensitive_strings", [])
        assert len(s_strings) >= 2, f"Fixture {fid} has {len(s_strings)} sensitive strings (must be >= 2)"
        fix_path = ROOT / "tests" / "fixtures" / "persian_layout" / fix["rel_path"]
        content = fix_path.read_text(encoding="utf-8")
        for s in s_strings:
            assert s in content, f"Sensitive string '{s}' not found in source fixture {fid}"


def test_q15_intentional_corruption_detection(tmp_path):
    """Q15: The oracles must detect and fail each of the 6 intentional corruptions."""
    import sys
    import zipfile
    from xml.etree import ElementTree as ET
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.matrix_runner import run_structural_oracle, run_content_oracle, extract_docx_text
    from md_to_docx.mermaid import validate_rendered_diagram_image

    md = """---
lang: fa-IR
dir: rtl
---

# عنوان اصلی سند

این یک پاراگراف حاوی متن بسیار حساس است: **SQL Server Database Engine**.

```sql
SELECT @@VERSION, @@SERVERNAME;
GO
```

| ستون اول | ستون دوم |
| :--- | :--- |
| داده ۱ | داده ۲ |

[پیوند به مایکروسافت](https://learn.microsoft.com)
"""
    clean_docx = tmp_path / "clean.docx"
    convert_markdown_to_docx(content=md, output_path=clean_docx, template="purple_book", overwrite=True)

    manifest_entry = {
        "id": "CORRUPT_TEST",
        "sensitive_strings": ["SQL Server Database Engine", "SELECT @@VERSION", "داده ۱"]
    }

    # 1. Clean DOCX passes both oracles
    struct_ok, _ = run_structural_oracle(clean_docx)
    content_ok, _ = run_content_oracle(clean_docx, manifest_entry)
    assert struct_ok and content_ok

    # Corruption 1: Deletion of sensitive paragraph text
    c1_docx = tmp_path / "c1_para_deleted.docx"
    with zipfile.ZipFile(clean_docx, "r") as zin, zipfile.ZipFile(c1_docx, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = data.replace(b"<w:t>Engine</w:t>", b"")
            zout.writestr(item, data)
    c1_ok, c1_issues = run_content_oracle(c1_docx, manifest_entry)
    assert not c1_ok, "Oracle failed to detect paragraph deletion"
    assert any("SQL Server Database Engine" in iss for iss in c1_issues)

    # Corruption 2: Truncation of code block
    c2_docx = tmp_path / "c2_code_truncated.docx"
    with zipfile.ZipFile(clean_docx, "r") as zin, zipfile.ZipFile(c2_docx, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = data.replace(b"<w:t>VERSION</w:t>", b"")
            zout.writestr(item, data)
    c2_ok, c2_issues = run_content_oracle(c2_docx, manifest_entry)
    assert not c2_ok, "Oracle failed to detect code block truncation"
    assert any("SELECT @@VERSION" in iss for iss in c2_issues)

    # Corruption 3: Column data swapped/missing
    c3_docx = tmp_path / "c3_column_swapped.docx"
    with zipfile.ZipFile(clean_docx, "r") as zin, zipfile.ZipFile(c3_docx, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = data.replace("<w:t>داده</w:t>".encode("utf-8"), b"")
            zout.writestr(item, data)
    c3_ok, c3_issues = run_content_oracle(c3_docx, manifest_entry)
    assert not c3_ok, "Oracle failed to detect table column corruption"
    assert any("داده ۱" in iss for iss in c3_issues)

    # Corruption 4: Diagram replaced by solid rectangular placeholder (E01)
    from PIL import Image
    blank_png = tmp_path / "fake_placeholder.png"
    Image.new("RGB", (800, 400), "#6B2FA0").save(blank_png)
    assert not validate_rendered_diagram_image(blank_png), "Diagram oracle failed to reject blank placeholder"

    # Corruption 5: Broken link / corrupt relationship XML
    c5_docx = tmp_path / "c5_broken_rel.docx"
    with zipfile.ZipFile(clean_docx, "r") as zin, zipfile.ZipFile(c5_docx, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/_rels/document.xml.rels":
                data = b"<malformed_xml>broken"
            zout.writestr(item, data)
    c5_ok, c5_issues = run_structural_oracle(c5_docx)
    assert not c5_ok, "Structural oracle failed to detect malformed relationship XML"
    assert any("Malformed XML" in iss for iss in c5_issues)

    # Corruption 6: requested image width larger than the printable area is clamped
    from md_to_docx.renderer import DocxRenderer
    renderer = DocxRenderer(template=Template.load("purple_book"))
    disp_w, _disp_h = renderer._fit_image_size(9600, 5400, width_in=10.0)
    assert disp_w <= renderer.content_width_in + 0.01, (
        f"Oversized image width {disp_w}in was not clamped to content width {renderer.content_width_in}in"
    )


def _paragraph_bidi_on(paragraph) -> bool:
    from docx.oxml.ns import qn
    pPr = paragraph._p.find(qn("w:pPr"))
    if pPr is None:
        return False
    bidi = pPr.find(qn("w:bidi"))
    if bidi is None:
        return False
    return bidi.get(qn("w:val"), "1") != "0"


def test_docx_never_emits_word_invalid_justification(tmp_path):
    """OOXML ST_Jc values must be valid. 'start' and 'end' ARE valid per ECMA-376 §17.18.44
    and are written by Word itself in real Persian documents (1043 occurrences in reference docs).
    The docstring previously claimed they were invalid — that claim was wrong and is corrected here.
    Invalid values would be raw strings like 'PRIMARY_LIGHT' or typos.
    """
    import zipfile
    from lxml import etree
    from docx.oxml.ns import qn

    md = """---
lang: fa-IR
dir: rtl
---

# عنوان فارسی

متن پاراگراف.

* آیتم فارسی
* English only item
"""
    out_docx = tmp_path / "word_safe_jc.docx"
    convert_markdown_to_docx(content=md, output_path=out_docx, template="purple_book", overwrite=True)
    with zipfile.ZipFile(out_docx) as z:
        root = etree.fromstring(z.read("word/document.xml"))
    jc_vals = {el.get(qn("w:val")) for el in root.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}jc")}
    # All values must be valid ST_Jc entries (start/end are valid per spec and used by Word itself)
    valid_jc = {"left", "right", "center", "both", "start", "end",
                "distribute", "highKashida", "lowKashida", "mediumKashida", "numTab", "thaiDistribute"}
    assert jc_vals <= valid_jc, f"Invalid jc values found: {jc_vals - valid_jc}"


def test_mixed_list_items_share_container_direction(tmp_path):
    """E05: an English-only item must not flip indent/bidi of a Persian list.
    Lists indent from the logical START edge via w:ind/@w:left (direction-aware) plus
    @w:hanging — never the physical right_indent, and never the non-CT_Ind @w:start.
    """
    import zipfile
    from lxml import etree

    md = """---
lang: fa-IR
dir: rtl
---

* نصب و راه‌اندازی پایگاه داده
* Windows Server Failover Clustering
* پیکربندی لایه مجازی‌سازی
    * تنظیمات کارت شبکه مجازی
    * Windows Server Failover Clustering (WSFC)
"""
    out_docx = tmp_path / "mixed_list.docx"
    convert_markdown_to_docx(content=md, output_path=out_docx, template="purple_book", overwrite=True)

    import docx
    doc = docx.Document(str(out_docx))
    # Marker is now bullet '•' followed by tab
    list_paras = [p for p in doc.paragraphs if p.text.strip().startswith("•")]
    assert len(list_paras) == 5
    english = [p for p in list_paras if "Windows Server Failover Clustering" in p.text]
    persian = [p for p in list_paras if "Windows Server Failover Clustering" not in p.text]
    assert len(english) == 2
    assert len(persian) == 3

    # Indent must come from the logical START edge: w:ind/@w:left, plus @w:hanging.
    # Any attribute outside CT_Ind (notably @w:start) is a Word-compatibility trap.
    from md_to_docx.oxml import CT_IND_ATTRIBUTES
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    with zipfile.ZipFile(out_docx) as z:
        doc_root = etree.fromstring(z.read("word/document.xml"))

    list_ps = [
        p for p in doc_root.findall(f".//{{{W}}}p")
        if any("•" in (t.text or "") for t in p.iter(f"{{{W}}}t"))
    ]
    assert len(list_ps) == 5
    for p_el in list_ps:
        ind = p_el.find(f".//{{{W}}}ind")
        assert ind is not None, "List item must have w:ind element"
        attrs = {etree.QName(k).localname for k in ind.attrib}
        illegal = attrs - CT_IND_ATTRIBUTES
        assert not illegal, (
            f"w:ind carries attributes outside CT_Ind: {sorted(illegal)}; "
            f"allowed: {sorted(CT_IND_ATTRIBUTES)}"
        )
        start_val = ind.get(f"{{{W}}}left")
        assert start_val is not None and int(start_val) > 0, (
            f"List item must have w:ind/@w:left > 0 (logical START indent), got: {start_val!r}"
        )
        # All items in this RTL doc should be bidi
        assert _paragraph_bidi_on(docx.text.paragraph.Paragraph(p_el, None)), \
            f"list item should stay RTL"


def test_validate_rejects_unreadable_image(tmp_path):
    """E01: unreadable/corrupt files must fail closed, not be treated as valid diagrams."""
    from md_to_docx.mermaid import validate_rendered_diagram_image

    bad = tmp_path / "not_an_image.png"
    bad.write_bytes(b"this is not a png")
    assert not validate_rendered_diagram_image(bad)


def test_mermaid_runtime_css_includes_overflow_without_font(tmp_path):
    """E02 overflow CSS must be injected even when the template has no font file."""
    from md_to_docx.mermaid import _effective_mermaid_css
    from md_to_docx.template import Template

    tmpl = Template.load("purple_book")
    tmpl.font_files = {}
    # Point body font at a name that will not resolve under fonts/
    tmpl.fonts = dict(tmpl.fonts)
    tmpl.fonts["body"] = "MissingFontFamily"
    css_path = _effective_mermaid_css(tmpl, tmp_path)
    assert css_path is not None and css_path.exists()
    css = css_path.read_text(encoding="utf-8")
    assert "overflow: visible" in css
    assert "foreignObject" in css


def test_paragraph_align_defaults_to_start_ragged_right(tmp_path):
    """G06 & M1 Test A: Default paragraph alignment for Persian body must be flush-right (start).
    'start' is the logical RTL-aware value: LibreOffice and Word both render it right-aligned.
    Previously the code omitted w:jc in RTL paragraphs and relied on inheriting jc=right from Normal,
    which caused LibreOffice to flip it to left (the bug). Now we write jc=start explicitly.
    """
    import zipfile
    from lxml import etree
    from docx.oxml.ns import qn

    md = """---
lang: fa-IR
dir: rtl
---

# عنوان اصلی

این یک پاراگراف بدنه به زبان فارسی است که باید تراز راست با انتهای آزاد داشته باشد.
"""
    out_docx = tmp_path / "ragged_right.docx"
    convert_markdown_to_docx(content=md, output_path=out_docx, template="persian_book", overwrite=True)

    with zipfile.ZipFile(out_docx) as z:
        doc_root = etree.fromstring(z.read("word/document.xml"))
        styles_root = etree.fromstring(z.read("word/styles.xml"))

    # Check Normal style in styles.xml: must have jc=start (not jc=right which flips in bidi)
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    normal_jc = None
    for style in styles_root.findall(f"{{{W}}}style"):
        if style.get(f"{{{W}}}styleId") == "Normal":
            jc_el = style.find(f".//{{{W}}}jc")
            if jc_el is not None:
                normal_jc = jc_el.get(f"{{{W}}}val")
    assert normal_jc == "start", (
        f"Normal style jc should be 'start' (logical RTL-safe), got: {normal_jc!r}. "
        "jc=right in a bidi paragraph is flipped to left by LibreOffice."
    )

    # Check body paragraph has jc=start (either explicitly or inherited from Normal)
    for p in doc_root.findall(f".//{{{W}}}p"):
        texts = [t.text for t in p.iter(f"{{{W}}}t") if t.text]
        if "این یک پاراگراف بدنه" in "".join(texts):
            jc_el = p.find(f".//{{{W}}}jc")
            if jc_el is not None:
                val = jc_el.get(f"{{{W}}}val")
                assert val in ("start", "right"), (
                    f"Body paragraph jc should be 'start' or inherit start from Normal, got: {val!r}"
                )
            # 'both' must never appear for start alignment
            assert jc_el is None or jc_el.get(f"{{{W}}}val") != "both"
            break


def test_paragraph_align_both_restores_justification(tmp_path):
    """G06 & M1 Test B: Setting page.paragraph_align: both restores justified text."""
    import zipfile
    from xml.etree import ElementTree as ET
    from docx.oxml.ns import qn

    md = """---
lang: fa-IR
dir: rtl
---

# عنوان اصلی

این یک پاراگراف بدنه به زبان فارسی است که باید تراز دوطرفه (both) داشته باشد.
"""
    out_docx = tmp_path / "justified_both.docx"
    # finilize.v3.md Section 1.2: purple_book now defaults to start; explicit text_align="both" restores justified text.
    convert_markdown_to_docx(content=md, output_path=out_docx, template="purple_book", text_align="both", overwrite=True)

    with zipfile.ZipFile(out_docx) as z:
        root = ET.fromstring(z.read("word/document.xml"))

    body_jc_vals = []
    for p in root.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
        texts = [t.text for t in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t") if t.text]
        full_text = "".join(texts)
        if "این یک پاراگراف بدنه" in full_text:
            jc = p.find(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}jc")
            if jc is not None:
                body_jc_vals.append(jc.get(qn("w:val")))

    assert len(body_jc_vals) == 1
    assert body_jc_vals[0] == "both"


def test_caption_size_and_paragraph_spacing(tmp_path):
    """G08 & M8: caption.size_pt and page.space_after_pt must be applied to DOCX output."""
    import shutil
    import yaml
    import zipfile
    from xml.etree import ElementTree as ET
    from docx.oxml.ns import qn
    from md_to_docx import Template

    pb_dir = ROOT / "templates" / "purple_book"
    custom_tmpl_dir = tmp_path / "custom_caption_tmpl"
    shutil.copytree(pb_dir, custom_tmpl_dir)

    cfg_path = custom_tmpl_dir / "config.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    cfg["name"] = "custom_caption_tmpl"
    cfg["caption"] = {"size_pt": 10.0}
    cfg["page"]["space_after_pt"] = 8.0
    with open(cfg_path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True)

    loaded_tmpl = Template.load(str(custom_tmpl_dir))
    assert loaded_tmpl.caption_size_pt == 10.0
    assert loaded_tmpl.paragraph_space_after_pt == 8.0

    # Convert document with image + caption
    asset_img = ROOT / "tests" / "fixtures" / "persian_layout" / "assets" / "horizontal_sample.png"
    md = f"""---
lang: fa-IR
dir: rtl
---

پاراگراف اول با فاصله ۸ پوینت بعد از آن.

![نمودار تست]({asset_img.as_posix()})
شکل ۱-۱. شرح تصویر آزمایشی با فونت ده پوینت
"""
    out_docx = tmp_path / "caption_size_out.docx"
    convert_markdown_to_docx(content=md, output_path=out_docx, template=loaded_tmpl, overwrite=True)

    with zipfile.ZipFile(out_docx) as z:
        root = ET.fromstring(z.read("word/document.xml"))

    # Verify caption paragraph run size is 10pt = 20 half-points
    found_caption = False
    for p in root.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
        texts = [t.text for t in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t") if t.text]
        full_text = "".join(texts)
        if "شکل ۱-۱. شرح تصویر آزمایشی" in full_text:
            found_caption = True
            sz_els = p.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sz")
            assert len(sz_els) > 0
            assert any(el.get(qn("w:val")) == "20" for el in sz_els), "Caption run size must be 20 half-points (10pt)"
    assert found_caption

    # Verify body paragraph space after is 8pt = 160 twips
    found_body_spacing = False
    for p in root.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
        texts = [t.text for t in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t") if t.text]
        full_text = "".join(texts)
        if "پاراگراف اول با فاصله ۸ پوینت" in full_text:
            sp = p.find(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}spacing")
            if sp is not None:
                assert sp.get(qn("w:after")) == "160", "Paragraph space_after must be 160 twips (8pt)"
                found_body_spacing = True
    assert found_body_spacing


def test_oracle_extracts_only_body_and_rejects_header_only_text(tmp_path):
    """G09 & M4: Sensitive strings present only in header/footer must NOT satisfy content oracle."""
    import sys
    import zipfile
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.matrix_runner import run_content_oracle, extract_docx_text

    md = """---
lang: fa-IR
dir: rtl
---

# عنوان بدنه

متن معمولی در بدنه سند.
"""
    clean_docx = tmp_path / "body_doc.docx"
    convert_markdown_to_docx(content=md, output_path=clean_docx, template="purple_book", overwrite=True)

    # Corrupt by adding sensitive string strictly into header
    header_docx = tmp_path / "header_leak.docx"
    with zipfile.ZipFile(clean_docx, "r") as zin, zipfile.ZipFile(header_docx, "w") as zout:
        for item in zin.infolist():
            if item.filename != "word/header1.xml":
                zout.writestr(item, zin.read(item.filename))
        zout.writestr(
            "word/header1.xml",
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            b'<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            b'<w:p><w:r><w:t>SENSITIVE_SECRET_HEADER_TEXT</w:t></w:r></w:p>'
            b'</w:hdr>',
        )

    # Verify extract_docx_text does NOT include header text by default
    extracted = extract_docx_text(header_docx)
    assert "SENSITIVE_SECRET_HEADER_TEXT" not in extracted

    manifest_entry = {
        "id": "HEADER_TEST",
        "sensitive_strings": ["SENSITIVE_SECRET_HEADER_TEXT"]
    }
    content_ok, issues = run_content_oracle(header_docx, manifest_entry)
    assert not content_ok, "Content oracle must fail when sensitive text is only in header"
    assert any("SENSITIVE_SECRET_HEADER_TEXT" in iss for iss in issues)


def test_oracle_validates_counts_and_fails_on_deleted_table(tmp_path):
    """G10 & M2: Structural counts (headings, code_blocks, tables, callouts) must be verified against manifest counts."""
    import sys
    import zipfile
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.matrix_runner import run_content_oracle

    md = """---
lang: fa-IR
dir: rtl
---

# فصل اول: بررسی

متن معرفی.

```sql
SELECT 1;
```

::: {custom-style="DBA Note"}
نکته دیتابیس
:::

| ستون ۱ | ستون ۲ |
| :--- | :--- |
| الف | ب |
"""
    doc_path = tmp_path / "counts_doc.docx"
    convert_markdown_to_docx(content=md, output_path=doc_path, template="purple_book", overwrite=True)

    manifest_entry = {
        "id": "COUNTS_TEST",
        "sensitive_strings": ["فصل اول", "SELECT 1"],
        "counts": {
            "headings": 1,
            "code_blocks": 1,
            "callouts": 1,
            "tables": 1,
        }
    }

    # 1. Clean document passes count checks
    ok, issues = run_content_oracle(doc_path, manifest_entry)
    assert ok, f"Expected clean doc to pass count check, got: {issues}"

    # 2. Corrupt document by deleting the data table
    corrupt_docx = tmp_path / "table_deleted.docx"
    with zipfile.ZipFile(doc_path, "r") as zin, zipfile.ZipFile(corrupt_docx, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                import re
                # Delete table marked with descr data_table
                data = re.sub(rb"<w:tbl>.*?<w:tblDescription\s+w:val=\"data_table\".*?</w:tbl>", b"", data, flags=re.DOTALL)
            zout.writestr(item, data)

    ok_c, issues_c = run_content_oracle(corrupt_docx, manifest_entry)
    assert not ok_c, "Oracle must fail when data table is deleted"
    assert any("table" in iss.lower() for iss in issues_c)


def test_matrix_runner_reports_pending_reviews_when_no_page_rendering(tmp_path):
    """G01 & G02: When LibreOffice is missing, reviews.json must report 'pending', NOT 'accepted'."""
    import sys
    import json
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.matrix_runner import generate_matrix_reports

    sample_results = [
        {
            "fixture_id": "S01",
            "template": "persian_book",
            "status": "pass",
            "conversion_time_sec": 0.5,
            "file_size_bytes": 12000,
            "structural_pass": True,
            "content_pass": True,
            "issues": [],
            "warnings": [],
        }
    ]

    out_dir = tmp_path / "reports_test"
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_matrix_reports(sample_results, out_dir, "test_run", 1.0)

    # 1. reviews.json must have status "pending", NOT "accepted"
    with open(out_dir / "reviews.json", "r", encoding="utf-8") as f:
        reviews = json.load(f)
    assert len(reviews) == 1
    assert reviews[0]["status"] == "pending", "Status must be 'pending' when visual rendering was not performed"
    assert reviews[0]["reviewed_by"] == "none"

    # 2. run.json must report environment detection
    with open(out_dir / "run.json", "r", encoding="utf-8") as f:
        run_meta = json.load(f)
    assert "environment" in run_meta
    assert "soffice" in run_meta["environment"]
    assert "word" in run_meta["environment"]

    # 3. summary.md must report distinct counts
    with open(out_dir / "summary.md", "r", encoding="utf-8") as f:
        summary_txt = f.read()
    assert "صفحات مرورشده" in summary_txt or "مرور بصری" in summary_txt


def test_verify_warnings_logic():
    """G11 & M3: verify_warnings must catch missing expected warnings and unexpected warnings."""
    import sys
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.matrix_runner import verify_warnings

    # 1. Matching warnings passes
    act = ["Standalone caption without associated image: 'شکل ۱-۱' at path"]
    exp = ["caption_without_image"]
    issues = verify_warnings(act, exp)
    assert len(issues) == 0

    # 2. Missing expected warning fails
    issues_missing = verify_warnings([], ["caption_without_image"])
    assert len(issues_missing) > 0
    assert any("Missing expected warning" in iss for iss in issues_missing)

    # 3. Unexpected warning fails
    issues_unexpected = verify_warnings(["Unexpected unknown warning: bad format"], [])
    assert len(issues_unexpected) > 0
    assert any("Unexpected warning" in iss for iss in issues_unexpected)

    # 4. Five caption expectations consume five distinct actuals (no reuse)
    five_act = [
        f"Standalone caption without associated image: 'شکل ۱-{i}' at path"
        for i in range(1, 6)
    ]
    five_exp = [
        "caption_without_image @ شکل ۱-۱",
        "caption_without_image @ شکل ۱-۲",
        "caption_without_image @ شکل ۱-۳",
        "caption_without_image @ شکل ۱-۴",
        "caption_without_image @ شکل ۱-۵",
    ]
    persian_nums = ["۱", "۲", "۳", "۴", "۵"]
    five_act_ident = [
        f"caption_without_image: Standalone caption without associated image @ شکل ۱-{n} at path"
        for n in persian_nums
    ]
    assert verify_warnings(five_act_ident, five_exp) == []
    assert verify_warnings(five_act_ident[:4], five_exp)
    assert any("Missing expected warning" in iss for iss in verify_warnings(five_act_ident[:4], five_exp))
    wrong_ident = ["caption_without_image @ block 999"] * 5
    wrong_issues = verify_warnings(five_act_ident, wrong_ident)
    assert wrong_issues, "Identity-mismatched caption warnings must not match"


@pytest.mark.mermaid
def test_mermaid_svg_label_verification(tmp_path):
    """G12 & M5: Mermaid Persian node labels must be verifiable from rendered SVG output."""
    from md_to_docx import Template
    from md_to_docx.mermaid import render_mermaid_to_png, extract_mermaid_svg_labels, validate_mermaid_svg_labels

    tmpl = Template.load("templates/purple_book")
    svg_out = tmp_path / "diagram_test.svg"
    code = "graph TD; A[شروع فرآیند دیتابیس] --> B[پایان عملیات ذخیره‌سازی];"

    render_mermaid_to_png(code, svg_out, tmpl)
    assert svg_out.exists()
    assert svg_out.stat().st_size > 0

    labels = extract_mermaid_svg_labels(svg_out)
    assert any("شروع فرآیند" in l for l in labels), f"Label 'شروع فرآیند' not found in {labels}"
    assert any("پایان عملیات" in l for l in labels), f"Label 'پایان عملیات' not found in {labels}"

    # Positive test with validate_mermaid_svg_labels
    ok, missing = validate_mermaid_svg_labels(svg_out, ["شروع فرآیند", "پایان عملیات"])
    assert ok, f"Expected validation to pass, missing: {missing}"

    # Negative test: missing expected label must fail validation
    ok_neg, missing_neg = validate_mermaid_svg_labels(svg_out, ["شروع فرآیند", "برچسب مفقود ناموجود"])
    assert not ok_neg, "Expected validation to fail on missing label"
    assert "برچسب مفقود ناموجود" in missing_neg


def test_embedded_image_aspect_ratio_preserved(tmp_path):
    """G13 & Section 8.2: Aspect ratio of embedded images in DOCX must match source within 1%."""
    import zipfile
    from PIL import Image
    from xml.etree import ElementTree as ET

    s09_path = ROOT / "tests" / "fixtures" / "persian_layout" / "synthetic" / "S09.md"
    out_docx = tmp_path / "s09_aspect.docx"
    convert_markdown_to_docx(input_path=s09_path, output_path=out_docx, template="purple_book", overwrite=True)

    with zipfile.ZipFile(out_docx, "r") as z:
        doc_root = ET.fromstring(z.read("word/document.xml"))
        rels_root = ET.fromstring(z.read("word/_rels/document.xml.rels"))

        rid_to_target = {}
        for rel in rels_root.iter("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
            rid_to_target[rel.get("Id")] = rel.get("Target")

        # Find all drawings and compare cx/cy with media pixel dimensions
        drawings = list(doc_root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing"))
        assert len(drawings) >= 4, f"Expected at least 4 images in S09, found {len(drawings)}"

        for drawing in drawings:
            extent = drawing.find(".//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}extent")
            blip = drawing.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip")
            if extent is not None and blip is not None:
                cx = int(extent.get("cx"))
                cy = int(extent.get("cy"))
                docx_aspect = cx / cy

                embed_id = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
                target_media = rid_to_target.get(embed_id)
                if target_media:
                    norm_target = "word/" + target_media if not target_media.startswith("word/") else target_media
                    with Image.open(z.open(norm_target)) as orig_img:
                        orig_w, orig_h = orig_img.size
                        orig_aspect = orig_w / orig_h

                    rel_diff = abs(docx_aspect - orig_aspect) / orig_aspect
                    assert rel_diff < 0.01, (
                        f"Aspect ratio distortion on {target_media}: "
                        f"original {orig_w}x{orig_h} (aspect={orig_aspect:.4f}) vs "
                        f"docx extent {cx}x{cy} (aspect={docx_aspect:.4f}), rel diff: {rel_diff:.4f}"
                    )


def test_b00_exact_expected_warnings_emitted(tmp_path):
    """G11 & M3: Converting B00 must produce exactly 5 caption_without_image warnings."""
    b00_path = ROOT / "tests" / "fixtures" / "persian_layout" / "source" / "B00.md"
    out_docx = tmp_path / "b00_warnings.docx"
    warnings: list[str] = []
    convert_markdown_to_docx(input_path=b00_path, output_path=out_docx, template="purple_book", warnings=warnings, overwrite=True)

    assert len(warnings) == 5, f"Expected exactly 5 warnings for B00, got {len(warnings)}: {warnings}"
    for w in warnings:
        assert "Standalone caption without associated image" in w or "caption without" in w.lower()

    # Verify each of the 5 expected figure captions is present
    expected_figures = ["شکل ۱-۱", "شکل ۱-۲", "شکل ۱-۳", "شکل ۲-۱", "شکل ۲-۲"]
    for fig in expected_figures:
        assert any(fig in w for w in warnings), f"Missing warning for {fig} in {warnings}"


def test_representative_fixtures_structural_counts(tmp_path):
    """G10 & M2: Output structures of representative fixtures must strictly match manifest counts."""
    import yaml
    import sys
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.matrix_runner import run_content_oracle, extract_docx_structural_counts

    manifest_path = ROOT / "tests" / "fixtures" / "persian_layout" / "manifest.yaml"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    fid_to_entry = {f["id"]: f for f in manifest["fixtures"]}

    representative_ids = ["C01", "C04", "S05", "S07", "S09"]
    for fid in representative_ids:
        f_entry = fid_to_entry[fid]
        in_path = ROOT / "tests" / "fixtures" / "persian_layout" / f_entry["rel_path"]
        out_docx = tmp_path / f"{fid}_counts.docx"

        warnings: list[str] = []
        convert_markdown_to_docx(
            input_path=in_path,
            output_path=out_docx,
            template="purple_book",
            overwrite=True,
            warnings=warnings,
        )

        ok, issues = run_content_oracle(out_docx, f_entry)
        assert ok, f"Content oracle failed on representative fixture {fid}: {issues}"

        counts = extract_docx_structural_counts(out_docx)
        exp_counts = f_entry["counts"]
        for k in ("headings", "code_blocks", "tables", "callouts", "mermaid_blocks", "images"):
            if k in exp_counts:
                assert counts[k] == exp_counts[k], (
                    f"Structural count mismatch on {fid} for '{k}': expected {exp_counts[k]}, got {counts[k]}"
                )


