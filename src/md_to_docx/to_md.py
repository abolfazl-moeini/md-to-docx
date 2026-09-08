"""Conversion from DOCX to Markdown (FINAL-16)."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from md_to_docx.mermaid import ConvertError


def convert_docx_to_markdown(
    docx_path: str | Path,
    output_path: Optional[str | Path] = None,
    overwrite: bool = False,
    media_dir: Optional[str | Path] = None,
) -> Path:
    """
    Extracts content and embedded media from a DOCX document into Markdown and asset files.
    """
    in_file = Path(docx_path).resolve()
    if not in_file.exists():
        raise FileNotFoundError(f"DOCX input file '{docx_path}' does not exist.")
    if not in_file.is_file():
        raise IsADirectoryError(f"DOCX input path '{docx_path}' is a directory, not a regular file.")

    if in_file.suffix.lower() == ".doc":
        raise ConvertError("Word 97-2003 .doc is not supported. Please provide a modern .docx file.")
    if in_file.suffix.lower() != ".docx":
        raise ConvertError(f"Input file must have a .docx extension, got '{in_file.suffix}'.")

    if not shutil.which("pandoc"):
        raise ConvertError("Pandoc executable not found in PATH. Please install pandoc: 'brew install pandoc'")

    if output_path is None:
        out_file = in_file.with_suffix(".md")
    else:
        out_file = Path(output_path).resolve()

    if out_file.suffix.lower() != ".md":
        raise ConvertError(f"Output path must have a .md extension, got '{out_file.suffix}'.")

    if out_file == in_file or (out_file.exists() and os.path.samefile(out_file, in_file)):
        raise ValueError("Output path cannot be identical to input DOCX file.")

    if out_file.exists() and not overwrite:
        raise ConvertError(f"Output file '{out_file}' already exists. Pass overwrite=True to overwrite.")

    out_file.parent.mkdir(parents=True, exist_ok=True)
    target_media_dir = Path(media_dir).resolve() if media_dir else out_file.parent / f"{out_file.stem}_media"

    stage_dir = Path(tempfile.mkdtemp(prefix=f".stage_docx_{uuid.uuid4().hex[:8]}_", dir=out_file.parent))
    try:
        stage_md = stage_dir / "output.md"
        stage_media = stage_dir / "media_extract"
        stage_media.mkdir(parents=True, exist_ok=True)

        cmd = [
            "pandoc",
            "--from=docx",
            "--to=gfm+pipe_tables",
            "--wrap=none",
            f"--extract-media={stage_media}",
            str(in_file),
            "-o",
            str(stage_md),
        ]

        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        except subprocess.TimeoutExpired as e:
            raise ConvertError("Pandoc conversion from DOCX timed out after 60 seconds.") from e

        if proc.returncode != 0:
            raise ConvertError(f"Pandoc DOCX to Markdown conversion failed:\n{proc.stderr}")

        md_content = stage_md.read_text(encoding="utf-8")

        # Pandoc places media in <stage_media>/media/...
        extracted_media_dir = stage_media / "media"
        has_media = extracted_media_dir.exists() and any(extracted_media_dir.iterdir())

        if has_media:
            target_media_dir.mkdir(parents=True, exist_ok=True)
            # Rewrite only Markdown/HTML image/link targets that point at the
            # extracted `media/` folder; never touch prose containing "media/".
            # Pandoc emits `](media/name)` and `src="media/name"` forms.
            import re

            rel_name = target_media_dir.name
            md_content = md_content.replace(f"{stage_media}/media/", f"{rel_name}/")
            md_content = re.sub(r"\]\(media/", f"]({rel_name}/", md_content)
            md_content = re.sub(r'src="media/', f'src="{rel_name}/', md_content)
            md_content = re.sub(r"src='media/", f"src='{rel_name}/", md_content)

            for item in extracted_media_dir.iterdir():
                if item.is_file():
                    shutil.copy2(str(item), str(target_media_dir / item.name))

        # Atomic publish of markdown file
        tmp_out = out_file.with_name(f".tmp_{out_file.name}_{uuid.uuid4().hex[:8]}")
        tmp_out.write_text(md_content, encoding="utf-8")
        os.replace(tmp_out, out_file)

        return out_file

    finally:
        if stage_dir.exists():
            shutil.rmtree(stage_dir, ignore_errors=True)
