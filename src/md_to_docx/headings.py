"""Heading parsing and extraction for Persian / bilingual headings."""

import re
from dataclasses import dataclass
from typing import Optional

# Regex matching numbers (Latin digits, Persian digits ۰-۹, Arabic-Indic digits ٠-٩) separated by . or -
HEADING_NUMBER_RE = re.compile(
    r"^(?P<num>[\d\u06F0-\u06F9\u0660-\u0669]+(?:[.\-][\d\u06F0-\u06F9\u0660-\u0669]+)*)\s+(?P<title>.+)$"
)

HASHES_RE = re.compile(r"^(#{1,6})\s*(.*)$")


@dataclass
class HeadingInfo:
    level: int
    number: Optional[str]
    title: str
    raw_text: str


def parse_heading(text_or_line: str, level: Optional[int] = None) -> HeadingInfo:
    """
    Parse a heading line or text.
    Extracts heading level (from # hashes or provided level argument),
    number prefix (Persian/Latin/Arabic-Indic digits), and remaining title text.
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
        raw_text=text_or_line
    )
