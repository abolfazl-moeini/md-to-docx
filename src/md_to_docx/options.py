"""Generator options and direction resolution for md_to_docx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

DEFAULT_FONT_FAMILY = "Vazirmatn"
DEFAULT_LATIN_FONT = "Segoe UI"
DEFAULT_CODE_FONT = "Courier New"

ALLOWED_DIRECTIONS = ("auto", "rtl", "ltr")
ALLOWED_TEXT_ALIGNS = ("start", "right", "left", "center", "both")

RTL_PRIMARY_SUBTAGS = {
    "fa", "ar", "ur", "he", "ps", "sd", "ug", "yi", "syr", "ckb", "bqi"
}
RTL_SCRIPT_SUBTAGS = {
    "arab", "hebr", "syrc", "thaa", "mand", "samr"
}
LTR_PRIMARY_SUBTAGS = {
    "en", "fr", "de", "es", "ru", "it", "zh", "ja", "ko", "pt", "nl", "tr",
    "sv", "pl", "da", "fi", "no", "cs", "el", "hu", "ro", "uk", "vi", "id", "ms"
}



@dataclass
class GeneratorOptions:
    """Configuration options controlling conversion generation.

    Attributes:
        font_family: Primary font family for body and complex script text (default 'Vazirmatn').
        embed_fonts: Whether to embed TrueType fonts in the DOCX package (default False).
        direction: Document direction ('auto', 'rtl', 'ltr', default 'auto').
        text_align: Paragraph alignment ('start', 'right', 'left', 'both', default 'start').
        heading_font: Optional override for heading font.
        latin_font: Optional override for Latin text font.
        code_font: Optional override for monospace code font.
    """
    font_family: Optional[str] = None
    embed_fonts: bool = False
    direction: str = "auto"       # auto | rtl | ltr
    text_align: Optional[str] = None     # start | right | left | both | justify
    heading_font: Optional[str] = None
    latin_font: Optional[str] = None
    code_font: Optional[str] = None

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Central validation for GeneratorOptions according to finilize.v3.md Section 3.1."""
        if not isinstance(self.embed_fonts, bool):
            raise ValueError(
                f"embed_fonts must be a boolean (got {type(self.embed_fonts).__name__}: {self.embed_fonts!r})"
            )

        if not isinstance(self.direction, str):
            raise ValueError(
                f"direction must be a string (got {type(self.direction).__name__}: {self.direction!r})"
            )
        dir_norm = self.direction.strip().lower()
        if dir_norm not in ALLOWED_DIRECTIONS:
            raise ValueError(
                f"Invalid direction '{self.direction}'. Allowed values are: {', '.join(ALLOWED_DIRECTIONS)}"
            )
        self.direction = dir_norm

        if self.text_align is not None:
            if not isinstance(self.text_align, str):
                raise ValueError(
                    f"text_align must be a string (got {type(self.text_align).__name__}: {self.text_align!r})"
                )
            align_norm = self.text_align.strip().lower()
            if align_norm == "justify":
                align_norm = "both"
            if align_norm not in ALLOWED_TEXT_ALIGNS:
                raise ValueError(
                    f"Invalid text_align '{self.text_align}'. Allowed values are: {', '.join(ALLOWED_TEXT_ALIGNS)}"
                )
            self.text_align = align_norm

        for font_field in ("font_family", "heading_font", "latin_font", "code_font"):
            val = getattr(self, font_field)
            if val is not None:
                if not isinstance(val, str):
                    raise ValueError(
                        f"{font_field} must be a string (got {type(val).__name__}: {val!r})"
                    )
                val_stripped = val.strip()
                if not val_stripped:
                    raise ValueError(f"{font_field} cannot be an empty or whitespace-only string")
                setattr(self, font_field, val_stripped)

    @classmethod
    def from_dict(cls, d: dict) -> GeneratorOptions:
        if not isinstance(d, dict):
            raise ValueError(f"Expected dict for options, got {type(d).__name__}")
        valid_fields = {
            "font_family", "embed_fonts", "direction", "text_align",
            "heading_font", "latin_font", "code_font"
        }
        unknown = set(d.keys()) - valid_fields
        if unknown:
            raise ValueError(f"Unknown generator option(s): {', '.join(sorted(unknown))}")
        return cls(**d)


def resolve_effective_direction(
    option_direction: Optional[str] = "auto",
    meta_direction: Optional[str] = None,
    template_direction: str = "rtl",
    meta_lang: Optional[str] = None,
    narrative_direction: Optional[str] = None,
) -> str:
    """Determines effective document direction from option, metadata, narrative text, and template.

    Precedence (finilize.v3.md Section 1.1):
    1. Explicit option ('rtl' or 'ltr') when not 'auto' / None.
    2. Document metadata 'dir' / 'direction' ('rtl' or 'ltr').
    3. Document metadata 'lang' / 'language' standard primary subtag match.
    4. Dominant narrative text direction from AST ('R/AL' vs 'L').
    5. Template direction ('rtl' or 'ltr').
    Default fallback is 'rtl'.
    """
    if option_direction:
        opt = str(option_direction).strip().lower()
        if opt in ("rtl", "ltr"):
            return opt

    if meta_direction:
        md = str(meta_direction).strip().lower()
        if md in ("rtl", "ltr"):
            return md

    if meta_lang:
        lang_clean = str(meta_lang).strip().lower().replace("_", "-")
        subtags = lang_clean.split("-")
        primary_subtag = subtags[0]
        if primary_subtag in RTL_PRIMARY_SUBTAGS:
            return "rtl"
        if any(st in RTL_SCRIPT_SUBTAGS for st in subtags[1:]):
            return "rtl"
        if primary_subtag in LTR_PRIMARY_SUBTAGS:
            return "ltr"

    if narrative_direction:
        nd = str(narrative_direction).strip().lower()
        if nd in ("rtl", "ltr"):
            return nd

    if template_direction:
        td = str(template_direction).strip().lower()
        if td in ("rtl", "ltr"):
            return td

    return "rtl"

