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

from md_to_docx.template import Template
from md_to_docx.admonitions import preprocess_admonitions
from md_to_docx.mermaid import process_mermaid_blocks, ConvertError
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
    Acquires an in-process thread lock and an inter-process file lock (flock)
    to guarantee safe atomic publishing and eliminate race conditions during concurrent runs (R-04).
    """
    with _THREAD_LOCK:
        lock_fd = None
        try:
            try:
                import fcntl
                lock_path.parent.mkdir(parents=True, exist_ok=True)
                lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
                fcntl.flock(lock_fd, fcntl.LOCK_EX)
            except (ImportError, OSError):
                lock_fd = None
            yield
        finally:
            if lock_fd is not None:
                try:
                    import fcntl
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    os.close(lock_fd)
                except OSError:
                    pass
                try:
                    if lock_path.exists():
                        lock_path.unlink()
                except OSError:
                    pass


def convert_markdown_to_docx(
    input_path: str | Path,
    output_path: str | Path,
    template: str | Path | Template = "purple_book",
    render_mermaid_fn: Optional[Callable] = None,
    media_dir: Optional[str | Path] = None,
) -> Path:
    """
    Executes the full conversion pipeline from Markdown to styled DOCX.
    Uses staging directories for atomic publish (R-02) and cleans up on failure.
    Diagram images are persisted to media_dir (defaults to {output_stem}_media beside docx).
    """
    in_file = Path(input_path).resolve()
    if not in_file.exists():
        raise FileNotFoundError(f"Input file '{input_path}' does not exist.")
    if not in_file.is_file():
        raise IsADirectoryError(f"Input path '{input_path}' is a directory, not a regular file.")
    if not os.access(in_file, os.R_OK):
        raise PermissionError(f"Permission denied: cannot read input file '{in_file}'.")

    # Enforce maximum input size (R-11)
    file_size = in_file.stat().st_size
    if file_size > MAX_INPUT_SIZE_BYTES:
        raise ConvertError(
            f"Input file size ({file_size} bytes) exceeds maximum supported limit of {MAX_INPUT_SIZE_BYTES} bytes."
        )

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

    raw_text = in_file.read_text(encoding="utf-8")

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

        # 4. Preprocess Mermaid diagrams into staging media directory
        mermaid_processed = process_mermaid_blocks(
            admon_processed,
            output_dir=stage_media_dir,
            template=tmpl,
            render_fn=render_mermaid_fn,
        )

        # 5. Parse to Pandoc JSON AST
        ast_data = run_pandoc_ast(mermaid_processed)

        # 6. Initialize Renderer and Translate AST to DOCX
        renderer = DocxRenderer(template=tmpl, base_dir=in_file.parent)
        ast_to_docx(ast_data, renderer)

        # 7. Save to staged DOCX file first
        renderer.doc.save(str(stage_docx))

        # 8. Atomic Publish (R-02 / R-04)
        target_media_dir = Path(media_dir).resolve() if media_dir else out_file.parent / f"{out_file.stem}_media"
        diagram_files = list(stage_media_dir.glob("*.png"))
        lock_path = out_file.parent / f".{out_file.stem}.publish.lock"

        with _publish_lock(lock_path):
            backup_docx: Optional[Path] = None
            backup_media: Optional[Path] = None
            docx_previously_existed = out_file.exists()
            media_previously_existed = target_media_dir.exists()

            if docx_previously_existed:
                backup_docx = out_file.with_name(f".backup_{out_file.name}_{uuid.uuid4().hex[:8]}")
                shutil.copy2(str(out_file), str(backup_docx))

            if media_previously_existed:
                backup_media = target_media_dir.with_name(f".backup_{target_media_dir.name}_{uuid.uuid4().hex[:8]}")
                try:
                    os.replace(target_media_dir, backup_media)
                except OSError:
                    shutil.copytree(str(target_media_dir), str(backup_media))
                    shutil.rmtree(target_media_dir, ignore_errors=True)

            try:
                # Move staged docx to final destination
                try:
                    os.replace(stage_docx, out_file)
                except OSError:
                    shutil.move(str(stage_docx), str(out_file))

                # Publish media directory if diagrams were produced
                if diagram_files:
                    try:
                        os.replace(stage_media_dir, target_media_dir)
                    except OSError:
                        if target_media_dir.exists():
                            shutil.rmtree(target_media_dir, ignore_errors=True)
                        shutil.copytree(str(stage_media_dir), str(target_media_dir))
                elif media_dir is None and backup_media:
                    # Clean up stale auto-managed media directory from a previous run without diagrams (R-02)
                    pass

                # Success: cleanup backups
                if backup_docx and backup_docx.exists():
                    backup_docx.unlink(missing_ok=True)
                if backup_media and backup_media.exists():
                    shutil.rmtree(backup_media, ignore_errors=True)

            except Exception:
                # Rollback docx and media on failure (R3-05)
                if backup_docx and backup_docx.exists():
                    try:
                        os.replace(backup_docx, out_file)
                    except OSError:
                        shutil.move(str(backup_docx), str(out_file))
                elif not docx_previously_existed and out_file.exists():
                    out_file.unlink(missing_ok=True)

                if backup_media and backup_media.exists():
                    if target_media_dir.exists():
                        shutil.rmtree(target_media_dir, ignore_errors=True)
                    try:
                        os.replace(backup_media, target_media_dir)
                    except OSError:
                        shutil.move(str(backup_media), str(target_media_dir))
                elif not media_previously_existed and target_media_dir.exists():
                    shutil.rmtree(target_media_dir, ignore_errors=True)

                raise

        return out_file

    finally:
        # Guarantee cleanup of staging directory on both success and failure (R-02)
        if stage_dir_path.exists():
            shutil.rmtree(stage_dir_path, ignore_errors=True)

