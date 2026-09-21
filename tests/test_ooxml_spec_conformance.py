"""Spec-driven OOXML conformance tests for RTL / Persian output.

These tests assert *structural* properties of the emitted package rather than the content of
one particular fixture, so they survive changes to the sample Markdown and to the templates.
Each test names the clause it enforces.

They exist to make a whole class of defect impossible to reintroduce silently: an attribute
or enum value that is not in the WordprocessingML schema. Such a value is invisible in local
verification because LibreOffice is lenient and accepts things Word never writes — the
``w:ind/@w:start`` defect was exactly this shape. It rendered identically to ``@w:left`` in
LibreOffice (verified to 0.01 pt) while appearing in 0 of 3350 real ``.docx`` files on this
machine, so every local check passed and only Word would have disagreed.

Scope note — three clauses from the draft plan (``implementation_plan.md``) are deliberately
*not* re-implemented here because the suite already covers them:

* ``SPEC-01`` (``w:jc`` values are valid ``ST_Jc``) →
  ``test_persian_layout_quality.py::test_docx_never_emits_word_invalid_justification``
* ``SPEC-06`` partially (RTL tables carry ``bidiVisual``) →
  ``test_rtl_quality.py`` R-07 and ``test_renderer.py``
* ``SPEC-10`` partially (``w:szCs`` present) → ``test_renderer.py``, ``test_final_closure.py``

and one is corrected: the plan's ``SPEC-07``/``SPEC-12`` required ``w:ind/@w:start``. That
attribute is not a member of ``CT_Ind``; see ``SPEC-07`` below, which now forbids it.
"""

from __future__ import annotations

import re
import zipfile

import pytest
from lxml import etree

from md_to_docx.oxml import CT_IND_ATTRIBUTES
from md_to_docx.pipeline import convert_markdown_to_docx

pytestmark = pytest.mark.spec

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

TEMPLATES = ["purple_book", "persian_book", "persian_compact", "persian_report"]

#: Attribute set of ``CT_Fonts`` (the ``w:rFonts`` element). Anything outside this set is not
#: part of the schema and would be ignored or trigger a repair prompt in Word.
CT_FONTS_ATTRIBUTES = frozenset({
    "ascii", "hAnsi", "eastAsia", "cs",
    "asciiTheme", "hAnsiTheme", "eastAsiaTheme", "csTheme", "hint",
})

#: Fonts that ship no Arabic glyphs. A Complex Script run resolved to one of these renders as
#: tofu boxes. This is a heuristic denylist, not a schema rule — it exists to catch a
#: template whose ``fonts.body`` was pointed at a Latin-only family.
LATIN_ONLY_FONTS = frozenset({
    "Calibri", "Arial", "Times New Roman", "Helvetica", "Courier New",
    "DejaVu Sans", "DejaVu Serif", "Liberation Serif", "Liberation Sans",
    "Linux Libertine G", "Cambria", "Georgia", "Verdana", "Segoe UI",
})

#: Arabic script blocks: Arabic, Arabic Supplement, Arabic Presentation Forms A and B.
ARABIC_SCRIPT = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")

RTL_FIXTURE_MD = """---
lang: fa-IR
dir: rtl
---

# تیتر سطح یک

پاراگراف بدنه فارسی برای آزمون انطباق با schema.

## تیتر سطح دو

* آیتم فهرست نقطه‌ای
* آیتم دوم فهرست

1. آیتم فهرست شماره‌دار
2. آیتم دوم شماره‌دار

| سرستون الف | سرستون ب |
|---|---|
| سلول یک | سلول دو |

کد درون‌خطی `pip install md-to-docx` در متن.

> نقل‌قول فارسی برای آزمون.
"""


@pytest.fixture(scope="module", params=TEMPLATES)
def package(request, tmp_path_factory):
    """Convert the shared RTL fixture once per template and return its parsed XML parts."""
    template = request.param
    out = tmp_path_factory.mktemp("spec") / f"{template}.docx"
    convert_markdown_to_docx(
        content=RTL_FIXTURE_MD, output_path=out, template=template, overwrite=True
    )
    with zipfile.ZipFile(out) as z:
        parts = {name: z.read(name) for name in z.namelist()}
    return {
        "template": template,
        "parts": parts,
        "document": etree.fromstring(parts["word/document.xml"]),
        "styles": etree.fromstring(parts["word/styles.xml"]),
    }


