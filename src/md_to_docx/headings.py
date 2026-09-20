"""Heading parsing and extraction for Persian / bilingual headings."""

import re
from dataclasses import dataclass
from typing import Optional

# Regex matching numbers (Latin digits, Persian digits ۰-۹, Arabic-Indic digits ٠-٩) separated by . or -
# Accepts optional trailing dot/dash separator before the space (e.g. "۱. عنوان" or "1. Introduction")
HEADING_NUMBER_RE = re.compile(
    r"^(?P<num>[\d\u06F0-\u06F9\u0660-\u0669]+(?:[.\-][\d\u06F0-\u06F9\u0660-\u0669]+)*)\.?\s+(?P<title>.+)$"
)

HASHES_RE = re.compile(r"^(#{1,6})\s*(.*)$")


HEADING_ID_RE = re.compile(r"\s*\{#(?P<id>[a-zA-Z0-9_\-\.]+)\}\s*$")


@dataclass
class HeadingInfo:
    level: int
    number: Optional[str]
    title: str
    raw_text: str
    heading_id: Optional[str] = None


def parse_heading(text_or_line: str, level: Optional[int] = None) -> HeadingInfo:
    """
    Parse a heading line or text.
    Extracts heading level (from # hashes or provided level argument),
    number prefix (Persian/Latin/Arabic-Indic digits), optional {#id} anchor,
    and remaining title text.
    """
    cleaned = text_or_line.strip()
    detected_level = 1
    
    hash_match = HASHES_RE.match(cleaned)
    if hash_match:
        hashes, remaining = hash_match.groups()
        detected_level = len(hashes)
        content = remaining.strip()
    else:
        content = cleaned

    final_level = level if level is not None else detected_level

    # Check and extract trailing {#id} anchor so it does not leak into visible text (E03)
    id_match = HEADING_ID_RE.search(content)
    if id_match:
        custom_id = id_match.group("id")
        content = content[:id_match.start()].strip()
    else:
        custom_id = None

    num_match = HEADING_NUMBER_RE.match(content)
    if num_match:
        num = num_match.group("num")
        title = num_match.group("title").strip()
    else:
        num = None
        title = content

    return HeadingInfo(
        level=final_level,
        number=num,
        title=title,
        raw_text=text_or_line,
        heading_id=custom_id,
    )
