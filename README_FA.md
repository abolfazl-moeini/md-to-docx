# md-to-docx

<p align="left">
  <b>فارسی</b> | <a href="README.md"><b>English Version</b></a>
</p>

**مبدل متون فنی Markdown دو زبانه (فارسی و انگلیسی) + نمودارهای Mermaid به اسناد رسمی Word (.docx) و PDF (.pdf)**

این ابزار مستندات متنی Markdown را به اسناد حرفه‌ای Word و فایل‌های آمادهٔ چاپ PDF با استایل اداری تبدیل می‌کند: متن راست‌به‌چپ (RTL)، جداسازی خودکار عبارات ترکیبی فارسی و انگلیسی، بج‌های شماره‌گذاری‌شدهٔ عناوین، کادرهای هشدار و نکته (Callouts)، جداول استاندارد راست‌به‌چپ، بلوک‌های کد چپ‌چین با رنگ‌آمیزی ساختاری (Syntax Highlighting)، و نمودارهای شفاف و باکیفیت Mermaid.

<p align="center">
  <img src="sample-template/1.jpg" alt="نمونه خروجی سند Word: بج‌های عناوین، نمودار Mermaid، کادر نکته" width="100%">
</p>
<p align="center">
  <img src="sample-template/2.jpg" alt="نمونه خروجی سند Word: کادر هشدار، نقل‌قول و جدول راست‌به‌چپ" width="420">
</p>

---

## TL;DR — راهنمای راه‌اندازی و تبدیل سریع

خلاصهٔ جریان تبدیل: **قالب (Template) + فایل یا متن مستقیم (Markdown Content / File) → سند Word (.docx) یا سند PDF (.pdf)**

### ۱. راه‌اندازی و نصب پیش‌نیازها (فقط یک‌بار)

```bash
./scripts/bootstrap.sh
source .venv/bin/activate
```

### ۲. تبدیل سریع از طریق خط فرمان (CLI)

```bash
# الف) تبدیل فایل Markdown به سند Word (.docx):
md2docx convert input.md -o output.docx --template purple_book

# ب) تبدیل مستقیم فایل Markdown به سند PDF (.pdf) از طریق LibreOffice Headless:
md2docx convert input.md -o output.pdf --template purple_book

# ج) ورودی مستقیم از طریق پایپ متن (Standard Input):
echo "# عنوان سند\n\nمتن نمونه برای تبدیل." | md2docx convert - -o output.docx --template purple_book

# د) تبدیل فایل DOCX موجود به PDF:
md2docx to-pdf input.docx -o output.pdf
```

### ۳. استفاده از کتابخانه در پایتون (Python API)

```python
from md_to_docx import convert_markdown_to_docx, convert_markdown_to_pdf, convert_docx_to_pdf

# تبدیل Markdown به سند Word (.docx)
convert_markdown_to_docx(
    input_path="document.md",
    output_path="output.docx",
    template="purple_book",  # یا مسیر پوشه قالب سفارشی: './templates/my_theme'
    overwrite=True,
)

# تبدیل مستقیم Markdown به PDF (.pdf) با استفاده از LibreOffice Headless
convert_markdown_to_pdf(
    input_path="document.md",
    output_path="output.pdf",
    template="purple_book",
    overwrite=True,
    keep_docx=False,  # در صورت True، فایل میانی output.docx نیز حفظ می‌شود
)

# تبدیل فایل DOCX موجود به PDF
convert_docx_to_pdf("output.docx", "output.pdf", overwrite=True)
```

| مؤلفه | نوع | توضیحات |
| :--- | :--- | :--- |
| **ورودی ۱: Template** | نام یا مسیر پوشه | تم پیش‌فرض `purple_book` یا هر پوشهٔ حاوی `config.yaml` با تنظیم رنگ‌ها، ابعاد صفحه، قلم‌ها و استایل‌ها |
| **ورودی ۲: Markdown** | مسیر فایل یا متن رشته‌ای | فایل `.md` از طریق مسیر (`input_path`) یا متن مستقیم مارک‌داون (`content` در پایتون / stdin `-` در CLI) |
| **خروجی: Word File** | فایل خروجی Word | سند رسمی با پسوند **`.docx`** (چینش کامل راست‌به‌چپ، قلم وزیرمتن، بج‌های عناوین، جداول و نمودارهای تعبیه‌شده) |
| **خروجی: PDF File** | فایل خروجی PDF | سند نهایی با پسوند **`.pdf`** تولیدشده توسط موتور ایزولهٔ LibreOffice همراه با تزریق قلم و اعتبارسنجی یکپارچگی |

