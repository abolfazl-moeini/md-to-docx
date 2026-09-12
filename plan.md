# پلن نهایی و بازبینی‌شدهٔ افزودن پشتیبانی از خروجی PDF به پروژهٔ `md-to-docx`
# Hardened Implementation Plan: Markdown-to-PDF Support in `md-to-docx`

**نسخه:** 2.0 (Post-Principal Review)  
**تاریخ:** ۲۰۲۶-۰۹-۱۲  
**وضعیت:** پلن نهایی تصویب‌شده — **بدون پیاده‌سازی کد (Design & Architecture Only)**  
**مراجع:** `AGENTS.md`، `finilize.v3.md`، `persian_layout_quality_plan.md`

---

## ۱. خلاصهٔ اجرایی و معماری نهایی (Architectural Strategy)

### ۱.۱. چرا تبدیل دومرحله‌ای بر پایهٔ DOCX تنها گزینهٔ قابل اتکاست؟
رویکرد انتخابی برای تولید PDF:
$$\text{Markdown} \longrightarrow \text{Pandoc AST} \longrightarrow \text{DocxRenderer} \longrightarrow \text{Staged DOCX} \longrightarrow \text{Headless LibreOffice} \longrightarrow \text{Atomic Staged PDF} \longrightarrow \text{Publish}$$

**دلایل تصمیم‌گیری (Design Rationale):**
1. **۱۰۰٪ تطابق و هویت بصری:** کتابخانهٔ `md-to-docx` دارای صدها ساعت بهینه‌سازی اختصاصی برای تراز راست‌به‌چپ (Bidi/RTL)، فونت فارسی Vazirmatn، شماره‌گذاری تیترها و بَج‌های رنگی، کادرهای نقل‌قول و هشدار، جدول‌ها با سرستون و خطوط استایل‌داده‌شده، پوسته‌های ورد (`shell.docx`)، سرصفحه/پاصفحه و فرمول‌های OMML است.
2. **پرهیز از ساخت موتور موازی:** رندر مستقیم Markdown به HTML و تبدیل آن با مرورگر (Puppeteer / WeasyPrint) مستلزم بازنویسی کامل تمام این قوانین در CSS Paged Media و نگهداری دو رندرر مجزا در آینده بود که طبق صراحت `persian_layout_quality_plan.md` مردود است: *«PDF حاصل از HTML یا PDF مستقیم جایگزین رندر DOCX نیست.»*

---

## ۲. تصمیمات کلیدی بازبینی مهندسی ارشد (L8 Architecture Refinements)

در نسخهٔ ۲ پلن، ۵ دام عملیاتی که در محیط‌های سروری و سیستم‌های کاربران موجب باگ و شکست می‌شوند شناسایی و مهار شدند:

### اصلاح ۱: حذف اتوماسیون Word و استانداردسازی روی موتور قطعی (Deterministic Engine)
- **رد گزارهٔ اولیه:** اتوماسیون Microsoft Word از طریق AppleScript در مک یا COM در ویندوز برای تولید خودکار رد شد. Word در پس‌زمینه واقعاً Headless اجرا نمی‌شود؛ پنجرهٔ رابط کاربری باز می‌شود، فوکوس سیستم‌عامل را می‌گیرد و با کوچک‌ترین دیالوگ آپدیت یا لایسنس، فرآیند برای همیشه قفل (Hang) می‌شود. علاوه بر این، خروجی مک/ویندوز با لینوکس متفاوت می‌شد.
- **تصمیم نهایی:** **LibreOffice Headless (`soffice`) به عنوان یگانه موتور استاندارد و معین (Single Deterministic Reference Engine)** در تمام پلتفرم‌ها (لینوکس، مک، ویندوز و CI) تعیین شد. اتوماسیون ورد صرفاً به عنوان اسکریپت دستی کنترل کیفیت در `scripts/` باقی می‌ماند و وارد خط لولهٔ اصلی نمی‌شود.

