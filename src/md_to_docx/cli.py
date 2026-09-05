"""Command-Line Interface (CLI) for md-to-docx."""

import sys
from pathlib import Path
import click

from md_to_docx.template import Template, TemplateError, TemplateNotFoundError, TemplateValidationError
from md_to_docx.pipeline import convert_markdown_to_docx
from md_to_docx.mermaid import ConvertError


@click.group()
def main():
    """md-to-docx: Convert Persian / RTL Markdown + Mermaid to beautiful DOCX."""
    pass


@main.command()
@click.argument("input_path", type=click.Path(exists=False, dir_okay=False))
@click.option("-o", "--output", "output_path", type=click.Path(dir_okay=False), help="Output DOCX path.")
@click.option("-t", "--template", "template_name", default="purple_book", help="Template name or directory path.")
def convert(input_path: str, output_path: str | None, template_name: str):
    """Converts a Markdown file into a DOCX document."""
    in_file = Path(input_path)
    if not in_file.exists():
        click.echo(f"Error: Input file '{input_path}' does not exist.", err=True)
        sys.exit(2)

    if not output_path:
        out_file = in_file.with_suffix(".docx")
    else:
        out_file = Path(output_path)

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
        saved = convert_markdown_to_docx(in_file, out_file, template=tmpl)
        click.echo(f"Success: Generated DOCX at '{saved}'")
    except ConvertError as e:
        click.echo(f"Conversion Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected Error: {e}", err=True)
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
    """Validates a template configuration."""
    try:
        tmpl = Template.load(template_name_or_path)
        click.echo(f"Template '{tmpl.name}' is valid.")
    except TemplateError as e:
        click.echo(f"Validation failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
