"""Template loading and validation for md-to-docx."""

import re
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class TemplateError(Exception):
    """Base exception for template errors."""
    pass


class TemplateNotFoundError(TemplateError):
    """Raised when a specified template cannot be found."""
    pass


class TemplateValidationError(TemplateError):
    """Raised when a template config is invalid or missing required fields."""
    pass


REQUIRED_SECTIONS = ["name", "direction", "fonts", "colors", "headings", "callouts", "quotes", "tables"]
REQUIRED_FONTS = ["body", "heading", "code"]
REQUIRED_COLORS = ["primary", "primary_dark", "on_primary", "quote_bg", "warning_bg", "warning_title", "body", "caption"]
PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent.parent


HEX_COLOR_RE = re.compile(r"^#?(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

ALLOWED_TOP_LEVEL = {
    "schema_version", "name", "direction", "language_bidi", "language_latin",
    "fonts", "font_files", "page", "colors", "headings", "callouts", "quotes",
    "tables", "code_block", "mermaid", "shell", "custom_styles", "caption",
}

PAGE_SIZES = {"A4", "Letter", "Legal", "A5"}
PAGE_DIMENSIONS_CM = {
    "A4": (21.0, 29.7),
    "A5": (14.8, 21.0),
    "Letter": (21.59, 27.94),
    "Legal": (21.59, 35.56),
}


def normalize_hex_color(value: str, field: str) -> str:
    raw = str(value).strip()
    if not HEX_COLOR_RE.match(raw):
        raise TemplateValidationError(f"Field '{field}' must be a 3- or 6-digit hex color, got '{value}'")
    hexpart = raw.lstrip("#")
    if len(hexpart) == 3:
        hexpart = "".join(ch * 2 for ch in hexpart)
    return hexpart.upper()


def require_number(value: Any, field: str, *, positive: bool = True, allow_zero: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TemplateValidationError(f"Field '{field}' must be a finite number, got '{value!r}'")
    import math
    if not math.isfinite(float(value)):
        raise TemplateValidationError(f"Field '{field}' must be a finite number, got '{value!r}'")
    if positive and value <= 0 and not allow_zero:
        raise TemplateValidationError(f"Field '{field}' must be a positive number, got '{value}'")
    if allow_zero and value < 0:
        raise TemplateValidationError(f"Field '{field}' must be non-negative, got '{value}'")
    return float(value)


class Template:
    """Represents a loaded and validated template."""

    def __init__(self, raw_config: Dict[str, Any], dir_path: Path):
        self.raw_config = raw_config
        self.dir_path = Path(dir_path).resolve()
        self._validate()

        self.name: str = raw_config.get("name", self.dir_path.name)
        self.direction: str = raw_config.get("direction", "rtl")
        self.language_bidi: str = raw_config.get("language_bidi", "fa-IR")
        self.language_latin: str = raw_config.get("language_latin", "en-US")
        self.fonts: Dict[str, str] = raw_config.get("fonts", {})
        self.font_files: Dict[str, str] = raw_config.get("font_files", {})
        self.page: Dict[str, Any] = raw_config.get("page", {
            "size": "A4",
            "margin_cm": {"top": 2.0, "bottom": 2.0, "left": 2.0, "right": 2.0}
        })
        self.colors: Dict[str, str] = raw_config.get("colors", {})
        self.headings: Dict[str, Any] = raw_config.get("headings", {})
        self.callouts: Dict[str, Any] = raw_config.get("callouts", {})
        self.quotes: Dict[str, Any] = raw_config.get("quotes", {})
        self.tables: Dict[str, Any] = raw_config.get("tables", {})
        self.code_block: Dict[str, Any] = raw_config.get("code_block", {})
        self.mermaid: Dict[str, Any] = raw_config.get("mermaid", {})

        # Custom styles mapping and strict mode (G04)
        self.custom_styles: Dict[str, str] = {}
        self.custom_styles_strict: bool = False
        raw_cs = raw_config.get("custom_styles")
        if isinstance(raw_cs, dict):
            self.custom_styles_strict = bool(raw_cs.get("strict", False))
            mappings = raw_cs.get("mappings", raw_cs)
            if isinstance(mappings, dict):
                for k, v in mappings.items():
                    if k != "strict" and isinstance(v, str):
                        self.custom_styles[k.strip().lower()] = v.strip().lower()

        # Paragraph alignment and spacing (G06, G08)
        self.paragraph_align: str = self.page.get("paragraph_align", "start")
        self.paragraph_space_after_pt: float = float(self.page.get("space_after_pt", 6.0))

        # Caption settings (G08)
        self.caption: Dict[str, Any] = raw_config.get("caption", {})
        self.caption_size_pt: float = float(self.caption.get("size_pt", 9.5))

        # Resolve paths relative to template directory (validates file existence)
        self.mermaid_theme_path: Optional[Path] = self._resolve_path(
            self.mermaid.get("theme_file"), field_name="mermaid.theme_file"
        )
        self.mermaid_css_path: Optional[Path] = self._resolve_path(
            self.mermaid.get("css_file"), field_name="mermaid.css_file"
        )
        self.mermaid_puppeteer_path: Optional[Path] = self._resolve_path(
            self.mermaid.get("puppeteer_config"), field_name="mermaid.puppeteer_config"
        )

        custom_shell = self.raw_config.get("shell")
        if custom_shell:
            self.shell_docx_path: Optional[Path] = self._resolve_path(
                custom_shell, field_name="shell"
            )
        else:
            shell_path = self.dir_path / "shell.docx"
            self.shell_docx_path: Optional[Path] = shell_path if shell_path.exists() else None

    def _resolve_path(self, relative_name: Optional[str], field_name: Optional[str] = None) -> Optional[Path]:
        if not relative_name:
            return None
        target = (self.dir_path / relative_name).resolve()
        field_info = f" for '{field_name}'" if field_name else ""
        if not target.exists():
            raise TemplateValidationError(
                f"Referenced file '{relative_name}'{field_info} not found in template directory '{self.dir_path}'."
            )
        if target.is_dir():
            raise TemplateValidationError(
                f"Referenced path '{relative_name}'{field_info} is a directory; a file is required."
            )
        return target

    def _validate(self) -> None:
        if self.raw_config.get("schema_version") != 1:
            raise TemplateValidationError(
                "Template config missing or invalid required field: 'schema_version' (expected 1)"
            )
        unknown = [k for k in self.raw_config.keys() if k not in ALLOWED_TOP_LEVEL]
        if unknown:
            raise TemplateValidationError(
                f"Unknown template field(s): {', '.join(sorted(unknown))}"
            )
        for section in REQUIRED_SECTIONS:
            if section not in self.raw_config:
                raise TemplateValidationError(f"Template config missing required section: '{section}'")

        direction = self.raw_config.get("direction")
        if direction not in ("rtl", "ltr"):
            raise TemplateValidationError(
                f"Field 'direction' must be 'rtl' or 'ltr', got '{direction}'"
            )

        fonts = self.raw_config.get("fonts")
        if fonts is None or not isinstance(fonts, dict):
            raise TemplateValidationError("Field 'fonts' must be a mapping")
        for font_key in REQUIRED_FONTS:
            if font_key not in fonts or not fonts[font_key] or not isinstance(fonts[font_key], str):
                raise TemplateValidationError(f"Field 'fonts.{font_key}' is required and must be a non-empty string")
        if "latin" in fonts and (not isinstance(fonts["latin"], str) or not fonts["latin"]):
            raise TemplateValidationError("Field 'fonts.latin' must be a non-empty string")

        font_files = self.raw_config.get("font_files")
        if font_files is not None:
            if not isinstance(font_files, dict):
                raise TemplateValidationError("Field 'font_files' must be a mapping")
            for fname, fpath in font_files.items():
                self._resolve_path(fpath, field_name=f"font_files.{fname}")

        colors = self.raw_config.get("colors", {})
        if not isinstance(colors, dict):
            raise TemplateValidationError("Field 'colors' must be a mapping")
        for col_key in REQUIRED_COLORS:
            if col_key not in colors or not colors[col_key]:
                raise TemplateValidationError(f"Field 'colors.{col_key}' is required and must not be empty")
            colors[col_key] = normalize_hex_color(colors[col_key], f"colors.{col_key}")

        if "page" in self.raw_config:
            page = self.raw_config.get("page")
            if page is None or not isinstance(page, dict):
                raise TemplateValidationError("Field 'page' must be a mapping")
            if "size" in page and str(page["size"]) not in PAGE_SIZES:
                raise TemplateValidationError(
                    f"Field 'page.size' must be one of {sorted(PAGE_SIZES)}, got '{page['size']}'"
                )
            size_name = str(page.get("size", "A4"))
            page_w_cm, page_h_cm = PAGE_DIMENSIONS_CM.get(size_name, (21.0, 29.7))
            margin_cm = page.get("margin_cm")
            if margin_cm is not None:
                if not isinstance(margin_cm, dict):
                    raise TemplateValidationError("Field 'page.margin_cm' must be a mapping")
                for side in ("top", "bottom", "left", "right"):
                    if side in margin_cm:
                        margin_cm[side] = require_number(margin_cm[side], f"page.margin_cm.{side}")
                top_m = float(margin_cm.get("top", 2.0))
                bottom_m = float(margin_cm.get("bottom", 2.0))
                left_m = float(margin_cm.get("left", 2.0))
                right_m = float(margin_cm.get("right", 2.0))
                vert = top_m + bottom_m
                horiz = left_m + right_m
                usable_w = page_w_cm - horiz
                usable_h = page_h_cm - vert
                if usable_w < 2.0 or usable_h < 2.0:
                    raise TemplateValidationError(
                        f"Field 'page.margin_cm' leaves no usable content area ({usable_w:.1f}x{usable_h:.1f} cm) for page size '{size_name}'"
                    )
            for num_field in ("font_size_pt", "line_spacing"):
                if num_field in page:
                    page[num_field] = require_number(page[num_field], f"page.{num_field}")
            if "paragraph_align" in page:
                align_val = str(page["paragraph_align"]).strip().lower()
                if align_val == "justify":
                    align_val = "both"
                    page["paragraph_align"] = "both"
                if align_val not in ("start", "both", "left", "right", "center"):
                    raise TemplateValidationError(
                        f"Field 'page.paragraph_align' must be one of ['start', 'both', 'left', 'right', 'center'] "
                        f"(justify is accepted as both), got '{page['paragraph_align']}'"
                    )
            if "space_after_pt" in page:
                page["space_after_pt"] = require_number(page["space_after_pt"], "page.space_after_pt", positive=False, allow_zero=True)

        headings = self.raw_config.get("headings")
        if headings is not None:
            if not isinstance(headings, dict):
                raise TemplateValidationError("Field 'headings' must be a mapping")
            if "badge" in headings and not isinstance(headings["badge"], bool):
                raise TemplateValidationError("Field 'headings.badge' must be a boolean")
            if "extract_number" in headings and not isinstance(headings["extract_number"], bool):
                raise TemplateValidationError("Field 'headings.extract_number' must be a boolean")
            for h in ("h1", "h2", "h3", "h4", "h5", "h6"):
                if h in headings:
                    if not isinstance(headings[h], dict):
                        raise TemplateValidationError(f"Field 'headings.{h}' must be a mapping, got '{headings[h]}'")
                    if "size_pt" in headings[h]:
                        headings[h]["size_pt"] = require_number(headings[h]["size_pt"], f"headings.{h}.size_pt")
                    if "page_break_before" in headings[h] and not isinstance(headings[h]["page_break_before"], bool):
                        raise TemplateValidationError(f"Field 'headings.{h}.page_break_before' must be a boolean")
                    for col_field in ("badge_bg", "badge_fg"):
                        if col_field in headings[h]:
                            cval = str(headings[h][col_field])
                            if not (HEX_COLOR_RE.match(cval) or cval in colors):
                                raise TemplateValidationError(
                                    f"Field 'headings.{h}.{col_field}' must be a valid hex color or palette reference, got '{cval}'"
                                )
                            if HEX_COLOR_RE.match(cval) and cval not in colors:
                                headings[h][col_field] = normalize_hex_color(cval, f"headings.{h}.{col_field}")

        callouts = self.raw_config.get("callouts")
        if callouts is not None:
            if not isinstance(callouts, dict):
                raise TemplateValidationError("Field 'callouts' must be a mapping")
            for cname, cspec in callouts.items():
                if not isinstance(cspec, dict):
                    raise TemplateValidationError(f"Field 'callouts.{cname}' must be a mapping")
                if "classes" in cspec and not isinstance(cspec["classes"], list):
                    raise TemplateValidationError(f"Field 'callouts.{cname}.classes' must be a list")
                for cfield in ("header_bg", "header_fg", "body_bg"):
                    if cfield in cspec:
                        cval = str(cspec[cfield])
                        if not (HEX_COLOR_RE.match(cval) or cval in colors):
                            raise TemplateValidationError(
                                f"Field 'callouts.{cname}.{cfield}' must be a valid hex color or palette reference, got '{cval}'"
                            )

        quotes = self.raw_config.get("quotes")
        if quotes is not None:
            if not isinstance(quotes, dict):
                raise TemplateValidationError("Field 'quotes' must be a mapping")
            if "border_pt" in quotes:
                quotes["border_pt"] = require_number(quotes["border_pt"], "quotes.border_pt")
            if "border_sz" in quotes:
                quotes["border_sz"] = require_number(quotes["border_sz"], "quotes.border_sz", allow_zero=True)
            if "border_side" in quotes:
                bs = quotes["border_side"]
                valid_sides = ("physical_right", "physical_left", "start", "end", "left", "right")
                if bs not in valid_sides:
                    raise TemplateValidationError(
                        f"Field 'quotes.border_side' must be one of {valid_sides}, got '{bs}'"
                    )
            for qfield in ("border_color", "bg"):
                if qfield in quotes:
                    qval = str(quotes[qfield])
                    if not (HEX_COLOR_RE.match(qval) or qval in colors):
                        raise TemplateValidationError(
                            f"Field 'quotes.{qfield}' must be a valid hex color or palette reference, got '{qval}'"
                        )

        tables = self.raw_config.get("tables")
        if tables is not None:
            if not isinstance(tables, dict):
                raise TemplateValidationError("Field 'tables' must be a mapping")
            if "bidi_visual" in tables and not isinstance(tables["bidi_visual"], bool):
                raise TemplateValidationError("Field 'tables.bidi_visual' must be a boolean")
            for tfield in ("header_bg", "header_fg"):
                if tfield in tables:
                    tval = str(tables[tfield])
                    if not (HEX_COLOR_RE.match(tval) or tval in colors):
                        raise TemplateValidationError(
                            f"Field 'tables.{tfield}' must be a valid hex color or palette reference, got '{tval}'"
                        )
                    if HEX_COLOR_RE.match(tval) and tval not in colors:
                        tables[tfield] = normalize_hex_color(tval, f"tables.{tfield}")

        code_block = self.raw_config.get("code_block")
        if code_block is not None:
            if not isinstance(code_block, dict):
                raise TemplateValidationError("Field 'code_block' must be a mapping")
            for cb_num in ("font_size_pt", "line_spacing"):
                if cb_num in code_block:
                    code_block[cb_num] = require_number(code_block[cb_num], f"code_block.{cb_num}")
            if "border_sz" in code_block:
                code_block["border_sz"] = require_number(
                    code_block["border_sz"], "code_block.border_sz", allow_zero=True
                )
            for cb_col in ("bg", "border_color", "color"):
                if cb_col in code_block:
                    cval = str(code_block[cb_col])
                    if not (HEX_COLOR_RE.match(cval) or cval in colors):
                        raise TemplateValidationError(
                            f"Field 'code_block.{cb_col}' must be a valid hex color or palette reference, got '{cval}'"
                        )
                    if HEX_COLOR_RE.match(cval) and cval not in colors:
                        code_block[cb_col] = normalize_hex_color(cval, f"code_block.{cb_col}")

        mermaid = self.raw_config.get("mermaid")
        if mermaid is not None:
            if not isinstance(mermaid, dict):
                raise TemplateValidationError("Field 'mermaid' must be a mapping")
            if "format" in mermaid and str(mermaid["format"]).lower() != "png":
                raise TemplateValidationError(
                    f"Field 'mermaid.format' must be 'png', got '{mermaid['format']}'"
                )
            if "scale" in mermaid:
                mermaid["scale"] = require_number(mermaid["scale"], "mermaid.scale")
            if "max_width_in" in mermaid:
                mermaid["max_width_in"] = require_number(mermaid["max_width_in"], "mermaid.max_width_in")
            for ref_file, field in (
                ("theme_file", "mermaid.theme_file"),
                ("css_file", "mermaid.css_file"),
                ("puppeteer_config", "mermaid.puppeteer_config"),
            ):
                if ref_file in mermaid and mermaid[ref_file]:
                    self._resolve_path(mermaid[ref_file], field_name=field)

        caption = self.raw_config.get("caption")
        if caption is not None:
            if not isinstance(caption, dict):
                raise TemplateValidationError("Field 'caption' must be a mapping")
            if "size_pt" in caption:
                caption["size_pt"] = require_number(caption["size_pt"], "caption.size_pt", positive=True)

        custom_styles = self.raw_config.get("custom_styles")
        if custom_styles is not None:
            if not isinstance(custom_styles, dict):
                raise TemplateValidationError("Field 'custom_styles' must be a mapping")
            if "strict" in custom_styles and not isinstance(custom_styles["strict"], bool):
                raise TemplateValidationError("Field 'custom_styles.strict' must be a boolean")
            if "mappings" in custom_styles:
                extra = [k for k in custom_styles if k not in ("strict", "mappings")]
                if extra:
                    raise TemplateValidationError(
                        "Field 'custom_styles' cannot mix 'mappings' with direct style keys "
                        f"({', '.join(sorted(str(k) for k in extra))}). Use one form."
                    )
                mappings = custom_styles.get("mappings")
            else:
                mappings = custom_styles
            if not isinstance(mappings, dict):
                raise TemplateValidationError("Field 'custom_styles.mappings' must be a mapping")
            callout_roles = {
                str(k).strip().lower()
                for k in (self.raw_config.get("callouts") or {})
                if isinstance(k, str)
            }
            seen_keys: dict[str, str] = {}
            for s_name, s_role in mappings.items():
                if s_name == "strict":
                    continue
                if not isinstance(s_name, str) or not s_name.strip():
                    raise TemplateValidationError("Custom style keys must be non-empty strings")
                if not isinstance(s_role, str):
                    raise TemplateValidationError(
                        f"Custom style mapping for '{s_name}' must be a string role name, got '{s_role}'"
                    )
                key = s_name.strip().lower()
                if key in seen_keys:
                    raise TemplateValidationError(
                        f"Custom style '{s_name}' collides with '{seen_keys[key]}' after normalization"
                    )
                seen_keys[key] = s_name
                role = s_role.strip().lower()
                if role not in callout_roles:
                    raise TemplateValidationError(
                        f"Custom style '{s_name}' maps to unknown callout role '{s_role}'. "
                        f"Define that role under 'callouts' first."
                    )

        custom_shell = self.raw_config.get("shell")
        if custom_shell:
            self._resolve_path(custom_shell, field_name="shell")

    @classmethod
    def find_template_dir(cls, name_or_path: str | Path) -> Path:
        target = Path(name_or_path)
        if target.is_dir() and (target / "config.yaml").exists():
            return target

        # Prefer a checkout/cwd theme so local edits to templates/ take effect;
        # fall back to the copy shipped inside the installed package (wheels).
        candidate_roots = [
            Path("templates"),
            PROJECT_ROOT / "templates",
            PACKAGE_DIR / "templates",
        ]
        for root in candidate_roots:
            candidate = (root / name_or_path).resolve()
            if candidate.is_dir() and (candidate / "config.yaml").exists():
                return candidate

        raise TemplateNotFoundError(f"Template '{name_or_path}' not found.")

    @classmethod
    def load(cls, name_or_path: str | Path) -> "Template":
        tmpl_dir = cls.find_template_dir(name_or_path)
        config_file = tmpl_dir / "config.yaml"
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            raise TemplateValidationError(f"Failed to parse '{config_file}': {e}") from e

        if not isinstance(data, dict):
            raise TemplateValidationError(f"Template config '{config_file}' must be a YAML dictionary.")

        return cls(data, tmpl_dir)

    @classmethod
    def list_available(cls) -> list[str]:
        names = []
        candidate_roots = [
            Path("templates"),
            PROJECT_ROOT / "templates",
            PACKAGE_DIR / "templates",
        ]
        for root in candidate_roots:
            if root.is_dir():
                for sub in root.iterdir():
                    if sub.is_dir() and (sub / "config.yaml").exists():
                        if sub.name not in names:
                            names.append(sub.name)
        return names
