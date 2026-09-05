"""Mermaid diagram block extraction, rendering via mermaid-cli, and caption binding."""

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from md_to_docx.template import Template, PROJECT_ROOT


class ConvertError(Exception):
    """Raised when diagram or document conversion fails."""
    pass


CAPTION_RE = re.compile(r"^(?:شکل|Figure|Fig\.)\s+.*", re.IGNORECASE)
MERMAID_FENCE_START = re.compile(r"^```mermaid\s*$")
FENCE_END = re.compile(r"^```\s*$")


@dataclass
class MermaidBlock:
    index: int
    code: str
    caption: Optional[str]
    start_line: int
    end_line: int
    caption_line: Optional[int] = None


def extract_mermaid_blocks(markdown_text: str) -> List[MermaidBlock]:
    """
    Extracts all mermaid code blocks and any immediately following caption line.
    """
    lines = markdown_text.splitlines()
    blocks: List[MermaidBlock] = []
    idx = 0
    i = 0
    num_lines = len(lines)

    while i < num_lines:
        line = lines[i]
        if MERMAID_FENCE_START.match(line):
            start_line = i
            code_lines = []
            i += 1
            while i < num_lines and not FENCE_END.match(lines[i]):
                code_lines.append(lines[i])
                i += 1
            end_line = i  # Closing fence line

            # Check immediately following lines for caption (skipping at most empty lines)
            caption = None
            caption_line = None
            next_line_idx = end_line + 1
            while next_line_idx < num_lines and not lines[next_line_idx].strip():
                next_line_idx += 1

            if next_line_idx < num_lines:
                candidate = lines[next_line_idx].strip()
                if CAPTION_RE.match(candidate):
                    caption = candidate
                    caption_line = next_line_idx

            blocks.append(
                MermaidBlock(
                    index=idx,
                    code="\n".join(code_lines),
                    caption=caption,
                    start_line=start_line,
                    end_line=end_line,
                    caption_line=caption_line,
                )
            )
            idx += 1
        i += 1

    return blocks


def _find_mmdc_binary() -> str:
    """Finds the mmdc executable in local node_modules or system PATH."""
    candidates = [
        PROJECT_ROOT / "node_modules" / ".bin" / "mmdc",
        Path.cwd() / "node_modules" / ".bin" / "mmdc",
    ]
    for local_mmdc in candidates:
        if local_mmdc.exists():
            return str(local_mmdc.resolve())

    system_mmdc = shutil.which("mmdc")
    if system_mmdc:
        return system_mmdc

    if shutil.which("npx"):
        return "npx -y @mermaid-js/mermaid-cli"

    return "mmdc"


def _effective_mermaid_css(template: Template, work_dir: Path) -> Optional[Path]:
    """Builds CSS with an absolute @font-face so Chromium can load Vazirmatn."""
    font_file = template.dir_path / "fonts" / "Vazirmatn-Regular.ttf"
    base_css = ""
    if template.mermaid_css_path and template.mermaid_css_path.exists():
        base_css = template.mermaid_css_path.read_text(encoding="utf-8")

    if font_file.exists():
        font_url = font_file.resolve().as_uri()
        font_face = (
            "@font-face {\n"
            "  font-family: 'Vazirmatn';\n"
            f"  src: url('{font_url}') format('truetype');\n"
            "  font-weight: normal;\n"
            "  font-style: normal;\n"
            "}\n"
        )
        # Drop the relative @font-face from the template CSS; Chromium cannot resolve it.
        stripped = []
        skip = False
        for line in base_css.splitlines():
            if "@font-face" in line:
                skip = True
            if skip:
                if "}" in line:
                    skip = False
                continue
            stripped.append(line)
        css_text = font_face + "\n".join(stripped).strip() + "\n"
        out = work_dir / "mermaid-runtime.css"
        out.write_text(css_text, encoding="utf-8")
        return out

    if template.mermaid_css_path and template.mermaid_css_path.exists():
        return template.mermaid_css_path
    return None


def render_mermaid_to_png(mmd_code: str, output_path: Path, template: Template) -> Path:
    """
    Renders Mermaid code into a PNG image using mermaid-cli (mmdc).
    Fails explicitly with ConvertError if compilation fails or produces an empty file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_mmd = output_path.with_suffix(".mmd")
    temp_mmd.write_text(mmd_code, encoding="utf-8")

    mmdc_cmd = _find_mmdc_binary()
    cmd = (
        mmdc_cmd.split()
        + [
            "-i", str(temp_mmd),
            "-o", str(output_path),
            "-s", str(template.mermaid.get("scale", 3)),
            "-b", "white",
        ]
    )

    if template.mermaid_theme_path and template.mermaid_theme_path.exists():
        cmd.extend(["-c", str(template.mermaid_theme_path)])

    css_path = _effective_mermaid_css(template, output_path.parent)
    if css_path:
        cmd.extend(["-C", str(css_path)])
    if template.mermaid_puppeteer_path and template.mermaid_puppeteer_path.exists():
        cmd.extend(["-p", str(template.mermaid_puppeteer_path)])

    env = dict(os.environ)
    if "PUPPETEER_EXECUTABLE_PATH" not in env:
        candidate_browsers = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ]
        for b in candidate_browsers:
            if Path(b).exists():
                env["PUPPETEER_EXECUTABLE_PATH"] = b
                break

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            env=env,
        )
    except FileNotFoundError as e:
        raise ConvertError(
            f"Mermaid CLI (mmdc) not found: {e}. Run 'npm install' to install @mermaid-js/mermaid-cli."
        ) from e

    if proc.returncode != 0:
        err_msg = proc.stderr.strip() or proc.stdout.strip()
        raise ConvertError(f"Mermaid compilation failed with exit code {proc.returncode}:\n{err_msg}")

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ConvertError("Mermaid compilation produced empty or missing image file.")

    return output_path


def process_mermaid_blocks(
    markdown_text: str,
    output_dir: Path,
    template: Template,
    render_fn: Optional[Callable[[str, Path, Template], Path]] = None,
) -> str:
    """
    Extracts each Mermaid block, compiles it to PNG, and replaces the block
    and its following caption with a pandoc Div container.
    """
    blocks = extract_mermaid_blocks(markdown_text)
    if not blocks:
        return markdown_text

    render = render_fn or render_mermaid_to_png
    lines = markdown_text.splitlines()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process in reverse order so line numbers remain valid
    for blk in reversed(blocks):
        img_name = f"diagram_{blk.index + 1:03d}.png"
        img_path = output_dir / img_name
        render(blk.code, img_path, template)

        escaped_caption = (blk.caption or "").replace('"', '\\"')
        caption_attr = f' caption="{escaped_caption}"' if blk.caption else ""

        replacement = [
            f"::: {{.mermaid-figure{caption_attr}}}",
            f"![]({img_path.as_posix()})",
            ":::",
        ]

        # Determine lines to replace: from start_line to end_line (or caption_line)
        end_replace = blk.caption_line if blk.caption_line is not None else blk.end_line
        lines[blk.start_line : end_replace + 1] = replacement

    ending = "\n" if markdown_text.endswith("\n") else ""
    return "\n".join(lines) + ending
