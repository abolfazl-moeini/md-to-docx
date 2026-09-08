# پلن جمع‌بندی نهایی `md-to-docx`

تاریخ: ۲۰۲۶-۰۹-۰۸  
این سند **جایگزین همهٔ پلن‌های قبلی برای کار باقی‌مانده است.** `finalize.md` و `persian_layout_*.md` تاریخچه و منبع رگرسیون‌اند، نه چک‌لیست اجرا. پلن جدید ننویس؛ همین را ببند.

وضعیت فعلی: **پروژه بسته نیست.** تبدیل Markdown→DOCX برای مسیرهای واحد کار می‌کند. ماتریس صادقانه، Mermaid واقعی، رندر همهٔ صفحات و مرور Word هنوز باز است.

---

## ۰. چه چیزی را دیگر باز نکن

این‌ها در کد و تست واحد هستند. بدون تست قرمز تازه دوباره پیاده‌سازی نکن:

| منبع | انجام‌شده |
| --- | --- |
| `finalize.md` FINAL-01…16 | OMML داخل `w:p`، فرمول دسته‌ای، کد چندخطی، admonition داخل fence، Mermaid در ظرف تو‌در‌تو، resolver تصویر بدون fallback نام‌فایل، پاورقی غنی، تیتر غنی، اعتبارسنجی قالب، bidi/فونت ظرف‌ها، انتشار/محافظت فایل، جدول tbody میانی، `to-md` |
| قالب‌ها | چهار قالب `purple_book` / `persian_book` / `persian_compact` / `persian_report` در `templates/` و `src/`؛ هویت رنگ/صفحه جدا؛ header کتاب SQL از `persian_book` حذف شده |
| F02 | fixture نامعتبر exit 2؛ fail/error exit 1؛ HTML escape؛ عدم تصادم run؛ `review=pending` |
| F04 | package oracle برای rId تکراری، target ناموجود، Content Type، footnote rId |
| F05–F11، F16 | شمارهٔ تیتر در چهار حالت badge/extract و nesting؛ فونت heading؛ نقش callout ناموجود رد می‌شود؛ `dir:ltr`؛ path ویندوزی یک run لاتین؛ hanging indent؛ نسبت تصویر افراطی بدون clamp جدا؛ TOC فقط با `toc: true` |
| F15 بخشی | تست wheel در venv ایزوله و خارج checkout؛ job wheel پاندوک دارد؛ S10 از representative واحد خارج است |
| F17 بخشی | OFL کامل SIL 1.1؛ PROVENANCE عکس‌ها اصلاح شده؛ AGENTS Node 22 |

کتاب منبع دست نخورد: SHA-256 `525a3e92016a946bf36fdd5b3a2a8c8829a6e71e3e433fe52b6d9e9f3352443b`. برای پنج caption بدون تصویر کتاب، تصویر جعل نکن.

---

## ۱. شکاف‌های واقعی که هنوز مانع بستن‌اند

شاهد زندهٔ اوراکل (همین روز، B00 + `purple_book`):

```
Body paragraph sequence mismatch at index 746:
  expected 'رابطهٔ Database، Filegroup، Data File و Transaction Log را می‌بینید.'
  got      '- رابطهٔ Database، Filegroup، Data File و Transaction Log را می‌بینید.'
```

یعنی تبدیل انجام شده؛ اوراکل متن فهرست را بدون نشانگر می‌سازد و DOCX نشانگر متنی `- ` دارد. این باگ محصول نیست مگر اینکه نشانگر غلط باشد.

شاهد ماتریس بدون Mermaid (`artifacts/final-closure-review-20260908/matrix-no-mermaid/`): ۲۲۸ زوج، ۳۲ fail، صفر صفحهٔ مرور. هشت fixture × چهار قالب:

- **B00 / C04 / R39** — semantic (نشانگر فهرست یا متن کد/پاراگراف)
- **C01 / C02 / R03 / R09 / R11** — `expected_warnings: []` در حالی که همان پنج caption بدون تصویر کتاب را دارند؛ B00 هشدار را درست ثبت کرده، برش‌ها نه

بقیهٔ شکاف‌های باز:

