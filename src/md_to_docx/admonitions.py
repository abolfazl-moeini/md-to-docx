"""Preprocess admonition / callout blocks in Markdown for pandoc fenced_divs."""

import re
from typing import Dict, Optional

from md_to_docx.mermaid import ConvertError, FENCE_LINE

# Matches lines like: ::: note نکتهٔ DBA or ::: warning
ADMONITION_OPEN_RE = re.compile(
    r"^:::[\t ]+(?P<cls>note|warning|tip|info|danger)(?:[\t ]+(?P<title>.+?))?\s*$"
)

# Matches GFM callout syntax: > [!NOTE] Optional title
GFM_CALLOUT_RE = re.compile(
    r"^>[\t ]*\[!(?P<type>NOTE|WARNING|TIP|IMPORTANT|CAUTION|DANGER|INFO)\](?:[\t ]+(?P<title>.+?))?\s*$",
    re.IGNORECASE,
)

GFM_CLASS_MAP = {
    "note": "note",
    "tip": "note",
    "info": "note",
    "warning": "warning",
    "caution": "warning",
    "important": "warning",
    "danger": "warning",
}

DEFAULT_TITLES = {
    "note": "نکته",
    "warning": "هشدار",
    "tip": "نکته",
    "info": "اطلاعات",
    "danger": "خطر",
}


def preprocess_admonitions(
    markdown_text: str,
    default_titles: Optional[Dict[str, str]] = None
) -> str:
    """
    Transforms `::: note [title]` and GFM `> [!NOTE] [title]` into
    `::: {.note title="[title]"}` so pandoc produces a Div with class and title attribute.

    Code fences (backtick/tilde) are skipped so literal `::: note` inside a code block
    is left unchanged.
    """
    titles = dict(DEFAULT_TITLES)
    if default_titles:
        titles.update(default_titles)

    lines = markdown_text.splitlines()
    transformed_lines = []
    i = 0
    num_lines = len(lines)
    fence_stack: list[tuple[str, int]] = []

    while i < num_lines:
        line = lines[i]
        fm = FENCE_LINE.match(line)
        if fm:
            fence = fm.group("fence")
            info = (fm.group("info") or "").strip()
            if fence_stack:
                top_ch, top_n = fence_stack[-1]
                if fence[0] == top_ch and len(fence) >= top_n and not info:
                    fence_stack.pop()
                transformed_lines.append(line)
                i += 1
                continue
            fence_stack.append((fence[0], len(fence)))
            transformed_lines.append(line)
            i += 1
            continue

        if fence_stack:
            transformed_lines.append(line)
            i += 1
            continue

        gfm_match = GFM_CALLOUT_RE.match(line)
        if gfm_match:
            raw_type = gfm_match.group("type").lower()
            cls = GFM_CLASS_MAP.get(raw_type, raw_type)
            raw_title = gfm_match.group("title")
            title = raw_title.strip() if raw_title else titles.get(cls, cls.capitalize())
            escaped_title = title.replace('"', '\\"')

            callout_body: list[str] = []
            i += 1
            while i < num_lines and lines[i].startswith(">"):
                cleaned_line = re.sub(r"^>[\t ]?", "", lines[i])
                callout_body.append(cleaned_line)
                i += 1

            transformed_lines.append(f'::: {{.{cls} title="{escaped_title}"}}')
            transformed_lines.extend(callout_body)
            transformed_lines.append(":::")
            continue

        match = ADMONITION_OPEN_RE.match(line)
        if match:
            cls = match.group("cls")
            raw_title = match.group("title")
            title = raw_title.strip() if raw_title else titles.get(cls, cls)
            escaped_title = title.replace('"', '\\"')
            transformed_lines.append(f'::: {{.{cls} title="{escaped_title}"}}')
        else:
            transformed_lines.append(line)
        i += 1

    if fence_stack:
        raise ConvertError("Unclosed code fence in Markdown input.")

    ending = "\n" if markdown_text.endswith("\n") else ""
    return "\n".join(transformed_lines) + ending
