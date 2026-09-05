"""Bidi text classification and script segmentation."""

import re
from enum import Enum
from typing import List, Tuple


class ScriptType(str, Enum):
    PERSIAN = "persian"
    LATIN = "latin"
    NEUTRAL = "neutral"


PERSIAN_CHARS = r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\u200C\u200D]"
PERSIAN_RE = re.compile(PERSIAN_CHARS)
LATIN_RE = re.compile(r"[a-zA-Z]")
LATIN_DIGITS_RE = re.compile(r"^[0-9]+(?:[.\-][0-9]+)*$")


def contains_persian(text: str) -> bool:
    """Returns True if text contains at least one Persian / Arabic character."""
    return bool(PERSIAN_RE.search(text))


def is_pure_persian(text: str) -> bool:
    """Returns True if text contains Persian characters and NO Latin characters."""
    return contains_persian(text) and not bool(LATIN_RE.search(text))


def is_pure_latin(text: str) -> bool:
    """Returns True if text contains Latin characters and NO Persian characters."""
    return bool(LATIN_RE.search(text)) and not contains_persian(text)


TOKEN_RE = re.compile(
    rf"(?P<latin>[a-zA-Z]+(?:[ \t]+[a-zA-Z]+)*)"
    rf"|(?P<digit>[0-9]+(?:[.\-][0-9]+)*)"
    rf"|(?P<persian>{PERSIAN_CHARS}+)"
    rf"|(?P<neutral>[^\sa-zA-Z0-9\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\u200C\u200D]+|\s+)"
)


def split_bidi_runs(text: str) -> List[Tuple[str, ScriptType]]:
    """
    Splits text into runs of Persian, Latin, and Neutral/Digit chunks.
    Keeps Latin phrases intact and prevents Latin digits from being absorbed into RTL runs.
    """
    if not text:
        return []

    tokens: List[Tuple[str, ScriptType]] = []
    for m in TOKEN_RE.finditer(text):
        if m.group("latin"):
            tokens.append((m.group("latin"), ScriptType.LATIN))
        elif m.group("digit"):
            tokens.append((m.group("digit"), ScriptType.NEUTRAL))
        elif m.group("persian"):
            tokens.append((m.group("persian"), ScriptType.PERSIAN))
        elif m.group("neutral"):
            tokens.append((m.group("neutral"), ScriptType.NEUTRAL))

    if not tokens:
        return [(text, ScriptType.NEUTRAL)]

    # Pass 2: Merge adjacent tokens where appropriate
    result: List[Tuple[str, ScriptType]] = []
    for tok_text, tok_script in tokens:
        if not result:
            result.append((tok_text, tok_script))
            continue

        prev_text, prev_script = result[-1]

        # Merge adjacent same scripts
        if prev_script == tok_script:
            result[-1] = (prev_text + tok_text, prev_script)
            continue

        # If current is neutral (e.g. spaces/punctuation, NOT pure digits)
        is_whitespace_or_punct = bool(re.match(r"^[\s\.,;:!?\(\)\[\]«»\-]+$", tok_text)) and not bool(re.search(r"[0-9]", tok_text))
        
        if tok_script == ScriptType.NEUTRAL and is_whitespace_or_punct:
            # If previous was Persian, merge neutral punctuation/space into Persian
            if prev_script == ScriptType.PERSIAN:
                result[-1] = (prev_text + tok_text, ScriptType.PERSIAN)
                continue

        result.append((tok_text, tok_script))

    # Second pass for neutrals that were at the beginning or before Persian
    cleaned: List[Tuple[str, ScriptType]] = []
    for chunk, script in result:
        if script == ScriptType.NEUTRAL and not bool(re.search(r"[0-9]", chunk)) and cleaned and cleaned[-1][1] == ScriptType.PERSIAN:
            cleaned[-1] = (cleaned[-1][0] + chunk, ScriptType.PERSIAN)
        else:
            cleaned.append((chunk, script))

    return cleaned
