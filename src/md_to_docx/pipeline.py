"""End-to-end conversion pipeline: Markdown -> Preprocess -> Pandoc AST -> DocxRenderer -> DOCX."""

import json
import shutil
import subprocess
import tempfile
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


def convert_markdown_to_docx(
    input_path: str | Path,
    output_path: str | Path,
    template: str | Path | Template = "purple_book",
    render_mermaid_fn: Optional[Callable] = None,
    media_dir: Optional[str | Path] = None,
) -> Path:
    """
    Executes the full conversion pipeline from Markdown to styled DOCX.
    Diagram images are persisted to media_dir (defaults to {output_stem}_media beside docx).
    """
    in_file = Path(input_path).resolve()
    if not in_file.exists() or not in_file.is_file():
        raise FileNotFoundError(f"Input file '{input_path}' does not exist or is not a regular file.")

    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. Load template
    if isinstance(template, Template):
        tmpl = template
    else:
        tmpl = Template.load(template)

    raw_text = in_file.read_text(encoding="utf-8")

    # 2. Preprocess Admonitions
    default_titles = {
        cls: spec.get("default_title", cls)
        for cls, spec in tmpl.callouts.items()
    }
    admon_processed = preprocess_admonitions(raw_text, default_titles=default_titles)

    # 3. Preprocess Mermaid diagrams into persistent media directory
    effective_media_dir = Path(media_dir).resolve() if media_dir else out_file.parent / f"{out_file.stem}_media"
    mermaid_processed = process_mermaid_blocks(
        admon_processed,
        output_dir=effective_media_dir,
        template=tmpl,
        render_fn=render_mermaid_fn,
    )

    # 4. Parse to Pandoc JSON AST
    ast_data = run_pandoc_ast(mermaid_processed)

    # 5. Initialize Renderer
    renderer = DocxRenderer(template=tmpl, base_dir=in_file.parent)

    # Normal style CS/bidi is applied in DocxRenderer._setup_normal_style.

    # 6. Translate AST to DOCX
    ast_to_docx(ast_data, renderer)

    # 7. Save output
    renderer.doc.save(str(out_file))

    return out_file
