"""End-to-end conversion pipeline: Markdown -> Preprocess -> Pandoc AST -> DocxRenderer -> DOCX."""

import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import copy
from md_to_docx.template import Template, PROJECT_ROOT
from md_to_docx.admonitions import preprocess_admonitions
from md_to_docx.mermaid import process_mermaid_ast, ConvertError
from md_to_docx.pandoc_json import ast_to_docx
from md_to_docx.renderer import DocxRenderer
from md_to_docx.options import GeneratorOptions
from md_to_docx.fonts_embed import embed_fonts_in_docx, strip_embedded_fonts
import md_to_docx.pdf as _pdf_module
from md_to_docx.pdf import (
    convert_docx_to_pdf,
    find_soffice_binary,
    is_valid_pdf,
    LibreOfficeNotFoundError,
    LIBREOFFICE_NOT_FOUND_MESSAGE,
)

# Import-time snapshots so the resolvers below can tell a pipeline-level
# monkeypatch apart from the live pdf module attribute (tests patch either
# md_to_docx.pipeline.* or md_to_docx.pdf.*).
_pdf_orig_convert = _pdf_module.convert_docx_to_pdf
_pdf_orig_find_soffice = _pdf_module.find_soffice_binary


def _resolve_find_soffice() -> Optional[Path]:
    """Late-bound soffice lookup so tests may patch md_to_docx.pdf or md_to_docx.pipeline."""
    if find_soffice_binary is not _pdf_orig_find_soffice:
        return find_soffice_binary()
    return _pdf_module.find_soffice_binary()


def _resolve_convert_docx() -> Callable:
    """Late-bound converter lookup so tests may patch md_to_docx.pdf or md_to_docx.pipeline."""
    if convert_docx_to_pdf is not _pdf_orig_convert:
        return convert_docx_to_pdf
    return _pdf_module.convert_docx_to_pdf

# Keep this string in sync with scripts/generate_fixtures.py and the manifest parser tests.
PANDOC_FROM = (
    "markdown+fenced_divs+pipe_tables+grid_tables+backtick_code_blocks"
    "+raw_html+markdown_in_html_blocks+lists_without_preceding_blankline"
)


