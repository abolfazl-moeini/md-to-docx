"""TeX-to-OMML converter utilizing Pandoc for accurate OOXML math rendering."""

from __future__ import annotations

import io
import json
import shutil
import subprocess
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET
import zipfile

from md_to_docx.mermaid import ConvertError

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

ET.register_namespace("m", M_NS)
ET.register_namespace("w", W_NS)

_CACHE: Dict[Tuple[str, bool], str] = {}


def _run_pandoc_json_to_docx(pandoc_bin: str, payload: bytes) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            [pandoc_bin, "-f", "json", "-t", "docx", "-o", "-"],
            input=payload,
            capture_output=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired as e:
        raise ConvertError("Pandoc math conversion timed out.") from e


def batch_convert_math(items: List[Tuple[str, bool]]) -> Dict[Tuple[str, bool], str]:
    """Convert a batch of (tex, display) pairs to OMML XML strings using Pandoc."""
    global _CACHE
    missing = [item for item in dict.fromkeys(items) if item not in _CACHE]
    if not missing:
        return {item: _CACHE[item] for item in items if item in _CACHE}

    pandoc_bin = shutil.which("pandoc")
    if not pandoc_bin:
        raise ConvertError("Pandoc executable not found in PATH for OMML math conversion.")

    blocks = []
    for tex, display in missing:
        kind = "DisplayMath" if display else "InlineMath"
        blocks.append({
            "t": "Para",
            "c": [{"t": "Math", "c": [{"t": kind}, tex]}],
        })

    proc = None
    # The AST reader accepts both 1.22.x and 1.23.x (Pandoc 2.11-3.x). Try the
    # current version first, then fall back for older Pandoc installs.
    for api_version in ([1, 23, 1], [1, 22, 2]):
        ast = {
            "pandoc-api-version": api_version,
            "meta": {},
            "blocks": blocks,
        }
        proc = _run_pandoc_json_to_docx(pandoc_bin, json.dumps(ast).encode("utf-8"))
        if proc.returncode == 0:
            break
        err_text = proc.stderr.decode("utf-8", errors="replace")
        if "pandoc-api-version" in err_text and api_version != [1, 22, 2]:
            continue
        break

    assert proc is not None
    if proc.returncode != 0:
        err_msg = proc.stderr.decode("utf-8", errors="replace").strip()
        raise ConvertError(f"Pandoc math conversion failed: {err_msg}")

    with zipfile.ZipFile(io.BytesIO(proc.stdout)) as z:
        doc_xml = z.read("word/document.xml")
        root = ET.fromstring(doc_xml)
        paras = root.findall(f".//{{{W_NS}}}p")

        for i, (tex, display) in enumerate(missing):
            if i < len(paras):
                p = paras[i]
                target_tag = f"{{{M_NS}}}oMathPara" if display else f"{{{M_NS}}}oMath"
                elem = p.find(f".//{target_tag}")
                if elem is None and display:
                    elem = p.find(f".//{{{M_NS}}}oMath")
                if elem is not None:
                    _CACHE[(tex, display)] = ET.tostring(elem, encoding="unicode")
                    continue
            err_msg = proc.stderr.decode("utf-8", errors="replace").strip()
            raise ConvertError(f"Invalid TeX math expression '{tex}': {err_msg or 'Pandoc failed to produce valid OMML'}")

    return {item: _CACHE[item] for item in items if item in _CACHE}


def tex_to_omml_xml(tex: str, display: bool = False) -> str:
    """Return an XML string for m:oMath or m:oMathPara."""
    key = (tex, display)
    if key in _CACHE:
        return _CACHE[key]
    results = batch_convert_math([key])
    return results[key]
