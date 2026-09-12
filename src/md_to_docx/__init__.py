"""md_to_docx package."""

from md_to_docx.pipeline import convert_markdown_to_docx, convert_markdown_to_pdf
from md_to_docx.pdf import (
    convert_docx_to_pdf,
    find_soffice_binary,
    is_valid_pdf,
    LibreOfficeNotFoundError,
)
from md_to_docx.template import Template
from md_to_docx.to_md import convert_docx_to_markdown
from md_to_docx.mermaid import ConvertError
from md_to_docx.options import GeneratorOptions, DEFAULT_FONT_FAMILY

__version__ = "0.3.0"
__all__ = [
    "convert_markdown_to_docx",
    "convert_markdown_to_pdf",
    "convert_docx_to_pdf",
    "find_soffice_binary",
    "is_valid_pdf",
    "LibreOfficeNotFoundError",
    "Template",
    "convert_docx_to_markdown",
    "ConvertError",
    "GeneratorOptions",
    "DEFAULT_FONT_FAMILY",
]