def run_pandoc_ast(markdown_text: str) -> Dict[str, Any]:
    """Invokes pandoc to parse Markdown into a JSON AST dictionary."""
    if not shutil.which("pandoc"):
        raise ConvertError(
            "Pandoc executable not found in PATH. Please install pandoc: 'brew install pandoc'"
        )

    cmd = [
        "pandoc",
        "-f",
        PANDOC_FROM,
        "-t", "json",
    ]
    try:
        proc = subprocess.run(
            cmd,
            input=markdown_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=60,
        )
    except FileNotFoundError as e:
        raise ConvertError(
            "Pandoc executable not found in PATH. Please install pandoc: 'brew install pandoc'"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise ConvertError("Pandoc AST parsing timed out after 60 seconds.") from e

    if proc.returncode != 0:
        raise ConvertError(f"Pandoc parsing failed with exit code {proc.returncode}:\n{proc.stderr}")

    try:
        return json.loads(proc.stdout)
    except Exception as e:
        raise ConvertError(f"Failed to parse pandoc JSON AST: {e}") from e


MAX_INPUT_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB limit (R-11)
_THREAD_LOCK = threading.RLock()


@contextlib.contextmanager
def _publish_lock(lock_path: Path):
    """
    Inter-process exclusive lock. The lock file is kept (not unlinked) so waiters
    share the same inode. Failure to lock is an error, not a silent fallback.
    """
    with _THREAD_LOCK:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            import fcntl
        except ImportError as e:
            raise ConvertError(
                "Inter-process publish locking requires fcntl (unavailable on this platform)."
            ) from e
        lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
        except OSError as e:
            os.close(lock_fd)
            raise ConvertError(f"Could not acquire publish lock '{lock_path}': {e}") from e
        try:
            yield
        finally:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
            except OSError:
                pass
            os.close(lock_fd)


def _assert_safe_media_dir(media: Path, in_file: Path, out_file: Path, template_path: Optional[Path] = None) -> None:
    forbidden = {
        in_file.parent.resolve(),
        PROJECT_ROOT.resolve(),
        Path.cwd().resolve(),
        out_file.parent.resolve(),
        Path("/").resolve(),
    }
    if template_path is not None:
        forbidden.add(template_path.resolve())
    if media in forbidden:
        raise ConvertError(
            f"Refusing to use '{media}' as media_dir because it is the input folder, "
            "project root, cwd, output parent, or template directory. Use a dedicated subdirectory."
        )


def _publish_diagrams(stage_media_dir: Path, target_media_dir: Path) -> None:
    """Copy only managed diagram_*.png files with transactional backup and rollback (FINAL-11)."""
    target_media_dir.mkdir(parents=True, exist_ok=True)
    incoming = sorted([p for p in stage_media_dir.glob("diagram_*") if p.suffix.lower() in (".png", ".svg")])
    new_names = {src.name for src in incoming}

    backups: dict[str, Path] = {}
    created_new: list[Path] = []
    tmp_files: list[Path] = []

    try:
        # 1. Back up any existing files that will be replaced
        for src in incoming:
            target_dest = target_media_dir / src.name
            if target_dest.exists():
                bk = target_media_dir / f".backup_{src.name}_{uuid.uuid4().hex[:8]}"
                shutil.copy2(str(target_dest), str(bk))
                backups[src.name] = bk
            else:
                created_new.append(target_dest)

        # 2. Stage new files with unique temporary names
        for src in incoming:
            tmp_target = target_media_dir / f".tmp_{src.name}_{uuid.uuid4().hex[:8]}"
            tmp_files.append(tmp_target)
            shutil.copy2(str(src), str(tmp_target))

        # 3. Atomically replace targets with tmp files
        for src, tmp_target in zip(incoming, tmp_files):
            os.replace(str(tmp_target), str(target_media_dir / src.name))

        # 4. Remove old diagrams no longer in the new set (with backup)
        for old in [p for p in target_media_dir.glob("diagram_*") if p.suffix.lower() in (".png", ".svg")]:
            if old.name not in new_names:
                bk = target_media_dir / f".backup_{old.name}_{uuid.uuid4().hex[:8]}"
                shutil.move(str(old), str(bk))
                backups[old.name] = bk

        # 5. Success: Clean up all backup files
        for bk in backups.values():
            if bk.exists():
                try:
                    bk.unlink()
                except OSError:
                    pass

    except Exception:
        # Rollback on failure: clean tmp files, remove newly created files, restore backups
        for tmp_target in tmp_files:
            if tmp_target.exists():
                try:
                    tmp_target.unlink()
                except OSError:
                    pass
        for new_p in created_new:
            if new_p.exists():
                try:
                    new_p.unlink()
                except OSError:
                    pass
        for orig_name, bk in backups.items():
            if bk.exists():
                try:
                    os.replace(str(bk), str(target_media_dir / orig_name))
                except OSError:
                    pass
        raise

def _render_stage_docx(
    tmpl: Template,
    raw_text: str,
    stage_dir_path: Path,
    stem: str,
    in_file: Path,
    opts: GeneratorOptions,
    renderer_opts: Optional[GeneratorOptions],
    render_mermaid_fn: Optional[Callable],
    warnings: Optional[List[str]],
    report: Optional[Dict[str, Any]],
) -> tuple[Path, Path, int]:
    """Helper to parse AST, render Mermaid diagrams, build DOCX, and handle font embedding."""
    stage_docx = stage_dir_path / f"stage_{uuid.uuid4().hex[:8]}.docx"
    stage_media_dir = stage_dir_path / f"{stem}_media"
    stage_media_dir.mkdir(parents=True, exist_ok=True)

    # Preprocess Admonitions
    default_titles = {
        cls: spec.get("default_title", cls)
        for cls, spec in tmpl.callouts.items()
    }
    admon_processed = preprocess_admonitions(raw_text, default_titles=default_titles)

    # Parse to Pandoc JSON AST, then render Mermaid CodeBlocks in-tree (FIN-06)
    ast_data = run_pandoc_ast(admon_processed)
    n_diagrams = process_mermaid_ast(
        ast_data,
        output_dir=stage_media_dir,
        template=tmpl,
        render_fn=render_mermaid_fn,
        options=opts,
    )

    # Initialize Renderer and Translate AST to DOCX
    renderer = DocxRenderer(template=tmpl, base_dir=in_file.parent, options=renderer_opts)
    ast_to_docx(ast_data, renderer)
    if renderer.warnings:
        if warnings is not None:
            warnings.extend(renderer.warnings)
        for warning in renderer.warnings:
            sys.stderr.write(f"Warning: {warning}\n")

    # Save to staged DOCX file first
    renderer.doc.save(str(stage_docx))

    # If font embedding is requested, embed font files into staged DOCX (V3-03); otherwise strip
    embedding_status = "referenced_only"
    if opts.embed_fonts:
        embedding_status = embed_fonts_in_docx(stage_docx, template=tmpl, options=opts)
    else:
        strip_embedded_fonts(stage_docx)

    if report is not None:
        report["effective_direction"] = renderer.effective_direction
        report["requested_direction"] = opts.direction
        report["effective_body_font"] = renderer.body_font
        report["effective_heading_font"] = renderer.heading_font
        report["effective_latin_font"] = renderer.latin_font
        report["effective_code_font"] = renderer.code_font
        report["embed_fonts"] = opts.embed_fonts
        report["embedding_status"] = embedding_status

    return stage_docx, stage_media_dir, n_diagrams


def convert_markdown_to_docx(
    input_path: Optional[str | Path] = None,
    output_path: str | Path = "output.docx",
    template: str | Path | Template = "purple_book",
    render_mermaid_fn: Optional[Callable] = None,
    media_dir: Optional[str | Path] = None,
    overwrite: bool = True,
    content: Optional[str] = None,
    base_dir: Optional[str | Path] = None,
    warnings: Optional[List[str]] = None,
    options: Optional[GeneratorOptions | dict] = None,
    font_family: Optional[str] = None,
    embed_fonts: Optional[bool] = None,
    direction: Optional[str] = None,
    text_align: Optional[str] = None,
    heading_font: Optional[str] = None,
    latin_font: Optional[str] = None,
    code_font: Optional[str] = None,
    report: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Executes the full conversion pipeline from Markdown to styled DOCX.
    Supports either an input file path (input_path) or raw markdown text (content).
    Uses staging directories for atomic publish (R-02) and cleans up on failure.
    Diagram images are persisted to media_dir (defaults to {output_stem}_media beside docx).
    """
    has_explicit_options = (options is not None) or any(
        x is not None for x in (font_family, embed_fonts, direction, text_align, heading_font, latin_font, code_font)
    )
    if options is None:
        opts = GeneratorOptions()
    elif isinstance(options, dict):
        opts = GeneratorOptions.from_dict(options)
    elif isinstance(options, GeneratorOptions):
        opts = copy.copy(options)
    else:
        raise ValueError(f"Invalid options type: {type(options)}")

    if font_family is not None:
        opts.font_family = font_family
    if embed_fonts is not None:
        opts.embed_fonts = embed_fonts
    if direction is not None:
        opts.direction = direction
    if text_align is not None:
        opts.text_align = text_align
    if heading_font is not None:
        opts.heading_font = heading_font
    if latin_font is not None:
        opts.latin_font = latin_font
    if code_font is not None:
        opts.code_font = code_font
    opts.validate()

    renderer_opts = opts if has_explicit_options else None


    if content is not None:
        raw_text = content
        file_size = len(raw_text.encode("utf-8"))
        if file_size > MAX_INPUT_SIZE_BYTES:
            raise ConvertError(
                f"Input content size ({file_size} bytes) exceeds maximum supported limit of {MAX_INPUT_SIZE_BYTES} bytes."
            )
        resolved_base = Path(base_dir).resolve() if base_dir else (
            Path(input_path).parent.resolve() if input_path and str(input_path) != "-" else Path.cwd().resolve()
        )
        in_file = resolved_base / ("input.md" if not input_path or str(input_path) == "-" else Path(input_path).name)
    else:
        if input_path is None:
            raise ValueError("Either input_path or content must be provided.")
        in_file = Path(input_path).resolve()
        if not in_file.exists():
            raise FileNotFoundError(f"Input file '{input_path}' does not exist.")
        if not in_file.is_file():
            raise IsADirectoryError(f"Input path '{input_path}' is a directory, not a regular file.")
        if not os.access(in_file, os.R_OK):
            raise PermissionError(f"Permission denied: cannot read input file '{in_file}'.")

        file_size = in_file.stat().st_size
        if file_size > MAX_INPUT_SIZE_BYTES:
            raise ConvertError(
                f"Input file size ({file_size} bytes) exceeds maximum supported limit of {MAX_INPUT_SIZE_BYTES} bytes."
            )
        raw_text = in_file.read_text(encoding="utf-8")

    out_file = Path(output_path).resolve()
    if out_file == in_file or (out_file.exists() and in_file.exists() and os.path.samefile(out_file, in_file)):
        raise ValueError("Output path cannot be identical to input path.")
    if out_file.suffix.lower() != ".docx":
        raise ConvertError(
            f"Output file must have a .docx extension, got '{out_file.suffix or out_file.name}'."
        )
    if out_file.is_dir():
        raise IsADirectoryError(f"Output path '{out_file}' is a directory, not a regular file.")

    # Validate output parent directory permissions (R-09)
    if out_file.parent.exists():
        if not os.access(out_file.parent, os.W_OK):
            raise PermissionError(f"Permission denied: cannot write to output directory '{out_file.parent}'.")
    else:
        out_file.parent.mkdir(parents=True, exist_ok=True)

    if out_file.exists() and not os.access(out_file, os.W_OK):
        raise PermissionError(f"Permission denied: output file '{out_file}' is not writable.")

    # 1. Load template
    if isinstance(template, Template):
        tmpl = template
    else:
        tmpl = Template.load(template)

    if tmpl.shell_docx_path and (out_file == tmpl.shell_docx_path or (out_file.exists() and tmpl.shell_docx_path.exists() and os.path.samefile(out_file, tmpl.shell_docx_path))):
        raise ConvertError("Output path cannot overwrite template shell file.")
    if tmpl.dir_path and (out_file == tmpl.dir_path or tmpl.dir_path in out_file.parents):
        raise ConvertError("Output path cannot be inside the template directory.")

    # 2. Stage conversion in an isolated temporary directory (R-02 / R-04)
    # Prefer staging within the same filesystem as out_file for atomic os.replace
    stage_parent = out_file.parent if out_file.parent.exists() and os.access(out_file.parent, os.W_OK) else None
    stage_dir_path = Path(tempfile.mkdtemp(prefix=f".stage_{out_file.stem}_{uuid.uuid4().hex[:8]}_", dir=stage_parent))

    try:
        stage_docx, stage_media_dir, n_diagrams = _render_stage_docx(
            tmpl=tmpl,
            raw_text=raw_text,
            stage_dir_path=stage_dir_path,
            stem=out_file.stem,
            in_file=in_file,
            opts=opts,
            renderer_opts=renderer_opts,
            render_mermaid_fn=render_mermaid_fn,
            warnings=warnings,
            report=report,
        )

        # 7. Publish DOCX; only managed diagram_*.png files are written to media_dir (FIN-01)
        target_media_dir = Path(media_dir).resolve() if media_dir else out_file.parent / f"{out_file.stem}_media"
        if media_dir is not None:
            _assert_safe_media_dir(target_media_dir, in_file, out_file, template_path=tmpl.dir_path)

        locks_to_acquire = [out_file.parent / f".{out_file.stem}.publish.lock"]
        if n_diagrams > 0:
            target_media_dir.mkdir(parents=True, exist_ok=True)
            media_lock = target_media_dir / ".media_publish.lock"
            if media_lock not in locks_to_acquire:
                locks_to_acquire.append(media_lock)
        locks_to_acquire.sort(key=lambda p: str(p.resolve()))

        with contextlib.ExitStack() as stack:
            for lp in locks_to_acquire:
                stack.enter_context(_publish_lock(lp))
            if out_file.exists() and not overwrite:
                raise ConvertError(
                    f"Output file '{out_file}' already exists. Pass overwrite=True or --overwrite."
                )

            backup_docx: Optional[Path] = None
            docx_previously_existed = out_file.exists()
            if docx_previously_existed:
                backup_docx = out_file.with_name(f".backup_{out_file.name}_{uuid.uuid4().hex[:8]}")
                shutil.copy2(str(out_file), str(backup_docx))

            try:
                try:
                    os.replace(stage_docx, out_file)
                except OSError:
                    shutil.move(str(stage_docx), str(out_file))

                if n_diagrams > 0:
                    _publish_diagrams(stage_media_dir, target_media_dir)

                if backup_docx and backup_docx.exists():
                    backup_docx.unlink(missing_ok=True)
            except Exception:
                if backup_docx and backup_docx.exists():
                    try:
                        os.replace(backup_docx, out_file)
                    except OSError:
                        shutil.move(str(backup_docx), str(out_file))
                elif not docx_previously_existed and out_file.exists():
                    out_file.unlink(missing_ok=True)
                raise

        return out_file

    finally:
        # Guarantee cleanup of staging directory on both success and failure (R-02)
        if stage_dir_path.exists():
            shutil.rmtree(stage_dir_path, ignore_errors=True)


def convert_markdown_to_pdf(
    input_path: Optional[str | Path] = None,
    output_path: str | Path = "output.pdf",
    template: str | Path | Template = "purple_book",
    render_mermaid_fn: Optional[Callable] = None,
    media_dir: Optional[str | Path] = None,
    overwrite: bool = True,
    content: Optional[str] = None,
    base_dir: Optional[str | Path] = None,
    warnings: Optional[List[str]] = None,
    options: Optional[GeneratorOptions | dict] = None,
    font_family: Optional[str] = None,
    embed_fonts: Optional[bool] = None,
    direction: Optional[str] = None,
    text_align: Optional[str] = None,
    heading_font: Optional[str] = None,
    latin_font: Optional[str] = None,
    code_font: Optional[str] = None,
    report: Optional[Dict[str, Any]] = None,
    keep_docx: bool = False,
    pdf_timeout: int = 120,
) -> Path:
    """
    Executes the full conversion pipeline from Markdown to styled PDF via headless LibreOffice.
    Stages intermediate DOCX and PDF files for atomic publication.
    Media directory is suppressed unless keep_docx=True or media_dir is explicitly specified.
    """
    has_explicit_options = (options is not None) or any(
        x is not None for x in (font_family, embed_fonts, direction, text_align, heading_font, latin_font, code_font)
    )
    if options is None:
        opts = GeneratorOptions()
    elif isinstance(options, dict):
        opts = GeneratorOptions.from_dict(options)
    elif isinstance(options, GeneratorOptions):
        opts = copy.copy(options)
    else:
        raise ValueError(f"Invalid options type: {type(options)}")

    if font_family is not None:
        opts.font_family = font_family
    if embed_fonts is not None:
        opts.embed_fonts = embed_fonts
    if direction is not None:
        opts.direction = direction
    if text_align is not None:
        opts.text_align = text_align
    if heading_font is not None:
        opts.heading_font = heading_font
    if latin_font is not None:
        opts.latin_font = latin_font
    if code_font is not None:
        opts.code_font = code_font
    opts.validate()

    renderer_opts = opts if has_explicit_options else None

    if pdf_timeout <= 0:
        raise ValueError(f"pdf_timeout must be positive, got {pdf_timeout}.")

    if content is not None:
        raw_text = content
        file_size = len(raw_text.encode("utf-8"))
        if file_size > MAX_INPUT_SIZE_BYTES:
            raise ConvertError(
                f"Input content size ({file_size} bytes) exceeds maximum supported limit of {MAX_INPUT_SIZE_BYTES} bytes."
            )
        resolved_base = Path(base_dir).resolve() if base_dir else (
            Path(input_path).parent.resolve() if input_path and str(input_path) != "-" else Path.cwd().resolve()
        )
        in_file = resolved_base / ("input.md" if not input_path or str(input_path) == "-" else Path(input_path).name)
    else:
        if input_path is None:
            raise ValueError("Either input_path or content must be provided.")
        in_file = Path(input_path).resolve()
        if not in_file.exists():
            raise FileNotFoundError(f"Input file '{input_path}' does not exist.")
        if not in_file.is_file():
            raise IsADirectoryError(f"Input path '{input_path}' is a directory, not a regular file.")
        if not os.access(in_file, os.R_OK):
            raise PermissionError(f"Permission denied: cannot read input file '{in_file}'.")

        file_size = in_file.stat().st_size
        if file_size > MAX_INPUT_SIZE_BYTES:
            raise ConvertError(
                f"Input file size ({file_size} bytes) exceeds maximum supported limit of {MAX_INPUT_SIZE_BYTES} bytes."
            )
        raw_text = in_file.read_text(encoding="utf-8")

    out_file = Path(output_path).resolve()
    if out_file == in_file or (out_file.exists() and in_file.exists() and os.path.samefile(out_file, in_file)):
        raise ValueError("Output path cannot be identical to input path.")
    if out_file.suffix.lower() != ".pdf":
        raise ConvertError(
            f"Output file must have a .pdf extension, got '{out_file.suffix or out_file.name}'."
        )
    if out_file.is_dir():
        raise IsADirectoryError(f"Output path '{out_file}' is a directory, not a regular file.")
    if out_file.exists() and not overwrite:
        raise ConvertError(
            f"Output file '{out_file}' already exists. Pass overwrite=True or --overwrite."
        )

    keep_docx_file: Optional[Path] = None
    if keep_docx:
        keep_docx_file = out_file.with_suffix(".docx")
        if keep_docx_file == in_file or (keep_docx_file.exists() and in_file.exists() and os.path.samefile(keep_docx_file, in_file)):
            raise ValueError("Intermediate DOCX path cannot be identical to input path.")
        if keep_docx_file.is_dir():
            raise IsADirectoryError(f"Intermediate DOCX path '{keep_docx_file}' is a directory, not a regular file.")
        if keep_docx_file.exists() and not overwrite:
            raise ConvertError(
                f"Intermediate DOCX file '{keep_docx_file}' already exists. Pass overwrite=True or --overwrite."
            )

    # Fail fast if LibreOffice is missing
    soffice_lookup = _resolve_find_soffice()
    if not soffice_lookup:
        env_override = (os.environ.get("MD2DOCX_SOFFICE") or "").strip()
        if env_override:
            raise LibreOfficeNotFoundError(
                f"MD2DOCX_SOFFICE is set to '{env_override}' but is not a usable soffice binary. "
                "Fix the path or unset MD2DOCX_SOFFICE to use PATH discovery.\n"
                + LIBREOFFICE_NOT_FOUND_MESSAGE
            )
        raise LibreOfficeNotFoundError(LIBREOFFICE_NOT_FOUND_MESSAGE)

    # Validate output parent directory permissions
    if out_file.parent.exists():
        if not os.access(out_file.parent, os.W_OK):
            raise PermissionError(f"Permission denied: cannot write to output directory '{out_file.parent}'.")
    else:
        out_file.parent.mkdir(parents=True, exist_ok=True)

    if out_file.exists() and not os.access(out_file, os.W_OK):
        raise PermissionError(f"Permission denied: output file '{out_file}' is not writable.")

    # 1. Load template
    if isinstance(template, Template):
        tmpl = template
    else:
        tmpl = Template.load(template)

    if tmpl.shell_docx_path and (out_file == tmpl.shell_docx_path or (out_file.exists() and tmpl.shell_docx_path.exists() and os.path.samefile(out_file, tmpl.shell_docx_path))):
        raise ConvertError("Output path cannot overwrite template shell file.")
    if tmpl.dir_path and (out_file == tmpl.dir_path or tmpl.dir_path in out_file.parents):
        raise ConvertError("Output path cannot be inside the template directory.")

    if keep_docx_file is not None:
        if tmpl.shell_docx_path and (keep_docx_file == tmpl.shell_docx_path or (keep_docx_file.exists() and tmpl.shell_docx_path.exists() and os.path.samefile(keep_docx_file, tmpl.shell_docx_path))):
            raise ConvertError("Intermediate DOCX path cannot overwrite template shell file.")
        if tmpl.dir_path and (keep_docx_file == tmpl.dir_path or tmpl.dir_path in keep_docx_file.parents):
            raise ConvertError("Intermediate DOCX path cannot be inside the template directory.")

    # Collect template font directories for LibreOffice discovery
    font_dirs: list[Path] = []
    if tmpl.dir_path:
        t_fonts = tmpl.dir_path / "fonts"
        if t_fonts.is_dir():
            font_dirs.append(t_fonts)
    if hasattr(tmpl, "font_files") and tmpl.font_files:
        for fpath in tmpl.font_files.values():
            try:
                resolved = tmpl._resolve_path(fpath)
                if resolved and resolved.parent.is_dir() and resolved.parent not in font_dirs:
                    font_dirs.append(resolved.parent)
            except Exception:
                pass

    # 2. Stage conversion in an isolated temporary directory
    stage_parent = out_file.parent if out_file.parent.exists() and os.access(out_file.parent, os.W_OK) else None
    stage_dir_path = Path(tempfile.mkdtemp(prefix=f".stage_{out_file.stem}_{uuid.uuid4().hex[:8]}_", dir=stage_parent))

    try:
        stage_docx, stage_media_dir, n_diagrams = _render_stage_docx(
            tmpl=tmpl,
            raw_text=raw_text,
            stage_dir_path=stage_dir_path,
            stem=out_file.stem,
            in_file=in_file,
            opts=opts,
            renderer_opts=renderer_opts,
            render_mermaid_fn=render_mermaid_fn,
            warnings=warnings,
            report=report,
        )

        stage_pdf = stage_dir_path / f"stage_{uuid.uuid4().hex[:8]}.pdf"
        # Convert staged DOCX to staged PDF
        convert_fn = _resolve_convert_docx()
        convert_fn(
            docx_path=stage_docx,
            output_pdf_path=stage_pdf,
            timeout=pdf_timeout,
            overwrite=True,
            font_dirs=font_dirs if font_dirs else None,
        )

        if not is_valid_pdf(stage_pdf):
            raise ConvertError(f"Generated PDF at '{stage_pdf}' is invalid or corrupt.")

        if report is not None:
            report["pdf_engine"] = "libreoffice"
            report["pdf_timeout"] = pdf_timeout
            report["keep_docx"] = keep_docx
            report["intermediate_docx"] = str(keep_docx_file) if keep_docx_file is not None else None

        # 3. Publish PDF and optionally intermediate DOCX / media
        should_publish_media = (media_dir is not None) or keep_docx
        target_media_dir = Path(media_dir).resolve() if media_dir else out_file.parent / f"{out_file.stem}_media"
        if media_dir is not None:
            _assert_safe_media_dir(target_media_dir, in_file, out_file, template_path=tmpl.dir_path)

        # Locks: PDF lock, optionally DOCX lock and media lock
        locks_to_acquire = [out_file.parent / f".{out_file.stem}.pdf.publish.lock"]
        if keep_docx_file is not None:
            locks_to_acquire.append(keep_docx_file.parent / f".{keep_docx_file.stem}.publish.lock")
        if should_publish_media and n_diagrams > 0:
            target_media_dir.mkdir(parents=True, exist_ok=True)
            locks_to_acquire.append(target_media_dir / ".media_publish.lock")
        # Deduplicate and sort locks
        unique_locks = sorted(list({str(p.resolve()): p for p in locks_to_acquire}.values()), key=lambda p: str(p.resolve()))

        with contextlib.ExitStack() as stack:
            for lp in unique_locks:
                stack.enter_context(_publish_lock(lp))

            if out_file.exists() and not overwrite:
                raise ConvertError(
                    f"Output file '{out_file}' already exists. Pass overwrite=True or --overwrite."
                )
            if keep_docx_file is not None and keep_docx_file.exists() and not overwrite:
                raise ConvertError(
                    f"Intermediate DOCX file '{keep_docx_file}' already exists. Pass overwrite=True or --overwrite."
                )

            backup_pdf: Optional[Path] = None
            pdf_previously_existed = out_file.exists()
            if pdf_previously_existed:
                backup_pdf = out_file.with_name(f".backup_{out_file.name}_{uuid.uuid4().hex[:8]}")
                shutil.copy2(str(out_file), str(backup_pdf))

            backup_docx: Optional[Path] = None
            docx_previously_existed = False
            if keep_docx_file is not None:
                docx_previously_existed = keep_docx_file.exists()
                if docx_previously_existed:
                    backup_docx = keep_docx_file.with_name(f".backup_{keep_docx_file.name}_{uuid.uuid4().hex[:8]}")
                    shutil.copy2(str(keep_docx_file), str(backup_docx))

            try:
                try:
                    os.replace(stage_pdf, out_file)
                except OSError:
                    shutil.move(str(stage_pdf), str(out_file))

                if keep_docx_file is not None:
                    try:
                        os.replace(stage_docx, keep_docx_file)
                    except OSError:
                        shutil.move(str(stage_docx), str(keep_docx_file))

                if should_publish_media and n_diagrams > 0:
                    _publish_diagrams(stage_media_dir, target_media_dir)

                if backup_pdf and backup_pdf.exists():
                    backup_pdf.unlink(missing_ok=True)
                if backup_docx and backup_docx.exists():
                    backup_docx.unlink(missing_ok=True)

            except Exception:
                # Rollback PDF
                if backup_pdf and backup_pdf.exists():
                    try:
                        os.replace(backup_pdf, out_file)
                    except OSError:
                        shutil.move(str(backup_pdf), str(out_file))
                elif not pdf_previously_existed and out_file.exists():
                    out_file.unlink(missing_ok=True)

                # Rollback DOCX if kept
                if keep_docx_file is not None:
                    if backup_docx and backup_docx.exists():
                        try:
                            os.replace(backup_docx, keep_docx_file)
                        except OSError:
                            shutil.move(str(backup_docx), str(keep_docx_file))
                    elif not docx_previously_existed and keep_docx_file.exists():
                        keep_docx_file.unlink(missing_ok=True)

                raise

        return out_file

    finally:
        # Guarantee cleanup of staging directory on both success and failure
        if stage_dir_path.exists():
            shutil.rmtree(stage_dir_path, ignore_errors=True)


