# AGENTS.md — راهنمای عامل هوش مصنوعی

این فایل نقطهٔ شروع کار در پروژهٔ `md-to-docx` است. هدف، معماری، قراردادهای فعلی، مسیر فایل‌ها و روش بررسی تغییرات را توضیح می‌دهد. راهنما برای کل مخزن کاربرد دارد؛ دستور صریح کاربر دربارهٔ دامنهٔ هر کار مقدم است. اگر درخواست «فقط بررسی» یا «فقط پلن» است، کد را پیاده‌سازی یا اصلاح نکن.

مسیر این نسخه از مخزن `/Users/moeini/Downloads/md-to-docx` است. مسیرهای کوتاه در این راهنما نسبت به ریشهٔ مخزن هستند تا راهنما پس از جابه‌جایی پروژه نیز قابل استفاده بماند.

## ۱. پروژه چه مسئله‌ای را حل می‌کند؟

کاربر می‌خواهد **قالب قابل تنظیم + فایل یا متن Markdown → سند Word با کیفیت مناسب برای فارسی و متن دوزبانه** داشته باشد. محتوا شامل متن، تیتر، جدول، تصویر، نمودار Mermaid و کد دارای رنگ‌بندی نحوی است. فونت‌ها، رنگ‌ها، فاصله‌ها، حاشیه‌ها و طراحی عناصر باید در سراسر سند مطابق قالب باشند.

- خروجی‌های رسمی بسته، **`.docx`** و **`.pdf`** هستند. تبدیل به فرمت قدیمی Word یعنی `.doc` پیاده‌سازی نشده و CLI آن پسوند را رد می‌کند. تغییر نام فایل، تبدیل فرمت نیست.
- محصول فعلی یک **کتابخانهٔ Python و ابزار خط فرمان** است؛ رابط گرافیکی، وب‌سرویس یا ویرایشگر آنلاین جزو پیاده‌سازی فعلی نیست.
- قالب پیش‌فرض `purple_book` است؛ دو تصویر در `sample-template/1.jpg` و `sample-template/2.jpg` مرجع بصری طراحی اولیه‌اند.
- فونت فارسی پیش‌فرض **Vazirmatn** است و باید قابل تغییر بماند. متن لاتین و کد نقش‌های فونت جدا دارند.
- هدف محصول، تبدیل درست و یک‌دست است؛ وجود یک فایل خروجی یا سبز بودن تست‌های XML به‌تنهایی اثبات کیفیت ظاهری تمام صفحات نیست.
- ترجیح صریح کاربر: توسعه با **Python یا فناوری عمومی مانند Node، بدون Haskell**؛ تغییرات رفتاری به روش **TDD** انجام شوند.

درخواست اولیه از Pandoc و مخزن `Achuan-2/pandoc_docx_template` نام برده بود. معماری موجود از آن مخزن به‌عنوان موتور تبدیل استفاده نمی‌کند: Pandoc فقط Markdown را تجزیه می‌کند و خروجی Word با رندرکنندهٔ اختصاصی Python ساخته می‌شود.

## ۲. شروع کار برای عاملی که هیچ پیش‌زمینه‌ای ندارد

1. درخواست جاری کاربر و وضعیت `git status --short` را بخوان؛ تغییرات موجود ممکن است متعلق به کاربر یا عامل دیگری باشند.
2. این فایل، `README.md` و تنظیمات وابستگی در `pyproject.toml` و `package.json` را مرور کن.
3. برای مسیر اصلی، به ترتیب `pipeline.py`، `template.py`، `pandoc_json.py` و بخش مرتبط `renderer.py` را در `src/md_to_docx/` بخوان.
4. تست‌های همان قابلیت و نمونهٔ Markdown مرتبط را پیدا کن. پیش از تغییر رفتار، نمونهٔ مشکل و خروجی مورد انتظار را مشخص کن.
5. نوع کار را مشخص نگه دار: مستندسازی، بازبینی، نوشتن پلن یا پیاده‌سازی. کار مستندسازی مجوز بازنویسی موتور تبدیل یا بازتولید خروجی‌های نمونه نیست.

**مرجع رفتار واقعی، کد و تست‌های فعلی‌اند.** README و راهنماها ممکن است عقب بمانند. نام commit، تیک‌های چک‌لیست یا نمرهٔ نوشته‌شده توسط عامل قبلی را نتیجهٔ آزمون مستقل تلقی نکن.

## ۳. ساختار مخزن و مسئولیت فایل‌ها

