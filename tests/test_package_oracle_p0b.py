import sys
from pathlib import Path
import zipfile
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from md_to_docx import convert_markdown_to_docx
from scripts.package_oracle import run_package_oracle


def test_p0b_missing_footnote_rid_fails(tmp_path):
    md = "متن همراه با پاورقی.[^1]\n\n[^1]: متن پاورقی.\n"
    out = tmp_path / "valid.docx"
    convert_markdown_to_docx(content=md, output_path=out, template="purple_book", overwrite=True)
    ok, issues = run_package_oracle(out)
    assert ok, f"Expected valid docx, got: {issues}"

    # Corrupt footnotes.xml by adding an undefined r:id reference
    corrupt = tmp_path / "bad_fn_rid.docx"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(corrupt, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/footnotes.xml":
                data = data.replace(b"<w:p>", b'<w:p r:id="rIdUndefinedInFn">', 1)
            zout.writestr(item, data)
    ok2, issues2 = run_package_oracle(corrupt)
    assert not ok2, "Undefined rId in footnotes.xml must fail package oracle"


def test_p0b_wrong_document_content_type_fails(tmp_path):
    md = "متن سند تستی.\n"
    out = tmp_path / "valid.docx"
    convert_markdown_to_docx(content=md, output_path=out, template="purple_book", overwrite=True)
    ok, issues = run_package_oracle(out)
    assert ok, f"Expected valid docx, got: {issues}"

    # Corrupt [Content_Types].xml by setting document.xml to text/plain
    corrupt = tmp_path / "bad_ct.docx"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(corrupt, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml":
                data = data.replace(
                    b'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"',
                    b'ContentType="text/plain"',
                )
            zout.writestr(item, data)
    ok2, issues2 = run_package_oracle(corrupt)
    assert not ok2, "Wrong ContentType for word/document.xml must fail package oracle"


def test_p0b_nonexistent_relationship_target_fails(tmp_path):
    md = "متن سند.\n"
    out = tmp_path / "valid.docx"
    convert_markdown_to_docx(content=md, output_path=out, template="purple_book", overwrite=True)
    ok, issues = run_package_oracle(out)
    assert ok, f"Expected valid docx, got: {issues}"

    # Add a dangling relationship pointing to nonexistent part
    corrupt = tmp_path / "dangling_rel.docx"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(corrupt, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/_rels/document.xml.rels":
                data = data.replace(
                    b"</Relationships>",
                    b'<Relationship Id="rIdDangling" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/nonexistent.png"/></Relationships>',
                )
            zout.writestr(item, data)
    ok2, issues2 = run_package_oracle(corrupt)
    assert not ok2, "Dangling relationship target must fail package oracle"


def test_p0b_part_without_content_type_fails(tmp_path):
    md = "متن سند.\n"
    out = tmp_path / "valid.docx"
    convert_markdown_to_docx(content=md, output_path=out, template="purple_book", overwrite=True)

    # Add a custom part that has neither Default nor Override in [Content_Types].xml
    corrupt = tmp_path / "orphan_part.docx"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(corrupt, "w") as zout:
        for item in zin.infolist():
            zout.writestr(item, zin.read(item.filename))
        zout.writestr("custom/extra.xyz", b"binary payload")
    ok2, issues2 = run_package_oracle(corrupt)
    assert not ok2, "Part without ContentType must fail package oracle"
