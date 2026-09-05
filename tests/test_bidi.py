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


def test_parentheses_around_latin_in_persian():
    text = "احراز هویت (Auth) و کنترل دسترسی"
    runs = split_bidi_runs(text)
    # (Auth) must be treated as Latin / LTR so parentheses do not flip
    auth_runs = [r for r in runs if "(Auth)" in r[0]]
    assert len(auth_runs) == 1
    assert auth_runs[0][1] == ScriptType.LATIN


def test_parentheses_around_persian():
    text = "این یک متن (به زبان فارسی) است."
    runs = split_bidi_runs(text)
    assert all(r[1] == ScriptType.PERSIAN for r in runs)


def test_latin_identifiers_with_underscores_and_hyphens():
    text = "شاخص‌های IX_Orders_Pending و redis-master-01 پیکربندی شدند."
    runs = split_bidi_runs(text)
    ix_run = [r for r in runs if "IX_Orders_Pending" in r[0]]
    assert len(ix_run) == 1
    assert ix_run[0][1] == ScriptType.LATIN

    redis_run = [r for r in runs if "redis-master-01" in r[0]]
    assert len(redis_run) == 1
    assert redis_run[0][1] == ScriptType.LATIN


def test_urls_and_file_paths():
    text = "فایل در /var/log/app.log و وبسایت https://example.com/api قرار دارد."
    runs = split_bidi_runs(text)
    path_run = [r for r in runs if "/var/log/app.log" in r[0]]
    assert len(path_run) == 1
    assert path_run[0][1] == ScriptType.LATIN

    url_run = [r for r in runs if "https://example.com/api" in r[0]]
    assert len(url_run) == 1
    assert url_run[0][1] == ScriptType.LATIN


def test_persian_numbers_caption():
    text = "شکل ۲-۱. معماری داخلی پایگاه داده"
    runs = split_bidi_runs(text)
    # Entire caption with Persian numbers should remain PERSIAN
    assert all(r[1] == ScriptType.PERSIAN for r in runs)


def test_parentheses_around_latin_between_persian_words():
    text = "موتور (Database Engine) اصلی"
    runs = split_bidi_runs(text)
    assert len(runs) == 3
    assert runs[0] == ("موتور ", ScriptType.PERSIAN)
    assert runs[1] == ("(Database Engine)", ScriptType.LATIN)
    assert runs[2] == (" اصلی", ScriptType.PERSIAN)

