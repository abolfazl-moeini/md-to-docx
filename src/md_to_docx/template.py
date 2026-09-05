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
        if not target.exists():
            field_info = f" for '{field_name}'" if field_name else ""
            raise TemplateValidationError(
                f"Referenced file '{relative_name}'{field_info} not found in template directory '{self.dir_path}'."
            )
        return target

    def _validate(self) -> None:
        if self.raw_config.get("schema_version") != 1:
            raise TemplateValidationError(
                "Template config missing required field: 'schema_version' (expected 1)"
            )
        for section in REQUIRED_SECTIONS:
            if section not in self.raw_config:
                raise TemplateValidationError(f"Template config missing required section: '{section}'")

        direction = self.raw_config.get("direction")
        if direction not in ("rtl", "ltr"):
            raise TemplateValidationError(
                f"Template config 'direction' must be 'rtl' or 'ltr', got '{direction}'"
            )

        fonts = self.raw_config.get("fonts", {})
        if not isinstance(fonts, dict):
            raise TemplateValidationError("Template config 'fonts' must be a mapping")
        for font_key in REQUIRED_FONTS:
            if font_key not in fonts or not fonts[font_key] or not isinstance(fonts[font_key], str):
                raise TemplateValidationError(f"Template config missing required font: 'fonts.{font_key}'")

        colors = self.raw_config.get("colors", {})
        if not isinstance(colors, dict):
            raise TemplateValidationError("Template config 'colors' must be a mapping")
        for col_key in REQUIRED_COLORS:
            if col_key not in colors or not colors[col_key]:
                raise TemplateValidationError(f"Template config missing required color: 'colors.{col_key}'")
            col_val = str(colors[col_key])
            if not HEX_COLOR_RE.match(col_val):
                raise TemplateValidationError(
                    f"Template config color 'colors.{col_key}' must be a valid hex color, got '{col_val}'"
                )

        page = self.raw_config.get("page")
        if page is not None and isinstance(page, dict):
            margin_cm = page.get("margin_cm")
            if margin_cm is not None:
                if not isinstance(margin_cm, dict):
                    raise TemplateValidationError("Field 'page.margin_cm' must be a mapping")
                for side in ("top", "bottom", "left", "right"):
                    if side in margin_cm:
                        val = margin_cm[side]
                        if not isinstance(val, (int, float)) or val <= 0:
                            raise TemplateValidationError(
                                f"Field 'page.margin_cm.{side}' must be a positive number, got '{val}'"
                            )

        headings = self.raw_config.get("headings")
        if headings is not None and isinstance(headings, dict):
            for h in ("h1", "h2", "h3"):
                if h in headings and isinstance(headings[h], dict):
                    if "size_pt" in headings[h]:
                        sz = headings[h]["size_pt"]
                        if not isinstance(sz, (int, float)) or sz <= 0:
                            raise TemplateValidationError(
                                f"Field 'headings.{h}.size_pt' must be a positive number, got '{sz}'"
                            )

        mermaid = self.raw_config.get("mermaid")
        if mermaid is not None and isinstance(mermaid, dict):
            if "scale" in mermaid:
                sc = mermaid["scale"]
                if not isinstance(sc, (int, float)) or sc <= 0:
                    raise TemplateValidationError(
                        f"Field 'mermaid.scale' must be a positive number, got '{sc}'"
                    )

    @classmethod
    def find_template_dir(cls, name_or_path: str | Path) -> Path:
        target = Path(name_or_path)
        if target.is_dir() and (target / "config.yaml").exists():
            return target

        # Check default template locations
        candidate_roots = [
            Path("templates"),
            PROJECT_ROOT / "templates",
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
        ]
        for root in candidate_roots:
            if root.is_dir():
                for sub in root.iterdir():
                    if sub.is_dir() and (sub / "config.yaml").exists():
                        if sub.name not in names:
                            names.append(sub.name)
        return names
