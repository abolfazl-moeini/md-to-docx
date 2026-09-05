import pytest
from md_to_docx.admonitions import preprocess_admonitions

def test_preprocess_note_with_title():
    input_text = """::: note نکتهٔ DBA
در شکل، SSMS و Application به Database Engine متصل می‌شوند.
:::"""
    expected = """::: {.note title="نکتهٔ DBA"}
در شکل، SSMS و Application به Database Engine متصل می‌شوند.
:::"""
    result = preprocess_admonitions(input_text)
    assert result == expected

def test_preprocess_warning_with_title():
    input_text = """::: warning هشدار
System Databaseها را به چشم Databaseهای کم‌اهمیت نگاه نکنید.
:::"""
    expected = """::: {.warning title="هشدار"}
System Databaseها را به چشم Databaseهای کم‌اهمیت نگاه نکنید.
:::"""
    result = preprocess_admonitions(input_text)
    assert result == expected

def test_preprocess_without_title_uses_default():
    input_text = """::: note
بدون عنوان صریح.
:::"""
    default_titles = {"note": "نکته", "warning": "هشدار"}
    expected = """::: {.note title="نکته"}
بدون عنوان صریح.
:::"""
    result = preprocess_admonitions(input_text, default_titles=default_titles)
    assert result == expected

def test_preprocess_already_bracketed_fence_preserved():
    input_text = """::: {.note title="از قبل فرمت شده"}
محتوا
:::"""
    result = preprocess_admonitions(input_text)
    assert result == input_text

def test_preprocess_unrecognized_fence_passed_through():
    input_text = """::: custom_box چیزی
محتوا
:::"""
    result = preprocess_admonitions(input_text)
    assert result == input_text

def test_preprocess_title_with_quotes_escaped():
    input_text = """::: note نکتهٔ "مهم"
محتوا
:::"""
    result = preprocess_admonitions(input_text)
    assert 'title="نکتهٔ \\"مهم\\""' in result or 'title="نکتهٔ &quot;مهم&quot;"' in result

def test_preprocess_gfm_note_and_warning():
    input_text = """> [!NOTE]
> این یک نکته مهم است.
> خط دوم نکته.

متن میانی.

> [!WARNING] اخطار امنیتی
> رمز عبور را به اشتراک نگذارید!"""

    result = preprocess_admonitions(input_text)
    assert '::: {.note title="نکته"}' in result
    assert "این یک نکته مهم است." in result
    assert "خط دوم نکته." in result
    assert '::: {.warning title="اخطار امنیتی"}' in result
    assert "رمز عبور را به اشتراک نگذارید!" in result
    assert ":::" in result

def test_preprocess_gfm_preserves_regular_blockquote():
    input_text = """> Login معمولاً هویت ورود در سطح Instance است.
> خط دوم نقل قول."""
    result = preprocess_admonitions(input_text)
    assert result == input_text
