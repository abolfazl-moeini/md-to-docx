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
from md_to_docx.pipeline import convert_markdown_to_docx, convert_markdown_to_pdf
from md_to_docx.pdf import convert_docx_to_pdf, LibreOfficeNotFoundError
from md_to_docx.mermaid import ConvertError


import logging
import os
import traceback


from md_to_docx.options import GeneratorOptions


@click.group()
def main():
    """md-to-docx: Convert Persian / RTL Markdown + Mermaid to beautiful DOCX."""
    pass


@main.command()
@click.argument("input_path", type=click.Path(exists=False, dir_okay=True, readable=False))
@click.option("-o", "--output", "output_path", type=click.Path(dir_okay=False), help="Output DOCX or PDF path.")
@click.option("-t", "--template", "template_name", default="purple_book", help="Template name or directory path.")
@click.option("-f", "--overwrite", is_flag=True, default=False, help="Overwrite existing output file.")
@click.option("--keep-docx", is_flag=True, default=False, help="Keep intermediate DOCX file when generating PDF.")
@click.option("--pdf-timeout", default=120, type=click.IntRange(min=1), show_default=True, help="LibreOffice conversion timeout in seconds.")
@click.option("--font", "--font-family", "font_family", default=None, help="Font family for body / complex script text (defaults to template font).")
@click.option("--embed-fonts/--no-embed-fonts", default=False, show_default=True, help="Embed TrueType fonts in DOCX package.")
@click.option("--direction", type=click.Choice(["auto", "rtl", "ltr"], case_sensitive=False), default="auto", show_default=True, help="Document text direction.")
@click.option("--text-align", type=click.Choice(["start", "right", "left", "center", "both", "justify"], case_sensitive=False), default=None, help="Paragraph alignment (defaults to template paragraph_align).")
@click.option("--heading-font", default=None, help="Font family override for headings.")
@click.option("--latin-font", default=None, help="Font family override for Latin text.")
@click.option("--code-font", default=None, help="Font family override for monospace code.")
def convert(
    input_path: str,
    output_path: str | None,
    template_name: str,
    overwrite: bool,
    keep_docx: bool,
    pdf_timeout: int,
    font_family: str | None,
    embed_fonts: bool,
    direction: str,
    text_align: str | None,
    heading_font: str | None,
    latin_font: str | None,
    code_font: str | None,
):
    """Converts a Markdown file into a styled DOCX or PDF document."""
    try:
        opts = GeneratorOptions(
            font_family=font_family,
            embed_fonts=embed_fonts,
            direction=direction,
            text_align=text_align,
            heading_font=heading_font,
            latin_font=latin_font,
            code_font=code_font,
        )
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)
    if input_path == "-":
        if not output_path:
            click.echo("Error: Output path (-o / --output) is required when reading from standard input.", err=True)
            sys.exit(2)
        out_file = Path(output_path).resolve()
        if out_file.suffix.lower() == ".doc":
            click.echo(
                "Error: Word 97-2003 .doc is not supported. Use a .docx or .pdf output path.",
                err=True,
            )
            sys.exit(2)
        if out_file.suffix.lower() not in (".docx", ".pdf"):
            click.echo(
                f"Error: Output path must have a .docx or .pdf extension (got '{out_file.suffix or out_file.name}').",
                err=True,
            )
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
        if out_file.suffix.lower() == ".pdf" and keep_docx:
            keep_docx_file = out_file.with_suffix(".docx")
            if keep_docx_file.exists():
                if not overwrite:
                    click.echo(
                        f"Error: Intermediate DOCX file '{keep_docx_file}' already exists. Use --overwrite (-f) to overwrite.",
                        err=True,
                    )
                    sys.exit(2)
                if not os.access(keep_docx_file, os.W_OK):
                    click.echo(f"Permission Error: Intermediate DOCX file '{keep_docx_file}' is not writable.", err=True)
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

        content = sys.stdin.read()
        report: dict = {}
        try:
            if out_file.suffix.lower() == ".pdf":
                saved = convert_markdown_to_pdf(
                    output_path=out_file,
                    content=content,
                    template=tmpl,
                    overwrite=overwrite,
                    options=opts,
                    report=report,
                    keep_docx=keep_docx,
                    pdf_timeout=pdf_timeout,
                )
                effective_font = report.get("effective_body_font") or opts.font_family or tmpl.fonts.get("body", "Vazirmatn")
                effective_direction = report.get("effective_direction", opts.direction)
                click.echo(
                    f"Success: Generated PDF at '{saved}' "
                    f"(font: {effective_font}, embedded: {'yes' if opts.embed_fonts else 'no'}, direction: {effective_direction})"
                )
                return
            else:
                saved = convert_markdown_to_docx(
                    output_path=out_file,
                    content=content,
                    template=tmpl,
                    overwrite=overwrite,
                    options=opts,
                    report=report,
                )
                effective_font = report.get("effective_body_font") or opts.font_family or tmpl.fonts.get("body", "Vazirmatn")
                effective_direction = report.get("effective_direction", opts.direction)
                click.echo(
                    f"Success: Generated DOCX at '{saved}' "
                    f"(font: {effective_font}, embedded: {'yes' if opts.embed_fonts else 'no'}, direction: {effective_direction})"
                )
                return
        except LibreOfficeNotFoundError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        except PermissionError as e:
            click.echo(f"Permission Error: {e}", err=True)
            sys.exit(1)
        except ConvertError as e:
            click.echo(f"Conversion Error: {e}", err=True)
            sys.exit(1)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(2)
        except Exception as e:
            logging.getLogger(__name__).exception("Unexpected error in CLI conversion: %s", e)
            click.echo(f"Unexpected Error: {e}\n{traceback.format_exc()}", err=True)
            sys.exit(1)

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

    if out_file == in_file:
        click.echo("Error: Output path cannot be identical to input path.", err=True)
        sys.exit(2)

    if out_file.suffix.lower() == ".doc":
        click.echo(
            "Error: Word 97-2003 .doc is not supported. Use a .docx or .pdf output path.",
            err=True,
        )
        sys.exit(2)
    if out_file.suffix.lower() not in (".docx", ".pdf"):
        click.echo(
            f"Error: Output path must have a .docx or .pdf extension (got '{out_file.suffix or out_file.name}').",
            err=True,
        )
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

    if out_file.suffix.lower() == ".pdf" and keep_docx:
        keep_docx_file = out_file.with_suffix(".docx")
        if keep_docx_file.exists():
            if not overwrite:
                click.echo(
                    f"Error: Intermediate DOCX file '{keep_docx_file}' already exists. Use --overwrite (-f) to overwrite.",
                    err=True,
                )
                sys.exit(2)
            if not os.access(keep_docx_file, os.W_OK):
                click.echo(f"Permission Error: Intermediate DOCX file '{keep_docx_file}' is not writable.", err=True)
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

    report = {}
    try:
        if out_file.suffix.lower() == ".pdf":
            saved = convert_markdown_to_pdf(
                input_path=in_file,
                output_path=out_file,
                template=tmpl,
                overwrite=overwrite,
                options=opts,
                report=report,
                keep_docx=keep_docx,
                pdf_timeout=pdf_timeout,
            )
            effective_font = report.get("effective_body_font") or opts.font_family or tmpl.fonts.get("body", "Vazirmatn")
            effective_direction = report.get("effective_direction", opts.direction)
            click.echo(
                f"Success: Generated PDF at '{saved}' "
                f"(font: {effective_font}, embedded: {'yes' if opts.embed_fonts else 'no'}, direction: {effective_direction})"
            )
        else:
            saved = convert_markdown_to_docx(
                in_file,
                out_file,
                template=tmpl,
                overwrite=overwrite,
                options=opts,
                report=report,
            )
            effective_font = report.get("effective_body_font") or opts.font_family or tmpl.fonts.get("body", "Vazirmatn")
            effective_direction = report.get("effective_direction", opts.direction)
            click.echo(
                f"Success: Generated DOCX at '{saved}' "
                f"(font: {effective_font}, embedded: {'yes' if opts.embed_fonts else 'no'}, direction: {effective_direction})"
            )
    except LibreOfficeNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except PermissionError as e:
        click.echo(f"Permission Error: {e}", err=True)
        sys.exit(1)
    except ConvertError as e:
        click.echo(f"Conversion Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)
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


@main.command(name="to-md")
@click.argument("docx_path", type=click.Path(exists=False, dir_okay=True, readable=False))
@click.option("-o", "--output", "output_path", type=click.Path(dir_okay=False), help="Output Markdown path.")
@click.option("-f", "--overwrite", is_flag=True, default=False, help="Overwrite existing output Markdown file.")
@click.option("--media-dir", default=None, help="Directory to save extracted images.")
def to_md(docx_path: str, output_path: str | None, overwrite: bool, media_dir: str | None):
    """Converts a DOCX document into Markdown and extracts media assets (FINAL-16)."""
    from md_to_docx.to_md import convert_docx_to_markdown

    in_file = Path(docx_path)
    if in_file.suffix.lower() == ".doc":
        click.echo("Error: Word 97-2003 .doc is not supported. Provide a .docx file.", err=True)
        sys.exit(2)
    if in_file.suffix.lower() != ".docx":
        click.echo(
            f"Error: Input file must have a .docx extension, got '{in_file.suffix or in_file.name}'.",
            err=True,
        )
        sys.exit(2)
    if not in_file.exists():
        click.echo(f"Error: Input DOCX file '{docx_path}' does not exist.", err=True)
        sys.exit(2)
    if in_file.is_dir():
        click.echo(f"Error: Input path '{docx_path}' is a directory, not a regular file.", err=True)
        sys.exit(2)
    if output_path is not None and Path(output_path).suffix.lower() != ".md":
        click.echo(
            f"Error: Output path must have a .md extension, got '{Path(output_path).suffix or output_path}'.",
            err=True,
        )
        sys.exit(2)

    try:
        saved = convert_docx_to_markdown(
            docx_path=in_file,
            output_path=output_path,
            overwrite=overwrite,
            media_dir=media_dir,
        )
        click.echo(f"Success: Generated Markdown at '{saved}'")
    except ConvertError as e:
        click.echo(f"Conversion Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected Error: {e}", err=True)
        sys.exit(1)


@main.command(name="to-pdf")
@click.argument("docx_path", type=click.Path(exists=False, dir_okay=True, readable=False))
@click.option("-o", "--output", "output_path", type=click.Path(dir_okay=False), help="Output PDF path.")
@click.option("-f", "--overwrite", is_flag=True, default=False, help="Overwrite existing output PDF file.")
@click.option("--timeout", "--pdf-timeout", "pdf_timeout", default=120, type=click.IntRange(min=1), show_default=True, help="LibreOffice conversion timeout in seconds.")
def to_pdf(docx_path: str, output_path: str | None, overwrite: bool, pdf_timeout: int):
    """Converts an existing DOCX document into a PDF document via headless LibreOffice."""
    raw_in = Path(docx_path)
    if raw_in.is_symlink() and not raw_in.exists():
        click.echo(f"Error: Input file '{docx_path}' does not exist (broken symlink).", err=True)
        sys.exit(2)
    if raw_in.suffix.lower() == ".doc":
        click.echo("Error: Word 97-2003 .doc is not supported. Provide a .docx file.", err=True)
        sys.exit(2)
    if raw_in.suffix.lower() != ".docx":
        click.echo(
            f"Error: Input file must have a .docx extension, got '{raw_in.suffix or raw_in.name}'.",
            err=True,
        )
        sys.exit(2)

    in_file = raw_in.resolve()
    if not in_file.exists():
        click.echo(f"Error: Input DOCX file '{docx_path}' does not exist.", err=True)
        sys.exit(2)
    if in_file.is_dir():
        click.echo(f"Error: Input path '{docx_path}' is a directory, not a regular file.", err=True)
        sys.exit(2)
    if not os.access(in_file, os.R_OK):
        click.echo(f"Permission Error: Input file '{in_file}' is not readable.", err=True)
        sys.exit(1)

    if not output_path:
        out_file = raw_in.with_suffix(".pdf").resolve()
    else:
        out_file = Path(output_path).resolve()

    if out_file == in_file:
        click.echo("Error: Output path cannot be identical to input path.", err=True)
        sys.exit(2)
    if out_file.suffix.lower() != ".pdf":
        click.echo(
            f"Error: Output path must have a .pdf extension, got '{out_file.suffix or out_file.name}'.",
            err=True,
        )
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
        saved = convert_docx_to_pdf(
            docx_path=in_file,
            output_pdf_path=out_file,
            timeout=pdf_timeout,
            overwrite=overwrite,
        )
        click.echo(f"Success: Generated PDF at '{saved}'")
    except LibreOfficeNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except PermissionError as e:
        click.echo(f"Permission Error: {e}", err=True)
        sys.exit(1)
    except ConvertError as e:
        click.echo(f"Conversion Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)
    except Exception as e:
        logging.getLogger(__name__).exception("Unexpected error in CLI to-pdf: %s", e)
        click.echo(f"Unexpected Error: {e}\n{traceback.format_exc()}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
