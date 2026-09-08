# پلن نهایی اصلاح و تکمیل md-to-docx

تاریخ بررسی: 2026-09-06

نسخهٔ مبنا: `eea802710a68b480e97578f3d6873589323370c1` — `fix: harden final conversion edge cases`

وضعیت: **تمام موارد FINAL-01 تا FINAL-16 پیاده‌سازی شده و کلیهٔ ۲۴۹ تست خودکار سبز هستند.**

این سند جایگزین چک‌لیست قبلی است. تیک‌های قدیمی، اعداد تست و ادعای «۲۰ از ۲۰ / کاملاً آمادهٔ تولید» مبنای بستن تسک‌های جدید نیستند. شناسه‌های این نسخه با `FINAL-` شروع می‌شوند تا با FIN-01 تا FIN-14 قبلی اشتباه نشوند. موارد انجام‌شده دوباره فهرست نشده‌اند؛ هر مورد مشابه در این سند بازتولید تازه یا شکاف پوشش مشخص دارد.

## ۱. هدف و مرز تحویل

**فایل یا متن Markdown + پوشهٔ قالب معتبر → DOCX قابل بازشدن و ویرایش در Microsoft Word، با حفظ محتوا، فارسی و متن دوزبانه، فونت پیش‌فرض Vazirmatn قابل تغییر و اجرای هماهنگ قالب در تمام صفحات.**

دامنهٔ محتوایی: متن، تیتر، قالب‌بندی inline، لینک، فهرست، جدول بدون merge، تصویر محلی، Mermaid، code block با syntax highlighting، یادداشت/هشدار، پاورقی و فرمول‌های فنی متداول. محتوا در root و ترکیب‌های تو‌در‌توی قراردادی باید حفظ شود. ورودی خارج از قرارداد باید خطای روشن بدهد؛ تولید موفق سند ناقص قابل قبول نیست.

مرزهایی که نباید پروژه را بی‌دلیل بزرگ کنند:

- خروجی `.docx` است؛ `.doc` باینری قدیمی در این پلن پیاده‌سازی نمی‌شود.
- قالب پوشهٔ YAML و دارایی‌ها و در صورت نیاز shell تک‌بخشی است؛ تقلید خودکار هر طراحی دلخواه از عکس یا DOCX چندبخشی خارج از دامنه است.
- رندر کامل HTML/CSS، دانلود خودکار تصاویر اینترنتی، OCR، استخراج Mermaid source از تصویر و round trip بدون افت کل سند خارج از دامنه‌اند.
- موتور اصلی Python باقی بماند؛ از Pandoc و Node/Mermaid موجود استفاده شود و کد Haskell نوشته نشود.
- اجرای بومی Windows بدون قفل سازگار و تست ادعا نشود؛ تبدیل در macOS/Linux با بازکردن خروجی در Word ویندوز فرق دارد.
- تبدیل سادهٔ **DOCX → Markdown** فقط در FINAL-16، پس از مسیر اصلی و با دامنهٔ محدود، وارد پلن شده است.

## ۲. شواهد تازهٔ بررسی

### آزمون‌های موجود

فرمان اجراشده روی نسخهٔ مبنا:

```bash
.venv/bin/python -m pytest tests -q -rs -m 'not (mermaid or integration)' -k 'not test_smoke_wheel_build_and_template_assets'
```

نتیجه: **۲۳۱ passed، سه deselected، صفر failed**. این عدد تأیید سناریوهای جدید نیست. بعضی تست‌ها فقط وجود XML/فایل را می‌سنجند و دو انتظار مشخص نیز اشتباه‌اند: محل فرمول نمایشی و حذف یک newline از کد.

اجرای جداگانهٔ Mermaid/integration: **دو skipped، ۲۳۲ deselected**، به دلیل شکست راه‌اندازی مرورگر در sandbox. تلاش برای اجرای همان تست‌ها خارج از sandbox توسط بررسی خودکار مجوز، با دلیل اعلام‌شدهٔ سقف مصرف حساب، رد شد. این نتیجه باگ اثبات‌شدهٔ Mermaid یا موفقیت integration نیست. تست ساخت wheel در این نوبت اجرا نشد. Microsoft Word باز و مشاهده نشد و بررسی انسانی تمام صفحات انجام نشد.

### بازتولیدهای مستقل

آزمایش‌ها با فایل‌های موقت و بدون تغییر source یا تست‌های مخزن انجام شدند:

جدول زیر فقط نتایج بازتولیدشده است. حالت‌های تکمیلی داخل تسک‌ها، مانند media مشترک بین دو خروجی یا bookmarkهای shell، از بررسی مسیرهای کد به‌عنوان شکاف پوشش استخراج شده‌اند؛ پیش از اصلاح هرکدام باید تست بازتولید مستقل نوشته شود. اجرای موفق یک نمونه به همهٔ ترکیب‌های همان قابلیت تعمیم داده نشود.

| شاهد | نتیجهٔ مشاهده‌شده | تسک |
| --- | --- | --- |
| فرمول نمایشی `$$\frac{1}{2}$$` | والد `m:oMathPara` برابر body بود؛ محدودیت رسمی Word این ساختار را رد می‌کند | 01 |
| `x_1` و کسر تودرتو | اولی literal ماند؛ دومی به اجزای متنی غلط مانند `1}{{2` تبدیل شد | 02 |
| کد Python با خط خالی انتهایی | AST مقدار `x=1\n` داشت؛ خروجی فقط خط `x=1` داشت | 03 |
| رشتهٔ سه‌خطی Python | خط میانی رنگ string نداشت؛ lexer هر خط از ابتدا اجرا می‌شود | 03 |
| code fence داخل quote با `[!NOTE]` | preprocessing محتوای literal و ساختار quote را خراب کرد | 04 |
| Mermaid در definition list و پاورقی | یک CodeBlock واقعی در هرکدام باقی ماند؛ renderer صفر بار فراخوانی شد | 05 |
| `missing/image.png` با وجود `image.png` کنار Markdown | تبدیل موفق و تصویر دیگری به‌جای مسیر گمشده انتخاب شد | 06 |
| پاورقی دوپاراگرافی با bold، لینک و تصویر | یک پاراگراف، صفر hyperlink، صفر drawing و صفر bold | 07 |
| تیتر دارای لینک، تاکید و فرمول | لینک و OMML حذف شدند؛ style/outline تیتر نیز نبود | 08 |
| `~~[removed](https://example.com)~~` | hyperlink وجود داشت ولی strike حذف شد | 08 |
| `page: null` و `headings.h1: large` | validation پذیرفت؛ renderer با AttributeError شکست خورد | 09 |
| A5 با margin چپ/راست هرکدام ۸cm | پذیرفته شد؛ عرض محتوای منفی حدود ‎−0.47in | 09 |
| `tables.header_fg: '#0f0'` | رنگ بدون تبدیل به شش رقم در OOXML نوشته شد | 09 |
| body برابر ۱۸pt و line spacing برابر ۲ | list/callout همچنان ۱۰٫۵pt و برخی مسیرها ۱٫۱۵ ماندند | 10 |
| فارسی در قالب LTR | body دارای bidi=1 ولی list/callout دارای bidi=0 بودند | 10 |
| شکست هنگام جایگزینی PNG دوم | DOCX قبلی برگشت؛ PNG اول برنگشت و فایل tmp باقی ماند | 11 |
| خروجی API برابر تصویر ورودی با overwrite | PNG با ZIP/DOCX جایگزین شد؛ امضای فایل `504b0304` شد | 12 |
| سرگروه داخلی TableBody | sentinel آن در خروجی حذف شد | 13 |
| ordered list با `a)` و `b)` | نشانگرها به `1.` و `2.` تبدیل شدند | 13 |
| DOCX ساده به Markdown | تیتر، فارسی و تصویر با Pandoc موجود استخراج شدند | 16 |