---

## چرا این ابزار ساخته شد؟

خروجی پیش‌فرض پاندوک (Pandoc) برای DOCX همواره چپ‌چین (LTR) بوده و نمودارهای Mermaid را نادیده می‌گیرد. قالب‌های کمکی `--reference-doc` چینی نیز به دلیل فونت‌های شرق آسیا و تورفتگی سطر اول، خروجی مناسبی برای زبان فارسی ایجاد نمی‌کنند. این ابزار از پاندوک صرفاً به عنوان مفسر ساختار متن (AST Parser) بهره می‌برد و سپس با استفاده از `python-docx` مستقیماً عناصر باز OOXML را تولید می‌نماید:

- سند و جداول کاملاً راست‌به‌چپ هستند (`w:bidi`, `w:bidiVisual`).
- فونت‌های اسکریپت پیچیده (Complex Script) و اندازهٔ متناسب قلم تنظیم می‌شوند (`w:cs`, `w:szCs`, `fa-IR`).
- شمارهٔ عناوین مانند `۱.۴.۱` از متن مارک‌داون استخراج شده و شماره‌گذاری خودکار Word آن را مخدوش نمی‌کند.
- ساختارهای `::: note` و `::: warning` به کادرهای رنگی با سربرگ متمایز تبدیل می‌شوند.
- نمودارهای `mermaid` از طریق `mermaid-cli` رندر شده و به صورت تصاویر باکیفیت PNG درون سند تعبیه می‌گردند.

---

## ویژگی‌های اصلی

| ورودی Markdown | خروجی در Word |
| :--- | :--- |
| `# ۱.۵ عنوان فصل` | بج شماره‌گذاری بنفش در سمت راست + خط زیر عنوان |
| ترکیب فارسی و انگلیسی `Clientها` / `SQL Server` | جداسازی قطعه‌های متن جهت جلوگیری از معکوس شدن عبارات لاتین |
| `::: note نکتهٔ DBA` | کادر بنفش با نشانهٔ `◆` و بدنهٔ روشن |
| `::: warning هشدار` | کادر کرم-قهوه‌ای با عنوان واضح بدون اموجی |
| `> نقل قول` | نوار بنفش ضخیم در **سمت راست فیزیکی** + پس‌زمینه `#ECE4F1` |
| جدول GFM | هدر بنفش تیره با فونت سفید، ستون‌ها با جهت راست‌به‌چپ بصری |
| ` ```mermaid ` + `شکل ۲-۱. …` | نمودار وسط‌چین PNG با کپشن استاندارد زیر تصویر |
| ` ```python ` / `sql` / `ts` | کادر shaded چپ‌چین با رنگ‌آمیزی نحوی Pygments |

همچنین پشتیبانی کامل از هشدارهای مدرن گیت‌هاب (`> [!NOTE]` و `> [!WARNING]`)، لیست‌ها، تصاویر محلی، لینک‌های داخلی و خارجی، فرمول‌های ریاضی و پاورقی وجود دارد.

---

## پیش‌نیازهای سیستم

