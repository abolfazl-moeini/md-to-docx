"""Word-quality defects from word_quality_fix_plan.md (W-01 … W-09)."""

import zipfile

from docx.oxml.ns import qn

from md_to_docx import convert_markdown_to_docx
from md_to_docx.oxml import PPR_CHILD_ORDER, RPR_CHILD_ORDER

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

PURE = "این یک جملهٔ فارسی هفت کلمه‌ای برای سنجش تکه‌تکه شدن ران است."
MIXED = "فارسی SQL Server است."

SAMPLE = f"""# عنوان نمونه

{PURE}

{MIXED}

> نقل‌قول برای سبک Quote.

متن پاورقی اینجاست[^1].

[^1]: توضیح پاورقی

```python
def answer():
    return 1
```
"""


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _in_order(names: list[str], order: tuple[str, ...]) -> bool:
    rank = {name: i for i, name in enumerate(order)}
    ranked = [rank[name] for name in names if name in rank]
    return ranked == sorted(ranked)


def _convert(tmp_path):
    out = tmp_path / "quality.docx"
    convert_markdown_to_docx(
        content=SAMPLE,
        output_path=out,
        template="purple_book",
        base_dir=tmp_path,
        overwrite=True,
    )
    return out


def test_rpr_and_ppr_follow_schema_order(tmp_path):
    out = _convert(tmp_path)
    with zipfile.ZipFile(out) as zf:
        xmls = [zf.read("word/document.xml"), zf.read("word/styles.xml")]
        if "word/footnotes.xml" in zf.namelist():
            xmls.append(zf.read("word/footnotes.xml"))
    from lxml import etree

    bad_r = bad_p = 0
    for blob in xmls:
        root = etree.fromstring(blob)
        for rPr in root.iter(f"{W}rPr"):
            names = [_local(child.tag) for child in rPr]
            if not _in_order(names, RPR_CHILD_ORDER):
                bad_r += 1
        for pPr in root.iter(f"{W}pPr"):
            names = [_local(child.tag) for child in pPr]
            if not _in_order(names, PPR_CHILD_ORDER):
                bad_p += 1
    assert bad_r == 0
    assert bad_p == 0


def test_pure_persian_sentence_is_not_split_into_a_run_per_word(tmp_path):
    out = _convert(tmp_path)
    from docx import Document

    doc = Document(str(out))
    paragraph = next(p for p in doc.paragraphs if PURE in p.text)
    assert paragraph.text == PURE
    assert len(paragraph.runs) <= 3


def test_mixed_sentence_breaks_only_on_script_change(tmp_path):
    out = _convert(tmp_path)
    from docx import Document

    doc = Document(str(out))
    paragraph = next(p for p in doc.paragraphs if "SQL Server" in p.text and "فارسی" in p.text)
    assert paragraph.text == MIXED
    assert any(run.text == "SQL Server" for run in paragraph.runs)
    assert len(paragraph.runs) == 3


def test_semantic_styles_and_no_east_asia_font(tmp_path):
    out = _convert(tmp_path)
    from lxml import etree

    with zipfile.ZipFile(out) as zf:
        root = etree.fromstring(zf.read("word/document.xml"))
        styles = etree.fromstring(zf.read("word/styles.xml"))
        settings = zf.read("word/settings.xml")
    assert b"ja-JP" not in settings
    style_ids = {el.get(qn("w:val")) for el in root.iter(f"{W}pStyle")}
    assert "Heading1" in style_ids
    assert "Quote" in style_ids
    assert "CodeBlock" in style_ids
    for fonts in list(root.iter(f"{W}rFonts")) + list(styles.iter(f"{W}rFonts")):
        assert fonts.get(f"{W}eastAsia") is None
    rtl_gutter = root.find(f".//{W}sectPr/{W}rtlGutter")
    assert rtl_gutter is not None


def test_heading_levels_caption_and_footnote_styles(tmp_path):
    """Heading 2–6, an image caption, and a footnote must carry their paragraph styles."""
    from pathlib import Path

    img = Path("tests/fixtures/persian_layout/assets/tiny_inline.png").resolve()
    md = f"""# سطح یک

## سطح دو

### سطح سه

#### سطح چهار

##### سطح پنج

###### سطح شش

بدنهٔ سند[^note].

[^note]: توضیح پاورقی

![]({img})

شکل ۱-۱. نمای نمونه
"""
    warnings: list[str] = []
    out = tmp_path / "levels.docx"
    convert_markdown_to_docx(
        content=md,
        output_path=out,
        template="purple_book",
        base_dir=tmp_path,
        overwrite=True,
        warnings=warnings,
    )
    from lxml import etree

    with zipfile.ZipFile(out) as zf:
        root = etree.fromstring(zf.read("word/document.xml"))
        notes = etree.fromstring(zf.read("word/footnotes.xml"))
    styles = {el.get(qn("w:val")) for el in root.iter(f"{W}pStyle")}
    for level in range(1, 7):
        assert f"Heading{level}" in styles
    assert "Caption" in styles
    note_styles = {el.get(qn("w:val")) for el in notes.iter(f"{W}pStyle")}
    assert "FootnoteText" in note_styles
    text = "".join(el.text or "" for el in root.iter(f"{W}t"))
    assert "شکل ۱-۱. نمای نمونه" in text
    assert not any("شکل ۱-۱" in item and "caption_without_image" in item for item in warnings)


def test_paragraph_mark_and_footnote_reference_are_bidi(tmp_path):
    out = _convert(tmp_path)
    from lxml import etree

    with zipfile.ZipFile(out) as zf:
        root = etree.fromstring(zf.read("word/document.xml"))
    bidi = list(root.iter(f"{W}bidi"))
    # Paragraph bidi lives on pPr, not on runs.
    p_bidi = [el for el in bidi if _local(el.getparent().tag) == "pPr"]
    marks = []
    for pPr in root.iter(f"{W}pPr"):
        mark = pPr.find(f"{W}rPr")
        if mark is not None and mark.find(f"{W}rtl") is not None:
            marks.append(mark)
    assert p_bidi
    assert len(marks) == len(p_bidi)
    refs = list(root.iter(f"{W}footnoteReference"))
    assert refs
    for ref in refs:
        rPr = ref.getparent().find(f"{W}rPr")
        assert rPr is not None
        assert rPr.find(f"{W}rtl") is not None
        assert rPr.find(f"{W}cs") is not None
        assert rPr.getparent().index(rPr) == 0