1. **Label اوراکل Mermaid ظاهری است.** `mmdc` فقط PNG می‌نویسد؛ SVG sidecar ساخته نمی‌شود؛ اگر SVG نباشد `mermaid_label_pass=True` می‌شود. در runner اندیس SVG برابر `len(issues)` است نه شمارهٔ نمودار.
2. **Mermaid واقعی روی همین macOS بسته نیست.** تست‌ها launch را mock می‌کنند. `scripts/bootstrap.sh` هنوز `npm ci || npm install` و `npx puppeteer browsers install chrome` دارد و پیام fallback به Chrome سیستم می‌دهد. CI integration هم `chrome` نصب می‌کند نه `chrome-headless-shell`.
3. **رندر صفحه به ماتریس وصل نیست.** `scripts/page_render.py` هست و PDF کهنه را رد می‌کند، ولی runner همیشه `render_status=not_run` و `review=pending` می‌نویسد. ۲۴۴ مجموعهٔ PDF/PNG وجود ندارد.
4. **Word و مرور انسانی انجام نشده.** `word-windows-review/` بدون نتیجهٔ مرور، اثبات نیست.
5. **اوراکل معنایی هنوز identity تصویر/پاورقی را کامل نمی‌سنجد.** تصویر فقط با تعداد؛ تصاویر/فرمول پاورقی در سمت DOCX جمع نمی‌شوند؛ `heading_badge` همیشه level 1 ثبت می‌شود.
6. **S06 جدول HTML خام است.** renderer موتور HTML نیست؛ تصویر/فهرست/کد داخل `<table>` تضمین AST جدول نیست. پوشش «سلول تو‌در‌تو» باید pipe/grid بومی باشد نه HTML.

---

## ۲. کار باقی‌مانده — شش تسک، به همین ترتیب

هر تسک: تست قرمز مستقل → کوچک‌ترین اصلاح → تست سبز. معماری را عوض نکن. TDD.

### V1 — ماتریس بدون Mermaid باید صادقانه سبز شود

**هدف:** همهٔ زوج‌های بدون نمودار (حدود ۲۲۸) با اوراکل فعلی pass؛ fail فقط اگر محتوای واقعی خراب باشد.

1. اوراکل: نشانگر متنی فهرست (`- ` / `1.` / حروف) را در مدل expected یا actual یکسان کن. مقایسهٔ ترتیبی پاراگراف/جدول/کد را ضعیف نکن.
2. در `manifest.yaml` برای C01، C02، R03، R09، R11 (و هر برش دیگری که caption بدون تصویر دارد) `expected_warnings` را با **کد + هویت شکل** پر کن؛ `[]` یعنی هیچ هشداری مجاز نیست.
3. تصویر را علاوه بر count با occurrence/story بسنج (هدف شکسته باید fail شود). تصاویر پاورقی را در `actual_from_docx` جمع کن.
4. S06 را به جدول Pandoc واقعی با تصویر/فهرست/کد داخل سلول برگردان؛ HTML خام را پوشش تو‌در‌تو حساب نکن.
5. اجرا:

```bash
python scripts/matrix_runner.py --fixtures B00,C01,C02,C04,R03,R09,R11,R39 --templates purple_book
python scripts/matrix_runner.py --fixtures B00,C01,C02,C03,C04,R01,R02,R03,R04,R05,R06,R07,R08,R09,R10,R11,R12,R13,R14,R15,R16,R17,R18,R19,R20,R21,R22,R23,R24,R25,R26,R27,R28,R29,R30,R31,R32,R33,R34,R35,R36,R37,R38,R39,R40,S01,S02,S03,S04,S05,S06,S07,S08,S09,S13,S14,S15 --templates purple_book,persian_book,persian_compact,persian_report
```

**پذیرش:** صفر fail/error برای این مجموعه؛ `conversion_success` از وجود DOCX بیاید نه از جمع اوراکل‌ها.

### V2 — Mermaid: یا PNG واقعی، یا blocked صریح

1. `bootstrap.sh` و CI integration: فقط `npm ci`؛ مرورگر `chrome-headless-shell` مطابق Puppeteer قفل‌شده؛ پیام «system Chrome fallback» حذف شود.
2. pipeline برای هر occurrence یک SVG هم‌فرایند بسازد (یا خروجی mmdc را SVG+PNG کند). اگر نمودار هست و SVG/label نیست → fail، نه pass خالی.
3. در `matrix_runner.py` به‌جای `idx = len(mermaid_label_issues)` از `enumerate` و تطبیق پایدار نام فایل استفاده کن.
4. یک smoke واقعی فارسی روی همین macOS. اگر launch شکست: `blocked`، بدون retry، بدون باز کردن Chrome دسکتاپ. **قابلیت Mermaid را با skip سبز نبند.**
5. بعد از smoke سالم: S10، S11، S12، S16 × چهار قالب. خوانایی A5 (`persian_compact`) را با PNG درج‌شده بسنج نه فقط وجود فایل.

### V3 — رندر صفحه را به runner وصل کن

