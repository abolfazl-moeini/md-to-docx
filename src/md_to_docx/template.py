"""Template loading and validation for md-to-docx."""

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


class Template:
    """Represents a loaded and validated template."""

    def __init__(self, raw_config: Dict[str, Any], dir_path: Path):
        self.raw_config = raw_config
        self.dir_path = dir_path
        self._validate()

        self.name: str = raw_config.get("name", dir_path.name)
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

        # Resolve paths relative to template directory
        self.mermaid_theme_path: Optional[Path] = self._resolve_path(self.mermaid.get("theme_file"))
        self.mermaid_css_path: Optional[Path] = self._resolve_path(self.mermaid.get("css_file"))
        self.mermaid_puppeteer_path: Optional[Path] = self._resolve_path(self.mermaid.get("puppeteer_config"))
        
        shell_path = self.dir_path / "shell.docx"
        self.shell_docx_path: Optional[Path] = shell_path if shell_path.exists() else None

    def _resolve_path(self, relative_name: Optional[str]) -> Optional[Path]:
        if not relative_name:
            return None
        target = self.dir_path / relative_name
        return target if target.exists() else target

    def _validate(self) -> None:
        if self.raw_config.get("schema_version") != 1:
            raise TemplateValidationError(
                "Template config missing required field: 'schema_version' (expected 1)"
            )
        for section in REQUIRED_SECTIONS:
            if section not in self.raw_config:
                raise TemplateValidationError(f"Template config missing required section: '{section}'")

        fonts = self.raw_config.get("fonts", {})
        if not isinstance(fonts, dict):
            raise TemplateValidationError("Template config 'fonts' must be a mapping")
        for font_key in REQUIRED_FONTS:
            if font_key not in fonts or not fonts[font_key]:
                raise TemplateValidationError(f"Template config missing required font: 'fonts.{font_key}'")

        colors = self.raw_config.get("colors", {})
        if not isinstance(colors, dict):
            raise TemplateValidationError("Template config 'colors' must be a mapping")
        for col_key in REQUIRED_COLORS:
            if col_key not in colors or not colors[col_key]:
                raise TemplateValidationError(f"Template config missing required color: 'colors.{col_key}'")

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
