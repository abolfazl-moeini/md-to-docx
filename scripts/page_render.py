"""DOCX → PDF/PNG page renderer (F13 / P0-D). LibreOffice path is configurable; never hardcode a user cache."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Tuple


def find_soffice() -> Optional[str]:
    env = os.environ.get("MD2DOCX_SOFFICE")
    if env and Path(env).is_file():
        return env
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found
    mac = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    if mac.is_file():
        return str(mac)
    return None


def _is_valid_pdf(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 32:
        return False
    try:
        with open(path, "rb") as f:
            header = f.read(1024)
            if not header.startswith(b"%PDF-"):
                return False
            f.seek(max(0, path.stat().st_size - 1024))
            footer = f.read(1024)
            if b"%%EOF" not in footer and b"startxref" not in footer and b"xref" not in footer:
                return False
        return True
    except OSError:
        return False


def _is_valid_png(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 16:
        return False
    try:
        with open(path, "rb") as f:
            return f.read(8) == b"\x89PNG\r\n\x1a\n"
    except OSError:
        return False


def render_docx_to_pdf(docx_path: Path, out_dir: Path, timeout: int = 120) -> Tuple[bool, str]:
    soffice = find_soffice()
    if not soffice:
        return False, "soffice absent"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf = out_dir / (docx_path.stem + ".pdf")

    # Remove any existing/stale PDF before running conversion (P0-D)
    if pdf.exists():
        try:
            pdf.unlink()
        except OSError:
            pass

    start_time = time.time()
    try:
        proc = subprocess.run(
            [soffice, "--headless", "--norestore", "--convert-to", "pdf", "--outdir", str(out_dir), str(docx_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, "soffice timeout"

    if proc.returncode != 0:
        return False, proc.stderr.strip() or f"soffice exit {proc.returncode}"

    # Verify that a fresh, valid, non-empty PDF was produced in this run
    if not pdf.exists():
        return False, "PDF missing after conversion"
    if pdf.stat().st_size == 0 or pdf.stat().st_mtime < start_time - 1.0:
        return False, "PDF is empty or stale"
    if not _is_valid_pdf(pdf):
        return False, "Generated file is not a valid PDF"

    return True, str(pdf)


def render_pdf_to_pngs(pdf_path: Path, out_dir: Path, timeout: int = 120) -> Tuple[bool, List[Path], str]:
    """Rasterize PDF pages. Prefers pdftoppm; does not claim success from a stale PNG (P0-D)."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Clean out any stale PNGs from earlier runs before rasterizing (P0-D)
    for old_png in out_dir.glob("page*.png"):
        try:
            old_png.unlink()
        except OSError:
            pass

    start_time = time.time()
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        prefix = out_dir / "page"
        try:
            proc = subprocess.run(
                [pdftoppm, "-png", str(pdf_path), str(prefix)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return False, [], "pdftoppm timeout"
        if proc.returncode != 0:
            return False, [], proc.stderr.strip() or f"pdftoppm exit {proc.returncode}"

        pages = sorted(out_dir.glob("page*.png"))
        if not pages:
            return False, [], "PNG missing: pdftoppm produced 0 pages"
        for p in pages:
            if not _is_valid_png(p) or p.stat().st_mtime < start_time - 1.0:
                return False, pages, f"PNG '{p.name}' is invalid, empty, or stale"
        return True, pages, f"{len(pages)} pages"

    magick = shutil.which("magick") or shutil.which("convert")
    if magick:
        dest = out_dir / "page.png"
        try:
            proc = subprocess.run(
                [magick, "-density", "120", str(pdf_path), str(dest)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return False, [], "magick timeout"
        if proc.returncode != 0:
            return False, [], proc.stderr.strip() or "magick failed"

        pages = sorted(out_dir.glob("page*.png"))
        if not pages:
            return False, [], "PNG missing: magick produced 0 pages"
        for p in pages:
            if not _is_valid_png(p) or p.stat().st_mtime < start_time - 1.0:
                return False, pages, f"PNG '{p.name}' is invalid, empty, or stale"
        return True, pages, f"{len(pages)} pages"

    return False, [], "no PDF rasterizer (pdftoppm/magick) in PATH"


def render_docx_pages(docx_path: Path, out_dir: Path, timeout: int = 180) -> dict:
    """Full adapter: DOCX → PDF → PNG. Status fields are independent."""
    result = {
        "soffice": find_soffice() or "absent",
        "executable_found": bool(find_soffice()),
        "render_ran": False,
        "pdf": None,
        "pages": [],
        "error": None,
    }
    ok, pdf_or_err = render_docx_to_pdf(Path(docx_path), Path(out_dir), timeout=timeout)
    if not ok:
        result["error"] = pdf_or_err
        return result
    result["render_ran"] = True
    result["pdf"] = pdf_or_err
    png_ok, pages, msg = render_pdf_to_pngs(Path(pdf_or_err), Path(out_dir) / "pages", timeout=timeout)
    result["pages"] = [str(p) for p in pages]
    if not png_ok:
        result["error"] = msg
    return result
