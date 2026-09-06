import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Tuple

from md_to_docx.template import Template, PROJECT_ROOT


class ConvertError(Exception):
    """Raised when diagram or document conversion fails."""
    pass


class MermaidSyntaxError(ConvertError):
    """Raised when Mermaid syntax in Markdown is malformed (e.g. unclosed fence)."""

    def __init__(self, message: str, line_number: Optional[int] = None):
        super().__init__(message)
        self.line_number = line_number


CAPTION_RE = re.compile(r"^(?:شکل|Figure|Fig\.)\s+.*", re.IGNORECASE)
MERMAID_FENCE_START = re.compile(r"^[ ]{0,3}(?P<fence>`{3,}|~{3,})[ \t]*mermaid[ \t]*$")
# CommonMark allows up to three leading spaces and permits spaces in an info
# string.  Consumers use an empty stripped ``info`` to recognize a closer.
FENCE_LINE = re.compile(r"^[ ]{0,3}(?P<fence>`{3,}|~{3,})(?P<info>[^`~]*?)[ \t]*$")


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
    Extracts mermaid fences that are not nested inside a longer outer fence.
    Supports ```mermaid and ~~~mermaid. Raises MermaidSyntaxError for unclosed fences.
    """
    lines = markdown_text.splitlines()
    blocks: List[MermaidBlock] = []
    idx = 0
    i = 0
    num_lines = len(lines)
    outer_stack: List[Tuple[str, int]] = []

    while i < num_lines:
        fm = FENCE_LINE.match(lines[i])
        if fm:
            fence = fm.group("fence")
            info = (fm.group("info") or "").strip()
            if outer_stack:
                top_ch, top_n = outer_stack[-1]
                if fence[0] == top_ch and len(fence) >= top_n and not info:
                    outer_stack.pop()
                    i += 1
                    continue
                i += 1
                continue
            if info == "mermaid":
                start_line = i
                code_lines: List[str] = []
                i += 1
                while i < num_lines:
                    close_m = FENCE_LINE.match(lines[i])
                    if (
                        close_m
                        and close_m.group("fence")[0] == fence[0]
                        and len(close_m.group("fence")) >= len(fence)
                        and not close_m.group("info")
                    ):
                        break
                    nested = MERMAID_FENCE_START.match(lines[i])
                    if nested and len(nested.group("fence")) <= len(fence):
                        raise MermaidSyntaxError(
                            f"Nested mermaid fence found at line {i + 1} before block at line {start_line + 1} was closed.",
                            line_number=i + 1,
                        )
                    code_lines.append(lines[i])
                    i += 1
                if i >= num_lines:
                    raise MermaidSyntaxError(
                        f"Unclosed mermaid code block starting at line {start_line + 1}.",
                        line_number=start_line + 1,
                    )
                end_line = i
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
                continue
            outer_stack.append((fence[0], len(fence)))
            i += 1
            continue
        i += 1

    if outer_stack:
        raise MermaidSyntaxError("Unclosed code fence in Markdown input.", line_number=num_lines)

    return blocks


MERMAID_TIMEOUT_SECONDS = 60.0


def probe_mermaid_renderer(
    browser_bin: Optional[str] = None,
    template: Optional[Template] = None,
    timeout: float = 30.0,
) -> Tuple[bool, Optional[str]]:
    """
    Actively probes whether the Mermaid renderer (mmdc + Chromium/Puppeteer) is operational.
    Does NOT cache the result. Distinguishes launch, permission, architecture, and sandbox errors.
    Returns (True, None) if operational, or (False, error_reason) on failure.
    """
    mmdc_cmd = _find_mmdc_cmd()
    if mmdc_cmd and not shutil.which(mmdc_cmd[0]) and not Path(mmdc_cmd[0]).is_file():
        return (False, f"Launch error: Mermaid CLI command '{mmdc_cmd[0]}' not found.")

    if browser_bin:
        classified = _classify_browser_binary(browser_bin)
        if classified is not None:
            return (False, classified)
    elif not _iter_browser_candidates():
        return (False, "Launch error: No Chromium/Chrome browser executable found.")

    tmpl = template or Template.load("purple_book")
    with tempfile.TemporaryDirectory(prefix="mermaid_probe_") as probe_dir:
        test_out = Path(probe_dir) / "probe.png"
        try:
            render_mermaid_to_png(
                "graph TD\nA-->B",
                test_out,
                tmpl,
                timeout=timeout,
                browser_bin=browser_bin,
            )
            if test_out.exists() and test_out.stat().st_size > 0:
                return (True, None)
            return (False, "Launch error: Probe diagram output was missing or empty.")
        except ConvertError as e:
            return (False, _classify_launch_message(str(e)))
        except Exception as e:
            return (False, f"Launch error: Unexpected probe failure: {e}")


def _classify_launch_message(message: str) -> str:
    msg = message.lower()
    if "sandbox" in msg:
        return f"Sandbox error: {message}"
    if "permission" in msg or "eacces" in msg:
        return f"Permission error: {message}"
    if "architecture" in msg or "bad cpu" in msg or "exec format" in msg:
        return f"Architecture error: {message}"
    return f"Launch error: {message}"


def _classify_browser_binary(target_browser: str) -> Optional[str]:
    """Returns an error string if the binary cannot be executed, else None."""
    browser_path = Path(target_browser)
    if not browser_path.exists():
        return f"Launch error: Browser binary '{target_browser}' does not exist."
    if os.name != "nt" and not os.access(browser_path, os.X_OK):
        return f"Permission error: Browser binary '{target_browser}' lacks execute permission."

    try:
        ver_proc = subprocess.run(
            [str(browser_path), "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5.0,
            check=False,
        )
        if ver_proc.returncode != 0:
            err = (ver_proc.stderr or ver_proc.stdout).strip().lower()
            if "bad cpu" in err or "exec format" in err or "architecture" in err:
                return (
                    f"Architecture error: Browser binary '{target_browser}' "
                    f"is incompatible with host architecture: {err}"
                )
            if "permission" in err or "eacces" in err:
                return f"Permission error: Permission denied launching '{target_browser}': {err}"
            if "sandbox" in err:
                return f"Sandbox error: Browser sandbox error launching '{target_browser}': {err}"
            return (
                f"Launch error: Browser binary '{target_browser}' "
                f"exited with code {ver_proc.returncode}: {err}"
            )
    except PermissionError as e:
        return f"Permission error: Permission denied executing '{target_browser}': {e}"
    except OSError as e:
        err_str = str(e).lower()
        if "exec format" in err_str or "bad cpu" in err_str:
            return f"Architecture error: Binary '{target_browser}' architecture mismatch: {e}"
        return f"Launch error: Failed to execute '{target_browser}': {e}"
    except subprocess.TimeoutExpired:
        return f"Launch error: Browser --version timed out at '{target_browser}'."
    return None


_BROWSER_FULL_NAMES = {
    "Google Chrome for Testing",
    "chrome",
    "chrome.exe",
    "chromium",
    "Chromium",
}
_BROWSER_FALLBACK_NAMES = {
    "chrome-headless-shell",
    "headless_shell",
}
_SKIP_BROWSER_DIR_PARTS = {"Helpers", "Frameworks"}


def _puppeteer_cache_dirs() -> List[Path]:
    dirs: List[Path] = []
    env_dir = os.environ.get("PUPPETEER_CACHE_DIR")
    if env_dir:
        dirs.append(Path(env_dir))
    dirs.extend(
        [
            Path.home() / ".cache" / "puppeteer",
            Path.home() / "Library" / "Caches" / "puppeteer",
            PROJECT_ROOT / "node_modules" / ".cache" / "puppeteer",
        ]
    )
    seen: set[str] = set()
    unique: List[Path] = []
    for d in dirs:
        key = str(d)
        if key not in seen:
            seen.add(key)
            unique.append(d)
    return unique


def _chrome_version_key(path: Path) -> Tuple[int, int, int, int]:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)\.(\d+)", str(path))
    if match:
        return tuple(int(g) for g in match.groups())  # type: ignore[return-value]
    return (0, 0, 0, 0)


def _is_usable_browser_binary(path: Path, names: Iterable[str]) -> bool:
    if path.name not in names or not path.is_file():
        return False
    if any(part in _SKIP_BROWSER_DIR_PARTS for part in path.parts):
        return False
    if os.name != "nt" and not os.access(path, os.X_OK):
        return False
    return True


def _browsers_in_puppeteer_cache() -> List[str]:
    """Puppeteer-managed Chrome, newest full browser first, headless-shell last."""
    found_full: List[Path] = []
    found_fallback: List[Path] = []
    names = tuple(_BROWSER_FULL_NAMES | _BROWSER_FALLBACK_NAMES)
    for cdir in _puppeteer_cache_dirs():
        if not cdir.is_dir():
            continue
        for name in names:
            for candidate in cdir.rglob(name):
                if _is_usable_browser_binary(candidate, _BROWSER_FULL_NAMES):
                    found_full.append(candidate)
                elif _is_usable_browser_binary(candidate, _BROWSER_FALLBACK_NAMES):
                    found_fallback.append(candidate)

    found_full.sort(key=_chrome_version_key, reverse=True)
    found_fallback.sort(key=_chrome_version_key, reverse=True)
    result: List[str] = []
    seen: set[str] = set()
    for path in found_full + found_fallback:
        resolved = str(path.resolve())
        if resolved not in seen:
            seen.add(resolved)
            result.append(resolved)
    return result


def _system_browser_candidates() -> List[str]:
    return [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        str(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        str(Path.home() / "Applications/Chromium.app/Contents/MacOS/Chromium"),
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/snap/bin/chromium",
    ]


def _iter_browser_candidates() -> List[str]:
    """Preference order: env override, Puppeteer cache, PATH, then system apps."""
    seen: set[str] = set()
    ordered: List[str] = []

    def add(path_str: Optional[str]) -> None:
        if not path_str:
            return
        path = Path(path_str)
        if not path.is_file():
            return
        key = str(path.resolve())
        if key in seen:
            return
        seen.add(key)
        ordered.append(key)

    add(os.environ.get("PUPPETEER_EXECUTABLE_PATH"))
    for cached in _browsers_in_puppeteer_cache():
        add(cached)
    for bin_name in (
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "chrome",
        "brave-browser",
        "microsoft-edge",
        "msedge",
    ):
        add(shutil.which(bin_name))
    for candidate in _system_browser_candidates():
        add(candidate)
    return ordered


def _find_browser_executable() -> Optional[str]:
    """Finds a Chromium-family binary, preferring Puppeteer's bundled Chrome over system Chrome."""
    candidates = _iter_browser_candidates()
    return candidates[0] if candidates else None


def _find_mmdc_cmd() -> List[str]:
    """Finds the mmdc executable command as a structured argv list."""
    candidates = [
        PROJECT_ROOT / "node_modules" / ".bin" / "mmdc",
        Path.cwd() / "node_modules" / ".bin" / "mmdc",
    ]
    for local_mmdc in candidates:
        if local_mmdc.is_file() and os.access(local_mmdc, os.X_OK):
            return [str(local_mmdc.resolve())]

    system_mmdc = shutil.which("mmdc")
    if system_mmdc:
        return [system_mmdc]

    if shutil.which("npx"):
        return ["npx", "-y", "@mermaid-js/mermaid-cli"]

    return ["mmdc"]


def _headless_mode_for_browser(browser_bin: Optional[str]):
    """mermaid-cli defaults to headless: 'shell' (chrome-headless-shell). Full Chrome needs new headless."""
    if browser_bin and Path(browser_bin).name in _BROWSER_FALLBACK_NAMES:
        return "shell"
    return True


def _get_puppeteer_config_path(template: Template, work_dir: Path, browser_bin: Optional[str] = None) -> Path:
    """Writes a runtime puppeteer config that includes --no-sandbox flags and explicit executablePath."""
    cfg: dict = {
        "args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ],
        "headless": _headless_mode_for_browser(browser_bin),
    }
    if browser_bin:
        cfg["executablePath"] = str(browser_bin)

    if template.mermaid_puppeteer_path and template.mermaid_puppeteer_path.exists():
        try:
            existing = json.loads(template.mermaid_puppeteer_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
        if isinstance(existing, dict):
            user_args = list(existing.get("args") or [])
            merged = dict(existing)
            for flag in ("--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"):
                if flag not in user_args:
                    user_args.append(flag)
            merged["args"] = user_args
            merged["headless"] = _headless_mode_for_browser(browser_bin)
            if browser_bin:
                merged["executablePath"] = str(browser_bin)
            cfg = merged

    runtime_cfg = work_dir / "puppeteer-runtime.json"
    runtime_cfg.write_text(json.dumps(cfg), encoding="utf-8")
    return runtime_cfg


def _effective_mermaid_css(template: Template, work_dir: Path) -> Optional[Path]:
    """Builds CSS with an absolute @font-face so Chromium can load the configured font."""
    body_font = template.fonts.get("body", "Vazirmatn")
    font_file = None
    font_rel = template.font_files.get(body_font)
    if font_rel:
        font_file = template.dir_path / font_rel
    if not font_file or not font_file.exists():
        cand = template.dir_path / "fonts" / f"{body_font}-Regular.ttf"
        font_file = cand if cand.exists() else None
    if (not font_file or not font_file.exists()) and body_font == "Vazirmatn":
        vazir = template.dir_path / "fonts" / "Vazirmatn-Regular.ttf"
        font_file = vazir if vazir.exists() else None

    base_css = ""
    if template.mermaid_css_path and template.mermaid_css_path.exists():
        base_css = template.mermaid_css_path.read_text(encoding="utf-8")

    if font_file and font_file.exists():
        font_url = font_file.resolve().as_uri()
        font_face = (
            "@font-face {\n"
            f"  font-family: '{body_font}';\n"
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
        css_text = (
            font_face
            + "\n".join(stripped).strip()
            + f"\nbody, svg, text, .node, .edgeLabel, .label {{ font-family: '{body_font}', Tahoma, sans-serif !important; }}\n"
        )
        out = work_dir / "mermaid-runtime.css"
        out.write_text(css_text, encoding="utf-8")
        return out

    if template.mermaid_css_path and template.mermaid_css_path.exists():
        return template.mermaid_css_path
    return None


_LAUNCH_ERROR_HINTS = (
    "failed to launch",
    "browser process",
    "sandbox",
    "could not find browser",
    "executable doesn't exist",
    "executable does not exist",
    "chrome not found",
    "target closed",
    "econnrefused",
)


def _is_browser_launch_error(message: str) -> bool:
    msg = message.lower()
    return any(hint in msg for hint in _LAUNCH_ERROR_HINTS)


def _run_mmdc(
    mmd_code: str,
    output_path: Path,
    template: Template,
    timeout: float,
    browser_bin: Optional[str],
) -> Path:
    """Single mmdc invocation against one browser binary."""
    mmdc_cmd = _find_mmdc_cmd()
    with tempfile.TemporaryDirectory(prefix="mmdc_work_") as work:
        work_dir = Path(work)
        temp_mmd = work_dir / "diagram.mmd"
        temp_mmd.write_text(mmd_code, encoding="utf-8")

        cmd = (
            list(mmdc_cmd)
            + [
                "-i", str(temp_mmd),
                "-o", str(output_path),
                "-s", str(template.mermaid.get("scale", 3)),
                "-b", "white",
            ]
        )

        if template.mermaid_theme_path and template.mermaid_theme_path.exists():
            cmd.extend(["-c", str(template.mermaid_theme_path)])

        css_path = _effective_mermaid_css(template, work_dir)
        if css_path:
            cmd.extend(["-C", str(css_path)])

        puppeteer_cfg = _get_puppeteer_config_path(template, work_dir, browser_bin=browser_bin)
        cmd.extend(["-p", str(puppeteer_cfg)])

        env = dict(os.environ)
        if browser_bin:
            env["PUPPETEER_EXECUTABLE_PATH"] = browser_bin

        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                env=env,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as e:
            raise ConvertError(f"Mermaid compilation timed out after {timeout} seconds.") from e
        except FileNotFoundError as e:
            raise ConvertError(
                f"Mermaid CLI executable not found: {e}. Run 'npm install' or 'scripts/bootstrap.sh' to install dependencies."
            ) from e

    if proc.returncode != 0:
        err_msg = proc.stderr.strip() or proc.stdout.strip()
        browser_info = browser_bin if browser_bin else "None found"
        raise ConvertError(
            f"Mermaid compilation failed with exit code {proc.returncode}:\n"
            f"{err_msg}\n"
            f"Detected browser executable: {browser_info}\n"
            "Troubleshooting:\n"
            "  1. Ensure Google Chrome or Chromium is installed.\n"
            "  2. Or set PUPPETEER_EXECUTABLE_PATH to your browser binary.\n"
            "  3. Or install Chromium via: npx puppeteer browsers install chrome\n"
            "  4. Run 'npm install' or 'scripts/bootstrap.sh' to set up all dependencies."
        )

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ConvertError("Mermaid compilation produced empty or missing image file.")

    return output_path


def render_mermaid_to_png(
    mmd_code: str,
    output_path: Path,
    template: Template,
    timeout: float = MERMAID_TIMEOUT_SECONDS,
    browser_bin: Optional[str] = None,
) -> Path:
    """
    Renders Mermaid code into a PNG image using mermaid-cli (mmdc).
    Fails explicitly with ConvertError if compilation fails, times out, or produces an empty file.
    When browser_bin is omitted, launch/sandbox failures retry the next discovered browser.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if browser_bin:
        candidates: List[Optional[str]] = [browser_bin]
    else:
        found = _iter_browser_candidates()
        candidates = found if found else [None]

    last_error: Optional[ConvertError] = None
    for candidate in candidates:
        try:
            return _run_mmdc(mmd_code, output_path, template, timeout, candidate)
        except ConvertError as e:
            last_error = e
            if browser_bin or not _is_browser_launch_error(str(e)):
                raise
    if last_error:
        raise last_error
    raise ConvertError("Mermaid compilation failed: no browser candidate succeeded.")


def process_mermaid_blocks(
    markdown_text: str,
    output_dir: Path,
    template: Template,
    render_fn: Optional[Callable[[str, Path, Template], Path]] = None,
    use_relative_paths: bool = False,
    base_dir: Optional[Path] = None,
) -> str:
    """
    Extracts each Mermaid block, compiles it to PNG, and replaces the block
    and its following caption with a pandoc Div container.

    Lifecycle and API Contract:
    - The caller owns `output_dir` and is responsible for its retention or cleanup.
    - Each diagram is persisted as 'diagram_{index:03d}.png' in `output_dir`.
    - When `use_relative_paths=True` and `base_dir` is provided, relative POSIX
      paths are written into Markdown; otherwise absolute POSIX paths are used.
    - Callers requiring isolated, concurrency-safe execution across parallel runs
      should provide distinct output directories (e.g. staging directories).
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

        if use_relative_paths and base_dir:
            try:
                img_ref = Path(os.path.relpath(img_path, base_dir)).as_posix()
            except ValueError:
                img_ref = img_path.as_posix()
        else:
            img_ref = img_path.as_posix()

        escaped_caption = (blk.caption or "").replace('"', '\\"')
        caption_attr = f' caption="{escaped_caption}"' if blk.caption else ""

        replacement = [
            f"::: {{.mermaid-figure{caption_attr}}}",
            f"![]({img_ref})",
            ":::",
        ]

        # Determine lines to replace: from start_line to end_line (or caption_line)
        end_replace = blk.caption_line if blk.caption_line is not None else blk.end_line
        lines[blk.start_line : end_replace + 1] = replacement

    ending = "\n" if markdown_text.endswith("\n") else ""
    return "\n".join(lines) + ending


def _codeblock_language(block: dict) -> Optional[str]:
    c = block.get("c")
    if not isinstance(c, list) or not c:
        return None
    attr = c[0]
    classes = attr[1] if isinstance(attr, list) and len(attr) > 1 else []
    return classes[0] if classes else None


def process_mermaid_ast(
    ast_dict: dict,
    output_dir: Path,
    template: Template,
    render_fn: Optional[Callable[[str, Path, Template], Path]] = None,
) -> int:
    """
    Replace Pandoc CodeBlock nodes with class mermaid by rendered PNG Image nodes.
    Caption is taken from the following Para/Plain that matches CAPTION_RE.
    Returns the number of diagrams written.
    """
    render = render_fn or render_mermaid_to_png
    output_dir.mkdir(parents=True, exist_ok=True)
    counter = {"n": 0}

    def consume_caption(blocks: list, idx: int) -> Optional[str]:
        j = idx + 1
        while j < len(blocks):
            nxt = blocks[j]
            if nxt.get("t") in ("Para", "Plain"):
                text = ""
                for inl in nxt.get("c") or []:
                    if isinstance(inl, dict) and inl.get("t") == "Str":
                        text += str(inl.get("c", ""))
                    elif isinstance(inl, dict) and inl.get("t") in ("Space", "SoftBreak"):
                        text += " "
                text = text.strip()
                if CAPTION_RE.match(text):
                    blocks.pop(j)
                    return text
                return None
            if nxt.get("t") is None:
                j += 1
                continue
            return None
        return None

    def walk(blocks: list) -> None:
        i = 0
        while i < len(blocks):
            b = blocks[i]
            t = b.get("t")
            c = b.get("c")
            if t == "CodeBlock" and _codeblock_language(b) == "mermaid":
                code = c[1] if isinstance(c, list) and len(c) > 1 else ""
                counter["n"] += 1
                img_path = output_dir / f"diagram_{counter['n']:03d}.png"
                render(code, img_path, template)
                caption = consume_caption(blocks, i)
                kvs = [["caption", caption]] if caption else []
                img_node = {
                    "t": "Image",
                    "c": [["", [], []], [], [str(img_path), ""]],
                }
                blocks[i] = {
                    "t": "Div",
                    "c": [
                        ["", ["mermaid-figure"], kvs],
                        [{"t": "Para", "c": [img_node]}],
                    ],
                }
                i += 1
                continue
            if t == "Div" and isinstance(c, list) and len(c) > 1 and isinstance(c[1], list):
                walk(c[1])
            elif t == "BlockQuote" and isinstance(c, list):
                walk(c)
            elif t in ("BulletList",) and isinstance(c, list):
                for item in c:
                    if isinstance(item, list):
                        walk(item)
            elif t == "OrderedList" and isinstance(c, list) and len(c) > 1 and isinstance(c[1], list):
                for item in c[1]:
                    if isinstance(item, list):
                        walk(item)
            elif t == "Note" and isinstance(c, list):
                walk(c)
            i += 1

    walk(ast_dict.get("blocks") or [])
    return counter["n"]