| مسیر | مسئولیت |
| --- | --- |
| `src/md_to_docx/__init__.py` | خروجی عمومی بسته: `Template`، `convert_markdown_to_docx`، `convert_markdown_to_pdf` و `convert_docx_to_pdf` |
| `src/md_to_docx/cli.py` | دستورات Click، ورودی فایل و stdin، پیام‌ها و کدهای خروج |
| `src/md_to_docx/pipeline.py` | هماهنگی تبدیل، فراخوانی Pandoc، staging، انتشار خروجی و مدیریت media |
| `src/md_to_docx/pdf.py` | آداپتور بدون‌سر LibreOffice برای تبدیل DOCX به PDF، ایزولاسیون فرآیند و اعتبارسنجی |
| `src/md_to_docx/options.py` | کلاس `GeneratorOptions`، اعتبارسنجی گزینه‌ها و تحلیل تقدم جهت سند |
| `src/md_to_docx/fonts_embed.py` | خواندن `fsType` فونت، ارزیابی مجوز، obfuscation و تعبیه یا پاکسازی فونت در DOCX |
| `src/md_to_docx/template.py` | یافتن قالب، خواندن YAML، اعتبارسنجی و حل مسیر فایل‌های قالب |
| `src/md_to_docx/admonitions.py` | تبدیل syntax یادداشت‌ها و هشدارها به fenced Div با توجه به code fence |
| `src/md_to_docx/mermaid.py` | تشخیص و اجرای mmdc/مرورگر، تنظیم فونت و CSS، تبدیل Mermaid در AST به تصویر |
| `src/md_to_docx/pandoc_json.py` | پیمایش AST، نگاشت block/inline، جدول‌ها، محتوای تو‌در‌تو و نسخهٔ API |
| `src/md_to_docx/renderer.py` | تولید پاراگراف، تیتر، کادر، جدول، تصویر، کد و اعمال قالب |
| `src/md_to_docx/bidi.py` | تشخیص متن فارسی/لاتین، قطعه‌بندی متن مخلوط و ابزارهای ارقام |
| `src/md_to_docx/oxml.py` | تنظیمات مستقیم OOXML برای جهت، فونت، جدول، حاشیه و صفحه‌بندی |
| `src/md_to_docx/headings.py` | استخراج شماره و متن تیتر از محتوای ورودی |
| `src/md_to_docx/paths.py` | حل مسیر محلی تصاویر و percent-encoding |
| `src/md_to_docx/omml.py` | تبدیل زیرمجموعه‌ای از TeX به فرمول بومی Word یعنی OMML |
| `src/md_to_docx/footnotes.py` | ساخت part و ارجاع‌های پاورقی Word |
| `src/md_to_docx/to_md.py` | تبدیل DOCX به Markdown و استخراج رسانه (FINAL-16) |
| `templates/purple_book/` | نسخهٔ قالب قابل ویرایش در checkout |
| `templates/persian_book/` | قالب کتاب استاندارد فارسی (A4، سرصفحه/پاصفحه خنثی، تراز start) |
| `templates/persian_compact/` | قالب جیبی فارسی (A5، حاشیه فشرده، تراز start) |
| `templates/persian_report/` | قالب گزارش سازمانی فارسی (Letter، لوگوی هدر، پاورقی PAGE پویا) |
| `src/md_to_docx/templates/` | نسخه‌های قالب‌ها و دارایی‌هایی که داخل بستهٔ قابل نصب قرار می‌گیرند |
| `tests/` | آزمون‌های واحد، رگرسیون، یکپارچه و بسته‌بندی |
| `tests/fixtures/` | ورودی‌های فارسی، انگلیسی و مخلوط، AST نمونه، تصاویر و DOCXهای نمونه |
| `tests/fixtures/persian_layout/` | ۶۱ فیکسچر کیفیت چیدمان فارسی، فایل `manifest.yaml` و دارایی‌های مربوطه |
| `tests/test_persian_layout_quality.py` | آزمون‌های جامع رگرسیون کیفیت چیدمان فارسی (Q03 تا Q16) |
| `examples/` | نمونه‌های قابل مطالعه و تبدیل برای مصرف‌کننده |
| `sample-template/` | تصاویر مرجع طراحی؛ ورودی اجرایی قالب نیستند |
| `scripts/bootstrap.sh` | آماده‌سازی محیط Python و Node، مرورگر Puppeteer و بررسی وجود Pandoc |
| `scripts/matrix_runner.py` | اجرای ماتریس کیفیت چیدمان فارسی (۲۴۴ زوج)، ارزیابی اوراکل ساختاری/محتوایی و تولید گزارش |
| `scripts/setup_templates.py` | بازسازی و همگام‌سازی پوسته‌ها و تنظیمات ۴ قالب در `templates/` و `src/` |
| `scripts/convert_fixtures.py` | تبدیل مجدد Markdownهای `examples/` و `tests/fixtures/` و بازنویسی DOCXهای کنارشان |
| `.github/workflows/test.yml` | سه مسیر CI برای unit، wheel و integration |
| `pyproject.toml` | وابستگی‌های Python، بسته‌بندی src، داده‌های قالب، entry point و markerهای pytest |
| `constraints.txt` / `requirements.txt` | محدودسازی نسخه‌های نصب و فهرست دیگر وابستگی‌های Python؛ هنگام تغییر وابستگی بررسی شوند |
| `package.json` / `package-lock.json` | وابستگی Mermaid CLI و نسخه‌های حل‌شدهٔ Node |
| `fix.md` / `finalize.md` / `persian_layout_gap_review_plan.md` | سوابق برنامه‌های اصلاح و معیارهای پذیرش؛ وضعیت جاری را از روی آن‌ها فرض نکن |

## ۴. محیط اجرا و راه‌اندازی

- Python حداقل `3.11`؛ نصب از `pyproject.toml` با setuptools.
- کتابخانه‌های اصلی: `python-docx`، `lxml`، `PyYAML`، `Click`، `Pillow` و `Pygments`. تست‌ها با `pytest` و `pytest-mock` هستند.
- Pandoc باید در `PATH` باشد. شمارهٔ نسخهٔ خود برنامه با `pandoc-api-version` در JSON یکسان نیست؛ adapter فعلی خانواده‌های API `1.22.x` و `1.23.x` را می‌پذیرد.
- نمودارهای Mermaid به Node **حداقل `22.12.0`** (مطابق `package.json` engines و lockfile)، `@mermaid-js/mermaid-cli` و runtime مدیریت‌شدهٔ Puppeteer نیاز دارند. CI از Node 22 استفاده می‌کند. پس از شکست launch، فراخوانی‌های بعدی همان فرایند **blocked** می‌شوند و مرورگر دسکتاپ Chrome/Edge به‌صورت پیش‌فرض انتخاب نمی‌شود مگر `MD2DOCX_ALLOW_SYSTEM_BROWSER=1`. نصب با `npx -y` انجام نمی‌شود.
- LibreOffice در مسیر integration نصب می‌شود و می‌تواند برای بررسی رندر کمک کند؛ وابستگی موتور اصلی تولید DOCX نیست.
- قفل انتشار از `fcntl` استفاده می‌کند. اجرای فعلی را برای محیط‌های Unix مانند macOS/Linux در نظر بگیر؛ پشتیبانی بومی Windows را بدون تغییر و تست ادعا نکن. باز کردن DOCX در Word ویندوز موضوع جداگانه‌ای است.

