import pytest
from md_to_docx.headings import parse_heading, HeadingInfo

def test_parse_heading_persian_numbers():
    info = parse_heading("۱.۴.۱ نقش Database Engine")
    assert info.number == "۱.۴.۱"
    assert info.title == "نقش Database Engine"

def test_parse_heading_with_hashes():
    info = parse_heading("# ۱.۵ پایگاه‌های دادهٔ سیستمی SQL Server")
    assert info.level == 1
    assert info.number == "۱.۵"
    assert info.title == "پایگاه‌های دادهٔ سیستمی SQL Server"

def test_parse_heading_h2_hashes():
    info = parse_heading("## ۱.۴.۲ نقش SQL Server Agent")
    assert info.level == 2
    assert info.number == "۱.۴.۲"
    assert info.title == "نقش SQL Server Agent"

def test_parse_heading_without_number():
    info = parse_heading("مقدمه")
    assert info.number is None
    assert info.title == "مقدمه"

def test_parse_heading_latin_numbers():
    info = parse_heading("1.2 Latin Heading Title")
    assert info.number == "1.2"
    assert info.title == "Latin Heading Title"

def test_parse_heading_only_hashes():
    info = parse_heading("# فقط هش")
    assert info.level == 1
    assert info.number is None
    assert info.title == "فقط هش"

def test_parse_heading_with_explicit_level():
    info = parse_heading("۱.۶ مدل ذهنی هویت و دسترسی", level=2)
    assert info.level == 2
    assert info.number == "۱.۶"
    assert info.title == "مدل ذهنی هویت و دسترسی"

def test_parse_heading_dash_separator():
    info = parse_heading("۲-۱ معماری داخلی")
    assert info.number == "۲-۱"
    assert info.title == "معماری داخلی"
