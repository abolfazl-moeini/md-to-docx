# وضعیت اجرای نهایی پروژه `md-to-docx` (مطابق `finilize.v2.md`)

تاریخ: 2026-09-08. این سند گزارش وضعیت واقعی و جامع جمع‌بندی پروژه بر اساس معیارهای `finilize.v2.md` است.

کتاب منبع بدون تغییر ماند: SHA-256 `525a3e92016a946bf36fdd5b3a2a8c8829a6e71e3e433fe52b6d9e9f3352443b`.

---

## ۱. خلاصهٔ وضعیت دروازه‌ها (Gate Summary)

| دروازه | وضعیت | جزئیات و شواهد |
| :--- | :--- | :--- |
| **۱. آزمون‌های خودکار (Pytest Suite)** | **PASS** | **۳۵۹ passed، ۱ skipped** در ۷۷ ثانیه. آزمون اسکیپ‌شده مربوط به عدم وجود LibreOffice روی هاست است. |
| **۲. ماتریس کامل (Full Matrix Run)** | **PASS** | **۲۴۴ از ۲۴۴ زوج PASS (صفر fail، صفر error)** در ۹۶ ثانیه (`artifacts/full_matrix_run/`). |
| **۳. اوراکل‌های ساختاری و محتوایی** | **PASS** | تمام ۲۴۴ زوج آزمون‌های Package Oracle (روابط، rId، Content Types) و Semantic Oracle (ترتیب پاراگراف‌ها، جداول، کدها، لیست‌ها، نقل‌قول‌ها) را گذراندند. |
| **۴. موتور Mermaid** | **PASS** | مرورگر اختصاصی `chrome-headless-shell` نسخه ۱۵۲ نصب شد؛ آزمون رندر واقعی فارسی و ساخت SVG label در همان فرایند پاس شد (`test_real_persian_mermaid_rendering_integration`). |
| **۵. بسته‌بندی و Wheel** | **PASS** | ساخت Wheel و نصب در `venv` ایزوله خارج از مخزن و تبدیل نمونه با هر ۴ قالب با موفقیت آزموده شد (`test_smoke_wheel_build_and_template_assets`). |
| **۶. رندر صفحات (LibreOffice)** | **BLOCKED / ABSENT** | برنامهٔ LibreOffice (`soffice`) روی این هاست نصب نیست؛ لذا تبدیل به PDF/PNG صفحات انجام نشد. |
| **۷. مرور انسانی در Microsoft Word** | **PENDING** | برنامهٔ Microsoft Word روی این هاست موجود نیست؛ فایل‌های DOCX آمادهٔ بازبینی در Word ویندوز هستند (`word-windows-review/`). |
| **۸. همگام‌سازی مستندات و اسکریپت‌ها** | **PASS** | `README.md`، `README_FA.md`، `AGENTS.md`، `bootstrap.sh` و `.github/workflows/test.yml` با الزامات Node `>=22.12.0`، `chrome-headless-shell` و فونت `Courier New` هماهنگ شدند. |

---

## ۲. گزارش اجرای ماتریس ۲۴۴ زوج (`artifacts/full_matrix_run/`)

- **شناسه اجرا:** `full_release_run`
- **زمان:** 2026-09-08T16:01:29
- **فایل‌های ورودی (Fixtures):** ۶۱ فیکسچر (`B00`, `C01`–`C04`, `R01`–`R40`, `S01`–`S16`)
- **قالب‌ها (Templates):** ۴ قالب استاندارد (`purple_book`, `persian_book`, `persian_compact`, `persian_report`)
- **کل موارد (Total Pairs):** 244
- **موفق (Passed):** 244
- **ناموفق (Failed):** 0
- **خطا (Errors):** 0
- **زمان کل اجرا:** 96.09 ثانیه
- **خروجی‌ها:** `run.json`, `matrix.csv` (شامل ۲۴۴ ردیف داده), `summary.md`, `index.html`, `reviews.json`

### تفکیک قالب‌ها

| نام قالب | اندازه صفحه | کل تبدیل‌ها | موفق | ناموفق |
| :--- | :--- | :--- | :--- | :--- |
| `purple_book` | A4 | 61 | 61 | 0 |
| `persian_book` | A4 | 61 | 61 | 0 |
| `persian_compact` | A5 | 61 | 61 | 0 |
| `persian_report` | Letter | 61 | 61 | 0 |

---

## ۳. وضعیت محیط و ابزارها

- **Python:** 3.11.15
- **Pandoc:** 3.11 (تأییدشده و فعال)
- **Node.js:** v22.14.0
- **Mermaid CLI (mmdc):** 11.4.2 (با Puppeteer و مرورگر مدیریت‌شده `chrome-headless-shell/mac_arm-152.0.7977.75`)
- **LibreOffice:** ندارد (`absent`)
- **Microsoft Word:** ندارد (`absent`)

---

## ۴. جمع‌بندی و وضعیت نهایی

موتور نرم‌افزاری تبدیل Markdown به DOCX، اعتبارسنجی قالب‌ها، پردازش bidi و فونت‌ها، رندرینگ نمودارهای Mermaid، خط لولهٔ انتشار، و اوراکل‌های اعتبارسنجی ساختاری و معنایی **به‌طور کامل و دقیق پیاده‌سازی و راستی‌آزمایی شده‌اند**.

مطابق قواعد سخت‌گیرانهٔ پروژه و `finilize.v2.md`، به دلیل عدم نصب LibreOffice و Microsoft Word در هاست بدون رابط گرافیکی جاری، رندر بصری تصاویر صفحات و بازبینی نهایی در Word در وضعیت `pending review / ready for visual review` باقی می‌ماند و ادعای دروغین پذیرش بصری ۱۰۰٪ ثبت نمی‌گردد.
