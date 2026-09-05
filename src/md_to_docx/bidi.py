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
    # Parenthesized Latin expressions like (Auth) or (Database Engine)
    r"(?P<paren_latin>\([ \t]*[a-zA-Z0-9_\.\-\/]+(?:[ \t]+[a-zA-Z0-9_\.\-\/]+)*[ \t]*\))"
    # URLs
    r"|(?P<url>https?://[^\s\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+)"
    # POSIX / file paths
    r"|(?P<path>/(?:[a-zA-Z0-9_\.\-]+/)+[a-zA-Z0-9_\.\-]*)"
    # Latin words, identifiers with _ or -, versions like v1.2.3, domain names
    r"|(?P<latin>[a-zA-Z0-9_\.\-\/]*[a-zA-Z][a-zA-Z0-9_\.\-\/]*(?:[ \t]+[a-zA-Z0-9_\.\-\/]*[a-zA-Z][a-zA-Z0-9_\.\-\/]*)*)"
    # Latin digits (e.g. 2024, 1.5, 10-20)
    r"|(?P<digit>[0-9]+(?:[.\-][0-9]+)*)"
    # Persian text & Persian numbers
    rf"|(?P<persian>{PERSIAN_CHARS}+)"
    # Neutral punctuation, whitespace, symbols
    rf"|(?P<neutral>[^\sa-zA-Z0-9\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\u200C\u200D]+|\s+)"
)


def split_bidi_runs(text: str) -> List[Tuple[str, ScriptType]]:
    """
    Splits text into runs of Persian, Latin, and Neutral/Digit chunks.
    Keeps Latin phrases, identifiers, URLs, and parenthesized terms intact,
    and prevents Latin digits from being absorbed into RTL runs.
    """
    if not text:
        return []

    tokens: List[Tuple[str, ScriptType]] = []
    for m in TOKEN_RE.finditer(text):
        if m.group("paren_latin"):
            tokens.append((m.group("paren_latin"), ScriptType.LATIN))
        elif m.group("url"):
            tokens.append((m.group("url"), ScriptType.LATIN))
        elif m.group("path"):
            tokens.append((m.group("path"), ScriptType.LATIN))
        elif m.group("latin"):
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
    i = 0
    num_tokens = len(tokens)

    while i < num_tokens:
        tok_text, tok_script = tokens[i]

        if not result:
            result.append((tok_text, tok_script))
            i += 1
            continue

        prev_text, prev_script = result[-1]

        # Merge adjacent same scripts
        if prev_script == tok_script:
            result[-1] = (prev_text + tok_text, prev_script)
            i += 1
            continue

        # Lookahead token
        next_script = tokens[i + 1][1] if i + 1 < num_tokens else None
        next_text = tokens[i + 1][0] if i + 1 < num_tokens else None

        # Check if current token is neutral punctuation or whitespace
        is_pure_digit = bool(re.search(r"[0-9]", tok_text))
        is_whitespace_or_punct = (
            bool(re.match(r"^[\s\.,;:!?\(\)\[\]«»\-—–/\\_]+$", tok_text)) and not is_pure_digit
        )

        if tok_script == ScriptType.NEUTRAL and is_whitespace_or_punct:
            # If current token is an opening paren followed by Latin, don't merge into preceding Persian
            if tok_text.strip() == "(" and next_script == ScriptType.LATIN:
                result.append((tok_text, tok_script))
                i += 1
                continue

            # If between two Persian runs or preceded by Persian and not followed by Latin
            if prev_script == ScriptType.PERSIAN and next_script != ScriptType.LATIN:
                result[-1] = (prev_text + tok_text, ScriptType.PERSIAN)
                i += 1
                continue

            # If between two Latin runs
            if prev_script == ScriptType.LATIN and next_script == ScriptType.LATIN:
                result[-1] = (prev_text + tok_text, ScriptType.LATIN)
                i += 1
                continue

            # Trailing sentence punctuation in Persian context (e.g. '.' at end of Persian sentence)
            if prev_script == ScriptType.PERSIAN and (next_script is None or next_script == ScriptType.PERSIAN):
                result[-1] = (prev_text + tok_text, ScriptType.PERSIAN)
                i += 1
                continue

        result.append((tok_text, tok_script))
        i += 1

    # Pass 3: Check leading neutrals before Persian (e.g. opening Persian bracket/quote, or space preceding Persian)
    cleaned: List[Tuple[str, ScriptType]] = []
    idx = 0
    while idx < len(result):
        chunk, script = result[idx]
        if (
            script == ScriptType.NEUTRAL
            and not bool(re.search(r"[0-9]", chunk))
            and not (chunk.startswith("(") and chunk.endswith(")"))
            and idx + 1 < len(result)
            and result[idx + 1][1] == ScriptType.PERSIAN
            and chunk.strip() == ""
        ):
            next_text, next_script = result[idx + 1]
            result[idx + 1] = (chunk + next_text, next_script)
            idx += 1
            continue

        if (
            script == ScriptType.NEUTRAL
            and not bool(re.search(r"[0-9]", chunk))
            and cleaned
            and cleaned[-1][1] == ScriptType.PERSIAN
            and not (chunk.startswith("(") and chunk.endswith(")"))
        ):
            cleaned[-1] = (cleaned[-1][0] + chunk, ScriptType.PERSIAN)
        else:
            cleaned.append((chunk, script))
        idx += 1

    return cleaned