### اصلاح ۲: حل قطعی چالش فونت در LibreOffice (فراتر از فرضیهٔ `SAL_FONTPATH`)
- **مشکل شناسایی‌شده:** متغیر `SAL_FONTPATH` در نسخه‌های مدرن LibreOffice (به‌ویژه در macOS که از CoreText استفاده می‌کند و لینوکس که به Fontconfig وابسته است) همیشه تضمین‌کنندهٔ لود فونت نیست و ممکن است LibreOffice در غیاب فونت، متن فارسی را به شکلی نامناسب به فونت سیستمی جایگزین کند.
- **راهکار چندلایه:**
  1. **بررسی پیش‌پرواز (Pre-flight Font Check):** بررسی وجود فونت بدنه (`Vazirmatn`) در دایرکتوری‌های فونت سیستم‌عامل (`~/Library/Fonts`, `/Library/Fonts`, `~/.local/share/fonts`).
  2. **تزریق Fontconfig در لینوکس:** ساخت یک کانفیگ موقت `fonts.conf` در پروفایل موقت LibreOffice که صریحاً پوشهٔ `fonts/` قالب را به عنوان منبع فونت به Fontconfig معرفی می‌کند.
  3. **جاسازی در DOCX میانی:** فعال‌سازی مکانیزم `embed_fonts_in_docx` برای فایل DOCX موقت در صورت لزوم.
  4. **ارزیابی در تست:** افزودن آزمون اعتبارسنجی خروجی برای اطمینان از اینکه فونت واقعی در PDF ثبت شده و فونت جایگزین نامعتبر استفاده نشده است.

### اصلاح ۳: مهار کامل فرآیندهای زامبی و قفل‌های معلق LibreOffice
- **مشکل شناسایی‌شده:** پروسهٔ `soffice.bin` در صورت مواجهه با خطای داخلی ممکن است دیالوگ باز کند و در صورت رسیدن به Timeout در پایتون، به صورت یک فرآیند زامبی در پس‌زمینه باز بماند.
- **راهکار امنیتی:**
  - اجرای فرآیند در یک Process Group مجزا با `start_new_session=True`.
  - در صورت وقوع `TimeoutExpired`، کل درخت پردازش با `os.killpg(os.getpgid(proc.pid), signal.SIGKILL)` به طور کامل کشته می‌شود.
  - فلگ‌های ضد قفل اجباری:
    ```bash
    soffice --headless --norestore --nofirststartwizard --nologo --nolockcheck "-env:UserInstallation=file:///tmp/.lo_prof_<uuid>" --convert-to pdf --outdir <stage_dir> <docx_path>
    ```
  - پاکسازی قطعی دایرکتوری پروفایل موقت در بلاک `finally`.

### اصلاح ۴: مدیریت پاکیزهٔ پوشهٔ رسانه (Media Directory Hygiene)
- **مشکل شناسایی‌شده:** در خط لولهٔ DOCX، تصاویر نمودارهای Mermaid به پوشهٔ `{stem}_media/` در کنار فایل خروجی کپی می‌شوند. در حالت خروجی PDF، چون تمام تصاویر درون باینری PDF جاسازی می‌شوند، ساخت پوشهٔ مدیا در دیسک کاربر آلودگی محیطی و بی‌فایده است.
- **راهکار:**
  - در حالت خروجی PDF، پوشهٔ مدیا صرفاً درون فولدر موقت Staging باقی می‌ماند و همراه آن پاک می‌شود.
  - پوشهٔ مدیا تنها زمانی در کنار فایل منتشر می‌شود که کاربر صریحاً فلگ `--media-dir` یا `--keep-docx` را تعیین کرده باشد.

### اصلاح ۵: ارگونومی شفاف و بدون افزونگی در CLI
- تفکیک شفاف مسئولیت دستورها:
  1. `md2docx convert input.md -o output.docx` (تبدیل پیش‌فرض Markdown به ورد)
  2. `md2docx convert input.md -o output.pdf` (تبدیل مستقیم Markdown به PDF بر اساس پسوند فایل)
  3. `md2docx to-pdf document.docx -o document.pdf` (دستور ابزاری اختصاصی برای تبدیل فایل DOCX موجود به PDF، متناظر با دستور موجود `to-md`)
