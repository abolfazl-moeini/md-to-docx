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

    Relative paths are resolved ONLY against the Markdown directory (base_dir),
    never falling back to arbitrary filenames or the process cwd (FINAL-06).
    Remote http(s)/data URIs and unsupported schemes are rejected.
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
    if scheme and scheme != "file":
        raise ConvertError(f"Unsupported image scheme '{scheme}:' in source '{src}'")

    if scheme == "file":
        path_str = unquote(parsed.path)
        if parsed.netloc and parsed.netloc not in ("localhost", "127.0.0.1"):
            path_str = f"//{parsed.netloc}{path_str}"
        candidate = Path(path_str)
        if candidate.is_file():
            return candidate.resolve()
        if candidate.is_dir():
            raise ConvertError(f"Image source '{src}' is a directory, not a regular file.")
        raise ConvertError(f"Image not found: '{src}'")

    # If raw path exists directly on filesystem as literal (e.g. generated Mermaid files)
    raw_path = Path(raw)
    if raw_path.is_absolute() and raw_path.is_file():
        return raw_path.resolve()
    if base_dir is not None:
        raw_from_base = (Path(base_dir) / raw).resolve()
        if raw_from_base.is_file():
            return raw_from_base

    # Decode percent-encoding once for URI targets
    decoded = decode_src(raw)
    direct = Path(decoded)
    if direct.is_absolute():
        if direct.is_file():
            return direct.resolve()
        if direct.is_dir():
            raise ConvertError(f"Image path '{direct}' is a directory, not a regular file.")
        raise ConvertError(f"Image not found: '{direct}'")

    if base_dir is not None:
        base = Path(base_dir)
        from_base = (base / decoded).resolve()
        if from_base.is_file():
            return from_base
        if from_base.is_dir():
            raise ConvertError(f"Image path '{from_base}' is a directory, not a regular file.")
        raise ConvertError(f"Image not found: '{decoded}' (resolved relative to '{base_dir}')")

    if direct.is_file():
        return direct.resolve()

    raise ConvertError(f"Image not found: '{decoded}'")
