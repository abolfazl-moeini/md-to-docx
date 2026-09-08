import sys
from pathlib import Path
import zipfile
from xml.etree import ElementTree as ET
from PIL import Image
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from md_to_docx import convert_markdown_to_docx
from scripts.semantic_oracle import run_semantic_oracle

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def test_p0a_swapped_paragraphs_fail(tmp_path):
    md = "# سند\n\nپاراگراف نخست سند.\n\nپاراگراف دوم سند.\n"
    out = tmp_path / "valid.docx"
    convert_markdown_to_docx(content=md, output_path=out, template="purple_book", overwrite=True)
    ok, _ = run_semantic_oracle(md, out)
    assert ok

    # Corrupt by swapping the two body paragraphs using XML manipulation
    corrupt = tmp_path / "swapped.docx"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(corrupt, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                root = ET.fromstring(data)
                body = root.find(f"{W}body")
                paras = [el for el in list(body) if el.tag == f"{W}p" and el.find(f".//{W}outlineLvl") is None]
                if len(paras) >= 2:
                    p1, p2 = paras[0], paras[1]
                    idx1 = list(body).index(p1)
                    idx2 = list(body).index(p2)
                    body.remove(p1)
                    body.remove(p2)
                    body.insert(idx1, p2)
                    body.insert(idx2, p1)
                    data = ET.tostring(root, encoding="utf-8")
            zout.writestr(item, data)
    ok2, issues = run_semantic_oracle(md, corrupt)
    assert not ok2, "Swapped paragraphs should fail semantic oracle"


def test_p0a_dropped_duplicate_sentence_fails(tmp_path):
    md = "# سند\n\nجمله تکراری مهم.\n\nمتن میانی.\n\nجمله تکراری مهم.\n"
    out = tmp_path / "valid.docx"
    convert_markdown_to_docx(content=md, output_path=out, template="purple_book", overwrite=True)
    ok, _ = run_semantic_oracle(md, out)
    assert ok

    # Corrupt by removing one occurrence of the repeated paragraph
    corrupt = tmp_path / "dropped_occ.docx"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(corrupt, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                root = ET.fromstring(data)
                body = root.find(f"{W}body")
                target = next((p for p in list(body) if "جمله تکراری" in "".join(p.itertext())), None)
                if target is not None:
                    body.remove(target)
                    data = ET.tostring(root, encoding="utf-8")
            zout.writestr(item, data)
    ok2, issues = run_semantic_oracle(md, corrupt)
    assert not ok2, "Dropping one occurrence of a duplicate sentence must fail semantic oracle"


def test_p0a_swapped_code_lines_fail(tmp_path):
    md = "```python\nx = 1\ny = 2\n```\n"
    out = tmp_path / "valid.docx"
    convert_markdown_to_docx(content=md, output_path=out, template="purple_book", overwrite=True)
    ok, _ = run_semantic_oracle(md, out)
    assert ok

    # Corrupt by swapping the two paragraphs (code lines) inside the code table
    corrupt = tmp_path / "swapped_code.docx"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(corrupt, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                root = ET.fromstring(data)
                tc = root.find(f".//{W}tc")
                if tc is not None:
                    lines = [p for p in list(tc) if p.tag == f"{W}p"]
                    if len(lines) >= 2:
                        p1, p2 = lines[0], lines[1]
                        tc.remove(p1)
                        tc.remove(p2)
                        tc.insert(0, p2)
                        tc.insert(1, p1)
                        data = ET.tostring(root, encoding="utf-8")
            zout.writestr(item, data)
    ok2, issues = run_semantic_oracle(md, corrupt)
    assert not ok2, "Swapped code lines must fail semantic oracle"


def test_p0a_stripped_code_indentation_fails(tmp_path):
    md = "```python\ndef test():\n    return 42\n```\n"
    out = tmp_path / "valid.docx"
    convert_markdown_to_docx(content=md, output_path=out, template="purple_book", overwrite=True)
    ok, _ = run_semantic_oracle(md, out)
    assert ok

    # Corrupt by stripping leading spaces from the second line of code
    corrupt = tmp_path / "stripped_indent.docx"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(corrupt, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                root = ET.fromstring(data)
                for t in root.iter(f"{W}t"):
                    if t.text and t.text.startswith("    "):
                        t.text = t.text.lstrip()
                data = ET.tostring(root, encoding="utf-8")
            zout.writestr(item, data)
    ok2, issues = run_semantic_oracle(md, corrupt)
    assert not ok2, "Stripping code indentation must fail semantic oracle"


def test_p0a_body_text_moved_to_footnote_fails(tmp_path):
    md = "متن بدنه اصلی.[^1]\n\n[^1]: متن پاورقی.\n"
    out = tmp_path / "valid.docx"
    convert_markdown_to_docx(content=md, output_path=out, template="purple_book", overwrite=True)
    ok, _ = run_semantic_oracle(md, out)
    assert ok

    # Corrupt: remove body text from document.xml and put into footnotes.xml
    corrupt = tmp_path / "moved_to_fn.docx"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(corrupt, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                root = ET.fromstring(data)
                body = root.find(f"{W}body")
                for p in list(body):
                    if p.tag == f"{W}p":
                        body.remove(p)
                        break
                data = ET.tostring(root, encoding="utf-8")
            elif item.filename == "word/footnotes.xml":
                fn_root = ET.fromstring(data)
                extra_p = ET.Element(f"{W}p")
                r = ET.SubElement(extra_p, f"{W}r")
                t = ET.SubElement(r, f"{W}t")
                t.text = "متن بدنه اصلی."
                fn_root.find(f"{W}footnote").append(extra_p)
                data = ET.tostring(fn_root, encoding="utf-8")
            zout.writestr(item, data)
    ok2, issues = run_semantic_oracle(md, corrupt)
    assert not ok2, "Moving body text to footnote must fail semantic oracle"


def test_p0a_internal_link_target_changed_fails(tmp_path):
    md = "[رفتن به بخش](#sec-intro)\n\n## مقدمه {#sec-intro}\n"
    out = tmp_path / "valid.docx"
    convert_markdown_to_docx(content=md, output_path=out, template="purple_book", overwrite=True)
    ok, _ = run_semantic_oracle(md, out)
    assert ok

    corrupt = tmp_path / "bad_link.docx"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(corrupt, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                root = ET.fromstring(data)
                for h in root.iter(f"{W}hyperlink"):
                    h.set(f"{W}anchor", "completely_wrong_anchor")
                data = ET.tostring(root, encoding="utf-8")
            zout.writestr(item, data)
    ok2, issues = run_semantic_oracle(md, corrupt)
    assert not ok2, "Altering internal link destination must fail semantic oracle"


def test_p0a_image_drawing_removed_fails(tmp_path):
    img = tmp_path / "img.png"
    Image.new("RGB", (20, 20), "blue").save(img)
    md = f"متن قبل.\n\n![تست]({img.name})\n\nمتن بعد.\n"
    out = tmp_path / "valid.docx"
    convert_markdown_to_docx(content=md, base_dir=tmp_path, output_path=out, template="purple_book", overwrite=True)
    ok, _ = run_semantic_oracle(md, out)
    assert ok

    corrupt = tmp_path / "no_drawing.docx"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(corrupt, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                import re
                data = re.sub(rb"<w:drawing>.*?</w:drawing>", b"", data, flags=re.DOTALL)
            zout.writestr(item, data)
    ok2, issues = run_semantic_oracle(md, corrupt)
    assert not ok2, "Removing image drawing must fail semantic oracle"


def test_p0a_math_removed_fails(tmp_path):
    md = "فرمول ساده: $E = mc^2$ در متن.\n"
    out = tmp_path / "valid.docx"
    convert_markdown_to_docx(content=md, output_path=out, template="purple_book", overwrite=True)
    ok, _ = run_semantic_oracle(md, out)
    assert ok

    corrupt = tmp_path / "no_math.docx"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(corrupt, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                import re
                data = re.sub(rb"<m:oMath>.*?</m:oMath>", b"", data, flags=re.DOTALL)
            zout.writestr(item, data)
    ok2, issues = run_semantic_oracle(md, corrupt)
    assert not ok2, "Removing math OMML must fail semantic oracle"


def test_p0a_external_link_target_changed_fails(tmp_path):
    md = "[وبگاه](https://example.org/valid)\n"
    out = tmp_path / "valid.docx"
    convert_markdown_to_docx(content=md, output_path=out, template="purple_book", overwrite=True)
    ok, _ = run_semantic_oracle(md, out)
    assert ok

    corrupt = tmp_path / "bad_ext_link.docx"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(corrupt, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/_rels/document.xml.rels":
                data = data.replace(b"https://example.org/valid", b"https://example.org/malicious")
            zout.writestr(item, data)
    ok2, issues = run_semantic_oracle(md, corrupt)
    assert not ok2, "Changing external link target must fail semantic oracle"


def test_p0a_malformed_ast_fails():
    from scripts.semantic_oracle import expected_from_markdown
    with pytest.raises(Exception):
        expected_from_markdown(12345)  # non-string input


def test_p0a_table_cell_image_removed_fails(tmp_path):
    img = tmp_path / "cell.png"
    Image.new("RGB", (24, 16), "green").save(img)
    md = (
        "| ستون |\n| --- |\n"
        f"| ![سلول]({img.name}) |\n"
    )
    out = tmp_path / "cell_img.docx"
    convert_markdown_to_docx(
        content=md, base_dir=tmp_path, output_path=out, template="purple_book", overwrite=True,
    )
    ok, issues = run_semantic_oracle(md, out, base_dir=tmp_path)
    assert ok, issues

    corrupt = tmp_path / "cell_img_gone.docx"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(corrupt, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                import re
                data = re.sub(rb"<w:drawing>.*?</w:drawing>", b"", data, flags=re.DOTALL)
            zout.writestr(item, data)
    ok2, issues2 = run_semantic_oracle(md, corrupt, base_dir=tmp_path)
    assert not ok2, "Removing a table-cell image must fail the semantic oracle"
    assert any("image" in i.lower() for i in issues2)


def test_p0a_swapped_image_bytes_fail(tmp_path):
    red = tmp_path / "red.png"
    blue = tmp_path / "blue.png"
    Image.new("RGB", (20, 20), "red").save(red)
    Image.new("RGB", (20, 20), "blue").save(blue)
    md = f"![قرمز]({red.name})\n\n![آبی]({blue.name})\n"
    out = tmp_path / "two_img.docx"
    convert_markdown_to_docx(
        content=md, base_dir=tmp_path, output_path=out, template="purple_book", overwrite=True,
    )
    ok, issues = run_semantic_oracle(md, out, base_dir=tmp_path)
    assert ok, issues

    corrupt = tmp_path / "swapped_img.docx"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(corrupt, "w") as zout:
        names = zin.namelist()
        media = sorted(n for n in names if n.startswith("word/media/") and n.endswith(".png"))
        assert len(media) >= 2
        blobs = {n: zin.read(n) for n in names}
        blobs[media[0]], blobs[media[1]] = blobs[media[1]], blobs[media[0]]
        for item in zin.infolist():
            zout.writestr(item, blobs[item.filename])
    ok2, issues2 = run_semantic_oracle(md, corrupt, base_dir=tmp_path)
    assert not ok2, "Swapping two embedded images must fail occurrence-aware hash match"
    assert any("image" in i.lower() or "hash" in i.lower() for i in issues2)


def test_p0a_heading_level_mismatch_fails(tmp_path):
    md = "## تیتر سطح دو\n\nمتن.\n"
    out = tmp_path / "h2.docx"
    convert_markdown_to_docx(content=md, output_path=out, template="persian_book", overwrite=True)
    ok, _ = run_semantic_oracle(md, out)
    assert ok

    corrupt = tmp_path / "h2_as_h1.docx"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(corrupt, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                root = ET.fromstring(data)
                olvl = root.find(f".//{W}outlineLvl")
                assert olvl is not None
                olvl.set(f"{W}val", "0")
                data = ET.tostring(root, encoding="utf-8")
            zout.writestr(item, data)
    ok2, issues2 = run_semantic_oracle(md, corrupt)
    assert not ok2
    assert any("level" in i.lower() or "heading" in i.lower() for i in issues2)