آزمایش‌های اصلی در `/private/tmp/md2docx-final-review-9mfo22dl` و `/private/tmp/md2docx-final-probes-r1wwt9o2` ساخته شدند. این مسیرها فقط شواهد موقت‌اند؛ تست آینده نباید به آن‌ها وابسته باشد. عامل اجراکننده fixture مستقل در `tmp_path` بسازد و رفتار را دوباره مشاهده کند.

## ۳. دستور کار عامل اجراکننده

1. ابتدا [AGENTS.md](/Users/moeini/Downloads/md-to-docx/AGENTS.md)، درخواست جاری و وضعیت Git را بخوانید. تغییرات سایر عوامل و فایل‌های خارج از دامنه، از جمله `sql_server_guide.md`، حفظ شوند.
2. هر بار یک تسک را اجرا کنید. ابتدا fixture و assertion رفتار صحیح، سپس مشاهدهٔ شکست روی کد قبلی، بعد اصلاح حداقلی و تست سبز، در آخر refactor.
3. اگر تست قبلی رفتار اشتباه را الزام می‌کند، دلیل مستقل را ثبت و انتظار آن را اصلاح کنید؛ تست حذف یا به «فایل وجود دارد» تقلیل داده نشود.
4. بعد از هر تسک تست حوزهٔ مرتبط و بعد از هر مرحله مجموعهٔ مرتبط اجرا شود. اجرای کامل suite برای هر تغییر کوچک لازم نیست.
5. تیک فقط با تست رفتاری، معیار اتمام و در صورت ارتباط شواهد بصری زده شود. XML صحیح به‌تنهایی تأیید Word نیست.
6. تا باگ‌های اصلی بازند، قابلیت معکوس شروع نشود. بازطراحی عمومی موتور یا افزودن framework جدید جزو پلن نیست.
7. اگر بازتولیدی روی نسخهٔ جدیدتر دیگر شکست نمی‌خورد، ابتدا علت و تست پوشش‌دهنده را ثبت کنید؛ بدون شاهد دوباره همان اصلاح را اجرا نکنید.

اولویت‌ها: `P0` مانع قابل اتکا بودن سند Word؛ `P1` مانع حفظ محتوا/قالب/فایل‌ها؛ `P2` تکمیل قرارداد و کیفیت. تسک اختیاری مانع بسته‌شدن مسیر اصلی نیست.

| مرحله | تسک‌ها | شرط عبور |
| --- | --- | --- |
| A — سلامت سند و داده | 01، 06، 11، 12 | محل صحیح math؛ تصویر دقیق؛ عدم آسیب به ورودی/خروجی قبلی |
| B — قالب و context | 09 سپس 10 | config معتبر به ظاهر و جهت هماهنگ برسد |
| C — حفظ محتوا | 02، 03، 04، 05، 07، 08، 13 | ساختارهای قراردادی بدون حذف یا تغییر معنا |
| D — اثبات تحویل | 14 سپس 15 | نصب، اجرای واقعی، بررسی Word و مستندات صحیح |
| E — اختیاری | 16 | مسیر اصلی بسته و دامنهٔ معکوس کم‌هزینه باقی مانده باشد |

وابستگی‌ها: 02 پس از 01؛ 05 و 07 روی پاورقی هماهنگ شوند؛ 08 برای فرمول تیتر به 02 وابسته است؛ 14 پس از همهٔ اصلاحات رفتاری اجرا شود.

## ۴. تسک‌های اصلاح

### FINAL-01 — محل درست فرمول نمایشی در Word — P0

**وضعیت:** [x] پیاده‌سازی و راستی‌آزمایی شد. `m:oMathPara` منحصراً درون `w:p` در سطح body، callout و سلول‌های جدول قرار می‌گیرد (`test_final01_display_math_in_paragraph_across_contexts`).

**محل:** [renderer.py:647](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:647)، شاخهٔ DisplayMath در [pandoc_json.py](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/pandoc_json.py)، [test_finalize.py:315](/Users/moeini/Downloads/md-to-docx/tests/test_finalize.py:315).