- **پایتون ۳.۱۱ یا بالاتر**
- **[Pandoc](https://pandoc.org) نسخه ۳ به بعد** (فقط برای پارس مارک‌داون)
- **Node.js نسخه ۲۲.۱۲.۰ به بعد** (جهت اجرای mermaid-cli)
- **گوگل کروم یا کرومیوم** (جهت رندر با Puppeteer)
- **[LibreOffice](https://www.libreoffice.org)** (الزامی برای تبدیل PDF: دستور `brew install --cask libreoffice` در مک، `sudo apt install libreoffice` در اوبونتو/دبیان، `sudo dnf install libreoffice` در فدورا؛ یا تنظیم متغیر محیطی `MD2DOCX_SOFFICE`)

> [!TIP]
> برای نمایش صحیح قلم‌ها در رایانهٔ مقصد، فونت [وزیرمتن (Vazirmatn)](https://github.com/rastikerdar/vazirmatn) را روی سیستم مقصد نصب کنید.

---

## راه‌اندازی و محیط توسعه

اسکریپت خودکار زیر تمام پیش‌نیازها شامل محیط مجازی پایتون، پکیج‌های Node، مرورگر کرومیوم برای Puppeteer و کنترل پاندوک را بررسی و تنظیم می‌کند:

```bash
./scripts/bootstrap.sh
```

یا به صورت دستی:

```bash
# در مک:
brew install pandoc
brew install --cask libreoffice    # الزامی برای خروجی PDF

python3.11 -m venv .venv
source .venv/bin/activate
pip install -c constraints.txt -e ".[dev]"
npm ci
npx puppeteer browsers install chrome-headless-shell
```

---

## دستورات خط فرمان (CLI)

### دستورات اصلی تبدیل

```bash
# تبدیل Markdown به سند Word (.docx)
md2docx convert chapter.md -o chapter.docx

# تبدیل مستقیم Markdown به PDF (.pdf) با LibreOffice
md2docx convert chapter.md -o chapter.pdf

# تبدیل Markdown به PDF همراه با ذخیره فایل میانی DOCX
md2docx convert chapter.md -o chapter.pdf --keep-docx

# تبدیل Markdown به PDF با مهلت زمانی سفارشی (پیش‌فرض: ۱۲۰ ثانیه)
md2docx convert chapter.md -o chapter.pdf --pdf-timeout 180

# تبدیل فایل DOCX موجود به PDF
md2docx to-pdf chapter.docx -o chapter.pdf --pdf-timeout 120

# رونویسی صریح فایل موجود با پرچم --overwrite
md2docx convert chapter.md -o chapter.docx --overwrite

# استفاده از قالب سفارشی
md2docx convert chapter.md -o chapter.docx --template purple_book
md2docx convert chapter.md -o chapter.docx --template ./templates/my_theme

# مشاهده و اعتبارسنجی قالب‌ها
md2docx templates list
md2docx templates validate purple_book

# تبدیل معکوس DOCX به مارک‌داون و استخراج تصاویر
md2docx to-md chapter.docx -o chapter.md
```

### گزینه‌ها و فلگ‌های خط فرمان (CLI)

#### گزینه‌ها و فلگ‌های دستور `convert`

دستور `convert` برای تبدیل Markdown به سند Word یا PDF با امکانات کامل کنترل چیدمان و تایپوگرافی استفاده می‌شود:

| فلگ | شرح | مقادیر / پیش‌فرض |
| :--- | :--- | :--- |
| `-o, --output` | مسیر فایل خروجی (`.docx` یا `.pdf`) | پیش‌فرض: `{input}.docx` |
| `-t, --template` | نام یا مسیر پوشهٔ قالب | پیش‌فرض: `purple_book` |
| `-f, --overwrite` | رونویسی روی فایل موجود در صورت وجود | `False` |
| `--keep-docx` | نگهداری فایل میانی DOCX هنگام تولید PDF | `False` |
| `--pdf-timeout` | مهلت زمانی اجرای LibreOffice بر حسب ثانیه | `120` |
| `--direction, --dir` | جهت متن سند | `auto` (پیش‌فرض با تشخیص هوشمند متن)، `rtl`، `ltr` |
| `--text-align, --align` | تراز متن پاراگراف‌های بدنه | `start` (راست‌چین آزاد)، `right`، `left`، `center`، `both` (تراز دوطرفه) |
| `--font, --font-family` | قلم متن فارسی / بدنه | قلم قالب (پیش‌فرض `Vazirmatn`) |
| `--heading-font` | قلم سفارشی عناوین | قلم عناوین در قالب |
| `--latin-font` | قلم سفارشی بخش‌های لاتین | قلم لاتین قالب (`Segoe UI`) |
| `--code-font` | قلم سفارشی بلوک‌ها و کدهای درون‌خطی | قلم کد قالب (`Courier New`) |
| `--embed-fonts / --no-embed-fonts` | جاسازی فایل فونت TrueType در فایل DOCX | `--no-embed-fonts` |

#### گزینه‌های دستور `to-pdf`

دستور `to-pdf` برای تبدیل مستقیم یک فایل موجود `.docx` به فایل `.pdf` از طریق LibreOffice استفاده می‌شود:

| فلگ | شرح | مقادیر / پیش‌فرض |
| :--- | :--- | :--- |
| `-o, --output` | مسیر فایل خروجی PDF | پیش‌فرض: `{input}.pdf` |
| `-f, --overwrite` | رونویسی روی فایل خروجی موجود | `False` |
| `--timeout, --pdf-timeout` | مهلت زمانی تبدیل LibreOffice بر حسب ثانیه | `120` |

---

## ماتریس سازگاری Pandoc AST

| دسته‌بندی | نوع گره‌ها | رفتار خروجی |
| :--- | :--- | :--- |
| **Inlines** | `Str`, `Space`, `SoftBreak`, `LineBreak` | جداسازی دوزبانه متن، اعمال قلم Vazirmatn و قلم لاتین |
| | `Strong`, `Emph` | بولد (`w:b`, `w:bCs`) و ایتالیک (`w:i`, `w:iCs`) |
| | `Strikeout` | خط‌خورده (`w:strike`) |
| | `Superscript`, `Subscript` | بالانویس و پایین‌نویس (`w:vertAlign`) |
| | `Underline` | خط زیرین تک‌خطه (`w:u`) |
| | `SmallCaps` | حروف کوچک بزرگ‌نما (`w:smallCaps`) |
| | `Code` | کد درون‌خطی مونو‌اسپیس با قلم `Courier New` و جهت LTR |
| | `Link`, `Quoted`, `Span` | پیوندهای واقعی Word، حفظ نشانه‌های نقل‌قول گیومه (« »)، و استایل‌های Span |
| | `Note` | پاورقی واقعی در سند Word (`word/footnotes.xml`) |
| | `Math` | فرمول‌های بومی آفیس (`m:oMath`) برای معادلات TeX نظیر کسرها و مجموع‌ها |
| **Blocks** | `Header` (سطوح ۱ تا ۶) | بج‌های شماره‌گذاری راست‌به‌چپ یا خط حاشیه زیر عنوان با کنترل حفظ صفحه |
| | `Para`, `Plain` | پاراگراف‌های متناسب تراز شده با فاصله خطوط استاندارد |
| | `BlockQuote` | جعبه با پس‌زمینهٔ ملایم و نوار ضخیم در سمت راست فیزیکی |
| | `Div` (کادرها) | پشتیبانی از ساختارهای `::: note` و هشدارهای GFM با حفظ قالب‌بندی داخلی |
| | `Div` (Mermaid) | کامپایل خودکار دیاگرام‌ها به تصویر PNG و قرارگیری در مرکز |
| | `Table` | جداول چند ردیفه با سربرگ تکرارشونده در صفحات بعد و چینش راست‌به‌چپ |
| | `CodeBlock` | بلوک کد چپ‌چین با پس‌زمینه رنگی و حفظ فواصل و خطوط خالی |
| | `BulletList`, `OrderedList`| لیست‌های ترتیبی و غیرترتیبی با تورفتگی مناسب |
| | `DefinitionList` | لیست‌های تعاریف با عبارات برجسته و توضیحات تو رفته |
| | `HorizontalRule` | خط جداکننده افقی ظریف |

---

## قالب‌های از پیش ساخته‌شده (Templates)

این مخزن شامل ۴ قالب آماده و استاندارد متناسب با انواع اسناد است:

| نام قالب | اندازه صفحه | تراز پاراگراف | توضیحات |
| :--- | :--- | :--- | :--- |
| `purple_book` | A4 | `start` (راست‌چین آزاد) | قالب پیش‌فرض با تم بنفش، بج‌های تزئینی عناوین، و لبهٔ راست‌چین آزاد برای تایپوگرافی بهینهٔ فارسی. |
| `persian_book` | A4 | `start` (راست‌چین آزاد) | قالب کتاب فنی با شکست صفحه قبل از هر عنوان سطح ۱، سرصفحه/پاصفحهٔ خنثی، و انتهای آزاد برای حداکثر خوانایی متن فارسی. |
| `persian_compact`| A5 | `start` (راست‌چین آزاد) | قالب کتابچهٔ فشرده با حاشیه‌های کم، مناسب قطع A5. |
| `persian_report` | Letter | `start` (راست‌چین آزاد) | قالب گزارش سازمانی رسمی با عناوین پیوسته، لوگوی تعبیه‌شده در سربرگ و شماره صفحهٔ پویا در پاورقی. |

### کلیدهای تنظیمی قالب (`config.yaml`)

- `page.paragraph_align`: تراز متن بدنه؛ مقدار `start` (راست‌چین با انتهای آزاد، جهت رفع کشیدگی‌های نامطلوب کلمات در متن فنی فارسی) یا `both` (تراز دوطرفه).
- `page.space_after_pt`: فاصلهٔ انتهای هر پاراگراف بر حسب پوینت (پیش‌فرض: `۶.۰`).
- `caption.size_pt`: اندازهٔ قلم زیرنویس تصاویر و جداول (مثلاً `۱۰.۰`).
- `custom_styles`: نگاشت نام سبک‌های سفارشی مارک‌داون به نقش‌های کادر. کلید `strict` باید **داخل همین نگاشت** باشد (کلید سطح‌بالای قالب نیست):
  ```yaml
  custom_styles:
    strict: false  # اگر true باشد، سبک‌های ناشناخته باعث خطا می‌شوند
    "Field Note": note
    "Security Alert": warning
  ```
- بلوک کد در هر چهار قالب با **Courier New** است. پلن چیدمان DejaVu Sans Mono را پیشنهاد کرده بود؛ آن قلم همراه بسته نیست. این یک انتخاب طراحی صریح است تا متن مونواسپیس روی قلمی باشد که معمولاً در Word موجود است.

### فونت‌ها و تصمیم طراحی قلم کد (Typography)

- **متن فارسی (`fonts.body`, `fonts.heading`)**: قلم پیش‌فرض `Vazirmatn` است. هر دو وزن عادی و ضخیم (`Vazirmatn-Regular.ttf`, `Vazirmatn-Bold.ttf`) در پوشهٔ تمام ۴ قالب همراه سند بسته‌بندی شده‌اند.
- **متن لاتین (`fonts.latin`)**: قلم `Segoe UI` (یا `Vazirmatn`).
- **بلوک‌های کد و متن یکپارچه (`fonts.code`)**: قلم `Courier New`.
  > **تصمیم طراحی در مورد فونت کد**: قلم `Courier New` به عنوان فونت پیش‌فرض کد در هر چهار قالب تنظیم شده است. وجود آن در سیستم‌عامل‌های مختلف یک واقعیت محیطی است و تضمین قطعی محسوب نمی‌شود (بررسی وجود آن در محیط نمایش سند توصیه می‌شود). قلم `DejaVu Sans Mono` همراه بسته نیست. در صورت تمایل، کاربر می‌تواند مقدار `fonts.code` را در `config.yaml` قالب دلخواه خود تغییر دهد.

### ساخت قالب اختصاصی جدید

```bash
cp -R templates/persian_book templates/my_theme
# ویرایش templates/my_theme/config.yaml
md2docx templates validate my_theme
md2docx convert input.md --template my_theme -o out.docx
```

---

## ماتریس و آزمون جامع کیفیت چیدمان فارسی

مجموعه آزمون ماتریسی خودکار ۲۴۴ ترکیب (۶۱ فیکسچر استاندارد × ۴ قالب) را با اوراکل‌های ساختاری و محتوایی مستقل اعتبارسنجی می‌کند:

```bash
python scripts/matrix_runner.py
# یا اجرای گزینشی:
python scripts/matrix_runner.py --fixtures S01,S05,S11,B00
```

گزارش‌های کامل و صادقانه در مسیر `artifacts/persian-layout/run_<timestamp>/` شامل فایل‌های `matrix.csv`, `run.json`, `reviews.json`, `summary.md` و `index.html` ذخیره می‌گردند.

---

## محدودیت‌ها و مشخصات عملیاتی
 
- **پسوند خروجی**: خروجی رسمی سند فایل‌های Word با پسوند **`.docx`** و فایل‌های چاپی با پسوند **`.pdf`** است. فرمت قدیمی `.doc` پشتیبانی نمی‌شود و با خطای کد ۲ متوقف می‌گردد.
- **موتور تبدیل PDF**: تولید PDF با استفاده از LibreOffice بدون سر (Headless) در محیط ایزوله، همراه با پروفایل موقت، مدیریت درخت پردازش‌ها و اعتبارسنجی ساختار خروجی صورت می‌پذیرد.
- **اندازهٔ ورودی**: سقف اندازهٔ فایل ورودی ۲۰ مگابایت است.
- **قفل هم‌زمانی**: انتشار سند نهایی با استفاده از قفل سیستمی پایدار و چندپلتفرمی (`fcntl.flock` در لینوکس/مک و `msvcrt` در ویندوز) بر روی فایل‌های `.{stem}.publish.lock` و `.{stem}.pdf.publish.lock` در برابر اجرای هم‌زمان محافظت می‌شود.
- **تصاویر وب**: در نسخهٔ فعلی آدرس‌های اینترنتی مستقیم (`http/https`) پشتیبانی نمی‌شوند؛ فایل‌ها باید پیش از تبدیل به صورت محلی در کنار سند قرار گیرند.
- **بخش‌های سند (Shell Sections)**: پوستهٔ سفارشی `shell.docx` باید تک‌سکشنی باشد.
- **نصب فونت**: فونت‌ها در سند تعریف می‌شوند؛ سیستم بازکننده سند برای نمایش بدون جایگزینی نیاز به فونت وزیرمتن دارد، یا می‌توانید با گزینهٔ `--embed-fonts` فونت را در فایل تعبیه نمایید.