اگر محیط از قبل آماده است، آن را بی‌دلیل دوباره نصب نکن. دستورات زیر از ریشهٔ مخزن اجرا می‌شوند:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -c constraints.txt -e ".[dev]"
npm ci
npx puppeteer browsers install chrome-headless-shell
```

Pandoc را باید جداگانه نصب کرد. `scripts/bootstrap.sh` راه جایگزین آماده‌سازی است؛ بسته‌ها را نصب می‌کند و نبود Pandoc را گزارش می‌دهد. آماده‌سازی ممکن است به شبکه نیاز داشته باشد. برای تکرارپذیری وابستگی‌های Node از lockfile استفاده کن و در صورت خطای نصب، علت را بررسی کن.

فرمان نصب‌شده `md2docx` است. معادل ماژولی موجود `python -m md_to_docx.cli` است؛ بسته فعلاً `__main__.py` ندارد، پس `python -m md_to_docx` فرمان صحیحی نیست.

## ۵. رابط عمومی و قرارداد ورودی/خروجی

### خط فرمان

```bash
md2docx convert input.md -o output.docx --template purple_book
md2docx convert input.md -o output.pdf --template purple_book
md2docx convert input.md -o output.pdf --keep-docx
md2docx to-pdf input.docx -o output.pdf
md2docx convert input.md -o output.docx --template ./templates/my_theme
md2docx templates list
md2docx templates validate purple_book
md2docx to-md input.docx -o output.md
```

- برای تبدیل Markdown مستقیم به PDF از پسوند `.pdf` در `-o` دستور `convert` استفاده می‌شود. فلگ اختیاری `--keep-docx` فایل DOCX میانی را نیز نگه می‌دارد.
- برای تبدیل اختصاصی DOCX به PDF از دستور `md2docx to-pdf input.docx -o output.pdf` استفاده می‌شود.
- برای تنظیم مهلت زمانی LibreOffice از گزینهٔ `--pdf-timeout` (در `convert`) و `--timeout` / `--pdf-timeout` (در `to-pdf`) استفاده می‌شود (پیش‌فرض: ۱۲۰ ثانیه).
- برای تبدیل معکوس DOCX به Markdown از دستور `md2docx to-md input.docx -o output.md` استفاده می‌شود.
- در ورودی فایل، اگر `-o` تعیین نشود خروجی کنار ورودی با پسوند `.docx` ساخته می‌شود.
- CLI به‌صورت پیش‌فرض فایل موجود را بازنویسی نمی‌کند؛ `--overwrite` یا `-f` این رفتار را فعال می‌کند.
- ورودی `-` به معنی خواندن متن از stdin است و در این حالت `-o` الزامی است.
- برای stdin، مبنای اولیهٔ مسیر تصاویر پوشهٔ جاری است. CLI گزینهٔ `--base-dir` ندارد.
- کد خروج کلی: `0` موفقیت، `1` خطای تبدیل/عملیاتی (مانند نبود LibreOffice یا خطای رندر)، `2` خطای کاربرد/اعتبارسنجی CLI یا پسوند نامعتبر.
- گزینه‌های تایپوگرافی و جهت در CLI:
  - `--direction [auto|rtl|ltr]`: جهت متن سند (پیش‌فرض `auto` با تحلیل هوشمند متن روایی).
  - `--text-align [start|right|left|center|both|justify]`: تراز پاراگراف‌های بدنه.
  - `--font, --font-family`: نام قلم متن فارسی / اسکریپت پیچیده (پیش‌فرض از قالب، مثلاً `Vazirmatn`).
  - `--heading-font`: نام قلم تیترها.
  - `--latin-font`: نام قلم عبارات لاتین (پیش‌فرض `Segoe UI`).
  - `--code-font`: نام قلم بلوک‌های کد و کدهای درون‌خطی (پیش‌فرض `Courier New`).
  - `--embed-fonts / --no-embed-fonts`: جاسازی قلم‌های TrueType در سند DOCX (پیش‌فرض: غیرفعال).

مثال stdin با newline واقعی:

```bash
md2docx convert - -o output.docx --template purple_book <<'MARKDOWN'
# عنوان سند

این یک متن فارسی در کنار SQL Server است.
MARKDOWN
```

### کتابخانهٔ Python

```python
from md_to_docx import Template, convert_markdown_to_docx, convert_markdown_to_pdf, convert_docx_to_pdf

saved_docx = convert_markdown_to_docx(
    input_path="input.md",
    output_path="output.docx",
    template="purple_book",
    overwrite=False,
)

saved_pdf = convert_markdown_to_pdf(
    input_path="input.md",
    output_path="output.pdf",
    template="purple_book",
    overwrite=False,
    keep_docx=False,
)

saved_converted_pdf = convert_docx_to_pdf(
    docx_path="output.docx",
    output_pdf_path="output.pdf",
    overwrite=False,
)