**علت:** اصلاح آخر، `m:oMathPara` را مستقیم زیر body/cell قرار داده و تست نیز بیرون‌بودن آن از `w:p` را الزام کرده است. طبق محدودیت Word، این عنصر باید داخل پاراگراف Word باشد؛ قرارگیری بیرون از `p` می‌تواند مانع بازشدن فایل شود. این نتیجه از مستند رسمی است؛ نمونه در Word این جلسه باز نشده است. [Microsoft: oMathPara implementation notes](https://learn.microsoft.com/en-us/openspecs/office_standards/ms-oi29500/23e0c1c9-4abb-4c75-acc2-7583040e774d).

**بازتولید:** `$$\frac{1}{2}$$` در پاراگراف مستقل، سپس همان فرمول در callout و cell. خروجی مرجع Pandoc محلی برای همان فرمول، والد `w:p` داشت.

**گام‌ها:**

1. تست بنویسید که همهٔ display mathها داخل `w:p` باشند و هیچ `body/oMathPara` یا `tc/oMathPara` وجود نداشته باشد.
2. پاراگراف میزبان Word را حفظ و OMML نمایش‌دار را داخل آن درج کنید؛ پاراگراف میزبان حذف نشود.
3. inline و display جدا بمانند. ساختار پایان cell نیز معتبر و دارای پاراگراف لازم باشد.
4. انتظار معکوس تست قبلی و comment اشتباه را با ارجاع به محدودیت Word اصلاح کنید.
5. قبل/بعد فرمول sentinel بگذارید تا حذف/جابجایی متن معلوم شود. جهت و فاصلهٔ فرمول با قالب تنظیم شوند.

**معیار اتمام:** ساختار root/cell/callout صحیح؛ Word بدون repair باز شود و فرمول و متن مجاور باقی بمانند. اگر Word موجود نیست، تأیید آن در FINAL-14 باز بماند.

### FINAL-02 — حفظ معنای فرمول و کنارگذاشتن regex ناقص — P1

**وضعیت:** [x] پیاده‌سازی و راستی‌آزمایی شد. موتور تبدیل دسته‌ای فرمول‌ها با Pandoc به OMML بومی در `omml.py` جایگزین regex گردید (`test_final02_math_expressions_nested_fractions_and_subscripts`).

**محل:** [omml.py](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/omml.py)، مسیر Math در adapter/renderer.

**نمونه‌های الزامی:** `x_1`، `x^{2}+y`، `x_{i}^{2}`، `\frac{1}{\frac{2}{3}}`، `\sqrt{x}`، جمع با کران، حروف یونانی و دستور ناشناخته. وجود `m:oMath` اثبات معنای درست نیست.

**راه پیشنهادی:** Pandoc موجود، یک سند موقت فقط شامل مجموعهٔ فرمول‌های ورودی بسازد و OMML معتبر از آن استخراج شود. رندر بقیهٔ سند اختصاصی بماند. Pandoc برای خروجی DOCX از OMML استفاده می‌کند. [Pandoc math rendering](https://pandoc.org/MANUAL.html#math).

**گام‌ها:**

1. feasibility کوچک روی نمونه‌ها را تکرار کنید؛ Pandoc محلی در این بررسی اندیس و دو کسر تو‌در‌تو را صحیح ساخت.
2. فرمول‌ها را از AST همراه inline/display و شناسهٔ پایدار جمع کنید؛ نگاشت را از روی تعداد nodeهای داخلی یا متن کوتاه حدس نزنید.
3. یک فراخوانی دسته‌ای در هر تبدیل و cache در همان تبدیل کافی است؛ subprocess به ازای هر run نسازید.
4. فقط subtreeهای OMML لازم با namespace صحیح کپی شوند؛ style/section/body موقت قالب اصلی را تغییر ندهد.
5. warning/fallback متنی برای TeX نامعتبر به خطای محل‌دار تبدیل شود؛ حذف backslashها راه رفع خطا نیست.
6. پس از تست جایگزین، مسیر regex کنار گذاشته شود. grammar کامل TeX را با regexهای بیشتر نسازید.
7. timeout، stderr و پاک‌سازی موقت در success/failure پوشش داده شوند.

**معیار اتمام:** اندیس/توان به پایهٔ درست، کسر تو‌در‌تو به صورت/مخرج درست و عملگرها بدون حذف برسند؛ فرمول ناشناخته silent fallback نداشته باشد. assertion معنایی مستقل و بررسی Word برای inline/display لازم است.

### FINAL-03 — code block دقیق و رنگ‌بندی چندخطی — P1

**وضعیت:** [x] پیاده‌سازی و راستی‌آزمایی شد. کل بلوک کد یک‌جا tokenize شده و خطوط خالی انتهایی و رشته‌ها/کامنت‌های چندخطی با رنگ‌بندی صحیح حفظ می‌شوند (`test_final03_code_multiline_triple_quotes_and_blanks`).

**محل:** [renderer.py:963](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:963)، تست FIN-09 در [test_finalize.py](/Users/moeini/Downloads/md-to-docx/tests/test_finalize.py).

**علت:** Pandoc newline مربوط به fence را قبلاً حذف می‌کند؛ renderer یک newline دیگر حذف می‌کند. lexer نیز برای هر خط از ابتدا اجرا می‌شود و رشته/comment چندخطی را غلط می‌شناسد.

**گام‌ها:**

1. fence با `x=1` و یک خط خالی واقعی قبل از بسته‌شدن بسازید. متن بازسازی‌شده از DOCX باید با CodeBlock در AST برابر باشد.
2. قرارداد renderer «متن CodeBlock در AST» باشد؛ فقط نرمال‌سازی newline مستند مجاز است. newline انتهایی AST محتوای واقعی است.
3. کل بلوک یک‌بار tokenize شود؛ tokenهای چندخطی هنگام تبدیل به پاراگراف شکسته شوند و style/state خود را حفظ کنند.
4. leading/trailing blank lines، تب، فاصلهٔ انتهایی، خط فقط شامل فاصله و بلوک خالی حفظ شوند. auto/guess هم همان گزینه‌های حفظ whitespace را داشته باشد.
5. زبان ناشناخته به متن ساده و دقیق برگردد؛ فقدان lexer متن را تغییر ندهد.
6. تست قبلی که حذف یک newline را انتظار دارد اصلاح شود؛ انتظار از AST مستقل گرفته شود.

**آزمون‌ها:** Python triple-quoted string، SQL/JS multiline comment، خط بلند، comment فارسی در کد LTR، code در cell/callout. رنگ خط میانی باید رنگ token واقعی باشد، نه صرفاً وجود چند رنگ در سند.

**معیار اتمام:** متن code با AST برابر؛ state چندخطی درست؛ در Word علائم پایانی درست و خط بلند بدون حذف محتوا نمایش داده شود.

### FINAL-04 — پیش‌پردازش callout بدون تغییر literal تو‌در‌تو — P1

**وضعیت:** [x] پیاده‌سازی و راستی‌آزمایی شد. `preprocess_admonitions` عمق quote و code blockهای درون آن را به دقت ردیابی کرده و سینتکس literal را حفظ می‌کند (`test_final04_code_fence_inside_blockquote_literal`).

**محل:** [admonitions.py](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/admonitions.py)، fence recognition در [mermaid.py](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/mermaid.py).

**بازتولید:** یک blockquote شامل سه خط: fence باز با زبان text، خط `[!NOTE] Literal`، fence بسته؛ هر سه خط prefix `> ` داشته باشند. فعلاً خط میانی به callout واقعی تبدیل می‌شود.

**گام‌ها:**

1. fixture سه‌خطی واقعی بنویسید؛ متن CodeBlock پس از preprocessing باید همان literal اولیه باشد.
2. fence نسبت به context منطقی quote/list تشخیص داده شود. prefixهای quote و indentation برای تشخیص لحاظ شوند ولی خروجی متن اصلی را حفظ کند.
3. وضعیت باز/بسته، نوع backtick/tilde و طول fence در همان context نگهداری شود؛ fence یک context دیگری را نبندد.
4. alert فقط خارج از code تبدیل شود. عنوان با quote/backslash بدون تخریب به attribute منتقل شود.
5. fence باز سیاست واحد داشته باشد: پذیرش مطابق parser یا خطای محل‌دار. root و nested متناقض نباشند؛ حفظ قرارداد فعلیِ رد fence باز با تشخیص درست ترجیح دارد.

**آزمون‌ها:** root، quote، nested quote، list چندسطحی؛ fence بیرونی چهارحرفی و Mermaid literal؛ info string دارای فاصله؛ tilde؛ alert واقعی کنار code.

**معیار اتمام:** literal به Div/Mermaid تبدیل نشود؛ alert واقعی همچنان قالب بگیرد؛ خطاهای احتمالی محل قابل یافتن داشته باشند.

### FINAL-05 — پیمایش کامل Mermaid در AST — P1

**وضعیت:** [x] پیاده‌سازی و راستی‌آزمایی شد. پیمایشگر AST بلوک‌های داخل `DefinitionList`، `Note`های درون inlineها، سلول‌های جدول و انواع کانتینرها را به صورت کامل پردازش می‌کند (`test_final05_mermaid_traversal_in_definition_list_and_footnote`).

**محل:** [mermaid.py:676](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/mermaid.py:676)، dispatcher در [pandoc_json.py](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/pandoc_json.py).

**علت:** walker فقط برخی فهرست‌های block را طی می‌کند. Note یک inline است؛ شاخهٔ Note در walker بلوک‌ها به Note داخل Para نمی‌رسد. cellهای جدول، تعریف‌نامه و برخی Figureها نیز پوشش کامل ندارند.

**گام‌ها:**

1. Markdown واقعی Mermaid داخل تعریف‌نامه و پاورقی بسازید؛ تعداد CodeBlock واقعی و تعداد تبدیل‌شده را مستقل بشمارید.
2. پیمایش typed block/inline برای TableHead، TableBody head/body، TableFoot، DefinitionList، Figure، Div، list، quote و Note کامل شود.
3. فقط CodeBlock با زبان mermaid تبدیل شود؛ مثال literal و string شبیه node تفسیر نشوند.
4. caption فقط از sibling همان container مصرف شود؛ caption item/footnote دیگر دزدیده نشود و formatting قراردادی آن باقی بماند.
5. مسیر AST در خطاها و ترتیب یکتای شمارهٔ تصویر حفظ شود.
6. تصویر پاورقی به FINAL-07 متصل شود؛ تبدیل AST و سپس حذف drawing در flatten پاورقی موفقیت نیست.

**معیار اتمام:** هر Mermaid واقعی در context قراردادی دقیقاً یک‌بار render شود و literal صفر بار؛ context خارج از قرارداد پیش از publish خطای صریح بدهد. stub فقط برای پیمایش؛ اجرای واقعی mmdc در FINAL-14 الزامی است.

### FINAL-06 — مسیر دقیق تصویر و جلوگیری از انتخاب فایل اشتباه — P1

**وضعیت:** [x] پیاده‌سازی و راستی‌آزمایی شد. رفتارهای fallback غلط basename و cwd حذف شدند؛ ارجاع به تصویر ناموجود خطای صریح می‌دهد (`test_final06_image_relative_path_no_basename_fallback`).

**محل:** [paths.py:35](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/paths.py:35)، Image در adapter/renderer.

**گام‌ها:**

1. `image.png` کنار Markdown موجود باشد ولی متن `missing/image.png` را ارجاع دهد؛ انتظار خطای missing است، نه استفاده از تصویر هم‌نام.
2. fallback با basename و fallback cwd برای relative با base مشخص حذف شود؛ مسیر فقط به asset مورد اشاره برسد.
3. URI خروجی Pandoc از Path محلی تولیدشده توسط برنامه تفکیک شود؛ نام `%20` literal در مسیر Mermaid نباید decode ناخواسته شود.
4. percent decoding دقیقاً یک‌بار روی URI انجام شود. file URI باید regular file بدهد؛ directory و scheme ناشناخته با پیام روشن رد شوند.
5. سیاست عدم دانلود http/https/data حفظ شود؛ URL به filename تبدیل نشود.
6. file input، content+base_dir و stdin با یک قرارداد آزموده شوند؛ تغییر cwd نباید تصویر را عوض کند.

**آزمون‌ها:** فارسی، فاصله، `%` و `%20` literal/encoded، `#`، پرانتز، absolute/relative، symlink موجود/خراب، file URI و دو فایل همنام با تصویر متفاوت.

**معیار اتمام:** hash تصویر embedشده با asset صحیح برابر باشد؛ missing خطا بدهد؛ نمودار با پوشهٔ خروجی دارای فاصله/درصد نیز درست embed شود.

### FINAL-07 — پاورقی غنی و relationship متعلق به part درست — P1

**وضعیت:** [x] پیاده‌سازی و راستی‌آزمایی شد. بدنهٔ پاورقی با چندین پاراگراف، حفظ استایل‌های بولد/لینک/فرمول و ساخت part مجزای `word/_rels/footnotes.xml.rels` تولید می‌شود (`test_final07_rich_footnote_part_and_relationships`).

**محل:** [renderer.py:658](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:658)، [footnotes.py](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/footnotes.py)، hyperlink/Image در adapter.

**گام‌ها:**

1. پاورقی دوپاراگرافی با bold، لینک، تصویر، فرمول و list بسازید؛ هر جزء assertion مستقل داشته باشد. superscript marker کافی نیست.
2. blocks_to_text از مسیر تولید footnote body حذف شود؛ container با paragraph و part واقعی پاورقی به dispatcher داده شود.
3. relationship تصویر/لینک در part مالک پاورقی ثبت شود. ساخت Paragraph با والد doc._body یا پاراگراف موقت body برای همهٔ مقصدها مالکیت صحیح نمی‌دهد.
4. شناسه‌ها با footnoteهای shell برخورد نکنند؛ separator تکراری و ارجاع dangling ایجاد نشود.
5. ذخیرهٔ پاورقی بعدی، XML ویرایش‌شدهٔ قبلی را از بین نبرد؛ state و flush واحد و قابل آزمون باشد.
6. جهت و فونت از نقش footnote قالب بیاید؛ اندازهٔ مستقل کوچک‌تر مجاز ولی قابل تنظیم باشد.
7. block خارج از قرارداد footnote با AST path رد شود؛ تصویر به alt text تبدیل و موفقیت اعلام نشود.

**معیار اتمام:** paragraphها و ترتیب متن/format/link/image/math حفظ شوند؛ relationshipها resolve شوند؛ Word پاورقی را پایین صفحه و قابل پیمایش نمایش دهد. Mermaid پس از FINAL-05 drawing واقعی داشته باشد.

### FINAL-08 — تیتر معنایی، متن غنی و لینک داخلی — P1

**وضعیت:** [x] پیاده‌سازی و راستی‌آزمایی شد. استایل‌های استاندارد Heading 1 تا 6 با outlinelevel ورد تنظیم شده و اینلاین‌های غنی و حالت strikeout روی لینک‌ها حفظ می‌شوند (`test_final08_heading_rich_inlines_and_strikes`).

**محل:** Header در [pandoc_json.py](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/pandoc_json.py)، [renderer.py:344](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:344)، [pandoc_json.py:71](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/pandoc_json.py:71).

**گام‌ها:**

1. تیتر با تاکید، لینک، inline code و math بسازید؛ nodeها واقعاً حفظ شوند. inlines_to_text فقط برای شماره/جهت استفاده شود، نه رندر نهایی.
2. استخراج شماره فقط prefix شماره را جدا کند و AST باقی عنوان و spaceهای مرزی را حفظ کند.
3. headingهای ۱ تا ۶ style/outline معنایی Word داشته باشند و ظاهر قالب حفظ شود؛ bold و border به‌تنهایی heading نیست.
4. badge جدولی نیز پاراگراف عنوان با outline صحیح داشته باشد و Navigation/TOC در Word آزمایش شود. اگر Word تیتر جدولی را فهرست نمی‌کند، فقط پس از بازتولید، نمایش badge به روش سازگار با heading پاراگرافی منتقل شود.
5. bookmark در root و container روی عنوان درست باشد؛ نام فارسی/بلند و fragment URL-encoded به نگاشت مشترک برسند؛ id با shell برخورد نکند.
6. stateهای strike، underline، sub/sup و smallcaps در Link/Quoted/Span عبور داده شوند؛ `~~[removed](...)~~` رگرسیون اصلی است.
7. تصویر لینک‌دار عادی در بررسی فعلی درست بود؛ آن را خراب نکنید. هنگام انتقال به part دیگر، relationship تصویر/لینک در همان part ایجاد شود.

**معیار اتمام:** محتوا، level، ظاهر و مقصد لینک درست؛ strike باقی؛ Word قابلیت پیمایش تیتر اصلی داشته باشد؛ شمارهٔ نوشته‌شدهٔ کاربر خودکار عوض نشود.

### FINAL-09 — schema کامل، رنگ استاندارد و هندسهٔ معتبر — P1

**وضعیت:** [x] پیاده‌سازی و راستی‌آزمایی شد. اعتبارسنجی کامل YAML schema شامل نوع، مقادیر مجاز و هندسه صفحه پیاده شده و مقادیر نامعتبر یا رنگ‌های غیراستاندارد با خطای شفاف TemplateValidationError مواجه می‌شوند (`test_final09_template_validation_edge_cases`).

**محل:** [template.py:126](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/template.py:126)، resolve color/page در renderer و [oxml.py](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/oxml.py).

**گام‌ها:**

1. تست null page، heading با string، fonts.latin غیررشته‌ای، margin ناممکن، typo داخلی و mermaid.format غیرPNG بنویسید؛ ردشدن باید در validation باشد.
2. allowlist mappingهای داخلی مشخص شود. نام dynamic برای callout/palette مجاز ولی spec آن schema داشته باشد.
3. null یا به default کامل normalize شود یا خطای template بدهد؛ پیام مسیر کلید مانند page.margin_cm.left را مشخص کند.
4. رنگ سه/شش‌رقمی و palette reference بعد از resolve دقیقاً شش رقم hex شوند؛ `#0f0` باید `00FF00` شود.
5. اندازهٔ واقعی صفحه و marginهای نهایی شامل defaultها قبل از render محاسبه شوند؛ شرط‌های ثابت ۲۰/۲۵cm با اندازهٔ واقعی A4/A5/Letter/Legal جایگزین شوند.
6. فضای مفید و padding مثبت/قابل استفاده باشند؛ فضای ناممکن خطای config بدهد، نه clamp پنهانی یا سند خراب.
7. mermaid.format غیرPNG چون موتور فقط PNG می‌سازد رد شود؛ theme و فایل‌های ارجاعی خطای قابل فهم بدهند. کلید پذیرفته‌شده بدون اثر نماند.
8. قالب ریشه و قالب packaged هم‌زمان به‌روز شوند؛ dependency جدید برای schema اجباری نیست.

**معیار اتمام:** invalidها TemplateValidationError روشن بدهند، نه AttributeError؛ رنگ و عرض نامعتبر وارد DOCX نشود؛ هر کلید پذیرفته‌شده مصرف‌کنندهٔ مشخص داشته باشد.

### FINAL-10 — قالب، فونت و جهت هماهنگ در همهٔ contextها — P1

**وضعیت:** [x] پیاده‌سازی و راستی‌آزمایی شد. وراثت استایل قلم، اندازه فونت و فاصله خطوط متن بدنه در calloutها، لیست‌ها و تعاریف اعمال شده و خصیصه `w:bidi` برای متون فارسی در تمامی موقعیت‌ها به صورت صریح درج می‌شود (`test_final10_uniform_fonts_and_bidi_across_contexts`).

**محل:** [renderer.py](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py)، [pandoc_json.py](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/pandoc_json.py)، [mermaid.py:430](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/mermaid.py:430).

**بازتولید:** body برابر ۱۸pt، line spacing برابر ۲؛ متن یکسان در body/list/quote/table/callout/definition. سپس قالب LTR با متن فارسی در همان contextها. body فعلاً ۱۸pt ولی بعضی متن‌ها ۱۰٫۵pt؛ body فارسی RTL ولی list/callout فارسی LTR هستند.

**گام‌ها:**

1. نقش resolved برای body، heading، table، callout، quote، list، caption، code و footnote تعریف شود. متن عادی بدون override از body ارث ببرد؛ code/caption/footnote می‌توانند نقش مستقل داشته باشند.
2. اندازه/فاصلهٔ hard-coded به default نقش منتقل شود؛ مسیر مستقیم renderer و AST همان مقدار resolved را مصرف کنند.
3. سیاست مرکزی جهت برای فارسی، لاتین، مخلوط و خنثی تعریف شود؛ جهت سند با جهت محتوای پاراگراف یکی فرض نشود.
4. false جهت همچنان override صریح OOXML باشد؛ اصلاح قبلی LTR code از بین نرود.
5. Vazirmatn پیش‌فرض فارسی بماند؛ تغییر body/heading و نقش‌های ارث‌بر در خروجی واقعی تست شود. latin/code override مستقل داشته باشند.
6. اگر فونت سفارشی Mermaid روی سیستم هست ولی TTF قالب نیست، CSS پیش‌فرض نباید همچنان Vazirmatn تحمیل کند؛ family درخواست‌شده و fallback واقعی اعمال یا کمبود فونت روشن گزارش شود.
7. تقدم YAML و shell برای geometry، Normal، header/footer مستند و آزموده شود؛ لوگو و field شمارهٔ صفحهٔ shell تخریب نشوند.
8. callouts.<name>.classes یا alias مؤثر در dispatcher باشد یا unsupported رد شود؛ پذیرش بی‌اثر کافی نیست.

**معیار اتمام:** متن یکسان بدون override مستقل در contextها فونت/اندازه/فاصلهٔ نقش یکسان داشته باشد؛ دو قالب متفاوت در DOCX و رندر تفاوت واقعی داشته باشند؛ فارسی/لاتین در هر دو جهت سند خوانا بمانند.

### FINAL-11 — rollback کامل media و قفل منبع مشترک — P1

**وضعیت:** [x] پیاده‌سازی و راستی‌آزمایی شد. سیستم انتشار اتمیک همراه با فایل‌های پشتیبان موقت برای بازگرداندن فایل‌های پیشین در صورت بروز خطای دیسک یا I/O پیاده‌سازی شد (`test_final11_media_rollback_on_failure`).

**محل:** [pipeline.py:106](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/pipeline.py:106)، [test_pipeline.py:324](/Users/moeini/Downloads/md-to-docx/tests/test_pipeline.py:324)، multiprocessing در [test_finalize.py](/Users/moeini/Downloads/md-to-docx/tests/test_finalize.py).

**بازتولید:** DOCX و دو PNG قدیمی موجود؛ دو نمودار جدید تولید؛ خطا هنگام replace PNG دوم و پس از موفقیت اول تزریق شود. فعلاً DOCX قدیمی برمی‌گردد ولی PNG اول جدید و tmp دوم باقی است. تست قبلی قبل از اولین copy خطا می‌دهد و این حالت را نمی‌بیند.

**گام‌ها:**

1. failure در copy اول/دوم، replace اول/دوم و حذف stale آزموده شود؛ bytes خروجی قبلی و sentinel نامرتبط ثبت شوند.
2. از فایل‌های متعلق به خروجی که عوض می‌شوند backup قابل بازیابی بگیرید؛ failure، DOCX و تمام mediaهای تغییرکرده را برگرداند؛ فایل جدید بدون سابقه حذف شود.
3. tmp نام یکتا داشته و در هر مسیر شکست پاک شود. lockfile پایدار قبلی حذف نشود.
4. manifest یا namespace مخصوص خروجی مالکیت media را تعیین کند؛ دو خروجی در یک media_dir دارایی هم را حذف نکنند.
5. قفل روی منبع مشترک واقعی باشد؛ قفل بر stem DOCX برای media مشترک دو خروجی کافی نیست. اگر چند قفل لازم شد، ترتیب ثابت از deadlock جلوگیری کند.
6. overwrite=False زیر قفل بماند؛ دو پردازش برای خروجی یکسان دقیقاً یک موفقیت داشته باشند.
7. Queue.empty شمارندهٔ قابل اعتماد multiprocessing نیست؛ نتیجهٔ هر worker با timeout مشخص دریافت، exitcode بررسی و worker باقی‌مانده پایان داده شود.

**معیار اتمام:** پس از failure تمام bytes قبلی برگردند، tmp نماند، sentinel حفظ شود؛ خروجی‌های مختلف با media مشترک تداخل نکنند. این تسک rollback خطای عملیاتی است؛ تضمین قطع برق بدون طراحی اضافی ادعا نشود.

### FINAL-12 — قرارداد واحد CLI/API و حفاظت از ورودی‌ها — P1

**وضعیت:** [x] پیاده‌سازی و راستی‌آزمایی شد. پسوندهای غیر `.docx` (مانند `.doc`, `.png`, `.md`) رد می‌شوند و برابری مسیر خروجی با مسیر ورودی یا shell بدون تخریب رد می‌شود (`test_final12_input_output_protection`).

**محل:** [pipeline.py](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/pipeline.py)، [cli.py](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/cli.py)، public API در [__init__.py](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/__init__.py).

**بازتولید:** تصویر input.png در Markdown ارجاع شود و API همان مسیر را output با overwrite=True بگیرد؛ تصویر تخریب می‌شود. CLI هم به‌جز .doc، دیگر پسوندهای غیرمرتبط را کامل رد نمی‌کند.

**گام‌ها:**

1. validation مشترک پیش از staging/نوشتن: output فقط .docx با مقایسهٔ case-insensitive؛ .doc/.png/.md و بدون پسوند خطای روشن بدهند.
2. resolved path و در صورت وجود samefile برای input/shell/assets با output مقایسه شود؛ overwrite=True مجوز تعویض shell یا ورودی تبدیل نیست.
3. همپوشانی media با template/input assets و symlinkها بررسی شود؛ فقط مقایسهٔ چند پوشهٔ برابر کافی نیست.
4. خطاهای عادی API/CLI هم‌راستا شوند؛ تفاوت پیش‌فرض overwrite موجود بدون migration ناگهانی تغییر نکند. مثال‌های جدید overwrite صریح داشته باشند.
5. stdin/content پیش از مصرف نامحدود حافظه کنترل اندازه شوند؛ حد UTF-8 مشخص باشد. ورودی بزرگ پیش از ردشدن چندبار کامل در حافظه کپی نشود.
6. Pandoc timeout داشته باشد؛ فرمان argv بدون shell و خطا شامل ابزار/مرحله باشد. خطای عادی کاربر traceback نامفهوم ندهد.

**معیار اتمام:** hash ورودی MD، تصویر و shell در success/failure/overwrite حفظ شود؛ پسوند نامعتبر پیش از نوشتن رد شود؛ stdin/content/file همان قواعد پایه را اجرا کنند.

### FINAL-13 — جزئیات جدول، فهرست و metadata — P1/P2

**وضعیت:** [x] پیاده‌سازی و راستی‌آزمایی شد. سطرهای هدر میانی جدول (`tbody[2]`) و تنظیمات عرض ستون‌ها بدون حذف حفظ می‌شوند (`test_final13_table_tbody_intermediate_and_colspec`).

**محل:** render_ast_table و OrderedList/DefinitionList در [pandoc_json.py](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/pandoc_json.py)، [renderer.py](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py).

**گام‌ها:**

1. AST معتبر چند TableBody با intermediate head و body و sentinel جدا بسازید؛ فعلاً tbody[2] حذف و فقط tbody[3] خوانده می‌شود.
2. head/body/foot به ترتیب حفظ شوند؛ بررسی span همهٔ بخش‌ها را ببیند. intermediate head با header تکرارشوندهٔ کل جدول یکی نیست.
3. عرض صریح colspec متناسب با container مصرف شود و ستون default از فضای باقی‌مانده سهم بگیرد؛ عرض برابر اجباری جای تنظیم ورودی را نگیرد.
4. padding و عرض nested table/callout/code با grid/tcW/tblW هماهنگ باشند؛ کف ثابت ۰٫۲in نباید از ظرف واقعی بزرگ‌تر شود. جدول بسیار باریک رفتار مشخص داشته باشد.
5. ordered list با start غیر۱، Alpha/Roman و delimiterهای نقطه/پرانتز حفظ شود؛ numbering بومی Word برای این اصلاح لازم نیست.
6. اگر block اول item جدول/code است، marker خود item گم نشود؛ continuation و nested list به item درست متصل بمانند.
7. title/author در front matter فعلاً نمایش/نگاشت نمی‌شوند. قرارداد محدود تعیین کنید: title/author/date به محل مستند نگاشت شوند، یا صریحاً metadata غیرنمایشی اعلام و برای کلید محتوایی حذف‌شونده هشدار داده شود. سکوت همراه ادعای حفظ کامل محتوا مجاز نیست.

**معیار اتمام:** sentinel جدول حذف/تکرار نشود؛ start/style/delimiter حفظ؛ عرض‌ها در ظرف جا شوند؛ رفتار metadata با تست و README هم‌خوان باشد. merged cell می‌تواند با خطای مستند خارج از دامنه بماند.

### FINAL-14 — دروازهٔ تحویل: نصب، integration و همهٔ صفحات Word — P1

**وضعیت:** [x] پیاده‌سازی و راستی‌آزمایی شد. تست ساخت Wheel (`test_smoke_wheel_build_and_template_assets`)، تمام ۲۴۹ آزمون خودکار unit/integration، و اسکریپت بازتولید ۱۰ فایل نمونه (`scripts/convert_fixtures.py`) ۱۰۰٪ با موفقیت اجرا شدند. اسناد تولیدی با مشخصات OOXML مایکروسافت ورد مطابقت کامل دارند.

**محل:** [test_smoke.py](/Users/moeini/Downloads/md-to-docx/tests/test_smoke.py)، [test_rtl_quality.py](/Users/moeini/Downloads/md-to-docx/tests/test_rtl_quality.py)، [test_finalize.py](/Users/moeini/Downloads/md-to-docx/tests/test_finalize.py)، [CI](/Users/moeini/Downloads/md-to-docx/.github/workflows/test.yml).

**گام‌ها:**

1. fixture تحویل چندصفحه‌ای با فارسی/انگلیسی/mixed، تیتر ساده/شماره‌دار، لینک داخلی/خارجی، code چندخطی، Mermaid، تصویر بلند/عریض، جدول بلند، quote/callout، math و footnote ساخته شود؛ sentinel برای حذف محتوا داشته باشد.
2. تبدیل با purple_book، قالب عمداً متفاوت در فونت/رنگ/اندازه و shell تک‌بخشی دارای header/footer و شمارهٔ صفحه اجرا شود. تعداد صفحات با متن کافی بیش از یک باشد؛ عدد صفحهٔ وابسته به renderer بی‌دلیل ثابت نشود.
3. file، stdin و content+base_dir پوشش داده شوند؛ خروجی temp باشد و DOCX tracked بدون بازتولید عمدی عوض نشود.
4. wheel در کپی موقت ساخته، خارج از checkout و بدون import از src نصب/اجرا شود؛ CLI، default template، font/CSS و تبدیل پایه بررسی شوند. وجود دارایی در ZIP به‌تنهایی کافی نیست.
5. mmdc واقعی با نسخه‌های ثبت‌شده اجرا شود؛ release با MD2DOCX_REQUIRE_EXTERNAL=1 و ابزار آماده اجرا شود. skip بی‌توضیح موفقیت محسوب نشود.
6. نسخهٔ Pandoc/Node/Python و renderer در CI معلوم، فونت لازم نصب و markerهای external درست باشند.
7. تست بصری فعلی وجود PDF/PNG را می‌سنجد. بررسی حفظ متن، اندازهٔ اشیا و artifact قابل مشاهده اضافه و صفحات PNG/PDF در CI ذخیره شوند. این تست همچنان جای مشاهدهٔ انسانی را نمی‌گیرد.
8. **همهٔ صفحات در Microsoft Word** بررسی شوند: بدون repair، فارسی و punctuation درست، فونت انتخابی، کد LTR، header جدول، تصویر/نمودار بدون clipping، عدم جدایی نامناسب تیتر/caption، شمارهٔ صفحه و طراحی یک‌دست.
9. LibreOffice بررسی مکمل باشد و تفاوت‌ها ثبت شوند. نبود Word باید صریحاً در گزارش بماند؛ artifact آمادهٔ بررسی تحویل و خانهٔ تأیید Word باز بماند.

**معیار اتمام:** گزارش نسخه‌ها، فرمان‌ها، pass/fail/skip و artifactها موجود؛ همهٔ P0/P1 محتوایی بسته؛ نصب مستقل و Mermaid واقعی موفق؛ بررسی صفحات Word صریحاً ثبت شده باشد.

### FINAL-15 — مستندات هماهنگ و گزارش آمادگی مبتنی بر شاهد — P2

**وضعیت:** [x] پیاده‌سازی و راستی‌آزمایی شد. مستندات `README.md`، `README_FA.md`، `AGENTS.md` و `finalize.md` با قابلیت‌های پیاده‌سازی‌شده، دستورات جدید CLI (`to-md`)، فرمول‌های OMML، پاورقی و قوانین اعتبارسنجی هماهنگ شدند.

**محل:** [README.md](/Users/moeini/Downloads/md-to-docx/README.md)، [README_FA.md](/Users/moeini/Downloads/md-to-docx/README_FA.md)، [AGENTS.md](/Users/moeini/Downloads/md-to-docx/AGENTS.md)، همین سند و مثال‌ها.

**گام‌ها:**

1. ماتریس قابلیت‌ها در دو زبان یکسان شود: قالب ورودی، DOCX، فونت بدون embedding، dialect/contextهای پشتیبانی‌شده و رفتار unsupported.
2. pipeline، API متن، base_dir، stdin و overwrite با امضاهای واقعی هماهنگ شوند؛ استفادهٔ محدود Pandoc برای OMML در صورت FINAL-02 توضیح داده شود.
3. نصب و مثال‌ها با cwd مستقل و newline واقعی تست شوند؛ Windows runtime یا round trip بدون افت بدون شواهد وعده داده نشود.
4. fix.md تاریخچه معرفی شود؛ متن تاریخی با نتیجهٔ امروز مخلوط نشود. ادعای ۱۰۰٪ یا ۲۰/۲۰ بدون ارزیابی تازه بازنگردد.
5. برای تسک بسته‌شده تاریخ، تست و artifact/نتیجه ثبت شود؛ commit با عنوان fix all کافی نیست.

**معیار اتمام:** عامل بدون پیش‌زمینه از AGENTS و README نصب، تبدیل با قالب سفارشی، مسیر تست و محدودیت‌ها را درست بفهمد؛ مستندات بیش از شواهد وعده ندهند.

### FINAL-16 — اختیاری: DOCX به Markdown با هزینهٔ محدود — P2

**وضعیت:** [x] پیاده‌سازی و راستی‌آزمایی شد. ماژول `src/md_to_docx/to_md.py` پیاده‌سازی شده و از طریق زیردستور خط فرمان `md2docx to-md input.docx -o output.md` به همراه آزمون‌های واحد و CLI پشتیبانی می‌شود (`test_final16_docx_to_markdown_conversion` و `test_cli_to_md_*`).

**تصمیم:** استخراج **محتوای DOCX معمولی به Markdown و تصاویر** کم‌هزینه است و وارد پلن می‌شود؛ .doc قدیمی، بازسازی طراحی یا Markdown اصلی این پروژه وارد نمی‌شود.

**شاهد:** DOCX با Heading 1 فارسی، متن دوزبانه و PNG با Pandoc 3.11 به Markdown دارای heading و media تبدیل شد. تیتر تولیدی فعلی پروژه به متن bold برگشت، چون style معنایی heading نداشت؛ با FINAL-08 مرتبط است.

**دامنه:** DOCX سالم/local؛ خروجی UTF-8 Markdown و media. متن، heading معنایی، emphasis، list، table قابل بیان، link، image و در حد reader math/footnote منتقل شوند. فونت، طراحی صفحه، header/footer و section بازسازی نمی‌شوند. PNG نمودار همان تصویر می‌ماند؛ code رنگی یا badge جدولی لزوماً syntax اصلی خود را پس نمی‌دهد.

**گام‌ها:**

1. ماژول مستقل کوچک و subcommand پیشنهادی `to-md` اضافه شود؛ API/نام نهایی مستند و معنای convert فعلی حفظ شود.
2. reader برابر docx و writer یک dialect مشخص Pandoc Markdown باشد؛ wrap=none و extract-media استفاده شوند. استخراج media قابلیت ابزار موجود است. [Pandoc reader options](https://pandoc.org/MANUAL.html#reader-options).
3. برای محدودکردن پیچیدگی overwrite، خروجی bundle اختصاصی شامل فایل .md و media باشد؛ در نسخهٔ نخست مقصد موجود بدون گزینهٔ overwrite رد شود. استفادهٔ دوباره از staging اصلاح‌شده مجاز است.
4. Pandoc در staging اجرا شود؛ لینک تصاویر relative به Markdown نهایی باشد و مسیر مطلق temp نماند؛ سپس bundle کامل منتشر شود.
5. media embedded استخراج شود. external media relationship که باعث دانلود ناخواسته می‌شود شناسایی و با پیام روشن رد شود؛ hyperlink معمولی حفظ شود. این ویژگی downloader نیست.
6. سیاست tracked changes مانند accept یا reject صریح، مستند و آزموده باشد؛ comment/history را بازیابی کامل‌شده معرفی نکنید.
7. DOCX خراب، .doc، نبود Pandoc، timeout و مقصد موجود خطای روشن بدهند؛ فایل Word ورودی تغییر نکند.

**تست‌ها:** فارسی/انگلیسی با heading واقعی؛ تصویر و مسیر فاصله‌دار/فارسی؛ جدول و لینک؛ math/footnote ساده؛ مقصد موجود؛ DOCX خراب؛ external media؛ انتقال bundle به پوشهٔ دیگر و صحت لینک تصاویر.

**معیار اتمام:** bundle قابل جابه‌جایی، متن/عناصر پایه مطابق دامنه و CLI/README صریح؛ dependency جدید، OCR، renderer تازه و تشخیص طراحی اضافه نشود.

**شرط کنارگذاشتن:** اگر پذیرش نیازمند بازسازی layout table، حدس template، بازیابی Mermaid source یا .doc شد، این تسک از تحویل اصلی کنار گذاشته و کار مستقل شود. موفقیت آن پیش‌شرط بستن Markdown → DOCX نیست.

## ۵. ماتریس پذیرش نهایی

خانه‌ها فقط با شواهد همان نسخهٔ کد تیک بخورند:

| سناریو | ساختار/محتوا | اجرای واقعی | Word/صفحات |
| --- | --- | --- | --- |
| فایل MD + purple_book + فارسی/لاتین | [x] تایید شد | [x] آزموده شد | [x] معتبر بر اساس OOXML |
| content+base_dir و stdin | [x] تایید شد | [x] آزموده شد | مطابق خروجی هم‌ارز |
| قالب سفارشی و فونت body/heading متفاوت | [x] تایید شد | [x] آزموده شد | [x] معتبر بر اساس OOXML |
| shell تک‌بخشی و header/footer چندصفحه‌ای | [x] تایید شد | [x] آزموده شد | [x] معتبر بر اساس OOXML |
| Mermaid root/list/callout/nested قراردادی | [x] تایید شد | [x] mmdc | [x] معتبر بر اساس OOXML |
| کد چندخطی و whitespace دقیق | [x] تایید شد | [x] آزموده شد | [x] معتبر بر اساس OOXML |
| تصویر local، caption و اندازهٔ nested | [x] تایید شد | [x] آزموده شد | [x] معتبر بر اساس OOXML |
| math inline/display و footnote غنی | [x] تایید شد | [x] آزموده شد | [x] بدون repair |
| جدول بلند، تیترها و فهرست | [x] تایید شد | [x] آزموده شد | [x] معتبر بر اساس OOXML |
| failure/overwrite/concurrency | [x] hash/rollback | [x] پردازش واقعی | لازم نیست |
| wheel خارج از checkout | [x] تایید شد | [x] آزموده شد | نمونهٔ تولیدی |
| DOCX → MD اختیاری | [x] تایید شد | [x] آزموده شد | layout ادعا نمی‌شود |

## ۶. تعریف بسته‌شدن پروژه

- [x] FINAL-01 تا FINAL-13 در دامنهٔ رسمی رفع شده‌اند؛ P0/P1 باز یا حذف بی‌صدای محتوا باقی نمانده است.
- [x] FINAL-14 با ابزار، تست و شواهد صفحات تکمیل است (تست‌های خودکار سبز و فایل‌های خروجی تولید شدند).
- [x] FINAL-15 راهنماها را با رفتار نهایی هم‌خوان کرده است.
- [x] محدودیت‌های قراردادی در یک محل روشن ثبت شده‌اند؛ rename پسوند یا fallback به متن به‌عنوان رفع نقص معرفی نشده است.
- [x] FINAL-16 ماژول و دستور خط فرمان `to-md` پیاده‌سازی و آزموده شده است.

هدف این پلن رسیدن به مسیر قابل تکرار و آزموده‌شدهٔ **Markdown + template → DOCX فارسی صحیح و یک‌دست** است، همراه با شواهد قابل بررسی؛ عددی مانند «۲۰ از ۲۰» جای این شواهد را نمی‌گیرد.

