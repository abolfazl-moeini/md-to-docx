"""Command-Line Interface (CLI) for md-to-docx.

Exit code contract:
  0: Successful execution.
  1: Conversion or operational failure (e.g. Pandoc/Mermaid execution, permission errors).
  2: Usage, CLI argument, input validation, or template lookup errors.
"""

import sys
from pathlib import Path
import click

from md_to_docx.template import (
    Template,
    TemplateError,
    TemplateNotFoundError,
    TemplateValidationError,
)
from md_to_docx.pipeline import convert_markdown_to_docx
from md_to_docx.mermaid import ConvertError


import logging
import os
import traceback


@click.group()
def main():
    """md-to-docx: Convert Persian / RTL Markdown + Mermaid to beautiful DOCX."""
    pass


@main.command()
@click.argument("input_path", type=click.Path(exists=False, dir_okay=True, readable=False))
@click.option("-o", "--output", "output_path", type=click.Path(dir_okay=False), help="Output DOCX path.")
@click.option("-t", "--template", "template_name", default="purple_book", help="Template name or directory path.")
@click.option("-f", "--overwrite", is_flag=True, default=False, help="Overwrite existing output file.")
def convert(input_path: str, output_path: str | None, template_name: str, overwrite: bool):
    """Converts a Markdown file into a styled DOCX document."""
    raw_in = Path(input_path)
    if raw_in.is_symlink() and not raw_in.exists():
        click.echo(f"Error: Input file '{input_path}' does not exist (broken symlink).", err=True)
        sys.exit(2)

    in_file = raw_in.resolve()

    if not in_file.exists():
        click.echo(f"Error: Input file '{input_path}' does not exist.", err=True)
        sys.exit(2)

    if not in_file.is_file():
        click.echo(f"Error: Input path '{input_path}' is a directory, not a regular file.", err=True)
        sys.exit(2)

    if not os.access(in_file, os.R_OK):
        click.echo(f"Permission Error: Input file '{in_file}' is not readable.", err=True)
        sys.exit(1)

    if not output_path:
        out_file = in_file.with_suffix(".docx")
    else:
        out_file = Path(output_path).resolve()

    if out_file.suffix.lower() == ".doc":
        click.echo(
            "Error: Word 97-2003 .doc is not supported. Use a .docx output path.",
            err=True,
        )
        sys.exit(2)

    if out_file == in_file:
        click.echo("Error: Output path cannot be identical to input path.", err=True)
        sys.exit(2)

    if out_file.is_dir():
        click.echo(f"Error: Output path '{out_file}' is a directory, not a regular file.", err=True)
        sys.exit(2)

    if out_file.parent.exists() and not os.access(out_file.parent, os.W_OK):
        click.echo(f"Permission Error: Output directory '{out_file.parent}' is not writable.", err=True)
        sys.exit(1)

    if out_file.exists():
        if not overwrite:
            click.echo(
                f"Error: Output file '{out_file}' already exists. Use --overwrite (-f) to overwrite.",
                err=True,
            )
            sys.exit(2)
        if not os.access(out_file, os.W_OK):
            click.echo(f"Permission Error: Output file '{out_file}' is not writable.", err=True)
            sys.exit(1)

    try:
        tmpl = Template.load(template_name)
    except TemplateNotFoundError:
        available = ", ".join(Template.list_available()) or "none found"
        click.echo(
            f"Error: Template '{template_name}' not found. Available templates: {available}",
            err=True,
        )
        sys.exit(2)
    except TemplateValidationError as e:
        click.echo(f"Error: Invalid template configuration: {e}", err=True)
        sys.exit(2)

    try:
        saved = convert_markdown_to_docx(in_file, out_file, template=tmpl, overwrite=overwrite)
        click.echo(f"Success: Generated DOCX at '{saved}'")
    except PermissionError as e:
        click.echo(f"Permission Error: {e}", err=True)
        sys.exit(1)
    except ConvertError as e:
        click.echo(f"Conversion Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logging.getLogger(__name__).exception("Unexpected error in CLI conversion: %s", e)
        click.echo(f"Unexpected Error: {e}\n{traceback.format_exc()}", err=True)
        sys.exit(1)


@main.group()
def templates():
    """Manage and inspect templates."""
    pass


@templates.command(name="list")
def list_templates():
    """Lists available templates."""
    available = Template.list_available()
    if not available:
        click.echo("No templates found.")
        return
    click.echo("Available templates:")
    for name in available:
        click.echo(f"  - {name}")


@templates.command(name="validate")
@click.argument("template_name_or_path")
def validate_template(template_name_or_path: str):
    """Validates a template configuration and its referenced assets."""
    try:
        tmpl = Template.load(template_name_or_path)
        click.echo(f"Template '{tmpl.name}' is valid.")
    except TemplateError as e:
        click.echo(f"Validation failed: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected validation error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