saved_from_text = convert_markdown_to_docx(
    content="# عنوان\n\nمتن فارسی و English.\n",
    base_dir=".",
    output_path="from-text.docx",
    template=Template.load("purple_book"),
    overwrite=False,
)
```

قرارداد فعلی `convert_markdown_to_docx`:

- `input_path`: مسیر فایل UTF-8؛ یا `content`: متن مستقیم Markdown. حداقل یکی لازم است.
- وقتی `content is not None` باشد، متن مستقیم بر محتوای فایل اولویت دارد؛ حتی رشتهٔ خالی ورودی مستقیم محسوب می‌شود.
- `base_dir` در شاخهٔ متن مستقیم برای مبنای مسیر دارایی‌هاست. اگر تعیین نشود، پوشهٔ `input_path` در صورت ارائه و سپس پوشهٔ جاری استفاده می‌شود. در شاخهٔ خواندن فایل، مبنا پوشهٔ فایل ورودی است.
- `output_path` در API پیش‌فرض `output.docx` دارد؛ مقدار برگشتی یک `Path` مطلق است.
- `template` نام قالب، مسیر پوشهٔ قالب یا شیء `Template` را می‌پذیرد.
- **پیش‌فرض `overwrite` در API برابر `True` است؛ با CLI فرق دارد.** در فراخوانی‌های جدید این مقدار را صریح تعیین کن.
- `media_dir` پوشهٔ اختصاصی PNGهای تولیدشدهٔ Mermaid را تعیین می‌کند؛ پیش‌فرض، `{output_stem}_media` کنار DOCX است.
- `render_mermaid_fn` نقطهٔ تزریق برای آزمون است؛ تابع، کد Mermaid، مسیر PNG و قالب را می‌گیرد و باید تصویر معتبر تولید کند.
- `warnings`: یک لیست اختیاری از رشته‌ها (`Optional[List[str]]`)؛ در صورت ارائه، هشدارهای تشخیصی تبدیل (مانند کپشن‌های بدون تصویر، استایل‌های سفارشی نگاشت‌نشده) در آن ثبت می‌شوند.
- محدودیت ورودی فعلی `20 * 1024 * 1024` بایت است؛ برای متن مستقیم با UTF-8 محاسبه می‌شود.
- API خودش تبدیل به `.doc` ندارد؛ همیشه نام خروجی `.docx` بده. کنترل پسوند API را هم‌ارز اعتبارسنجی CLI فرض نکن.

قرارداد `convert_markdown_to_pdf`:
- تمامی پارامترهای `convert_markdown_to_docx` را به همراه `keep_docx: bool = False` و `pdf_timeout: int = 120` می‌پذیرد.
- خروجی الزماً پسوند `.pdf` دارد؛ مسیر فایل میانی DOCX در صورت `keep_docx=True` با همان نام و پسوند `.docx` منتشر می‌شود.
- پوشهٔ مدیا در تبدیل PDF به‌طور خودکار سرکوب و پاکسازی می‌شود مگر اینکه `keep_docx=True` باشد یا `media_dir` صریحاً تعیین گردد.

قرارداد `convert_docx_to_pdf`:
- تبدیل مستقل سند DOCX موجود به PDF از طریق LibreOffice بدون‌سر.
- ورودی الزماً `.docx` موجود و خروجی الزماً `.pdf` است.
- پارامترهای `timeout: int = 120`، `overwrite: bool = True`، `soffice_binary: Optional[str | Path]` و `font_dirs: Optional[List[Path]]`.
- خروجی با اعتبارسنجی سربرگ `%PDF-` و تریلر `%%EOF` کنترل می‌شود.

## ۶. مسیر واقعی تبدیل

### مسیر ساخت DOCX:
```text
Markdown file / content / stdin
  → input validation + Template.load
  → temporary staging beside output
  → preprocess_admonitions
  → Pandoc: Markdown → JSON AST
  → process_mermaid_ast: Mermaid CodeBlock → PNG-backed figure
  → ast_to_docx + DocxRenderer
  → python-docx / OOXML → staged DOCX
  → locked publication + managed PNG files + staging cleanup
```

### مسیر ساخت PDF:
```text
Markdown file / content / stdin
  → preprocess_admonitions + Pandoc AST + process_mermaid_ast
  → DocxRenderer → Staged DOCX
  → Headless LibreOffice (ایزولاسیون با -env:UserInstallation، تزریق Fontconfig و کنترل Process Group)
  → Staged PDF → اعتبارسنجی یکپارچگی (is_valid_pdf: هدر، فوتر و اندازه)
  → انتشار اتمیک (قفل fcntl، بک‌آپ و rollback در صورت شکست)
  → پاکسازی دایرکتوری staging موقت
