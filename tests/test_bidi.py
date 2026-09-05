import pytest
from md_to_docx.bidi import (
    is_pure_persian,
    is_pure_latin,
    contains_persian,
    split_bidi_runs,
    ScriptType,
)

def test_pure_persian():
    text = "پایگاه‌های دادهٔ سیستمی"
    assert is_pure_persian(text) is True
    assert is_pure_latin(text) is False
    assert contains_persian(text) is True

def test_pure_latin():
    text = "SQL Server Database Engine 2024"
    assert is_pure_latin(text) is True
    assert is_pure_persian(text) is False
    assert contains_persian(text) is False

def test_mixed_bidi_split():
    text = "Clientها به Database Engine متصل می‌شوند."
    runs = split_bidi_runs(text)
    # Each item is (text_chunk, script_type)
    assert len(runs) >= 3
    # Check that "Client" is Latin
    assert any(chunk == "Client" and script == ScriptType.LATIN for chunk, script in runs)
    # Check that Persian parts are labeled PERSIAN
    assert any("به" in chunk and script == ScriptType.PERSIAN for chunk, script in runs)
    assert any(chunk == "Database Engine" and script == ScriptType.LATIN for chunk, script in runs)

def test_latin_digits_in_persian_sentence():
    text = "نسخهٔ 2024 منتشر شد."
    runs = split_bidi_runs(text)
    # Latin digits '2024' should not be forced into Persian RTL run
    digit_runs = [r for r in runs if "2024" in r[0]]
    assert len(digit_runs) == 1
    assert digit_runs[0][1] in (ScriptType.LATIN, ScriptType.NEUTRAL)