def _attr_names(element) -> set[str]:
    return {etree.QName(k).localname for k in element.attrib}


def _arabic_runs(document):
    """Yield runs whose text contains Arabic-script characters.

    Filtering on the *text* is what keeps this honest: a Latin-only inline-code run
    legitimately carries the code font on ``@w:cs`` and must not be flagged.
    """
    for run in document.iter(W + "r"):
        text = "".join(t.text or "" for t in run.iter(W + "t"))
        if ARABIC_SCRIPT.search(text):
            yield run, text


def _paragraph_is_bidi(p) -> bool:
    pPr = p.find(W + "pPr")
    if pPr is None:
        return False
    bidi = pPr.find(W + "bidi")
    if bidi is None:
        return False
    return bidi.get(W + "val", "1") != "0"


# --------------------------------------------------------------------------------------
# SPEC-02 · bidi paragraphs must not carry a physical alignment
# --------------------------------------------------------------------------------------
# In a `w:bidi` paragraph the physical keywords `left`/`right` are resolved against the
# writing direction, and engines disagree about the result: LibreOffice reads `right` as the
# logical END (= physically left) and therefore left-aligns the text. `start`/`end` are
# unambiguous in every engine. (Note: the draft plan cited this as "MS-OE376 §2.3.1.13";
# §2.3.1.13 is the ECMA-376 Part 4 clause number for `jc`, to which MS-OE376 only adds notes.)
def test_spec02_bidi_paragraphs_never_use_physical_alignment(package):
    offenders = []
    for p in package["document"].iter(W + "p"):
        if not _paragraph_is_bidi(p):
            continue
        jc = p.find(f"{W}pPr/{W}jc")
        if jc is not None and jc.get(W + "val") in {"left", "right"}:
            text = "".join(t.text or "" for t in p.iter(W + "t"))[:40]
            offenders.append((jc.get(W + "val"), text))
    assert not offenders, (
        f"[{package['template']}] bidi paragraphs use physical alignment: {offenders}"
    )


# --------------------------------------------------------------------------------------
# SPEC-03 · w:rtl is a run property, never a paragraph property
# --------------------------------------------------------------------------------------
def test_spec03_rtl_is_a_run_property_only(package):
    for pPr in package["document"].iter(W + "pPr"):
        assert pPr.find(W + "rtl") is None, (
            f"[{package['template']}] w:rtl found inside w:pPr; it belongs in w:rPr"
        )


# --------------------------------------------------------------------------------------
# SPEC-04 · Arabic runs declare a Complex Script font
# --------------------------------------------------------------------------------------
def test_spec04_arabic_runs_declare_a_complex_script_font(package):
    missing = []
    for run, text in _arabic_runs(package["document"]):
        rFonts = run.find(f"{W}rPr/{W}rFonts")
        if rFonts is None or not rFonts.get(W + "cs"):
            missing.append(text[:30])
    assert not missing, (
        f"[{package['template']}] Arabic runs without w:rFonts/@w:cs: {missing[:5]}"
    )


# --------------------------------------------------------------------------------------
# SPEC-05 · the Complex Script font is not a Latin-only family
# --------------------------------------------------------------------------------------
def test_spec05_complex_script_font_is_not_latin_only(package):
    bad = []
    for run, text in _arabic_runs(package["document"]):
        rFonts = run.find(f"{W}rPr/{W}rFonts")
        cs = rFonts.get(W + "cs") if rFonts is not None else None
        if cs in LATIN_ONLY_FONTS:
            bad.append((cs, text[:30]))
    assert not bad, (
        f"[{package['template']}] Arabic runs resolved to a Latin-only CS font: {bad[:5]}"
    )


# --------------------------------------------------------------------------------------
# SPEC-06 · RTL tables are mirrored with w:bidiVisual
# --------------------------------------------------------------------------------------
def test_spec06_rtl_tables_are_bidi_visual(package):
    tables = list(package["document"].iter(W + "tbl"))
    assert tables, f"[{package['template']}] fixture produced no table"
    for tbl in tables:
        assert tbl.find(f"{W}tblPr/{W}bidiVisual") is not None, (
            f"[{package['template']}] RTL table lacks w:tblPr/w:bidiVisual"
        )


