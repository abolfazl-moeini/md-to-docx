"""Headless LibreOffice adapter for DOCX to PDF conversion.

Provides robust discovery, isolated user profiles, process group isolation
with zombie cleanup on timeout, and output PDF validation.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import tempfile
import uuid
import xml.sax.saxutils
from pathlib import Path
from typing import List, Optional

from md_to_docx.mermaid import ConvertError

LIBREOFFICE_NOT_FOUND_MESSAGE = (
    "PDF conversion requires LibreOffice ('soffice').\n"
    "To install LibreOffice on your system:\n"
    "  - macOS:   brew install --cask libreoffice\n"
    "  - Ubuntu:  sudo apt install libreoffice\n"
    "  - Fedora:  sudo dnf install libreoffice\n"
    "Or set MD2DOCX_SOFFICE to the path of your soffice executable."
)


class LibreOfficeNotFoundError(ConvertError):
    """Raised when LibreOffice ('soffice') executable is not found."""

    def __init__(self, message: str = LIBREOFFICE_NOT_FOUND_MESSAGE) -> None:
        super().__init__(message)


def _is_usable_soffice(path: Path) -> bool:
    try:
        if not path.is_file():
            return False
        if os.name == "posix" and not os.access(path, os.X_OK):
            return False
        return True
    except OSError:
        return False


def find_soffice_binary() -> Optional[Path]:
    """Locates soffice binary via MD2DOCX_SOFFICE env var, PATH, or standard OS directories.

    If MD2DOCX_SOFFICE is set, it is an explicit override: an unusable value
    does not fall back to PATH or standard locations.
    """
    env_path = (os.environ.get("MD2DOCX_SOFFICE") or "").strip()
    if env_path:
        candidate = Path(env_path).expanduser()
        if _is_usable_soffice(candidate):
            return candidate.resolve()
        return None

    # 2. Check system PATH
    for name in ("soffice", "libreoffice"):
        which_path = shutil.which(name)
        if which_path:
            p = Path(which_path)
            try:
                if p.is_file():
                    return p.resolve()
            except OSError:
                pass

    # 3. Check standard OS installation directories
    standard_paths: List[Path] = [
        # macOS
        Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
        Path.home() / "Applications" / "LibreOffice.app" / "Contents" / "MacOS" / "soffice",
        # Linux / Unix
        Path("/usr/bin/soffice"),
        Path("/usr/local/bin/soffice"),
        Path("/usr/bin/libreoffice"),
        Path("/usr/local/bin/libreoffice"),
        Path("/snap/bin/libreoffice"),
        Path("/var/lib/flatpak/exports/bin/org.libreoffice.LibreOffice"),
        # Windows
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "LibreOffice" / "program" / "soffice.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "LibreOffice" / "program" / "soffice.exe",
        Path(os.environ.get("LOCALAPPDATA", r"C:\Users\Default\AppData\Local")) / "Programs" / "LibreOffice" / "program" / "soffice.exe",
    ]

    for cand in standard_paths:
        try:
            if cand.is_file():
                if os.name == "posix":
                    if os.access(cand, os.X_OK):
                        return cand.resolve()
                else:
                    return cand.resolve()
        except OSError:
            continue

    return None


def is_valid_pdf(path: Path | str, min_size: int = 1000) -> bool:
    """
    Verifies that the file exists, has %PDF- magic bytes header,
    meets minimum size threshold (>1000 bytes by default), and ends with
    a %%EOF trailer marker. A bare xref/startxref table without %%EOF
    (truncated writer output) is rejected.
    """
    p = Path(path)
    try:
        if not p.is_file():
            return False
        size = p.stat().st_size
    except OSError:
        return False

    if size < min_size:
        return False

    try:
        with open(p, "rb") as f:
            header = f.read(1024)
            if not header.startswith(b"%PDF-"):
                return False
            f.seek(max(0, size - 2048))
            footer = f.read(2048)
            if b"%%EOF" not in footer:
                return False
        return True
    except OSError:
        return False


def _kill_process_tree(proc: subprocess.Popen) -> None:
    """Kills the process group to ensure no orphaned LibreOffice child processes remain."""
    if proc.poll() is not None:
        return
    try:
        if os.name == "nt":
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    capture_output=True,
                    timeout=5,
                )
                return
            except Exception:
                pass
            proc.kill()
            return
        if hasattr(os, "killpg") and hasattr(os, "getpgid"):
            try:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGKILL)
                return
            except (ProcessLookupError, OSError):
                pass
        proc.kill()
    except OSError:
        pass


def _docx_is_rtl(docx_path: Path) -> bool:
    """Checks if a DOCX file defines RTL direction in section or body."""
    import zipfile
    try:
        with zipfile.ZipFile(docx_path) as z:
            if "word/document.xml" in z.namelist():
                content = z.read("word/document.xml")
                return b"<w:bidi" in content
    except Exception:
        pass
    return False


def _apply_pdf_r2l_direction(pdf_path: Path) -> None:
    """Injects /ViewerPreferences << /Direction /R2L >> into the PDF catalog so PDF viewers render RTL."""
    try:
        import pypdf
        from pypdf.generic import NameObject, DictionaryObject
        reader = pypdf.PdfReader(str(pdf_path))
        writer = pypdf.PdfWriter()
        writer.append(reader)
        vp = writer._root_object.get(NameObject("/ViewerPreferences"))
        if vp is None or not isinstance(vp, DictionaryObject):
            vp = DictionaryObject()
            writer._root_object[NameObject("/ViewerPreferences")] = vp
        vp[NameObject("/Direction")] = NameObject("/R2L")
        tmp_target = pdf_path.with_name(f"{pdf_path.stem}.r2l.tmp")
        with open(tmp_target, "wb") as f:
            writer.write(f)
        os.replace(tmp_target, pdf_path)
    except Exception:
        pass


def convert_docx_to_pdf(
    docx_path: str | Path,
    output_pdf_path: str | Path,
    timeout: int = 120,
    overwrite: bool = True,
    soffice_binary: Optional[str | Path] = None,
    min_size: int = 1000,
    font_dirs: Optional[List[Path]] = None,
) -> Path:
    """
    Executes headless LibreOffice conversion from DOCX to PDF with an isolated
    user profile, hard timeout with process group kill, and PDF validation.

    Args:
        docx_path: Path to the input DOCX file.
        output_pdf_path: Path where the output PDF should be written.
        timeout: Maximum seconds to wait for LibreOffice before killing the process.
        overwrite: If False and output_pdf_path exists, raises ConvertError.
        soffice_binary: Optional explicit path to soffice executable (skips auto-discovery).
        min_size: Minimum file size in bytes for the generated PDF to be considered valid.
        font_dirs: Optional list of directories containing fonts for Fontconfig / SAL_FONTPATH.

    Returns:
        Path to the generated PDF.

    Raises:
        LibreOfficeNotFoundError: If soffice is not found on the system.
        ConvertError: On conversion failure, timeout, or invalid output.
        FileNotFoundError: If input DOCX does not exist.
        ValueError / IsADirectoryError: If paths are invalid.
    """
    if timeout <= 0:
        raise ValueError(f"timeout must be positive, got {timeout}.")

    in_docx = Path(docx_path).resolve()
    if not in_docx.exists():
        raise FileNotFoundError(f"Input DOCX file '{docx_path}' does not exist.")
    if not in_docx.is_file():
        raise IsADirectoryError(f"Input DOCX path '{docx_path}' is a directory, not a regular file.")
    if in_docx.suffix.lower() == ".doc":
        raise ConvertError("Word 97-2003 .doc is not supported. Provide a .docx file.")
    if in_docx.suffix.lower() != ".docx":
        raise ConvertError(
            f"Input file must have a .docx extension, got '{in_docx.suffix or in_docx.name}'."
        )

    out_pdf = Path(output_pdf_path).resolve()
    if in_docx == out_pdf or (in_docx.exists() and out_pdf.exists() and os.path.samefile(in_docx, out_pdf)):
        raise ValueError("Output path cannot be identical to input path.")
    if out_pdf.is_dir():
        raise IsADirectoryError(f"Output path '{out_pdf}' is a directory, not a regular file.")
    if out_pdf.suffix.lower() != ".pdf":
        raise ConvertError(
            f"Output file must have a .pdf extension, got '{out_pdf.suffix or out_pdf.name}'."
        )
    if out_pdf.exists() and not overwrite:
        raise ConvertError(
            f"Output file '{out_pdf}' already exists. Pass overwrite=True or --overwrite."
        )

    # Validate output parent directory
    if out_pdf.parent.exists():
        if not os.access(out_pdf.parent, os.W_OK):
            raise PermissionError(f"Permission denied: cannot write to output directory '{out_pdf.parent}'.")
    else:
        out_pdf.parent.mkdir(parents=True, exist_ok=True)

    if out_pdf.exists() and not os.access(out_pdf, os.W_OK):
        raise PermissionError(f"Permission denied: output file '{out_pdf}' is not writable.")

    # Locate LibreOffice
    soffice_path: Optional[Path] = None
    if soffice_binary is not None:
        soffice_path = Path(soffice_binary).resolve()
        if not soffice_path.is_file():
            raise LibreOfficeNotFoundError(
                f"Specified LibreOffice binary '{soffice_binary}' does not exist or is not a file."
            )
        if os.name == "posix" and not os.access(soffice_path, os.X_OK):
            raise LibreOfficeNotFoundError(
                f"Specified LibreOffice binary '{soffice_binary}' is not executable."
            )
    else:
        soffice_path = find_soffice_binary()

    if not soffice_path:
        env_override = (os.environ.get("MD2DOCX_SOFFICE") or "").strip()
        if env_override:
            raise LibreOfficeNotFoundError(
                f"MD2DOCX_SOFFICE is set to '{env_override}' but is not a usable soffice binary. "
                "Fix the path or unset MD2DOCX_SOFFICE to use PATH discovery.\n"
                + LIBREOFFICE_NOT_FOUND_MESSAGE
            )
        raise LibreOfficeNotFoundError(LIBREOFFICE_NOT_FOUND_MESSAGE)

    # Create isolated temporary user profile to prevent lock conflicts and profile pollution
    profile_dir = Path(tempfile.mkdtemp(prefix=f".lo_prof_{uuid.uuid4().hex[:8]}_"))
    # Create temporary conversion stage directory
    stage_parent = out_pdf.parent if out_pdf.parent.exists() and os.access(out_pdf.parent, os.W_OK) else None
    conv_stage_dir = Path(tempfile.mkdtemp(prefix=f".lo_stage_{uuid.uuid4().hex[:8]}_", dir=stage_parent))

    try:
        # Pre-seed profile with CTL and RTL locale settings to ensure proper bidi layout
        user_dir = profile_dir / "user"
        user_dir.mkdir(parents=True, exist_ok=True)
        reg_mod = user_dir / "registrymodifications.xcu"
        reg_content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<oor:items xmlns:oor="http://openoffice.org/2001/registry" '
            'xmlns:xs="http://www.w3.org/2001/XMLSchema" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
            '  <item oor:path="/org.openoffice.Office.Common/I18N/CTL">\n'
            '    <prop oor:name="CTLFont" oor:type="xs:boolean"><value>true</value></prop>\n'
            '    <prop oor:name="CTLSequenceChecking" oor:type="xs:boolean"><value>true</value></prop>\n'
            '  </item>\n'
            '  <item oor:path="/org.openoffice.Setup/L10N">\n'
            '    <prop oor:name="ooSetupSystemLocale" oor:type="xs:string"><value>fa-IR</value></prop>\n'
            '  </item>\n'
            '</oor:items>\n'
        )
        reg_mod.write_text(reg_content, encoding="utf-8")

        profile_uri = profile_dir.resolve().as_uri()
        cmd = [
            str(soffice_path),
            "--headless",
            "--norestore",
            "--nofirststartwizard",
            "--nologo",
            "--nolockcheck",
            f"-env:UserInstallation={profile_uri}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(conv_stage_dir),
            str(in_docx),
        ]

        env = os.environ.copy()
        if font_dirs:
            valid_font_dirs = [str(d.resolve()) for d in font_dirs if d.is_dir()]
            if valid_font_dirs:
                env["SAL_FONTPATH"] = os.pathsep.join(valid_font_dirs)
                try:
                    fc_dirs_xml = "\n".join(
                        f"  <dir>{xml.sax.saxutils.escape(d)}</dir>" for d in valid_font_dirs
                    )
                    fc_content = (
                        '<?xml version="1.0"?>\n'
                        '<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n'
                        '<fontconfig>\n'
                        '  <include ignore_missing="yes">/etc/fonts/fonts.conf</include>\n'
                        '  <include ignore_missing="yes">/etc/fonts/local.conf</include>\n'
                        '  <include ignore_missing="yes">~/.config/fontconfig/fonts.conf</include>\n'
                        f'{fc_dirs_xml}\n'
                        '</fontconfig>\n'
                    )
                    fc_file = profile_dir / "fonts.conf"
                    fc_file.write_text(fc_content, encoding="utf-8")
                    env["FONTCONFIG_FILE"] = str(fc_file.resolve())
                except Exception:
                    pass

        proc: Optional[subprocess.Popen] = None
        try:
            popen_kwargs: dict = {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "text": True,
                "env": env,
            }
            if os.name == "posix":
                popen_kwargs["start_new_session"] = True
            else:
                popen_kwargs["creationflags"] = int(
                    getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                )
            proc = subprocess.Popen(cmd, **popen_kwargs)
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as e:
            if proc is not None:
                _kill_process_tree(proc)
                try:
                    proc.communicate(timeout=5)
                except Exception:
                    pass
            raise ConvertError(
                f"LibreOffice conversion timed out after {timeout} seconds."
            ) from e

        if proc.returncode != 0:
            err_msg = stderr.strip() or stdout.strip() or f"exit code {proc.returncode}"
            raise ConvertError(f"LibreOffice conversion failed: {err_msg}")

        expected_pdf = conv_stage_dir / f"{in_docx.stem}.pdf"
        if not expected_pdf.is_file():
            extras = sorted(p.name for p in conv_stage_dir.glob("*.pdf"))
            extra_note = f" Other PDFs present: {extras}." if extras else ""
            raise ConvertError(
                f"LibreOffice succeeded but no PDF output was found at '{expected_pdf}'.{extra_note}"
            )

        if not is_valid_pdf(expected_pdf, min_size=min_size):
            raise ConvertError(f"Generated PDF at '{expected_pdf}' is invalid, empty, or corrupt.")

        # Post-process: inject /ViewerPreferences << /Direction /R2L >> if document is RTL
        if _docx_is_rtl(in_docx):
            _apply_pdf_r2l_direction(expected_pdf)

        # Final publish under inter-process lock so concurrent converters
        # serialize on the same output (mirrors pipeline._publish_lock; the lock
        # file is intentionally retained). Lazy import avoids a circular import
        # with md_to_docx.pipeline, which imports this module.
        from md_to_docx.pipeline import _publish_lock

        lock_path = out_pdf.parent / f".{out_pdf.stem}.pdf.publish.lock"
        with _publish_lock(lock_path):
            if out_pdf.exists() and not overwrite:
                raise ConvertError(
                    f"Output file '{out_pdf}' already exists. Pass overwrite=True or --overwrite."
                )

            # Atomically replace target PDF
            try:
                os.replace(expected_pdf, out_pdf)
            except OSError:
                shutil.move(str(expected_pdf), str(out_pdf))

        return out_pdf

    finally:
        # Guarantee cleanup of temporary profile and stage directories
        if profile_dir.exists():
            shutil.rmtree(profile_dir, ignore_errors=True)
        if conv_stage_dir.exists():
            shutil.rmtree(conv_stage_dir, ignore_errors=True)
