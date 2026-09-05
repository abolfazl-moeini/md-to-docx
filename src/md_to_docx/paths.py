"""Resolve Markdown/Pandoc image sources to local filesystem paths."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlparse

from md_to_docx.mermaid import ConvertError

_REMOTE_SCHEMES = {"http", "https", "data"}


def _looks_percent_encoded(value: str) -> bool:
    if "%" not in value:
        return False
    i = 0
    while i < len(value):
        if value[i] == "%":
            hexpart = value[i + 1 : i + 3]
            if len(hexpart) != 2 or any(c not in "0123456789abcdefABCDEF" for c in hexpart):
                return False
            i += 3
            continue
        i += 1
    return True


def decode_src(src: str) -> str:
    """Decode a single layer of percent-encoding when the value looks encoded."""
    if _looks_percent_encoded(src):
        return unquote(src)
    return src


def resolve_image_source(src: str, base_dir: Path | None = None) -> Path:
    """
    Resolve a Pandoc Image target to a local file.

    Relative paths are resolved only against the Markdown file directory (base_dir),
    never against the process cwd. Remote http(s)/data URIs are rejected.
    """
    raw = (src or "").strip()
    if not raw:
        raise ConvertError("Image source is empty.")

    parsed = urlparse(raw)
    scheme = (parsed.scheme or "").lower()
    if scheme in _REMOTE_SCHEMES:
        raise ConvertError(
            f"Remote images are not supported in v1 ({scheme}:). "
            f"Download the file and reference a local path. Source: '{src}'"
        )

    if scheme == "file":
        path_str = unquote(parsed.path)
        if parsed.netloc and parsed.netloc not in ("localhost", "127.0.0.1"):
            path_str = f"//{parsed.netloc}{path_str}"
        candidate = Path(path_str)
        if candidate.exists():
            return candidate.resolve()
        raise ConvertError(f"Image not found: '{src}'")

    decoded = decode_src(raw)
    direct = Path(decoded)
    if direct.is_absolute():
        if direct.is_file():
            return direct.resolve()
        raise ConvertError(f"Image not found: '{direct}'")

    if base_dir is not None:
        base = Path(base_dir)
        from_base = (base / decoded).resolve()
        if from_base.is_file():
            return from_base
        by_name = (base / Path(decoded).name).resolve()
        if by_name.is_file():
            return by_name

    # Explicit relative paths with a directory component (never a bare cwd filename)
    rel = Path(decoded)
    if not rel.is_absolute() and len(rel.parts) > 1 and rel.is_file():
        return rel.resolve()

    raise ConvertError(f"Image not found: '{decoded}' (resolved relative to '{base_dir}')")