# --------------------------------------------------------------------------------------
# SPEC-07 · w:ind carries only CT_Ind attributes
# --------------------------------------------------------------------------------------
# This is the clause that forbids `w:ind/@w:start`. CT_Ind declares exactly:
#   left, leftChars, right, rightChars, hanging, hangingChars, firstLine, firstLineChars
# (`start`/`end` are `ST_Jc` *values* on `w:jc`; they are not `w:ind` attributes.)
def test_spec07_ind_uses_only_ct_ind_attributes(package):
    for part in ("document", "styles"):
        for ind in package[part].iter(W + "ind"):
            illegal = _attr_names(ind) - CT_IND_ATTRIBUTES
            assert not illegal, (
                f"[{package['template']}] {part}.xml has w:ind attributes outside CT_Ind: "
                f"{sorted(illegal)}; allowed: {sorted(CT_IND_ATTRIBUTES)}"
            )


# --------------------------------------------------------------------------------------
# SPEC-07b · w:rFonts carries only CT_Fonts attributes
# --------------------------------------------------------------------------------------
def test_spec07b_rfonts_uses_only_ct_fonts_attributes(package):
    for rFonts in package["document"].iter(W + "rFonts"):
        illegal = _attr_names(rFonts) - CT_FONTS_ATTRIBUTES
        assert not illegal, (
            f"[{package['template']}] w:rFonts attributes outside CT_Fonts: {sorted(illegal)}"
        )


# --------------------------------------------------------------------------------------
# SPEC-12 · a hanging indent is paired with the logical START indent
# --------------------------------------------------------------------------------------
# `@w:hanging` only pulls the first line back; it needs `@w:left` to define where "back" is.
# Without it the marker and the wrapped text have no common reference edge.
def test_spec12_hanging_indent_is_paired_with_logical_start(package):
    checked = 0
    for ind in package["document"].iter(W + "ind"):
        if ind.get(W + "hanging") is None:
            continue
        checked += 1
        assert ind.get(W + "left") is not None, (
            f"[{package['template']}] w:ind/@w:hanging without @w:left"
        )
    assert checked, f"[{package['template']}] fixture produced no hanging indent to check"


# --------------------------------------------------------------------------------------
# SPEC-08 · a bidi language is declared somewhere in the style hierarchy
# --------------------------------------------------------------------------------------
def test_spec08_bidi_language_is_declared(package):
    found = [
        lang.get(W + "bidi")
        for part in ("styles", "document")
        for lang in package[part].iter(W + "lang")
        if lang.get(W + "bidi")
    ]
    assert found, f"[{package['template']}] no w:lang/@w:bidi anywhere in styles or document"


# --------------------------------------------------------------------------------------
# SPEC-09 · the Normal style is RTL and start-aligned
# --------------------------------------------------------------------------------------
def test_spec09_normal_style_is_rtl_and_start_aligned(package):
    normal = None
    for style in package["styles"].iter(W + "style"):
        if style.get(W + "styleId") == "Normal":
            normal = style
            break
    assert normal is not None, f"[{package['template']}] styles.xml has no Normal style"
    assert normal.find(f".//{W}bidi") is not None, (
        f"[{package['template']}] Normal style is not bidi"
    )
    jc = normal.find(f".//{W}jc")
    assert jc is not None, f"[{package['template']}] Normal style has no explicit w:jc"
    assert jc.get(W + "val") == "start", (
        f"[{package['template']}] Normal style w:jc is {jc.get(W + 'val')!r}, expected 'start'"
    )


# --------------------------------------------------------------------------------------
# SPEC-10 · Arabic runs declare w:szCs
# --------------------------------------------------------------------------------------
def test_spec10_arabic_runs_declare_szCs(package):
    missing = []
    for run, text in _arabic_runs(package["document"]):
        if run.find(f"{W}rPr/{W}szCs") is None:
            missing.append(text[:30])
    assert not missing, f"[{package['template']}] Arabic runs without w:szCs: {missing[:5]}"


# --------------------------------------------------------------------------------------
# SPEC-11 · every XML part in the package is well formed
# --------------------------------------------------------------------------------------
def test_spec11_every_xml_part_is_well_formed(package):
    xml_parts = [n for n in package["parts"] if n.endswith(".xml")]
    assert xml_parts, f"[{package['template']}] package contains no XML parts"
    for name in xml_parts:
        try:
            etree.fromstring(package["parts"][name])
        except etree.XMLSyntaxError as exc:  # pragma: no cover - failure path
            pytest.fail(f"[{package['template']}] {name} is not well formed: {exc}")
