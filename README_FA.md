# md-to-docx

<p align="left">
  <b>فارسی</b> | <a href="README.md"><b>English Version</b></a>
</p>

**مبدل متون فنی Markdown دو زبانه (فارسی و انگلیسی) + نمودارهای Mermaid به اسناد رسمی Word (.docx)**

این ابزار مستندات متنی Markdown را به اسناد حرفه‌ای Word با استایل اداری تبدیل می‌کند: متن راست‌به‌چپ (RTL)، جداسازی خودکار عبارات ترکیبی فارسی و انگلیسی، بج‌های شماره‌گذاری‌شدهٔ عناوین، کادرهای هشدار و نکته (Callouts)، جداول استاندارد راست‌به‌چپ، بلوک‌های کد چپ‌چین با رنگ‌آمیزی ساختاری (Syntax Highlighting)، و نمودارهای شفاف و باکیفیت Mermaid.

<p align="center">
  <img src="sample-template/1.jpg" alt="نمونه خروجی سند Word: بج‌های عناوین، نمودار Mermaid، کادر نکته" width="100%">
</p>
<p align="center">
  <img src="sample-template/2.jpg" alt="نمونه خروجی سند Word: کادر هشدار، نقل‌قول و جدول راست‌به‌چپ" width="420">
</p>

---

## TL;DR — راهنمای راه‌اندازی و تبدیل سریع

خلاصهٔ جریان تبدیل: **قالب (Template) + فایل یا متن مستقیم (Markdown Content / File) → فایل سند Word (.docx)**

### ۱. راه‌اندازی و نصب پیش‌نیازها (فقط یک‌بار)

```bash
./scripts/bootstrap.sh
source .venv/bin/activate
```

### ۲. تبدیل سریع از طریق خط فرمان (CLI)

```bash
# الف) ورودی از طریق فایل Markdown:
md2docx convert input.md -o output.docx --template purple_book

# ب) ورودی مستقیم از طریق پایپ متن (Standard Input):
echo "# عنوان سند\n\nمتن نمونه برای تبدیل." | md2docx convert - -o output.docx --template purple_book
```

### ۳. استفاده از کتابخانه در پایتون (Python API)

```python
from md_to_docx import convert_markdown_to_docx

# حالت اول: ورودی فایل Markdown
convert_markdown_to_docx(
    input_path="document.md",
    output_path="output.docx",
    template="purple_book",  # یا مسیر پوشه قالب سفارشی: './templates/my_theme'
    overwrite=True,
)

# حالت دوم: ورودی مستقیم متن رشته‌ای Markdown
convert_markdown_to_docx(
    content="# عنوان سند\n\nتوضیحات، جداول و نمودارهای متنی مارک‌داون...",
    output_path="output.docx",
    template="purple_book",
    overwrite=True,
)
```

| مؤلفه | نوع | توضیحات |
| :--- | :--- | :--- |
| **ورودی ۱: Template** | نام یا مسیر پوشه | تم پیش‌فرض `purple_book` یا هر پوشهٔ حاوی `config.yaml` با تنظیم رنگ‌ها، ابعاد صفحه، قلم‌ها و استایل‌ها |
| **ورودی ۲: Markdown** | مسیر فایل یا متن رشته‌ای | فایل `.md` از طریق مسیر (`input_path`) یا متن مستقیم مارک‌داون (`content` در پایتون / stdin `-` در CLI) |
| **خروجی: Word File** | فایل خروجی Word | سند رسمی با پسوند **`.docx`** (چینش کامل راست‌به‌چپ، قلم وزیرمتن، بج‌های عناوین، جداول و نمودارهای تعبیه‌شده) |

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
- **Node.js نسخه ۱۸ به بعد** (جهت اجرای mermaid-cli)
- **گوگل کروم یا کرومیوم** (جهت رندر با Puppeteer)

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

python3.11 -m venv .venv
source .venv/bin/activate
pip install -c constraints.txt -e ".[dev]"
npm ci || npm install
npx puppeteer browsers install chrome
```

---

## دستورات خط فرمان (CLI)

```bash
# تبدیل عادی فایل مارک‌داون
md2docx convert chapter.md -o chapter.docx

# رونویسی صریح فایل موجود با پرچم --overwrite
md2docx convert chapter.md -o chapter.docx --overwrite

# استفاده از قالب سفارشی
md2docx convert chapter.md -o chapter.docx --template purple_book
md2docx convert chapter.md -o chapter.docx --template ./templates/my_theme

# مشاهده و اعتبارسنجی قالب‌ها
md2docx templates list
md2docx templates validate purple_book
```

- اگر پرچم `-o` داده نشود، خروجی با همان نام ورودی و پسوند `.docx` ساخته می‌شود.
- فرمت قدیمی `.doc` پشتیبانی نمی‌شود و با پیام خطا متوقف می‌گردد.
- نمودارهای Mermaid در کنار سند در پوشهٔ `{stem}_media` ذخیره می‌شوند و تمام تصاویر در خود فایل Word نیز embed می‌شوند تا سند به طور مستقل باز شود.

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

## ساختار پوشهٔ قالب‌ها (Templates)

پوشهٔ پیش‌فرض `templates/purple_book/` ساختار استاندارد قالب را نشان می‌دهد:

```
templates/purple_book/
├── config.yaml                 # نسخه الگو: ۱، رنگ‌ها، قلم‌ها و تعاریف کادرها
├── mermaid.json                # تنظیمات و تم Mermaid
├── mermaid.css                 # استایل و فونت اختصاصی رندر دیاگرام
├── puppeteer.json              # تنظیمات مرورگر رندرکننده
├── fonts/Vazirmatn-Regular.ttf # فونت آزاد وزیرمتن برای رندر تصاویر
└── shell.docx                  # فایل پایه اختیاری Word (سربرگ و پاورقی کلی)
```

جهت ساخت قالب اختصاصی جدید:
```bash
cp -R templates/purple_book templates/my_theme
# ویرایش templates/my_theme/config.yaml
md2docx templates validate my_theme
md2docx convert input.md --template my_theme -o out.docx
```

---

## محدودیت‌ها و مشخصات عملیاتی (نسخهٔ ۱)

- **پسوند خروجی**: خروجی رسمی سند فقط `.docx` است.
- **اندازهٔ ورودی**: سقف اندازهٔ فایل ورودی ۲۰ مگابایت است.
- **قفل هم‌زمانی**: انتشار سند نهایی با استفاده از قفل سیستمی پایدار (`fcntl.flock`) در برابر اجرای هم‌زمان محافظت می‌شود.
- **تصاویر وب**: در نسخهٔ فعلی آدرس‌های اینترنتی مستقیم (`http/https`) پشتیبانی نمی‌شوند؛ فایل‌ها باید پیش از تبدیل به صورت محلی در کنار سند قرار گیرند.
- **بخش‌های سند (Shell Sections)**: پوستهٔ سفارشی `shell.docx` باید تک‌سکشنی باشد.
- **نصب فونت**: فونت‌ها در سند تعریف می‌شوند؛ سیستم بازکننده سند برای نمایش بدون جایگزینی نیاز به فونت وزیرمتن دارد.