- در صورت نبود LibreOffice روی سیستم، برنامه با کد خروج ۱ و یک پیام راهنمای کاملاً خوانا، دوستانه و بدون Stack Trace خاتمه می‌یابد:
  ```text
  Error: PDF conversion requires LibreOffice ('soffice').
  To install LibreOffice on your system:
    - macOS:   brew install --cask libreoffice
    - Ubuntu:  sudo apt install libreoffice
    - Fedora:  sudo dnf install libreoffice
  Or set MD2DOCX_SOFFICE to the path of your soffice executable.
  ```

---

## ۳. ساختار ماژول‌ها و فایل‌های پروژه

```text
src/md_to_docx/
├── __init__.py           # افزودن اکسپورت convert_markdown_to_pdf و convert_docx_to_pdf
├── cli.py                # پشتیبانی از -o *.pdf در convert و ثبت دستور جدید to-pdf
├── pipeline.py           # تابع convert_markdown_to_pdf با staging و قفل اتمیک
├── pdf.py                # [جدید] ماژول موتور LibreOffice، ایزولاسیون پروفایل، کشنده‌ٔ زامبی، و اعتبارسنجی PDF
└── options.py            # تنظیمات GeneratorOptions و اعتبارسنجی پارامترهای جدید
```

### ۳.۱. ماژول جدید `src/md_to_docx/pdf.py`

```python
"""Robust LibreOffice headless adapter for DOCX to PDF conversion."""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional, Tuple

from md_to_docx.mermaid import ConvertError

def find_soffice_binary() -> Optional[Path]:
    """Locates soffice binary via MD2DOCX_SOFFICE, PATH, or standard OS directories."""
    ...

def is_valid_pdf(path: Path) -> bool:
    """Verifies that the file exists, has %PDF- header, valid size, and %%EOF trailer."""
    ...

def convert_docx_to_pdf(
    docx_path: Path,
    output_pdf_path: Path,
    timeout: int = 120,
    overwrite: bool = False,
) -> Path:
    """
    Executes headless LibreOffice conversion with isolated user profile,
    hard timeout with process group kill, and validation.
    """
    ...
```

### ۳.۲. افزودن تابع `convert_markdown_to_pdf` در `pipeline.py`

```python
def convert_markdown_to_pdf(
    input_path: Optional[str | Path] = None,
    output_path: Optional[str | Path] = None,
    content: Optional[str] = None,
    base_dir: Optional[str | Path] = None,
    template: str | Path | Template = "purple_book",
    overwrite: bool = True,
    media_dir: Optional[str | Path] = None,
    keep_docx: bool = False,
    pdf_timeout: int = 120,
    options: Optional[GeneratorOptions | dict] = None,
    warnings: Optional[List[str]] = None,
    report: Optional[Dict[str, Any]] = None,
    ...
) -> Path:
    """
    Full pipeline: Markdown -> Pandoc AST -> DocxRenderer -> Staged DOCX
                   -> convert_docx_to_pdf -> Validated Staged PDF
                   -> Publish with atomic lock and rollback.
    """
```

---

## ۴. برنامهٔ گام‌به‌گام پیاده‌سازی و آزمون‌ها (TDD Workflow)

### گام ۱: آزمون‌های واحد موتور تبدیل (`tests/test_pdf.py`)
- [ ] تست تشخیص مسیر اجرایی `find_soffice_binary` در شرایط مختلف (PATH، متغیر محیطی، مسیر برنامه‌های مک).
- [ ] تست اعتبارسنجی `is_valid_pdf` برای فایل‌های خراب، بدون مجیک‌بایت، و فایل‌های سالم.
- [ ] تست موک‌شده برای کشته شدن Process Group هنگام رخ دادن Timeout در LibreOffice.
- [ ] تست موک‌شده برای پاکسازی قطعی فولدر پروفایل موقت بعد از اجرای فرآیند.
- [ ] تست صادر شدن خطای واضح همراه با راهنمای نصب هنگام غیاب `soffice`.