1. پرچم صریح مثلاً `--render-pages`؛ پیش‌فرض خاموش.
2. `MD2DOCX_SOFFICE` یا `soffice` روی PATH؛ مسیر cache شخصی hardcode نشود (همین حالا در `page_render.py` درست است).
3. برای هر زوج: پوشهٔ خالی، PDF تازه، PNG تازه، page count و hash. PDF/PNG کهنه ممنوع.
4. چهار وضعیت جدا بماند: executable پیدا شد / رندر اجرا شد / صفحات سالم / مرور شد.
5. ابتدا B00+S11 یک قالب برای زمان/فضا، بعد همهٔ زوج‌های تبدیل‌شده.

بدون LibreOffice: `render=blocked` و پروژه «آمادهٔ رندر»، نه «بسته».

### V4 — مرور Word و صفحات

این کار تست واحد نیست.

1. هیچ `accepted` خودکاری از اوراکل XML نساز.
2. همهٔ صفحات LO (اگر V3 اجرا شد) رکورد `pending|issues_found|accepted` داشته باشند.
3. همان ۲۴۴ DOCX در Word هدف کاربر باز شود؛ Repair، فونت جایگزین، فیلد TOC، header/footer ثبت شود.
4. حداقل این‌ها انسانی دیده شوند: B00 هر چهار قالب، S02، S07، S08، S09، S10–S13، S14، S16، شروع/پایان فصل.
5. issue تأییدشده → fixture رگرسیون. review قدیمی به hash تازه منتقل نشود.

نبود Word = «آمادهٔ مرور»، نه done.

### V5 — CI و مستندات را با واقعیت یکی کن

1. job integration: Node 22 + lockfile + `chrome-headless-shell`؛ `MD2DOCX_REQUIRE_EXTERNAL=1` حق skip ندارد.
2. README / README_FA / AGENTS / bootstrap یک قرارداد بگویند: Node `>=22.12.0`، بدون `npx -y`، بدون system browser پیش‌فرض.
3. ادعای «۲۴۴ visually accepted»، «Mermaid کامل»، «Word تأیید شد» را تا عبور V2–V4 ننویس.
4. تست wheel را در CI اجرا کن (الان در job واحد deselect است؛ job `wheel` باید همان `test_smoke_wheel_build_and_template_assets` را واقعاً سبز کند).

### V6 — فریز و گزارش کوتاه

پس از V1–V5 روی **یک snapshot**:

- `run.json` + `matrix.csv` دقیقاً ۲۴۴ ردیف
- شمار pass/fail/error/blocked/pending جدا
- runtime Mermaid (binary/version/attempts) یا دلیل blocked
- آیا Word دیده شد یا نه
- محدودیت باقی‌مانده صریح

اگر هر دروازه pending است، پروژه را بسته اعلام نکن.

---

## ۳. معیار بستن — فقط وقتی همه برقرارند

| دروازه | PASS یعنی | PASS نیست |
| --- | --- | --- |
| واحد | تست‌های غیر Mermaid سبز | عدد تست قدیمی در پلن |
| ماتریس بدون نمودار | همهٔ زوج‌های V1 pass | ۲۲۸ با ۳۲ fail پنهان در warning |
| Mermaid | PNG واقعی + label همان فرایند، یا blocked با علت | mock launch یا SVG دست‌ساز |
| بسته | wheel در venv تازه، چهار قالب از site-packages | `pip install -e` داخل checkout |
| صفحات | PDF/PNG تازه برای زوج‌های اجراشده | وجود `soffice` بدون اجرا |
| مرور | صفر صفحه بدون وضعیت؛ Word یا «آمادهٔ مرور» | `accepted` از XML |
| سند | README/AGENTS مطابق رفتار | «همه انجام شد» در بالای پلن کهنه |

---

## ۴. خارج از این دور

`.doc` قدیمی، پوستهٔ چندبخشی، GUI/وب، دانلود تصویر اینترنتی، LaTeX کامل، Haskell، بازنویسی کل renderer، حذف `raw/` یا تغییرات دیگران، جعل تصویر برای captionهای کتاب.

---

## ۵. فرمان‌های پایه برای عامل بعدی

```bash
source .venv/bin/activate
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests -q -rs -m "not (mermaid or integration)" \
  -k "not test_smoke_wheel_build_and_template_assets"
python scripts/matrix_runner.py --fixtures B00,C01,R03 --templates purple_book
```

مرجع رفتار: کد و تست جاری. تیک پلن‌های قبلی و عدد «۳۱۵ passed» بستن پروژه نیست.
