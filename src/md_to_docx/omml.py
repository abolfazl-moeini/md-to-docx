"""Minimal TeX-to-OMML converter for common technical Markdown math."""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

ET.register_namespace("m", M_NS)
ET.register_namespace("w", W_NS)


def _m(tag: str, **attrs) -> ET.Element:
    el = ET.Element(f"{{{M_NS}}}{tag}")
    for k, v in attrs.items():
        el.set(f"{{{M_NS}}}{k}" if not k.startswith("{") else k, v)
    return el


def _run(text: str, italic: bool = True) -> ET.Element:
    r = _m("r")
    rpr = _m("rPr")
    sty = _m("sty")
    sty.set(f"{{{M_NS}}}val", "p" if not italic else "i")
    rpr.append(sty)
    r.append(rpr)
    t = _m("t")
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = text
    r.append(t)
    return r


def _tex_to_element(tex: str) -> ET.Element:
    s = tex.strip()
    frac = re.fullmatch(r"\\frac\s*\{(.+)\}\s*\{(.+)\}", s, re.DOTALL)
    if frac:
        f = _m("f")
        num = _m("num")
        den = _m("den")
        num.append(_tex_to_element(frac.group(1)))
        den.append(_tex_to_element(frac.group(2)))
        f.append(num)
        f.append(den)
        return f

    summed = re.fullmatch(r"\\sum(?:_\{(.+?)\})?(?:\^\{(.+?)\})?\s*(.*)", s, re.DOTALL)
    if summed and s.startswith("\\sum"):
        nary = _m("nary")
        narypr = _m("naryPr")
        chr_el = _m("chr")
        chr_el.set(f"{{{M_NS}}}val", "∑")
        narypr.append(chr_el)
        nary.append(narypr)
        sub = _m("sub")
        sub.append(_tex_to_element(summed.group(1) or ""))
        sup = _m("sup")
        sup.append(_tex_to_element(summed.group(2) or ""))
        e = _m("e")
        e.append(_tex_to_element(summed.group(3) or ""))
        nary.append(sub)
        nary.append(sup)
        nary.append(e)
        return nary

    if not s:
        return _run("")

    # Split on ^ and _ for simple super/sub while keeping other text as a run sequence in an e wrapper
    parts = re.split(r"(\^[^{]\S*|\^\{[^}]+\}|_{[^{]\S*}|_\{[^}]+\})", s)
    if len(parts) == 1:
        return _run(_unescape_tex(s), italic=any(c.isalpha() for c in s))

    ssub = _m("sSubSup") if any(p.startswith("^") for p in parts) and any(p.startswith("_") for p in parts) else None
    # Sequential: wrap each piece
    container = _m("e") if False else None
    # Build a linear oMath of runs and sSup/sSub
    wrapper = _m("e")
    i = 0
    tokens = parts
    buf = []
    while i < len(tokens):
        tok = tokens[i]
        if tok.startswith("^"):
            inner = tok[2:-1] if tok.startswith("^{") else tok[1:]
            node = _m("sSup")
            e = _m("e")
            if buf:
                e.append(_run(_unescape_tex("".join(buf))))
                buf = []
            else:
                e.append(_run(""))
            node.append(e)
            sup = _m("sup")
            sup.append(_tex_to_element(inner))
            node.append(sup)
            wrapper.append(node)
        elif tok.startswith("_"):
            inner = tok[2:-1] if tok.startswith("_{") else tok[1:]
            node = _m("sSub")
            e = _m("e")
            if buf:
                e.append(_run(_unescape_tex("".join(buf))))
                buf = []
            else:
                e.append(_run(""))
            node.append(e)
            sub = _m("sub")
            sub.append(_tex_to_element(inner))
            node.append(sub)
            wrapper.append(node)
        else:
            buf.append(tok)
        i += 1
    if buf:
        wrapper.append(_run(_unescape_tex("".join(buf))))
    if len(wrapper) == 1:
        return wrapper[0]
    return wrapper


def _unescape_tex(s: str) -> str:
    return (
        s.replace("\\,", " ")
        .replace("\\;", " ")
        .replace("\\ ", " ")
        .replace("\\times", "×")
        .replace("\\cdot", "·")
        .replace("\\infty", "∞")
        .replace("\\alpha", "α")
        .replace("\\beta", "β")
        .replace("\\pi", "π")
        .replace("\\sum", "∑")
        .replace("\\frac", "")
        .strip()
    )


def tex_to_omml_xml(tex: str, display: bool = False) -> str:
    """Return an XML string for m:oMath or m:oMathPara."""
    inner = _tex_to_element(tex)
    if display:
        para = _m("oMathPara")
        math = _m("oMath")
        math.append(inner)
        para.append(math)
        return ET.tostring(para, encoding="unicode")
    math = _m("oMath")
    math.append(inner)
    return ET.tostring(math, encoding="unicode")