### گام ۲: پیاده‌سازی ماژول `src/md_to_docx/pdf.py`
- [ ] پیاده‌سازی توابع بررسی، فرآیند `Popen` با `start_new_session=True` و هندلینگ تمیز سیگنال‌ها.

### گام ۳: ادغام پایپ‌لاین و انتشار اتمیک (`pipeline.py`)
- [ ] پیاده‌سازی `convert_markdown_to_pdf`.
- [ ] آزمون‌های یکپارچگی پایپ‌لاین: عدم انتشار پوشهٔ مدیا در حالت پیش‌فرض، انتشار فایل `.docx` فقط در صورت `keep_docx=True`، قفل انتشار `.{stem}.pdf.publish.lock`.
- [ ] اکسپورت توابع در `src/md_to_docx/__init__.py`.

### گام ۴: خط فرمان CLI (`cli.py`)
- [ ] پشتیبانی از پسوند `.pdf` در دستور `md2docx convert input.md -o output.pdf`.
- [ ] افزودن فلگ `--keep-docx` و `--pdf-timeout`.
- [ ] افزودن ساب‌کامند `md2docx to-pdf input.docx -o output.pdf`.
- [ ] آزمون‌های خط فرمان با خروجی‌های معتبر، خطاهای کاربردی (کد ۲) و خطاهای عملیاتی (کد ۱).

### گام ۵: همگام‌سازی ابزارهای داخلی (`scripts/page_render.py`)
- [ ] بازآرایی `scripts/page_render.py` تا از هستهٔ مشترک `src/md_to_docx/pdf.py` استفاده کند و از کدهای تکراری جلوگیری شود.
- [ ] حفظ کامل پاس شدن تست‌های موجود `tests/test_page_render_p0d.py` و `tests/test_rtl_quality.py`.

### گام ۶: مستندسازی و به‌روزرسانی راهنماها
- [ ] به‌روزرسانی `README.md` و `README_FA.md` با مثال‌های کامل تبدیل به PDF در پایتون و خط فرمان.
- [ ] به‌روزرسانی جدول قابلیت‌ها و قرارداد ورودی/خروجی در `AGENTS.md`.

---

## ۵. معیارهای سخت‌گیرانهٔ پذیرش (Acceptance Criteria)

1. **صحت تبدیل:** تبدیل نمونه‌های فارسی و انگلیسی (`examples/sample_input.md` و `examples/persian_technical_doc.md`) به PDF بدون خطا، بدون خطوط هم‌پوشان و با حفظ فونت Vazirmatn.
2. **عدم ایجاد فایل زائد:** تبدیل یک سند با نمودار Mermaid به PDF نباید هیچ پوشهٔ مدیایی روی دیسک باقی بگذارد مگر اینکه `--keep-docx` یا `--media-dir` صراحتاً درخواست شده باشد.
3. **مقاومت در برابر بن‌بست (No Hang / No Zombie):** در شرایط بروز خطای داخلی در موتور آفیس، تایم‌اوت قطعی اعمال شده و فرآیند با ارسال `SIGKILL` به کل گروه پروسه کشته شود و هیچ فرآیند پس‌زمینه‌ای باقی نماند.
4. **رفتار مستقل تست‌ها در غیاب LibreOffice:** تمامی تست‌های جدید واحد در ماشین‌های بدون LibreOffice با موک مناسب پاس شوند؛ تست‌های نیازمند اجرای واقعی با مارکر `pytest.mark.pdf` اسکیپ شوند تا CI دچار شکست نشود مگر با متغیر صریح `MD2DOCX_REQUIRE_EXTERNAL=1`.
5. **عدم رگرسیون:** تمام ۳۹۳ تست موجود در مخزن باید همچنان سبز باقی بمانند.
