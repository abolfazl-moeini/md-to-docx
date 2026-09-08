"""md_to_docx package."""

from md_to_docx.pipeline import convert_markdown_to_docx
from md_to_docx.template import Template
from md_to_docx.to_md import convert_docx_to_markdown
from md_to_docx.mermaid import ConvertError

__version__ = "0.1.0"
__all__ = ["convert_markdown_to_docx", "Template", "convert_docx_to_markdown", "ConvertError"]

