"""End-to-end regressions reproduced during the final-closure code review."""

from copy import deepcopy
import zipfile

from docx.oxml.ns import qn
from lxml import etree
from PIL import Image
import pytest

from md_to_docx import Template, convert_markdown_to_docx

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"


@pytest.mark.parametrize("badge,extract", [(True, True), (True, False), (False, True), (False, False)])
@pytest.mark.parametrize("location", ["callout", "table", "footnote"])
def test_nested_heading_keeps_number_without_a_badge_cell(tmp_path, badge, extract, location):
    base = Template.load("purple_book")
    config = deepcopy(base.raw_config)
    config["headings"].update(badge=badge, extract_number=extract)
    template = Template(config, base.dir_path)
    heading = "## ۱.۲ عنوان **غنی** {#nested}"
    if location == "callout":
        markdown = f"::: note\n\n{heading}\n\nبدنه.\n\n:::\n"
    elif location == "footnote":
        markdown = f"بدنه.[^n]\n\n[^n]: مقدمه.\n\n    {heading}\n"
    else:
        border = "+" + "-" * 80 + "+"
        row = "| " + heading.ljust(78) + " |"
        markdown = f"{border}\n{row}\n{border}\n"
    out = tmp_path / "nested.docx"
    convert_markdown_to_docx(content=markdown, output_path=out, template=template, overwrite=False)
    part = "word/footnotes.xml" if location == "footnote" else "word/document.xml"
    with zipfile.ZipFile(out) as archive:
        root = etree.fromstring(archive.read(part))
    headings = [p for p in root.iter(f"{W}p") if p.find(f"{W}pPr/{W}outlineLvl") is not None]
    assert len(headings) == 1
    paragraph = headings[0]
    assert "".join(paragraph.itertext()) == "۱.۲ عنوان غنی"
    assert paragraph.find(f".//{W}bookmarkStart") is not None
    strong_run = next(r for r in paragraph.findall(f"{W}r") if "غنی" in "".join(r.itertext()))
    assert strong_run.find(f"{W}rPr/{W}bCs").get(qn("w:val"), "1") == "1"


@pytest.mark.parametrize("in_footnote", [False, True])
def test_linked_image_relationship_belongs_to_its_story(tmp_path, in_footnote):
    image_path = tmp_path / "linked.png"
    Image.new("RGB", (32, 24), "red").save(image_path)
    linked_image = "[![تصویر](linked.png)](https://example.org/image)"
    markdown = f"بدنه.[^n]\n\n[^n]: {linked_image}\n" if in_footnote else f"متن {linked_image}\n"
    out = tmp_path / "linked.docx"
    convert_markdown_to_docx(content=markdown, base_dir=tmp_path, output_path=out, overwrite=False)
    story = "footnotes.xml" if in_footnote else "document.xml"
    with zipfile.ZipFile(out) as archive:
        root = etree.fromstring(archive.read(f"word/{story}"))
        rels = etree.fromstring(archive.read(f"word/_rels/{story}.rels"))
        by_id = {rel.get("Id"): rel for rel in rels}
        hyperlink = root.find(f".//{W}hyperlink")
        link_rel = by_id[hyperlink.get(f"{R}id")]
        assert link_rel.get("Target") == "https://example.org/image"
        assert link_rel.get("TargetMode") == "External"
        blip = hyperlink.find(f".//{A}blip")
        image_id = blip.get(f"{R}embed")
        assert image_id in by_id, f"{story} drawing references undefined relationship {image_id}"
        image_rel = by_id[image_id]
        assert image_rel.get("Type").endswith("/image")
        assert archive.read("word/" + image_rel.get("Target")) == image_path.read_bytes()


@pytest.mark.parametrize("pixels,extent", [
    ((2000, 1), ""),
    ((2000, 10), "{width=0.5in}"),
    ((2000, 10), "{height=0.01in}"),
    ((1, 2000), "{height=0.5in}"),
    ((2000, 10), ""),
])
def test_embedded_image_preserves_extreme_ratio_and_requested_extent(tmp_path, pixels, extent):
    image_path = tmp_path / "thin.png"
    Image.new("RGB", pixels, "red").save(image_path)
    out = tmp_path / "thin.docx"
    convert_markdown_to_docx(content=f"![باریک](thin.png){extent}\n", base_dir=tmp_path,
                             output_path=out, overwrite=False)
    with zipfile.ZipFile(out) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))
    drawing_extent = root.find(f".//{WP}extent")
    width = int(drawing_extent.get("cx"))
    height = int(drawing_extent.get("cy"))
    assert width > 0 and height > 0
    # DOCX extents are whole EMUs; each dimension can lose less than one EMU.
    assert abs(width * pixels[1] - height * pixels[0]) < sum(pixels)
    assert width / height == pytest.approx(pixels[0] / pixels[1], rel=0.01)
    if extent == "{width=0.5in}":
        assert width / 914400 == pytest.approx(0.5, abs=1 / 914400)
    elif extent == "{height=0.01in}":
        assert height / 914400 == pytest.approx(0.01, abs=1 / 914400)
    elif extent == "{height=0.5in}":
        assert height / 914400 == pytest.approx(0.5, abs=1 / 914400)
