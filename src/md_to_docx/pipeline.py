"""End-to-end conversion pipeline: Markdown -> Preprocess -> Pandoc AST -> DocxRenderer -> DOCX."""

import contextlib
import json
import os
import shutil
import subprocess
import tempfile
import threading
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from md_to_docx.template import Template, PROJECT_ROOT
from md_to_docx.admonitions import preprocess_admonitions
from md_to_docx.mermaid import process_mermaid_ast, ConvertError
from md_to_docx.pandoc_json import ast_to_docx
from md_to_docx.renderer import DocxRenderer


def run_pandoc_ast(markdown_text: str) -> Dict[str, Any]:
    """Invokes pandoc to parse Markdown into a JSON AST dictionary."""
    if not shutil.which("pandoc"):
        raise ConvertError(
            "Pandoc executable not found in PATH. Please install pandoc: 'brew install pandoc'"
        )

    cmd = [
        "pandoc",
        "-f",
        "markdown+fenced_divs+pipe_tables+backtick_code_blocks+raw_html+lists_without_preceding_blankline",
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
        )
    except FileNotFoundError as e:
        raise ConvertError(
            "Pandoc executable not found in PATH. Please install pandoc: 'brew install pandoc'"
        ) from e

    if proc.returncode != 0:
        raise ConvertError(f"Pandoc parsing failed with exit code {proc.returncode}:\n{proc.stderr}")

    try:
        return json.loads(proc.stdout)
    except Exception as e:
        raise ConvertError(f"Failed to parse pandoc JSON AST: {e}") from e


MAX_INPUT_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB limit (R-11)
_THREAD_LOCK = threading.Lock()


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


def _assert_safe_media_dir(media: Path, in_file: Path, out_file: Path) -> None:
    forbidden = {
        in_file.parent.resolve(),
        PROJECT_ROOT.resolve(),
        Path.cwd().resolve(),
        out_file.parent.resolve(),
        Path("/").resolve(),
    }
    if media in forbidden:
        raise ConvertError(
            f"Refusing to use '{media}' as media_dir because it is the input folder, "
            "project root, cwd, or output parent. Use a dedicated subdirectory."
        )


def _publish_diagrams(stage_media_dir: Path, target_media_dir: Path) -> None:
    """Copy only managed diagram_*.png files; never rmtree the whole target directory."""
    target_media_dir.mkdir(parents=True, exist_ok=True)
    incoming = sorted(stage_media_dir.glob("diagram_*.png"))
    new_names = {src.name for src in incoming}
    for src in incoming:
        shutil.copy2(str(src), str(target_media_dir / (src.name + ".tmp")))
    for src in incoming:
        os.replace(str(target_media_dir / (src.name + ".tmp")), str(target_media_dir / src.name))
    for old in target_media_dir.glob("diagram_*.png"):
        if old.name not in new_names:
            try:
                old.unlink()
            except OSError:
                pass


def convert_markdown_to_docx(
    input_path: Optional[str | Path] = None,
    output_path: str | Path = "output.docx",
    template: str | Path | Template = "purple_book",
    render_mermaid_fn: Optional[Callable] = None,
    media_dir: Optional[str | Path] = None,
    overwrite: bool = True,
    content: Optional[str] = None,
    base_dir: Optional[str | Path] = None,
) -> Path:
    """
    Executes the full conversion pipeline from Markdown to styled DOCX.
    Supports either an input file path (input_path) or raw markdown text (content).
    Uses staging directories for atomic publish (R-02) and cleans up on failure.
    Diagram images are persisted to media_dir (defaults to {output_stem}_media beside docx).
    """
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
    if out_file == in_file:
        raise ValueError("Output path cannot be identical to input path.")
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

    # 2. Stage conversion in an isolated temporary directory (R-02 / R-04)
    # Prefer staging within the same filesystem as out_file for atomic os.replace
    stage_parent = out_file.parent if out_file.parent.exists() and os.access(out_file.parent, os.W_OK) else None
    stage_dir_path = Path(tempfile.mkdtemp(prefix=f".stage_{out_file.stem}_{uuid.uuid4().hex[:8]}_", dir=stage_parent))

    try:
        stage_docx = stage_dir_path / f"stage_{uuid.uuid4().hex[:8]}.docx"
        stage_media_dir = stage_dir_path / f"{out_file.stem}_media"
        stage_media_dir.mkdir(parents=True, exist_ok=True)

        # 3. Preprocess Admonitions
        default_titles = {
            cls: spec.get("default_title", cls)
            for cls, spec in tmpl.callouts.items()
        }
        admon_processed = preprocess_admonitions(raw_text, default_titles=default_titles)

        # 4. Parse to Pandoc JSON AST, then render Mermaid CodeBlocks in-tree (FIN-06)
        ast_data = run_pandoc_ast(admon_processed)
        n_diagrams = process_mermaid_ast(
            ast_data,
            output_dir=stage_media_dir,
            template=tmpl,
            render_fn=render_mermaid_fn,
        )

        # 5. Initialize Renderer and Translate AST to DOCX
        renderer = DocxRenderer(template=tmpl, base_dir=in_file.parent)
        ast_to_docx(ast_data, renderer)

        # 6. Save to staged DOCX file first
        renderer.doc.save(str(stage_docx))

        # 7. Publish DOCX; only managed diagram_*.png files are written to media_dir (FIN-01)
        target_media_dir = Path(media_dir).resolve() if media_dir else out_file.parent / f"{out_file.stem}_media"
        if media_dir is not None:
            _assert_safe_media_dir(target_media_dir, in_file, out_file)
        lock_path = out_file.parent / f".{out_file.stem}.publish.lock"

        with _publish_lock(lock_path):
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

