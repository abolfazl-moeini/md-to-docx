"""Create real Word footnotes (word/footnotes.xml) rather than inline superscript text."""

from __future__ import annotations

from docx.document import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.opc.packuri import PackURI
from docx.opc.part import Part
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsmap, qn
from docx.text.paragraph import Paragraph

W_NS = nsmap["w"]
FOOTNOTES_URI = "/word/footnotes.xml"
FOOTNOTES_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"


def _nsmap() -> dict:
    return {"w": W_NS}


def _ensure_footnotes_part(doc: Document) -> Part:
    rels = doc.part.rels
    for rel in rels.values():
        if rel.reltype == RT.FOOTNOTES:
            return rel.target_part

    xml = (
        f'<w:footnotes xmlns:w="{W_NS}">'
        '<w:footnote w:type="separator" w:id="-1">'
        "<w:p><w:r><w:separator/></w:r></w:p>"
        "</w:footnote>"
        '<w:footnote w:type="continuationSeparator" w:id="0">'
        "<w:p><w:r><w:continuationSeparator/></w:r></w:p>"
        "</w:footnote>"
        "</w:footnotes>"
    )
    part = Part(
        PackURI(FOOTNOTES_URI),
        FOOTNOTES_CT,
        xml.encode("utf-8"),
        doc.part.package,
    )
    doc.part.relate_to(part, RT.FOOTNOTES)
    # Register content type
    try:
        ct = doc.part.package.content_types
        ct._overrides[FOOTNOTES_URI] = FOOTNOTES_CT
    except Exception:
        pass
    return part


def next_footnote_id(part: Part) -> int:
    root = part._element if hasattr(part, "_element") else parse_xml(part.blob)
    ids = [int(el.get(qn("w:id"))) for el in root.findall(qn("w:footnote")) if el.get(qn("w:id"))]
    return max(ids) + 1 if ids else 1


def add_footnote_reference(paragraph: Paragraph, footnote_id: int) -> None:
    r = paragraph.add_run()
    rPr = r._r.get_or_add_rPr()
    vert = OxmlElement("w:vertAlign")
    vert.set(qn("w:val"), "superscript")
    rPr.append(vert)
    ref = OxmlElement("w:footnoteReference")
    ref.set(qn("w:id"), str(footnote_id))
    r._r.append(ref)


def add_footnote_body(doc: Document, footnote_id: int):
    """Append an empty footnote paragraph and return (paragraph, root, part) for flushing."""
    part = _ensure_footnotes_part(doc)
    root = parse_xml(part.blob)
    fn = OxmlElement("w:footnote")
    fn.set(qn("w:id"), str(footnote_id))
    p = OxmlElement("w:p")
    r_mark = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    vert = OxmlElement("w:vertAlign")
    vert.set(qn("w:val"), "superscript")
    rPr.append(vert)
    r_mark.append(rPr)
    r_mark.append(OxmlElement("w:footnoteRef"))
    p.append(r_mark)
    fn.append(p)
    root.append(fn)
    part._blob = ET_to_bytes(root)
    return Paragraph(p, doc._body), root, part


def ET_to_bytes(root) -> bytes:
    from lxml import etree
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def list_footnote_ids(doc: Document) -> list[int]:
    try:
        part = None
        for rel in doc.part.rels.values():
            if rel.reltype == RT.FOOTNOTES:
                part = rel.target_part
                break
        if part is None:
            return []
        root = parse_xml(part.blob)
        out = []
        for el in root.findall(qn("w:footnote")):
            fid = el.get(qn("w:id"))
            if fid and int(fid) > 0:
                out.append(int(fid))
        return out
    except Exception:
        return []