```

Pandoc با این reader فراخوانی می‌شود:

```text
markdown+fenced_divs+pipe_tables+backtick_code_blocks+raw_html+lists_without_preceding_blankline
```

نکات معماری هنگام تغییر:

- **Pandoc سازندهٔ DOCX نیست.** گزینهٔ `--reference-doc` مسیر اصلی این پروژه نیست.
- Mermaid در مسیر فعال **بعد از تجزیهٔ Markdown و داخل AST** پردازش می‌شود. توابع قدیمی متنی مانند `process_mermaid_blocks` هنوز در مخزن هستند؛ وجودشان به معنی استفاده در pipeline نیست.
- `pandoc_json.py` مسئول معنای ساختار و پیمایش است؛ `renderer.py` مسئول ایجاد اجزای Word و اعمال ظاهر؛ `oxml.py` محل ابزارهای سطح پایین XML است.
- برای حفظ متن غنی در جدول، فهرست و callout، ساختار AST را حفظ کن. تبدیل زودهنگام به رشته ممکن است لینک، تصویر، قالب‌بندی یا مرز پاراگراف را از بین ببرد.
- خطاهای تبدیل معمولاً `ConvertError` از `mermaid.py` هستند؛ خطاهای قالب زیرمجموعهٔ `TemplateError` در `template.py` هستند. API خطاهای استاندارد فایل/مقدار هم دارد.

## ۷. قالب‌ها: تعریف، تقدم و محدودیت‌ها

قالب اجرایی **یک پوشه دارای `config.yaml`** است. عکس نمونه یا یک فایل Word دلخواه به‌تنهایی قالب قابل بارگذاری نیست.

برای ساخت قالب جدید، نسخهٔ کامل `templates/purple_book/` را در پوشه‌ای جدید کپی کن، `name` و تنظیمات آن را تغییر بده و سپس `md2docx templates validate PATH` را اجرا کن. دارایی‌های ارجاع‌شده، از جمله فونت و تنظیمات Mermaid، باید موجود باشند.

- `schema_version: 1` الزامی است. ساختار معتبر و کلیدهای مجاز را از `Template._validate` بگیر؛ پذیرفته‌شدن یک کلید را بدون بررسی مصرف آن در renderer معادل اثرگذاری بصری تلقی نکن.
- بخش‌های الزامی فعلی: `name`، `direction`، `fonts`، `colors`، `headings`، `callouts`، `quotes` و `tables`.
- کلیدهای دیگر شامل `language_bidi`، `language_latin`، `font_files`، `page`، `code_block`، `mermaid`، `shell`، `custom_styles` و `caption` هستند.
- `custom_styles`: نگاشت نام سبک‌های سفارشی Pandoc fenced div به نقش‌های callout (مانند `note`, `warning`, `important`, `overview`, `lab`, `editorial`). کلید `strict: true` باید داخل همین نگاشت باشد؛ در آن حالت سبک ناشناخته به‌جای هشدار خطای `ConvertError` می‌دهد. `custom_styles_strict` کلید سطح‌بالای قالب نیست و در `ALLOWED_TOP_LEVEL` پذیرفته نمی‌شود.
- `page.paragraph_align`: تراز پاراگراف‌های بدنه؛ مقادیر مجاز `start` (پیش‌فرض راست‌چین با انتهای آزاد برای متن فارسی جهت جلوگیری از کشیدگی نامطلوب) یا `both` (تراز کامل/justified دوطرفه).
- `page.space_after_pt`: فاصلهٔ انتهای پاراگراف‌های بدنه بر حسب پوینت (پیش‌فرض ۶ پوینت).
- `caption.size_pt`: اندازهٔ فونت متن کپشن شکل‌ها و جدول‌ها بر حسب پوینت (مثلاً ۱۰ پوینت).
- ترتیب جست‌وجو: مسیر پوشهٔ معتبرِ ارائه‌شده؛ سپس `templates/` در پوشهٔ جاری؛ سپس `templates/` در ریشهٔ پروژه؛ و سپس قالب‌های داخل بستهٔ نصب‌شده.
- نسخهٔ ریشه و نسخهٔ `src/md_to_docx/templates/` باید هنگام تغییر قالب پیش‌فرض هماهنگ بمانند. موفقیت در checkout ممکن است خرابی داده‌های wheel را پنهان کند.

نقش‌های فونت پیش‌فرض:

| نقش | مقدار فعلی | کاربرد |
| --- | --- | --- |
| `fonts.body` | `Vazirmatn` | متن فارسی/complex script |
| `fonts.heading` | `Vazirmatn` | تیترها |
| `fonts.latin` | `Segoe UI` | بخش‌های لاتین متن |
| `fonts.code` | `Courier New` | کد |

برای تغییر فونت فارسی در سراسر قالب، نقش‌های مرتبط از جمله `body` و `heading` را تنظیم کن؛ تغییر یک نقش لزوماً نقش‌های مستقل دیگر را تغییر نمی‌دهد. فونت کد پیش‌فرض `Courier New` انتخاب شده تا در تمام نسخه‌های Word روی ویندوز، مک و لینوکس بدون نیاز به نصب فونت سیستمی جداگانه (نظیر DejaVu Sans Mono) به‌صورت monospace صحیح و یک‌دست نمایش داده شود، در حالی که در صورت نیاز کاربر می‌تواند مقدار `fonts.code` را در `config.yaml` تغییر دهد. `font_files` مسیر فایل فونت برای استفاده در رندر Mermaid را فراهم می‌کند. ثبت نام فونت در Word با جاسازی فایل فونت فرق دارد: **به‌صورت پیش‌فرض فونت در DOCX جاسازی نمی‌شود** مگر آنکه با گزینهٔ `--embed-fonts` در CLI یا پارامتر `embed_fonts=True` در API درخواست شود (که در آن صورت فونت‌های TrueType معتبر قالب با اعتبارسنجی مجوز `fsType` درون پکیج جاسازی می‌شوند). در غیاب جاسازی، دستگاه نمایش‌دهنده باید فونت را داشته باشد یا از جایگزین استفاده خواهد کرد. مجوز فونت همراه دارایی‌ها در `fonts/OFL.txt` نگهداری می‌شود.

`page` اندازه و حاشیهٔ صفحه و تنظیمات متن پایه را تعیین می‌کند. اندازه‌های شناخته‌شدهٔ فعلی `A4`، `A5`، `Letter` و `Legal` هستند. رنگ‌ها می‌توانند hex یا در محل‌های پشتیبانی‌شده نام رنگ در palette باشند. واحدها را با نام کلید و مصرف‌کننده کنترل کن؛ واحد OOXML برای همهٔ اندازه‌ها یکسان نیست.

### پوستهٔ Word

- `shell.docx` در پوشهٔ قالب، یا فایل معرفی‌شده با کلید `shell`، اختیاری است.
- renderer تنها پوستهٔ **تک‌بخشی / single-section** را می‌پذیرد. پوستهٔ چندبخشی خطا می‌دهد.
- محتوای body پوسته حذف و محتوای جدید جایگزین می‌شود؛ این مسیر برای پر کردن placeholderهای دلخواه یا حفظ صفحات آمادهٔ body نیست.
- ساختار موجود header/footer و section مبنای سند می‌ماند، اما تنظیمات اندازه و حاشیهٔ صفحه از YAML بر هندسهٔ پوسته مقدم‌اند. استایل پایه و اجزای جدید نیز توسط renderer تنظیم می‌شوند.
- حفظ بی‌کم‌وکاست همهٔ ویژگی‌های هر فایل Word، تمام sectionها، طراحی‌های متفاوت صفحه یا هر لوگو/فیلد/شکل دلخواه را بدون آزمون نمونهٔ واقعی وعده نده.

## ۸. قابلیت‌های محتوایی و مرز پشتیبانی

| قابلیت | مسیر موجود و نکتهٔ مهم |
| --- | --- |
| متن فارسی و مخلوط | قطعه‌بندی script در `bidi.py` و اعمال مشخصات پاراگراف/run؛ ترتیب بصری باید جداگانه بررسی شود |
| تیترهای ۱ تا ۶ | طراحی بر پایهٔ قالب؛ شماره از متن Markdown استخراج می‌شود و شماره‌گذاری خودکار Word نیست |
| bold، italic، strike و سایر inlineها | در `emit_inlines` نگاشت می‌شوند؛ برای ترکیب‌ها و محتوای تو‌در‌تو تست لازم است |
| لینک | hyperlink واقعی ساخته می‌شود؛ متن، مقصد و لینک داخلی را جداگانه بررسی کن |
| code block | Pygments، فونت کد و جهت LTR؛ رنگ‌بندی باید با حفظ دقیق متن، indentation و خطوط خالی همراه باشد |
| Mermaid | fence با زبان `mermaid` به PNG تبدیل و در DOCX جاسازی می‌شود؛ داخل Word نمودار قابل ویرایش Mermaid نیست |
| تصویر Markdown | تصویر محلی inline یا block، همراه با مدیریت اندازه؛ PNG/JPEG نمونه‌های معمول‌اند، همهٔ فرمت‌های تصویر را قابل پشتیبانی فرض نکن |
| جدول | ساختار جدول Pandoc، سرستون، caption و جهت بصری؛ `rowspan` یا `colspan` بیشتر از ۱ صریحاً رد می‌شود |
| فهرست‌ها | bullet و ordered با نشانگر متنی؛ numbering بومی قابل ادامه‌دادن در Word تولید نمی‌شود |
| quote و callout | blockquote، fenced Div و alertهای شناخته‌شدهٔ GFM؛ پیش‌پردازش نباید محتوای literal داخل code fence را تغییر دهد |
| فرمول | OMML برای زیرمجموعهٔ محدودی از TeX مثل کسر، جمع و توان/اندیس؛ موتور کامل LaTeX نیست |
| پاورقی | part واقعی `word/footnotes.xml` با `FootnoteContainer` و dispatch بلوک‌ها؛ تصویر/جدول/کد تو‌در‌تو باید با نمونهٔ واقعی بررسی شوند |
| raw HTML | چند الگوی شناخته‌شده مثل break/comment پردازش می‌شوند؛ برخی الگوها رد و بقیه ممکن است به متن تبدیل شوند؛ موتور رندر HTML/CSS نیست |

«پشتیبانی کامل از Markdown» باید به **dialect مشخص، ASTهای پشتیبانی‌شده و نمونه‌های آزموده‌شده** ترجمه شود. پشتیبانی از یک node در سطح اصلی، تضمین پشتیبانی همان محتوا در هر ترکیب تو‌در‌تو نیست؛ به‌خصوص Mermaid در جدول، تعریف‌نامه یا پاورقی را با نمونهٔ واقعی بررسی کن. برای node ناشناخته مسیر خطا/جایگزین را در adapter ببین و حذف بی‌صدای محتوا اضافه نکن.

### مسیر تصاویر و caption

- برای فایل Markdown، مبنای اصلی تصویر پوشهٔ همان فایل است. برای متن مستقیم، قواعد `base_dir` بخش API اعمال می‌شوند.
- `paths.py` مسیر مطلق، `file:` و percent-encoding را پردازش می‌کند. `http:`، `https:` و `data:` برای تصویر رد می‌شوند؛ دانلود خودکار تصویر وجود ندارد.
- resolver تصویر مسیر مطلق، `file:` و percent-encoding را پردازش می‌کند و fallback نام‌فایل/cwd ندارد؛ تصویر گمشده باید خطا بدهد نه انتخاب فایل هم‌نام اتفاقی.
- caption پس از تصویر/نمودار با الگوهایی مانند `شکل`، `Figure` و `Fig.` شناخته می‌شود؛ پاراگراف معمولی بعدی نباید بی‌دلیل مصرف شود.
- تصاویر باید نسبت ابعاد را حفظ کنند و با عرض ظرف جاری و ارتفاع قابل استفاده سازگار باشند؛ عرض صفحه برای تصویر داخل سلول معیار کافی نیست.

## ۹. اصول فنی حساس به رگرسیون

- راست‌چین کردن با راست‌به‌چپ کردن یکسان نیست. تنظیمات پاراگراف `w:bidi`، run یعنی `w:rtl` و جدول یعنی `w:bidiVisual` نقش‌های جدا دارند.
- حذف تنظیم RTL همیشه معادل LTR صریح نیست؛ استایل به‌ارث‌رسیده می‌تواند جهت را برگرداند. کد و عبارت لاتین در قالب RTL را حتماً بررسی کن.
- complex script به تنظیم فونت و اندازه و bold/italic متناظر مثل `w:cs`، `w:szCs`، `w:bCs` و `w:iCs` نیاز دارد؛ فقط تنظیم Latin font کافی نیست.
- متن فارسی، نیم‌فاصله، علائم، شماره‌های تیتر و متن مخلوط را صرفاً برای بهتر شدن ظاهر بازنویسی نکن. تبدیل ارقام باید در محل و دامنهٔ مشخص باشد.
- کادر کد، callout و بعضی تیترها با جدول ساخته می‌شوند. تغییر table helper ممکن است روی چند قابلیت اثر بگذارد؛ همهٔ جدول‌ها جدول داده نیستند.
- badge تیتر، caption، مرز کادر و شکست صفحه باید در سند چندصفحه‌ای بررسی شوند؛ شمارهٔ چندبخشی طولانی می‌تواند مشکلی را آشکار کند که تیتر کوتاه نشان نمی‌دهد.
- برای افزودن ویژگی قالب، زنجیرهٔ **اعتبارسنجی → بارگذاری → مصرف در renderer → تست → نمونه و مستندات** باید کامل باشد.

## ۱۰. فایل‌های خروجی، staging و ایمنی تغییرات

pipeline ابتدا سند و نمودارها را در پوشهٔ staging کنار خروجی می‌سازد، سپس با قفل درون‌پردازه‌ای و `fcntl.flock` منتشر می‌کند. فایل قفل `.{output_stem}.publish.lock` عمداً باقی می‌ماند تا منتظرها روی همان inode هماهنگ باشند؛ آن را به‌عنوان فایل زائد هنگام اجرای هم‌زمان حذف نکن.

- PNGها در خود DOCX جاسازی می‌شوند؛ فایل Word پس از حذف پوشهٔ جانبی media هم باید تصاویر را داشته باشد.
- در پوشهٔ media، الگوی `diagram_*.png` متعلق به خروجی تولیدکننده تلقی می‌شود و نسخه‌های قدیمی با همین الگو ممکن است پاک شوند. پوشهٔ اختصاصی انتخاب کن.
- `media_dir` نباید خود پوشهٔ ورودی، پوشهٔ خروجی، ریشهٔ پروژه، cwd یا ریشهٔ فایل‌سیستم باشد؛ کنترل مربوط در `_assert_safe_media_dir` است.
- پاک‌سازی staging را به حذف بازگشتی پوشهٔ دارایی‌های کاربر تبدیل نکن. ورودی، قالب و فایل‌های نامرتبط باید حفظ شوند.
- وجود staging و backup به معنی تراکنش کاملاً اتمیک برای **مجموعهٔ DOCX و تمام mediaها** یا تضمین بازیابی پس از قطع برق نیست؛ ادعای رفتار قوی‌تر نیازمند تست و طراحی مربوط است.
- فایل‌های DOCX نمونه ممکن است tracked باشند. `scripts/convert_fixtures.py` آن‌ها را بازنویسی می‌کند؛ فقط برای بازتولید عمدی اجرا شود. خروجی آزمون موقت را در `tmp_path` یا پوشهٔ موقت مستقل بساز.

## ۱۱. تست، TDD و بررسی کیفیت

برای تغییر رفتار: **ابتدا تست شکست‌خوردهٔ مسئله، سپس کوچک‌ترین اصلاح لازم، سپس refactor**. یک شکست واقعی را مشاهده کن؛ تستی که فقط همان پیاده‌سازی را تکرار کند یا با mock نتیجهٔ مطلوب را تحمیل کند، اثبات رفع مشکل نیست. تغییر صرفاً مستنداتی به اجرای کامل موتور یا ساختن تست ساختگی نیاز ندارد.

دستورات زیر پس از فعال‌سازی `.venv` و از ریشهٔ پروژه اجرا می‌شوند:

```bash
# نزدیک‌ترین تست‌ها به حوزهٔ تغییر؛ مثال:
python -m pytest tests/test_template.py tests/test_renderer.py -q

