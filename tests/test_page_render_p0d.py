import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from scripts.page_render import render_docx_to_pdf, render_pdf_to_pngs


def test_p0d_stale_pdf_rejected_when_soffice_is_noop(tmp_path, monkeypatch):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    docx = tmp_path / "test.docx"
    docx.write_bytes(b"PK\x03\x04test")
    # Place a stale PDF from an earlier run
    stale_pdf = out_dir / "test.pdf"
    stale_pdf.write_bytes(b"%PDF-1.4 stale content %%EOF")

    # Mock find_soffice to point to a dummy script that does nothing (exits 0 without creating anything)
    dummy_soffice = tmp_path / "dummy_soffice.sh"
    dummy_soffice.write_text("#!/bin/sh\nexit 0\n")
    dummy_soffice.chmod(0o755)

    import scripts.page_render as pr
    monkeypatch.setattr(pr, "find_soffice", lambda: str(dummy_soffice))

    ok, msg = render_docx_to_pdf(docx, out_dir)
    assert not ok, f"Expected failure when soffice is a no-op, but got success with stale PDF! ({msg})"


def test_p0d_stale_png_rejected_when_rasterizer_is_noop(tmp_path, monkeypatch):
    out_dir = tmp_path / "pages"
    out_dir.mkdir()
    pdf = tmp_path / "test.pdf"
    pdf.write_bytes(b"%PDF-1.4 valid pdf content %%EOF")
    # Pre-existing stale PNG in output directory
    stale_png = out_dir / "page-1.png"
    stale_png.write_bytes(b"\x89PNG\r\n\x1a\nstale png")

    # Dummy pdftoppm that does nothing and exits 0
    dummy_pdftoppm = tmp_path / "dummy_pdftoppm.sh"
    dummy_pdftoppm.write_text("#!/bin/sh\nexit 0\n")
    dummy_pdftoppm.chmod(0o755)

    import shutil
    monkeypatch.setattr(shutil, "which", lambda cmd: str(dummy_pdftoppm) if cmd == "pdftoppm" else None)

    ok, pages, msg = render_pdf_to_pngs(pdf, out_dir)
    assert not ok, f"Expected failure when pdftoppm is a no-op, but got success with stale PNG! ({msg})"