# زیرمجموعهٔ مورد استفاده در job واحد CI:
python -m pytest tests -q -m "not (mermaid or integration)" -k "not test_smoke_wheel_build_and_template_assets"

# اجرای مجموعه و نمایش علت skipها:
python -m pytest tests -q -rs

# مسیر بررسی با ابزارهای خارجی آماده:
MD2DOCX_REQUIRE_EXTERNAL=1 python -m pytest tests -v -rs
```

حتی زیرمجموعهٔ «unit» بالا می‌تواند به Pandoc نیاز داشته باشد. markerهای تعریف‌شده `pandoc`، `mermaid` و `integration` هستند. در تست‌هایی که آن را رعایت می‌کنند، `MD2DOCX_REQUIRE_EXTERNAL=1` نبود renderer خارجی را از skip به failure تبدیل می‌کند؛ فرض نکن این متغیر هر نوع skip در کل suite را ممنوع می‌کند.

| نوع تغییر | نقطه‌های اصلی بررسی |
| --- | --- |
| CLI، stdin، API و انتشار | `test_cli.py`، `test_pipeline.py`، `test_finalize.py` |
| قالب، پوسته، فونت و هندسه | `test_template.py`، `test_renderer.py`، `test_oxml.py` و رندر چندصفحه‌ای |
| AST و محتوای تو‌در‌تو | `test_pandoc_json.py`، `test_comprehensive_ast.py`، `test_fixtures.py` |
| فارسی و متن مخلوط | `test_bidi.py`، `test_rtl_quality.py`، `test_text_fuzz.py` |
| Mermaid و fenceها | `test_mermaid.py`، `test_admonitions.py`، `test_pipeline.py` و اجرای واقعی mmdc |
| تیترها و شماره‌ها | `test_headings.py`، تست renderer و مشاهدهٔ شکست صفحه |
| فرمول، پاورقی و اصلاحات نهایی | `test_finalize.py` به‌علاوهٔ بررسی معنای محتوا و ساختار DOCX |
| کیفیت چیدمان فارسی و اوراکل‌ها | `test_persian_layout_quality.py` و ماتریس `scripts/matrix_runner.py` |
| بسته‌بندی و قالب همراه wheel | `test_smoke.py` و نصب/اجرا خارج از checkout |

نام‌های جدول نسبت به پوشهٔ `tests/` هستند. `test_finalize.py` رگرسیون‌های FIN-01 تا FIN-14 را نگهداری می‌کند؛ `test_persian_layout_quality.py` آزمون‌های Q03 تا Q16 و اوراکل‌های شمارشی و متنی را پوشش می‌دهد.

### بازتولید ماتریس کیفیت چیدمان فارسی (۲۴۴ زوج)

برای اجرای ماتریس کامل ۶۱ فیکسچر × ۴ قالب و ارزیابی اوراکل‌های ساختاری و محتوایی:

```bash
python scripts/matrix_runner.py
# یا اجرای گزینشی برای چند فیکسچر مشخص:
python scripts/matrix_runner.py --fixtures S01,S05,S11,B00 --templates purple_book,persian_book
```

خروجی در `artifacts/persian-layout/run_<timestamp>/` تولید شده و شامل فایل‌های `matrix.csv`، `run.json`، `reviews.json`، `summary.md` و `index.html` است.

### اعتبارسنجی خروجی برای تغییرات رندر

1. ورودی نمایندهٔ فارسی، انگلیسی و مخلوط را با قالب پیش‌فرض و یک قالب سفارشی تبدیل کن؛ مسیر فایل و متن مستقیم را متناسب با تغییر پوشش بده.
2. متن و ساختار DOCX را بررسی کن: ترتیب محتوا، style/runها، جدول‌ها، mediaها، relationshipها، پاورقی و فرمول در صورت وجود.
3. سند چندصفحه‌ای را در Word یا یک renderer در دسترس باز/رندر کن و **همهٔ صفحات** را بررسی کن: فونت فارسی، جهت، بریدگی کد، سرریز تصویر، جدول، تیتر یتیم و یک‌دستی header/footer.
4. نتیجهٔ مشاهده در Word را از LibreOffice جدا گزارش کن؛ فونت جایگزین و موتور صفحه‌بندی ممکن است خروجی متفاوتی بدهند. اگر Word بررسی نشده، صریح بگو.
5. تعداد pass/fail/skip، ابزار استفاده‌شده و محدودیت محیط را از اجرای واقعی گزارش کن. «همه‌چیز کامل است» را از وجود فایل یا موفقیت بخشی از تست‌ها نتیجه نگیر.

در محیط محدود، خطای دانلود وابستگی، نبود build backend در محیط ایزوله، نبود Pandoc یا اجرا نشدن Chrome را از اشکال خود تبدیل تفکیک کن. تست را برای سبز کردن گزارش حذف/ضعیف نکن. همان بررسی‌های ممکن را کامل کن و بخش اجرا‌نشده را مشخص نگه دار.

## ۱۲. روش تحویل و نگهداری راهنما

- دامنهٔ تغییر را به درخواست جاری محدود کن؛ تغییرات سایر عوامل را reset، پاک یا بازنویسی نکن.
- برای رفع یک مشکل، تا زمانی که لازم نیست معماری را عوض نکن یا وابستگی سنگین اضافه نکن.
- اگر ورودی پشتیبانی نمی‌شود، خطای روشن یا محدودیت مستند بهتر از خروجی ظاهراً موفق با محتوای ناقص است.
- هنگام تغییر قرارداد API/CLI، schema قالب یا معماری، همین راهنما و README را با رفتار نهایی هماهنگ کن.
- پلن‌های `fix.md` و `finalize.md` را تاریخچه و منبع سناریوهای رگرسیون بدان؛ قبل از بازکردن دوبارهٔ هر مورد، آن را روی کد فعلی بازتولید کن.
- برای ادعای آمادگی تحویل، تبدیل واقعی **Markdown + قالب سفارشی → DOCX** باید همراه با فارسی، Vazirmatn قابل تنظیم، Mermaid، کد رنگی، تصویر و یک‌دستی چندصفحه‌ای بررسی شده باشد. محدودیت‌های بخش‌های بالا باید شفاف بمانند.
- در پاسخ نهایی، به زبان کاربر توضیح بده چه چیزی تغییر کرد، چگونه بررسی شد و چه محدودیت مؤثری باقی است. مسیر فایل تحویلی را بده. نمره یا تضمین کیفیت را بدون شواهد تازه تکرار نکن.

این فایل راهنمای کار و شناخت پروژه است؛ نوشتن آن به معنی اجرای دوبارهٔ تست‌ها، رفع ایرادهای کد یا تأیید نهایی کیفیت محصول نیست.
