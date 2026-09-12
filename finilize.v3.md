# پلن نهایی `md-to-docx` — نسخهٔ ۳

تاریخ بازبینی: ۲۰۲۶-۰۹-۰۸ · وضعیت: **پلن فعال؛ پذیرش نهایی هنوز اثبات نشده است.**

این سند مرجع اجرای بعدی برای RTL، option فونت، جاسازی فونت و باقی‌ماندهٔ برنامه‌های قبلی است. **دامنهٔ درخواست جاری فقط اصلاح همین فایل است؛ کد، تست، قالب، نمونه، artifact و گزارش تاریخی در این بازبینی تغییر نمی‌کنند.** نسخهٔ قبلی طبق پیام کاربر در `scratchpad/finilize.v3.backup.md` نگهداری شده است؛ آن مسیر در checkout حاضر هنگام بررسی در دسترس نبود و نباید بازسازی یا بازنویسی شود.

عامل اجراکننده باید `AGENTS.md`، به‌ویژه بخش‌های ۹ تا ۱۲ را رعایت کند: رفتار را از کد و تست جاری بگیرد، تغییر رفتاری را با TDD انجام دهد و کیفیت ظاهری را جداگانه اثبات کند. اگر قابلیت موجود است، ابتدا شاهد و پوشش آن را بررسی کند؛ فقط شکاف واقعی را اصلاح کند. افزودن تست تکراری یا ساختن شکست مصنوعی برای هر ظرف الزامی نیست.

## ۰. مبنای این بازبینی و اعتبار وضعیت‌ها

این نوبت **بازبینی ایستا**ی پلن‌ها، کد، تست‌ها، READMEها، تنظیمات وابستگی و منابع رسمی Open XML است. هیچ suite، تبدیل، نصب، ماتریس یا رندر Word/LibreOffice در این نوبت اجرا نشده است. اعداد «۳۸۲ passed»، «۲۴۴ pass» و نسخه‌های محیط در متن قبلی، گزارش تاریخی‌اند؛ بدون log و fingerprint منطبق، نتیجهٔ checkout جاری محسوب نمی‌شوند. گزارش‌های قبلی حتی دربارهٔ اجرای Mermaid اختلاف دارند.

وضعیت‌ها در این سند:

- **موجود در کد:** مسیر پیاده‌سازی دیده شده؛ اجرای صحیح یا پذیرش بصری نتیجه گرفته نمی‌شود.
- **شکاف ایستا:** ناسازگاری مشخص در خواندن کد؛ بازتولید و تست قرمز در اجرای بعدی لازم است.
- **نیازمند شاهد:** ادعای تاریخی یا رفتار محیطی که هنوز برای snapshot نهایی اثبات نشده است.
- **بسته:** فقط با شاهد همان snapshot، فرمان، نتیجه و artifact مرتبط؛ فعلاً هیچ دروازهٔ انتشار با این بازبینی بسته نمی‌شود.

| موضوع | مشاهدهٔ جاری و مقصد |
| --- | --- |
| option عمومی | `options.py::GeneratorOptions` و export بسته موجود؛ `pipeline.py::convert_markdown_to_docx` شیء/دیکشنری و چهار alias مسطح را می‌پذیرد؛ اعتبارسنجی مرکزی کامل ندارد → V3-02 |
| CLI | `--font/--font-family`، embed، direction و **`--text-align` موجودند**؛ پیش‌فرض font و align با API/template یکسان نیست → V3-02 |
| جهت metadata | `pandoc_json.py::ast_to_docx`، `dir/direction` و `lang/language` را می‌خواند؛ renderer پس از تغییر جهت `_setup_page` را دوباره اجرا می‌کند؛ صرف ساخت renderer پیش از metadata باگ اثبات‌شده نیست → V3-01 |
| RTL پایه | helperهای section، paragraph، run و table و `Normal` موجودند؛ پوشش همهٔ ظرف‌ها و ارث‌بری هنوز نیازمند ممیزی است → V3-01 |
| header/footer | `_setup_page` شش نوع header/footer را می‌بیند، اما فقط پاراگراف‌های سطح اول؛ پیمایش جدول‌های تو‌در‌تو، فونت و fieldها کامل فرض نشود → V3-01/V3-06 |
| فونت تیتر | `heading_font` فقط option اختصاصی یا قالب را می‌خواند؛ `font_family` به آن نمی‌رسد. تفاوت دو نقش ذاتاً باگ نیست؛ قرارداد جدید بخش ۳ باید پیاده شود → V3-02 |
| embedding | `fonts_embed.py` وجود دارد و pipeline آن را **پیش از publish روی staging** اجرا می‌کند؛ font table/rels بازنویسی می‌شوند، settings نوشته نمی‌شود، فقط بدنه هدف است → V3-03 |
| فایل Bold | resolver جاسازی و CSS Mermaid ممکن است Bold خانوادهٔ سفارشی را از `Vazirmatn-Bold` بردارند؛ mismatch واقعی در مسیر انتخاب فایل وجود دارد → V3-02/V3-03/V3-05 |
| sidecar Mermaid | PNG و SVG با دو subprocess جدا ساخته می‌شوند؛ ادعای «همان فرایند» دقیق نیست. runner اکنون `enumerate` دارد و missing SVG را گزارش می‌کند؛ باگ قدیمی `len(issues)` دوباره برنامه‌ریزی نشود → V3-05 |
| oracle پاورقی | `semantic_oracle.py::actual_from_docx` تصویر و math پاورقی را جمع می‌کند؛ هویت کامل، ترتیب nesting و مقایسهٔ معنا همچنان باید سنجیده شوند → V3-04 |
| رندر و review | اتصال `--render-pages` موجود است؛ وضعیت review از تبدیل جداست. وجود کد و پوشهٔ `word-windows-review/` مدرک مشاهدهٔ صفحات نیست → V3-07 |
| مستندات | برخی قراردادهای جدید در README/AGENTS منعکس نیستند؛ متن «فونت جاسازی نمی‌شود» با وجود مسیر آزمایشی embedding نیازمند توضیح وضعیت نهایی است → V3-08 |
| مخزن | در شروع بررسی فایل‌های modified/untracked متعلق به کار قبلی وجود داشتند. `artifacts/` **هم‌اکنون در `.gitignore` است**؛ commit یا پاک‌سازی پیش‌شرط اجرای این پلن نیست → V3-00 |

## ۱. قرارداد محصول و تفسیر دقیق خواستهٔ RTL

هدف: **Markdown فارسی + قالب → DOCX با ساختار پایهٔ RTL، نثر فارسی راست‌چین و فونت اصلی قابل تنظیم از `options=`؛ embedding نیز از همان option روشن/خاموش شود.** نام تابع عمومی همان `convert_markdown_to_docx` می‌ماند؛ تابع موازی با نام generator ساخته نشود.

«کل ساختار RTL» یعنی جهت پایهٔ section، style، ظرف، ترتیب جدول و فهرست و storyهای پشتیبانی‌شده هماهنگ باشد. این عبارت به معنی معکوس‌کردن حروف لاتین، فرمول، کد یا جهت گراف Mermaid نیست. `text-direction=right` نام یک property در Word نیست؛ خواستهٔ کاربر به **جهت خواندن RTL + تراز `right`** ترجمه می‌شود.

- پاراگراف نثر فارسی/مخلوط، جهت RTL دارد؛ پاراگراف مستقلِ تماماً لاتین می‌تواند LTR باشد. در فهرست، جهت marker و continuation از ظرف فهرست می‌آید؛ لاتین‌بودن متن آیتم نباید marker را به سمت دیگری ببرد.
- قطعهٔ لاتین یا URL داخل جملهٔ فارسی فقط در سطح run سیاست LTR می‌گیرد؛ برای آن کل جمله را left-align یا LTR نکن.
- کدِ بلوکی ظرف LTR/left دارد. توضیح یا رشتهٔ فارسی داخل کد باید با حفظ متن و shaping درست آزموده شود؛ تحمیل `w:rtl=0` به همهٔ حروف فارسی راه‌حل عمومی نیست.
- جهت جدول از ظرف مؤثر می‌آید؛ جهت متن هر سلول مستقل است. ستون‌ها را در AST و XML دوباره reverse نکن؛ `bidiVisual` با حفظ تطابق header/data بررسی شود.
- caption و تصویر وسط‌چین، badge عددی، فرمول نمایشی و PAGE با طراحی صریح خود باقی می‌مانند؛ وجود تراز center در سند فارسی نقص RTL نیست.
- نیم‌فاصله، نویسه‌های جهتِ موجود در ورودی، علائم و ترتیب منطقی متن حفظ شوند. کنترل نامرئی تازه برای پوشاندن ایراد اضافه نشود. آزمون باید «نویسهٔ اضافه/حذف‌شده نسبت به منبع» را کشف کند؛ ممنوع‌کردن مطلق RLM/LRM موجود در ورودی غلط است.

### ۱.۱. تقدم و تشخیص جهت

قرارداد فعلی چهارلایه است: option صریح → metadata جهت → metadata زبان → قالب. برای پوشش «متن فارسی بدون metadata روی قالب LTR»، توسعهٔ زیر **تغییر رفتاری برنامه‌ریزی‌شده** است، نه قابلیت فعلی:

1. `options.direction=rtl|ltr` جهت پایهٔ سند را صریح انتخاب می‌کند؛ `auto` این لایه را کنار می‌گذارد.
2. metadata معتبر `dir` یا alias آن `direction`؛ سپس زبان شناخته‌شدهٔ `lang` یا `language`.
3. در نبود انتخاب بالا، زبان غالب متن روایی AST: شمار نویسه‌های قوی Unicode از نوع `R/AL` در برابر `L`؛ RTL اگر شمار RTL بیشتر باشد، LTR اگر لاتین بیشتر باشد. برابری/نبود متن قوی → جهت قالب. این heuristic زبان‌شناسی کامل نیست و نتیجه با option قابل override است.
4. جهت معتبر قالب؛ fallback داخلی RTL فقط در مسیر واقعاً فاقد مقدار معتبر.

متن روایی شامل نثر، تیتر، فهرست و متن سلول است؛ کد، فرمول، raw literal، نشانی لینک/تصویر، URL/مسیر فنی و منبع Mermaid از شمارش حذف شوند. یک comment فارسی در کد نباید سند انگلیسی را RTL کند. زبان با subtag اصلی استانداردش تطبیق داده شود، نه `startswith` آزاد؛ زبان نامشخص به لایهٔ بعد برود. تعارض aliasها یا مقدار نامعتبر جهت باید diagnostic روشن داشته باشد؛ مقدار نامعتبر option به auto تبدیل نشود.

جهت پایهٔ سند با جهت script هر run یکی نیست: سند صریح LTR می‌تواند پاراگراف فارسی RTL و run فارسی داشته باشد. آزمون «هیچ `w:bidi=1` در سند LTR نیست» فقط برای fixture تماماً انگلیسی و بدون استثنای محلی معنا دارد. قابلیت تازهٔ `dir` برای هر Div/Span در این پلن الزامی نیست؛ attribute خارج پشتیبانی نباید با ادعای اجرای override محلی همراه شود.

### ۱.۲. تراز و سازگاری

برای برآوردن خواستهٔ راست‌چینی پیش‌فرض، `page.paragraph_align` چهار قالب همراه در نسخهٔ نهایی `start` باشد؛ **تغییر `purple_book` از `both` به `start` یک تغییر ظاهر عمدی است** و با نمونه و رندر بررسی و مستند شود. قالب سفارشی با `both` یا option صریح همچنان معتبر است. `None` در option تراز یعنی پیروی از `config.yaml`؛ CLI نیز مقدار پیش‌فرض پنهان روی آن تحمیل نکند.

تراز نثر از option سپس قالب می‌آید؛ `start` بر اساس جهت پاراگراف به `right/left` نگاشت می‌شود. گزینهٔ تراز بدنه نباید کد، caption، badge یا طراحی صریح header/footer را بی‌قید بازنویسی کند.

## ۲. نقشهٔ OOXML و مواردی که نباید به الزام کاذب تبدیل شوند

| لایه | هدف و شیوهٔ بررسی |
| --- | --- |
| section | `w:sectPr/w:bidi` با جهت پایه هماهنگ؛ در LTR خلاف پوسته مقدار false مؤثر باشد. `w:bidi` در `settings.xml` درج نشود. تک‌بخشی‌بودن shell حفظ شود. |
| defaults و style | `docDefaults` و `Normal` برای پاراگراف‌های تولیدی، فونت CS، زبان و اندازه سازگار باشند؛ استایل Heading/Footnote/Header/Footer و ارث‌بری پوسته جدا ممیزی شوند. وجود نام فونت صریح با باقی‌ماندن theme attribute متعارض کافی نیست. |
| paragraph | `w:pPr/w:bidi` و `w:jc` طبق نقش و سیاست بخش ۱؛ paragraph mark یعنی `w:pPr/w:rPr` برای متن خالی، Enter، آخر پاراگراف و ارث‌بری آزموده شود. نبود `w:rtl` مستقیم در mark به‌تنهایی باگ یا نقص schema نیست. |
| run | `w:rtl` و در صورت نیاز `w:cs` طبق script و بافت؛ فونت `w:rFonts` و `w:szCs/bCs/iCs` و زبان نقش صحیح. جزیرهٔ لاتین علیه style RTL باید override مؤثر داشته باشد. bold/italic=false نیز در برابر ارث‌بری bold/italic آزموده شود. |
| table و cell | `w:tblPr/w:bidiVisual` مطابق ظرف؛ false صریح وقتی style/table پوسته RTL را به LTR برمی‌گردانیم. ترتیب logical ستون‌ها، grid/width و هر cell جدا سنجیده شوند؛ جدول تزئینی با جدول داده اشتباه نشود. |
| list/quote | indent و hanging از جهت ظرف محاسبه شود. `quotes.border_side=physical_right/physical_left` **ثابت** می‌ماند؛ فقط `start/end` باید با **effective_direction** بچرخد، نه `template.direction`. |
| header/footer | default/first/even برای هر دو story، جدول و سلول nested، لینک، لوگو، field و متن خالی بررسی شوند. دسترسی به story نباید ناخواسته part خالی بسازد یا طراحی center/PAGE را خراب کند. |
| footnote | همهٔ پاراگراف‌ها، marker، separator/continuation، لینک، جدول، کد، تصویر و Mermaid با رابطهٔ متعلق به `footnotes.xml`؛ paragraph اول و بعدی فونت/اندازهٔ یک نقش داشته باشند. |
| shell و story دیگر | محتوای body پوسته حذف می‌شود؛ endnote/textbox موجود فقط از حیث حفظ ساختار و عدم رگرسیون بررسی شوند. تولید endnote یا پشتیبانی عمومی textbox قابلیت الزامی تازه نیست؛ مورد خارج قرارداد diagnostic روشن بگیرد. |
| OMML و drawing | ترتیب عملوندها و متن فرمول حفظ؛ تصویر/نمودار در ظرف مناسب و بدون flip. جهت section جای سیاست ریاضی یا graph `LR/TB` را نگیرد. |

نکات استاندارد و تصمیم سازگاری:

- `w:rtl` نباید به متن قوی لاتین تحمیل شود؛ تنظیم run باید با script هماهنگ باشد. از این رو `rPrDefault/w:rtl=1` سراسری فقط پس از اثبات override همهٔ runهای استثنا مجاز است؛ مقداردهی کور defaults ممنوع است. [مرجع RightToLeftText](https://learn.microsoft.com/he-il/dotnet/api/documentformat.openxml.wordprocessing.righttolefttext?view=openxml-3.0.0)
- `w:rtlGutter` سمت فضای صحافی را تعیین می‌کند، نه جهت متن. نبود آن در سند بدون gutter نقص RTL نیست. gutter/mirrored margins پوسته حفظ شوند؛ افزودن یا تغییر gutter فقط برای نیاز صحافی مشخص با تست مستقل. [مرجع GutterOnRight](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.gutteronright?view=openxml-3.0.1)
- `w:textDirection` جریان افقی/عمودی متن در section/cell را تعیین می‌کند؛ ابزار راست‌چین‌کردن فارسی نیست. مقدار افقی موجود یا چرخش عمدی پوسته را صرف حضور این عنصر حذف نکن. [مرجع TextDirection](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.textdirection?view=openxml-3.0.1)
- ادعای «`start/end` همیشه نامعتبر و موجب Repair است» صحیح نیست: SDK آن‌ها را برای Office 2010+ معرفی می‌کند. سیاست این پروژه فعلاً خروجی فیزیکی `right/left/center/both` از `word_safe_jc` است؛ این تصمیم سازگاری با الزام استاندارد فرق دارد. [مرجع JustificationValues](https://learn.microsoft.com/it-it/dotnet/api/documentformat.openxml.wordprocessing.justificationvalues?view=openxml-2.19.0)
- همین ملاحظه دربارهٔ `w:ind@w:start/end` وجود دارد؛ تبدیل اجباری همهٔ `left/right`ها لازم نیست. مقدار فیزیکیِ درست بر اساس جهت می‌تواند باقی بماند؛ تغییر encoding به نسخهٔ Word هدف و آزمون ارث‌بری وابسته باشد. [مرجع Indentation.Start](https://learn.microsoft.com/it-it/dotnet/api/documentformat.openxml.wordprocessing.indentation.start?view=openxml-3.0.1)
- helperها باید ترتیب فرزندان schema، یکتایی property، namespace و مقدارهای مجاز را حفظ کنند. XML خوش‌ساخت یا یافتن یک tag با regex، اعتبار OOXML یا رفتار Word را اثبات نمی‌کند.

## ۳. قرارداد نهایی `GeneratorOptions`

فیلدهای فعلی حفظ شوند؛ این جدول **رفتار هدف** را مشخص می‌کند:

| فیلد | مقدار پیش‌فرض و قرارداد |
| --- | --- |
| `font_family` | `None` = فونت اصلی قالب؛ انتخاب صریح، خانوادهٔ اصلی فارسی برای body و heading در نبود override اختصاصی heading است. پیش‌فرض قالب‌های همراه `Vazirmatn`. |
| `heading_font` | `None`؛ تقدم: override خودش → `font_family` صریح → `fonts.heading` قالب → body مؤثر. |
| `latin_font` | `None`؛ override خودش → `fonts.latin` قالب؛ مستقل از font_family. |
| `code_font` | `None`؛ override خودش → `fonts.code` قالب؛ مستقل و پیش‌فرض همراه `Courier New`. |
| `embed_fonts` | boolean واقعی، پیش‌فرض `False`؛ دامنه و شکست طبق بخش ۴. |
| `direction` | `auto`؛ تنها `auto/rtl/ltr` و تقدم بخش ۱.۱. |
| `text_align` | `None`؛ مقادیر `start/right/left/center/both`؛ `justify` اگر به‌عنوان alias پذیرفته شد در API/CLI/template همگی به `both` normalize شود. |

تعداد فونت‌های CS سند الزاماً یک نیست. `--font X` لاتین و کد را تغییر نمی‌دهد؛ `heading_font=Y` مجاز است. نقش مورد انتظار هر run باید بررسی شود، نه اندازهٔ مجموعهٔ تمام نام‌های فونت در ZIP.

### ۳.۱. رابط، validation و تقدم

- API موجود `options=GeneratorOptions(...)` یا dict می‌پذیرد؛ چهار alias مسطح `font_family/embed_fonts/direction/text_align` حفظ شوند. مقدار **غیر None** مسطح بر options تقدم دارد؛ `embed_fonts=False` باید True داخل options را خاموش کند. `None` به معنی «override نشده» است، نه reset مقدار شیء.
- شیء option، dict ورودی و شیء `Template` کاربر تغییر نکنند؛ دو تبدیل پشت‌سرهم/هم‌زمان با فونت یا جهت متفاوت به هم نشت نکنند. نتیجهٔ مؤثر یک بار resolve و به renderer، Mermaid و embedding داده شود؛ font resolverهای متناقض باقی نمانند.
- کلید ناشناخته، نوع اشتباه، رشتهٔ خالی/فقط فاصله، direction/align نامعتبر و `embed_fonts="false"` پیش از Pandoc، مرورگر یا publish رد شوند. نام فونت می‌تواند فاصله، فارسی، apostrophe یا `&` داشته باشد؛ XML و CSS صحیح escape شوند.
- خطای option در API `ValueError` روشن؛ CLI برای کاربرد نامعتبر exit 2؛ خطای عملیاتی embedding/renderer در CLI exit 1. خطاهای template و فایل از قرارداد فعلی خود پیروی کنند.
- `font_family=None` استفادهٔ عادی از قالب است و W05 تولید نکند. تست فعلی `test_v3_02_font_family_none_fallback_warning` قرارداد قدیمی را قفل کرده؛ در اجرای TDD با انتظار جدید اصلاح شود، نه اینکه ناسازگاری‌اش پنهان شود.
- نام فونت به‌تنهایی حضور آن روی دستگاه مقصد را اثبات نمی‌کند. حالت reference اجازهٔ نام فونت دلخواه دارد؛ وضعیت availability نامعلوم با «فونت نامعتبر» یکی نیست. نبود فایل لازم برای Mermaid/embedding یا نبود فونت در محیط رندر مرجع diagnostic مشخص دارد.

### ۳.۲. CLI و گزارش نتیجه

`--font/--font-family` و `--text-align` موجودند؛ پیش‌فرض هر دو `None` شود. `--heading-font`، `--latin-font` و `--code-font` برای پوشش نقش‌های عمومی افزوده شوند. help نقش‌ها و دامنهٔ embedding را توضیح دهد؛ aliasهای موجود حذف نشوند.

پیام موفقیت از **نتیجهٔ مؤثر** ساخته شود، نه صرف مقدار درخواستی: direction=auto نتیجهٔ resolved نیست و embed=True مدرک جاسازی همهٔ فونت‌ها نیست. یک گزارش داخلی مشترک شامل requested/effective، منشأ هر مقدار، نقش‌های فونت و نتیجهٔ embedding برای CLI و runner تعریف شود. `run.json` متعلق به runner است؛ هر تبدیل معمولی نباید بی‌درخواست فایل sidecar گزارش بسازد. بازگشت عمومی API همچنان `Path` و `warnings` همچنان لیست رشته بماند؛ برای گزارش داخلی، شکستن API یا تعریف global لازم نیست.

نمونهٔ قرارداد هدف، پس از پیاده‌سازی و آزمون:

```python
from md_to_docx import GeneratorOptions, convert_markdown_to_docx

saved = convert_markdown_to_docx(
    content="# عنوان\n\nمتن فارسی و SQL Server.\n",
    output_path="output.docx",
    template="persian_book",
    options=GeneratorOptions(
        font_family="Vazirmatn",
        direction="auto",
        text_align="start",
        embed_fonts=True,
    ),
    overwrite=False,
)
```

## ۴. قرارداد جاسازی فونت و تنظیمات Word

دو موضوع جدا بررسی شوند: **وجود فونت واقعی در package** و **سیاست Word هنگام ذخیرهٔ بعدی**. `w:embedTrueTypeFonts` درخواست ذخیره با فونت است؛ به‌تنهایی part فونت نمی‌سازد. نبود آن هم ثابت نمی‌کند part موجود غیرقابل استفاده است. رفتار تیک UI، save/reopen و استفادهٔ واقعی باید در Word هدف مشاهده شود. [مرجع EmbedTrueTypeFonts](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.embedtruetypefonts?view=openxml-3.0.1)، [مرجع EmbedRegularFont](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.embedregularfont?view=openxml-3.0.1)

### ۴.۱. دامنه و دو حالت option

| حالت | رفتار هدف |
| --- | --- |
| `embed_fonts=False` | فایل خروجی فقط به فونت‌ها reference دهد؛ settings جاسازی غیرفعال باشد. اگر shell از قبل فونت جاسازی‌شده دارد، ارجاع‌های embed و رابطه‌ها/partهای فونت مربوط **در کپی خروجی** حذف شوند؛ خود shell و اعلان‌های فونت حفظ شوند. part مشترک فقط پس از تحلیل رابطه‌ها پاک شود. |
| `embed_fonts=True` | حداقل خانوادهٔ مؤثر body و heading جاسازی شوند؛ اگر یکی‌اند فایل تکراری نساز. خانواده‌های latin/code که همان خانواده‌اند از آن استفاده کنند؛ خانوادهٔ مستقل آن‌ها فقط با فایل معتبر و مجوز مشخص جاسازی شود، وگرنه `referenced_only` با علت گزارش شود. این دامنه در help و README صریح باشد. |
| خانوادهٔ اصلی غیرقابل جاسازی | `ConvertError` و عدم انتشار خروجی جدید؛ فایل قبلی DOCX/media سالم بماند. شکست را به موفقیت reference-only تبدیل نکن. |

حداقل فرمت تضمین‌شدهٔ این دور TTF ایستای دارای outline TrueType است. TTC، variable font، OTF/CFF و قالب‌های دیگر بدون نمونه و آزمون اعلام پشتیبانی نشوند. انتخاب نکردن embedding نباید نیاز تازه‌ای به فایل/مجوز embedding ایجاد کند؛ اعتبارسنجی موجود مسیرهای صریح قالب همچنان برقرار است.

Regular و Bold واقعی برای خانواده‌های اصلیِ استفاده‌شده فراهم شوند؛ در قالب همراه هر دو فایل Vazirmatn وجود دارند. Italic/BoldItalic اگر فایل واقعی معتبر دارند با face درست embed شوند؛ در نبودشان، synthetic italic با محدودیت صریح و آزمون Word قابل بررسی است. نبود face ایتالیک به‌تنهایی اثبات fallback نیست؛ فایل Regular را به نام Italic جا نزن و synthetic را «face جاسازی‌شده» گزارش نکن.

### ۴.۲. فایل، هویت و مجوز

- مسیرها از `font_files` و ریشهٔ قالب resolve شوند؛ حالت family و `Family-Regular/Family-Bold` یک قرارداد مشترک برای Mermaid و embedding داشته باشد. افزودن schema جدید فقط با زنجیرهٔ validation → load → مصرف → تست → نمونه/مستندات انجام شود.
- نام داخلی family/subfamily، وزن و style و سلامت جدول‌های فونت با نقش ادعاشده تطبیق داده شوند. fallback Bold یک family به `Vazirmatn-Bold` ممنوع؛ filename یا پسوند `.ttf` مدرک هویت نیست.
- heuristic فعلیِ جست‌وجوی کلمهٔ `embed/bundle` در مجوز حذف شود. منشأ، نسخه، hash فایل و مجوز واقعی خانواده ثبت شود. یک boolean مانند `font_files_embeddable=true` به‌تنهایی مجوز یا قابلیت فنی ایجاد نمی‌کند.
- `OS/2.fsType` با توجه به نسخهٔ جدول بررسی شود: Restricted/Bitmap-only یا وضعیت نامعتبر برای مسیر outline رد؛ Preview & Print برای خروجی قابل ویرایش این محصول کافی نیست؛ Editable/Installable همراه مجوز قابل استناد قابل بررسی‌اند. No-subsetting با جاسازی کامل سازگار است. بیت‌های محدودیت برای عبور آزمون تغییر نکنند. [مرجع رسمی OS/2 و fsType](https://learn.microsoft.com/en-us/typography/opentype/spec/os2#fstype)
- قالب همراه با manifest قابل اعتماد برای فایل‌های OFL پذیرفته شود؛ فونت سفارشی با منشأ/مجوز نامشخص در حالت true خطای روشن بگیرد. parser معتبر فونت در صورت نیاز انتخاب شود؛ اگر وابستگی افزوده شد، `pyproject.toml`، constraints و wheel پوشش داده شوند. حدس باینری و regex جای parser را نگیرد.

### ۴.۳. سلامت package و رفتار ذخیره

- `fontTable.xml`، rels و relationship موجود document **merge** شوند؛ مسیر font table از relationship resolve شود و همیشه hardcode فرض نشود. `altName/panose/charset` و دیگر اعلان‌ها و رابطه‌های غیرمرتبط حفظ شوند.
- part name و rId در scope خود یکتا باشند؛ برخورد با `font1.odttf` موجود و embedding دوباره، duplicate ZIP entry، dangling rel یا پاک‌شدن فونت نامرتبط نسازد. نوشتن XML با XML API و حفظ namespaceهای extension/MC باشد، نه الحاق family خام به رشته.
- `fontKey`، deobfuscation، content type فونت و font table و target هر `embedRegular/Bold/Italic/BoldItalic` کنترل شوند. obfuscation رمزنگاری امنیتی نیست. **round-trip با همان تابع XOR کافی نیست**؛ یک vector ثابت با انتظار مستقل و سپس deobfuscation/خواندن فونت با parser مستقل لازم است. بایت‌های پس از محدودهٔ obfuscation نباید تغییر کنند.
- برای true، `embedTrueTypeFonts` روشن و سیاست full-font برقرار باشد؛ `saveSubsetFonts` از shell اگر روشن است false شود یا مطابق معنای استاندارد حذف شود. این پرچم سیاست ذخیرهٔ آتی است، نه اثبات اینکه bytes فعلی subset شده‌اند. [مرجع SaveSubsetFonts](https://learn.microsoft.com/ja-jp/dotnet/api/documentformat.openxml.wordprocessing.savesubsetfonts?view=openxml-3.0.1)
- `embedSystemFonts` جدا از وجود فونت اصلی است. پیش‌فرض این پلن false برای خانواده‌های سیستمیِ صرفاً reference است؛ فقط با جاسازی هدفمند خانواده‌های مربوط و آزمون save/reopen روشن شود. از اسم «system font» نصب همگانی نتیجه نگیر. [مرجع EmbedSystemFonts](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.embedsystemfonts?view=openxml-3.0.1)
- تمام تغییرات بسته، از جمله حالت false، پیش از publish در staging انجام شوند؛ failure میانی، فایل فونت خراب، ورودی غیرقابل خواندن و خطای replace باید cleanup و بقای خروجی/دارایی قبلی را اثبات کنند. قفل و قرارداد overwrite فعلی تضعیف نشوند.

### ۴.۴. گزارش و پذیرش embedding

برای هر خانواده/face: نقش‌های مصرف‌کننده، نام واقعی، منبع و hash، نوع مجوز/fsType، وضعیت `embedded/referenced_only/unsupported` و علت ثبت شود. `synthetic_style` جدا باشد. جمع‌بندی شامل `requested`، وضعیت کل `embedded/partial/referenced_only/unsupported`، اندازهٔ پیش/پس و تنظیمات ذخیرهٔ Word باشد. `partial` فقط وقتی دامنهٔ ضروری body/heading کامل و نقش‌های اختیاری reference هستند موفق است؛ unsupported در دامنهٔ ضروری تبدیل را fail می‌کند. نتیجهٔ ناموفق API با Path موفق بازنگردد.

آزمون عملی ضروری: Word هدف در محیط تمیز **بدون نصب فونت فارسیِ آزمون**، خروجی true و false را جدا باز کند؛ true بدون Repair و با فونت اصلی نمایش داده شود، پس از ذخیرهٔ کپی و بازکردن دوباره پایدار بماند. false واقعاً part جاسازی‌شده نداشته باشد؛ برای پذیرش layout آن، محیط مرجع با فونت نصب‌شده استفاده شود. برای آزمایش، فونت‌های دستگاه شخصی کاربر حذف نشوند. Chromium/Mermaid، Word و LibreOffice سه محیط فونت جدا هستند؛ embedding در DOCX فونت نمودار PNG را عوض نمی‌کند.

## ۵. کارهای اجرایی و معیار پذیرش هر مرحله

هر تغییر رفتاری: fixture با انتظار مستقل → شکست واقعی روی رفتار قبلی → کوچک‌ترین اصلاح → تست مرتبط سبز → رگرسیون لازم → شاهد ساختاری/بصری. نام آزمون یا کامنت «red test» شاهد اجرای red نیست. تست‌های موجودی که انتظار غلط را تثبیت کرده‌اند با توضیح تغییر قرارداد به‌روز شوند؛ تست حذف یا ضعیف نشود.

### V3-00 — ثبت snapshot و بازتولید پایه · P0

- وضعیت dirty، commit، hash کد/قالب/font/lockfile و فرمان‌ها ثبت؛ وجود ابزار از اجرای موفق و review جدا گزارش شود. نصب مجدد محیط آماده لازم نیست.
- اصالت کتاب `SQL_Server_DBA_Book_Chapters_1_4_FIXED.md` با hash تاریخی `525a3e92016a946bf36fdd5b3a2a8c8829a6e71e3e433fe52b6d9e9f3352443b` کنترل شود؛ اختلاف ابتدا بررسی شود و با بازنویسی فایل رفع نشود. rawها و E01–E07 در صورت دسترسی با خروجی تازه جدا مقایسه شوند.
- ۶۱ ID manifest، برش‌های بسته و referenceها، provenance تصاویر و warningهای پنج caption بی‌تصویر B00 بررسی شوند؛ برای captionها تصویر ساخته نشود. فایل تاریخی `fix.md` در checkout بررسی‌شده یافت نشد؛ اگر در تاریخچه/نسخهٔ در دسترس کاربر باقی‌مانده‌ای دارد، با ID و مقصد در همین بخش ثبت شود؛ نبود فایل مساوی بسته‌بودن نیست.
- **پذیرش:** گزارش پایه با محدودیت روشن و snapshot واقعی؛ baseline خراب `known-bad/unapproved` بماند.

### V3-01 — جهت در همهٔ ظرف‌های پشتیبانی‌شده · P0

- سیاست بخش‌های ۱ و ۲ در `options.py`، adapter، renderer، `bidi.py` و `oxml.py` یکسان شود؛ استفادهٔ مستقیم از `template.direction` در مسیرهای فعال ممیزی شود. مسیر فعال AST و helper قدیمی/عمومی با هم اشتباه نشوند.
- resolution metadata/content پیش از emission محتوای وابسته انجام شود؛ دوباره‌اعمال سیاست بعد از shell idempotent باشد. فارسی/لاتین/خنثی، Enter و paragraph mark، defaults متعارض، code و rich inlineها پوشش داده شوند.
- فهرست چندسطحی با آیتم لاتین و پاراگراف دوم، جدول با header/data متمایز، پاورقی چندپاراگرافی و nested، هر شش header/footer با جدول و PAGE بررسی شوند.
- **پذیرش:** expectation بر اساس نقش هر عنصر، محتوای بدون تغییر و مشاهدهٔ Word؛ نه نسبت کلی tagهای RTL و نه الزام شکست شش تست از پیش تعیین‌شده.

### V3-02 — options، نقش فونت و diagnostic · P0

- قرارداد بخش ۳، validation مرکزی و precedence اجرا شود؛ CLI default font/align قالب را override نکند. حالت options بدون مقدار همان خروجی مؤثر بدون options را بدهد.
- آزمون probe با چهار family متمایز، font_family تنها، heading override، custom template، None و False صریح؛ reuse Template/options بدون mutation و نشت.
- تست فونت واقعی دوم برای body/heading/caption/footnote/header/footer و CSS Mermaid؛ تفاوت عمدی نقش‌ها حفظ شود. فونتِ نام‌برده با فونت واقعاً رندرشده تفکیک شود.
- **پذیرش:** API شیء/dict/alias، CLI فایل/stdin و گزارش requested/effective یک قرارداد بدهند؛ Validation پیش از اجرای ابزار خارجی رخ دهد.

### V3-03 — embedding درست و قابل خاموش‌کردن · P0

- بخش ۴ با tests منفی/مثبت اجرا شود؛ settings، merge، identity، full-font، faceهای مستقل، collision و false روی shell دارای embed الزامی‌اند.
- فونت خراب/ناقص، family اشتباه، Bold اشتباه، مجوز نامعلوم، fsType محدود، GUID نامعتبر، XML-sensitive family و failure حین ZIP/publish هرکدام انتظار روشن داشته باشند.
- **پذیرش:** package oracle و vector مستقل، عدم از دست‌رفتن partهای دیگر، عدم انتشار در خطا و Word تمیز/save/reopen؛ حجم ثابت نمونه شرط پذیرش نیست.

### V3-04 — oracle معنایی، جهت، package و هشدار · P0 برای پذیرش

- مدل مستقل ترتیب block/inline، متن دقیق کد، tab/blank line، level/number تیتر، cell/row/column، link/bookmark، media occurrence/hash/story و footnote reference به مقصد درست را مقایسه کند. تعداد درست با محتوای غلط pass نیست؛ math در محدودهٔ OMML با معنای عملگر/عملوند سنجیده شود.
- شکل‌های native و تزئینی جدول، TOC/PAGE و caption تولیدی از متن منبع تفکیک شوند؛ سطح heading_badge از outline/انتظار مستقل سنجیده شود. تصاویر/فرمول پاورقی اکنون استخراج می‌شوند، اما پوشش ترتیب/identity آن‌ها اثبات شود.
- هشدارها با multiset دقیق code + identity + محل/مرحله تطبیق کنند؛ صرف تعداد یا substring کافی نیست. W05 عادی حذف و missing/extra/duplicate warning آشکار شود؛ B00 و برش‌ها انتظار مستقل داشته باشند.
- oracle جهت، ارث‌بری و booleanهای OOXML را بفهمد؛ `0/false/off` و نبودِ مقدار با پیش‌فرض true درست تفسیر شوند. هر failure part/story/عنصر و انتظار/واقعیت داشته باشد؛ serializer خودش oracle خودش نباشد.
- schema/order و relationship همهٔ partها، font references، content types، rId تکراری/شکسته و media غیرمصرف‌شده سنجیده شوند. parser XML به‌تنهایی validator Word نیست؛ ابزار validator مستقل در تست می‌تواند استفاده شود، بدون تغییر فناوری موتور محصول.
- **پذیرش با خرابی عمدی روی کپی:** حذف/تکرار جمله، تغییر عدد SQL، قطع آخر کد، جابه‌جایی cell، حذف شمارهٔ heading، شکستن لینک/footnote ref، جابه‌جایی دو تصویر هم‌اندازه، خراب‌کردن fontKey، انتقال متن body به header و معکوس‌کردن bidi هرکدام fail شوند؛ clipping نیازمند رندر است.

### V3-05 — Mermaid واقعی و فونت/دارایی آن · P1؛ خرابی محتوا P0

- Node سازگار با lockfile، مرورگر Puppeteer مدیریت‌شده، override نامعتبرِ بدون fallback و setup بدون `npx -y` حفظ شوند. پشتیبانی runtime مدیریت‌شده به نام تنها یک binary تقلیل نیابد؛ configuration و نسخهٔ واقعاً آزموده ثبت شوند.
- preflight فقط برای ورودی دارای Mermaid؛ شکست launch یک بار در run ثبت و بقیهٔ زوج‌های وابسته blocked شوند، حتی در workerها. timeout/cancel تنها process/profile همان run را جمع کند؛ تبدیل بدون Mermaid ادامه یابد.
- فایل Regular/Bold از family صحیح، CSS escaped، font-ready و glyph/وزن واقعی قبل از تصویر کنترل شوند؛ هشدار fallback در گزارش عمومی گم نشود.
- ارتباط PNG/SVG با occurrenceِ AST، source/config/CSS/font/runtime hash و cache key اثبات شود. دو subprocess فعلی «همان فرایند» نیستند: یا یک خروجی میانی مشترک، یا تولید معادلِ قابل اثبات با fingerprint یکسان و آزمون همخوانی استفاده شود. index درست فعلی حفظ؛ extractor متنی runner برای nesting با پیمایش AST تطبیق داده شود.
- label چندخطی، تکراری، foreignObject/tspan و topology بررسی؛ نبود SVG fail باشد. وجود label در DOM اثبات خوانایی یا نبود clipping در PNG نیست. S10–S12 در A5 و nesting جدول/فهرست/Div/تعریف‌نامه/پاورقی بررسی شوند.
- **پذیرش:** PNG واقعی با graph direction و متن منبع محفوظ، theme هر قالب، label خوانا در اندازهٔ درج‌شده؛ smoke macOS و رگرسیون جلوگیری از crash مستقل از Linux ثبت شود.

### V3-06 — قالب، صفحه‌بندی، TOC و محتوای غنی · P1؛ بریدگی/افت محتوا P0

- چهار قالب ریشه و package همگام؛ تغییر پیش‌فرض تراز purple_book آشکار؛ font/size/color هر نقش از جمله nested callout/quote/caption/footnote مطابق قالب باشد. strict custom-style، مقصد mapping، canonicalization و Div/Span ناشناخته طبق قرارداد بررسی شوند.
- عرض واقعی ظرف پس از indent/padding/margin برای جدول، کد، تصویر و badge محاسبه شود؛ خط بلند کد، tab، انتهای خالی، جدول ۶۰ردیفی و code ۱۰۵خطی حفظ شوند. کادر بلند اجازهٔ شکست سالم داشته باشد؛ keepNext/cantSplit زنجیرهٔ ناممکن نسازند.
- تصویر کوچک/نسبت ۲۰۰:۱/EXIF/alpha، مسیر فارسی و فاصله/percent، file/content/stdin و فایل هم‌نام در base_dir دیگر؛ scaling واحد، هویت درست و caption مرتبط حفظ شوند. پوشهٔ media شرط نمایش DOCX نباشد.
- تیترهای ۱ تا ۶ با rich inline، چهار حالت badge/extract_number و شمارهٔ بلند در A5؛ outline، bookmark یکتا و navigation واقعی Word بررسی شوند.
- TOC فقط opt-in؛ مسیر metadata `toc: true` موجود کافی است مگر نیاز مستقل به option ثابت شود. comment یا عنوان «فهرست مطالب» آن را فعال نکند. fieldهای TOC/PAGE و لینک‌ها پیش/پس update در Word بررسی و شمارهٔ صفحه جعل نشود.
- single-section shell، تقدم هندسهٔ YAML، header/footer/logo در همهٔ انواع صفحه و حفظ محتوای مجاز پوسته آزموده شوند؛ body پوسته طبق قرارداد حذف می‌شود.
- **پذیرش:** تمام صفحات متاثر بدون clipping/overlap، تیتر یتیم، قطع متن و نسبت غلط؛ raw HTML، rowspan/colspan خارج قرارداد، math ناشناخته و nesting پشتیبانی‌نشده diagnostic روشن داشته باشند. `to-md` موجود فقط رگرسیون حفظ داده بگیرد؛ گسترش تبدیل معکوس هدف این دور نیست.

### V3-07 — ماتریس، رندر همهٔ صفحات و مرور هدفمند · P0 برای بستن

- ماتریس پایه همان ۶۱ × ۴ = ۲۴۴ زوج است. تست‌های گزینه/embedding و موارد منفی **اضافی** هستند؛ با حذف fixture سخت یا شمردن حالت option به‌جای fixture، عدد ۲۴۴ تکمیل نشود.
- runner انتخاب نامعتبر/خالی، ID تکراری، manifest ناسالم، missing pair، shard ناقص و output collision را رد کند؛ run گزینشی تعداد واقعی خودش را گزارش کند. HTML گزارش escape و لینک‌ها قابل حمل باشند.
- conversion، semantic، package، warnings، Mermaid، render هر engine و review جدا ثبت شوند. mapping وضعیت‌های فعلی مانند `done/not_run` در گزارش مستند باشد؛ نبود اجرای رندر «ابزار غایب» فرض نشود. conversion موفق از نتیجهٔ واقعی تولید DOCX مستقل از oracle محاسبه شود؛ صحت package دروازهٔ جداست.
- mode «تبدیل/بررسی ساختاری» با پذیرش release جدا باشد؛ fail/error/blocked/skip الزامی یا review الزامیِ pending در mode release خروج غیرصفر بدهد. سبزشدن unit با skip خارجی، release موفق نیست.
- برای هر ۲۴۴ زوج، PDF و PNG **تمام صفحات** LibreOffice و Word هدف با engine/version و hash تولید شوند: ۴۸۸ نتیجهٔ رندر مورد انتظار، تعداد صفحه فقط پس از اجرا معلوم می‌شود. original DOCX و کپی field-updated جدا بمانند.
- page count، page missing/stale، timeout و renderer error به‌روشنی گزارش شوند. زمان/فضای B00 و S11 ابتدا اندازه‌گیری، worker/profile محدود و cache مبتنی بر hash باشد؛ retry خرابی محتوایی ممنوع.
- تمام صفحات و مرزهایشان توسط ارزیاب تصویری یا انسان دیده شوند؛ thumbnail/contact sheet به‌تنهایی کافی نیست. رکورد شامل pair/engine/page/hash/reviewer/time و `pending/accepted/issues_found/uncertain` باشد؛ XML هرگز accepted بصری صادر نکند.
- مرور انسانی هدفمند: B00 هر چهار قالب و شروع/پایان فصل؛ S02، S07–S14 و S16، همهٔ severe/uncertain و اختلاف مهم Word/LO؛ علاوه بر آن حداقل ۱۰٪ صفحات پذیرفته‌شدهٔ ماشینی در هر قالب/engine با seed ثبت‌شده. در صورت یافتن خطای جدی، موارد همان الگو دوباره مرور شوند. این الزام به معنی مطالبهٔ مرور دستی همهٔ صفحات از کاربر نیست.
- صفحه/سند کنترل RTL و فونت شامل mixed text، heading، table/list، code، footnote، regular/bold/italic و PAGE باشد؛ جاگیری در «دقیقاً یک صفحه» شرط نباشد اگر خوانایی را کم کند. آزمایش embedding محیط تمیز بخش ۴ نیز جدا ثبت شود.
- **پذیرش:** artifact تازه، صفر صفحهٔ بدون review، severe/uncertain حل‌شده و تأیید انسانی لازم. نبود Word/LibreOffice/فونت/runtime یا پاسخ مرور، `blocked/pending` است؛ فقط همان دروازه باز می‌ماند و پیشرفت مستقل ادامه می‌یابد.

### V3-08 — wheel، CI، مستندات و تحویل · P1

- unit job عمداً بدون browser/Node و با Pandoc لازم؛ wheel job مستقل؛ integration با ابزار واقعی و بدون skip الزامی؛ PR نماینده و nightly/release با ماتریس کامل. متغیر `MD2DOCX_REQUIRE_EXTERNAL=1` به‌تنهایی همهٔ skipها را مهار نمی‌کند.
- wheel در venv تازه با cwd خارج checkout، بدون `PYTHONPATH` پروژه و با بررسی `__file__`/مسیر template آزموده شود. هر چهار قالب با config، shell، Regular/Bold/OFL، CSS/theme/logo و دارایی لازم؛ نام قالب و پوشهٔ سفارشی با مسیر فارسی/فاصله؛ API/CLI/stdin و embed on/off پوشش بگیرند.
- `README.md`، `README_FA.md`، `AGENTS.md`، docstring/help و setup/CI با رفتار نهایی همگام شوند: auto جدید، تراز پیش‌فرض، نقش‌ها، option precedence، دامنهٔ embedding، محدودیت فرمت/face و دستگاه مقصد. نمونهٔ مستند واقعاً اجرا و منبعش حفظ شود.
- بستهٔ تحویل شامل چهار DOCX کتاب، نمونه‌های تصویر/Mermaid و کنترل RTL/embedding، ورودی و قالب سفارشی قابل حمل، فرمان بازتولید، گزارش ماتریس و صفحات و محدودیت‌ها باشد. فایل اصلی برای مقایسه نگهداری و Word نهایی دستی تعمیر نشود.
- **پذیرش:** مصرف‌کنندهٔ تازه در محیط تمیز نمونهٔ MD + نام/مسیر قالب را بسازد؛ همهٔ ادعاها به شاهد همان snapshot وصل باشند.

## ۶. ترتیب و وابستگی اجرا

۱. V3-00: ثبت پایه و تعیین Word/renderer هدف، بدون commit اجباری.
۲. قرارداد بخش ۱ و ۳ و validation/گزارش V3-02؛ سپس V3-01 با تست‌های مستقل از ابتدا. RTL اولویت اصلی است.
۳. resolver فونت مشترک V3-02 → V3-03 و بخش فونت V3-05؛ Word embedding probe کوچک پیش از اجرای بزرگ انجام شود تا اشکال package زود آشکار شود.
۴. V3-04 هم‌زمان با هر اصلاح تکمیل شود؛ نوشتن oracle به پس از تولید همهٔ خروجی‌ها موکول نشود.
۵. V3-05/V3-06 → fixtureهای نماینده روی چهار قالب → ماتریس و review V3-07.
۶. V3-08 و تثبیت snapshot؛ اجرای نهایی شواهد مرتبط روی همان snapshot. تغییر کد/فونت/قالب، پذیرش قدیمی صفحات متاثر را باطل می‌کند.

این ترتیب وابستگی کارهاست، نه مجوز اجرای همین حالا؛ درخواست فعلی همچنان فقط ویرایش پلن است.

## ۷. انتقال قابل ردیابی همهٔ برنامه‌های قبلی

هیچ گروهی صرفاً با تیک تاریخی بسته نیست. «حفظ و راستی‌آزمایی» یعنی از پیاده‌سازی موجود شروع کن؛ «باز» یعنی معیار پذیرش این سند هنوز شاهد نهایی می‌خواهد. این جدول جایگزین حکم کلی و نادرست «FINAL-01…16 همگی بسته‌اند» است؛ FINAL-14/15 خود دروازهٔ تحویل/مستندات‌اند.

| `finalize.md` | مقصد و تکلیف |
| --- | --- |
| FINAL-01/02 | OMML و معنای فرمول → V3-04/V3-06؛ موجود، حفظ و راستی‌آزمایی nesting |
| FINAL-03/04 | کد دقیق و admonition داخل fence → V3-04/V3-06؛ رگرسیون literal و چندخطی |
| FINAL-05/06 | Mermaid nested و resolver تصویر → V3-05/V3-06؛ اجرای واقعی و identity لازم |
| FINAL-07/08 | پاورقی غنی و تیتر/anchor → V3-01/V3-04/V3-06 |
| FINAL-09/10 | schema، typography و جهت ظرف‌ها → V3-01/V3-02/V3-06 |
| FINAL-11/12 | rollback، locks، overwrite و API/CLI → V3-02/V3-03/V3-08؛ با embedding دوباره بررسی |
| FINAL-13 | table/list/metadata → V3-01/V3-04/V3-06 |
| FINAL-14/15 | نصب، integration، همهٔ صفحات Word و گزارش → V3-07/V3-08؛ باز تا شاهد نهایی |
| FINAL-16 | `to-md` اختیاری، اکنون موجود → رگرسیون V3-06/V3-08؛ توسعهٔ جدید لازم نیست |

| `persian_layout_quality_plan.md` | مقصد |
| --- | --- |
| Q00/Q01 | اصالت raw/source، corpus، extraction و manifest → V3-00/V3-04 |
| Q02 | محیط فونت و کنترل واقعی → V3-02/V3-03/V3-05/V3-07 |
| Q03 | runner و حاصل‌ضرب → V3-07/V3-08 |
| Q04 | custom-style، semantics و کمبود منبع → V3-00/V3-04/V3-06 |
| Q05/Q06 | RTL و نقش typography → V3-01/V3-02/V3-06 |
| Q07/Q08/Q09 | عرض، تیتر، list/table/code و شکست → V3-04/V3-06/V3-07 |
| Q10/Q11 | تصویر و Mermaid واقعی → V3-05/V3-06/V3-07 |
| Q12/Q13 | nesting، پاورقی، TOC و shell → V3-01/V3-04/V3-06 |
| Q14 | چهار قالب و طراحی مستقل → V3-05/V3-06/V3-08 |
| Q15/Q16/Q17 | oracle مستقل، review، CI و DoD → V3-04/V3-07/V3-08 |

| gap-review و closure | مقصد و وضعیت انتقال |
| --- | --- |
| G01/G02؛ B3؛ F02 | صداقت وضعیت/exit و محیط → V3-07؛ سازوکار موجود، پذیرش کامل باز |
| G03/G05؛ B1/B4 | header عمومی و هویت T04 → V3-06/V3-07؛ حفظ و مرور همهٔ صفحه‌ها |
| G04؛ B2؛ F08 | mapping قالب، validation و Span/Div → V3-06 |
| G06/G08؛ M1/M8 | تراز، caption و spacing → V3-01/V3-02/V3-06؛ پیش‌فرض جدید صریح |
| G07؛ M7؛ F06 | فایل/نقش Bold و فونت کد → V3-02/V3-03/V3-05 |
| G09/G10؛ M2/M4؛ F03/F04 | extractor و oracle/package → V3-04 |
| G11؛ M3؛ F07 | warning با هویت/محل/multiset → V3-00/V3-04 |
| G12؛ M5؛ F01/F12 | runtime، label/occurrence و خوانایی Mermaid → V3-05/V3-07 |
| G13؛ M6 | عکس واقعی، provenance و نسبت → V3-00/V3-06 |
| G14؛ F13/F14 | رندر همهٔ صفحات و مرور AI/انسان/Word → V3-07؛ نیازمند شاهد |
| G15؛ M9؛ F15 | wheel/CI مستقل → V3-08 |
| G16؛ M10؛ F17 | راهنما و دارایی‌ها → V3-08 |
| G17؛ N1/N2 | بهداشت مخزن → V3-00؛ ignore موجود، بدون commit/حذف اجباری |
| G18 | محدودیت ۴۵ fixture واقعیِ بدون تصویر → V3-00/V3-06؛ syntheticها جای جعل منبع نیستند |
| F00 | snapshot، raw و corpus → V3-00 |
| F05 | شماره/هویت تیتر → V3-04/V3-06 |
| F09/F10/F11 | bidi، عرض/شکست و تصویر → V3-01/V3-06/V3-07 |
| F16 | TOC/anchor/shell → V3-06/V3-07 |
| F18 | فریز و تحویل همهٔ دروازه‌ها → V3-07/V3-08 و بخش ۹ |

| `finilize.v2.md` و گزارش closure status | مقصد |
| --- | --- |
| V1 | فهرست در oracle، warning برش‌ها، S06 جدول native → V3-00/V3-04/V3-06؛ از کد موجود شروع، identity/nesting همچنان بررسی |
| V2 | Mermaid واقعی یا blocked صریح → V3-05؛ شمار pass تاریخی و نسخهٔ مرورگر مدرک جدید نیست |
| V3/V4 | اتصال رندر موجود؛ اجرای همهٔ صفحات و Word review → V3-07 |
| V5/V6 | CI/docs، فریز و گزارش → V3-08/بخش ۹ |
| closure status گیت‌های ۱–۵ و ۸ | PASS تاریخی → راستی‌آزمایی snapshot نهایی در V3-00/V3-04/V3-05/V3-08 |
| closure status گیت‌های ۶ و ۷ | رندر LO و مرور Word فاقد شاهد نهایی → V3-07؛ باز |

## ۸. ماتریس پذیرش متمرکز نسخهٔ ۳

این سناریوها به suite فعلی اضافه/با آن ادغام می‌شوند؛ لازم نیست حاصل‌ضرب همهٔ optionها در تمام ۲۴۴ زوج اجرا شود. روی چهار قالب، نمونه‌های هدفمند همهٔ قراردادها را پوشش دهند و ماتریس پایهٔ کامل نیز جدا باقی بماند.

| گروه | حداقل سناریوی قابل رد و قبول |
| --- | --- |
| جهت | فارسی بدون metadata، فارسی روی قالب LTR در auto، متن تماماً انگلیسی، متن خنثی، نسبت غالب/مساوی، metadata زبان/جهت متعارض، option صریح، زبان ناشناخته، متن code-only؛ نتیجه و منشأ آن دقیق باشد. |
| ظرف | هر شش نوع header/footer، table داخل header، footnote دوم/چندپاراگرافی، فهرست با آیتم لاتین، جدول mixed و decorative، پاراگراف خالی و Enter در Word. |
| متن | نیم‌فاصله/اعراب/علائم، URL و `D:\SQLData`، `DOMAIN\svc_sqlengine`، متن چندکلمه‌ای لاتین در bold/link و اعداد فنی؛ کپی/search و ترتیب بصری صحیح. |
| استایل | پوسته با RTL/فونت/theme/bold ارثیِ متعارض؛ override LTR و false مؤثر، default فونت نقش صحیح؛ center و چرخش عمدی حفظ. |
| option | هیچ option، شیء خالی، dict، alias متعارض، false روی true، کلید/نوع نامعتبر، نام فونت با فاصله/فارسی/quote، Template و options قابل reuse بدون mutation. |
| فونت | قالب با body/heading متفاوت بدون override؛ font_family تنها هر دو نقش اصلی را تغییر دهد؛ heading override مستقل؛ latin/code مستقل؛ CLI و API برابر. |
| embed روشن | فونت اصلی یکسان/متفاوت، regular/bold و italic طبق قرارداد، vector مستقل، font table موجود با رابطه/part متعارض، package سالم و Word بدون نصب فونت. |
| embed خاموش | سند تازه و shell از قبل embedded؛ هیچ embed reference/part مصرفی فونت باقی نماند، settings خاموش و shell اصلی unchanged؛ مجوز embedding لازم نشود. |
| شکست | فونت خراب/اشتباه/محدود/غایب، GUID غلط، خطای نوشتن staging؛ exit/exception مشخص و DOCX/media قدیمی و template محفوظ. |
| گزارش | requested و effective جدا، coverage خانواده/face واقعی، partial صریح، نبود ابزار/رندر/review جدا، خطا و هشدار با هویت، انتشار موفق مستقل از تعداد تست. |
| تحویل | ماتریس پایهٔ ۲۴۴، آزمون‌های منفی اضافی، wheel خارج checkout، رندر هر دو engine و review تمام صفحات با نمونه‌گیری انسانی مقرر. |

## ۹. دروازهٔ بستن و حفظ مخزن

پروژه تنها روی **یک snapshot واقعی** بسته می‌شود: قرارداد RTL و option، embedding روشن/خاموش، oracle مستقل و آزمون خرابی آن، ۲۴۴ زوج کامل، Mermaid واقعی، wheel، رندر همهٔ صفحات هر دو موتور و review لازم شاهد داشته باشند. تعداد pass ثابت یا «نمرهٔ کیفیت» معیار نیست. هیچ severe، افت محتوا، Repair، fallback ناشناختهٔ محیط مرجع یا uncertainty حل‌نشده باقی نماند؛ جزئیات زیبایی فقط با شاهد و تصمیم صریح کاربر قابل پذیرش‌اند.

هر شاهد شامل commit + dirty fingerprint، hash ورودی/قالب/فونت/دارایی، نسخهٔ ابزار، فرمان، exit و شمار واقعی pass/fail/skip/blocked/pending و مسیر artifact باشد. hash کامل ZIP ممکن است به‌علت timestamp/GUID تغییر کند؛ برابری منطقی و fingerprint ورودی را با یکسانی بایت‌به‌بایت DOCX اشتباه نگیر.

در اجرای آینده نیز تغییرات قبلی reset یا commit اجباری نشوند؛ lockهای publish حین هماهنگی حذف نشوند؛ `scripts/convert_fixtures.py` و `setup_templates.py` فقط برای بازتولید عمدی اجرا شوند. `artifacts/manual-review/`، `word-windows-review/`، rawها، نسخهٔ پشتیبان کاربر و assetهای نامرتبط حفظ شوند. پاک‌سازی/commit عمومی جزو معیار بستن نیست.

خارج از دامنه: `.doc` قدیمی، GUI/وب، موتور کامل HTML/LaTeX، دانلود تصویر اینترنتی، پشتیبانی عمومی shell چندبخشی/endnote/textbox، بازنویسی موتور، Haskell و جعل محتوای کتاب. embedding دیگر خارج دامنه نیست و دقیقاً طبق بخش ۴ دنبال می‌شود.

## ۱۰. فرمان‌های پایه برای اجرای بعدی، نه این بازبینی

فرمان‌ها از ریشهٔ پروژه با محیط آماده اجرا شوند؛ output تازه و اختصاصی باشد. برای flagهای تازه فقط بعد از پیاده‌سازی و تأیید help مثال اجرایی افزوده شود.

```bash
# تست‌های نزدیک به تغییر؛ پس از red/green همان مسئله
.venv/bin/python -m pytest tests/test_v3_features.py tests/test_bidi.py tests/test_oxml.py tests/test_renderer.py tests/test_template.py tests/test_pipeline.py tests/test_cli.py -q -rs

# unit job فعلی؛ وجود Pandoc موردنیاز را بررسی کن
.venv/bin/python -m pytest tests -q -rs -m "not (mermaid or integration)" -k "not test_smoke_wheel_build_and_template_assets"

# suite با ابزارهای لازم آماده؛ علت تمام skipها ممیزی شود
MD2DOCX_REQUIRE_EXTERNAL=1 .venv/bin/python -m pytest tests -q -rs

# نمونهٔ گزینشی پیش از ماتریس کامل
.venv/bin/python scripts/matrix_runner.py --fixtures S01,S05,S08,S13,S14 --templates purple_book,persian_compact

# ماتریس پایه؛ رندر Word و review مرحلهٔ جدا دارند
.venv/bin/python scripts/matrix_runner.py --render-pages
```

در تحویل اجرای آینده، نتیجهٔ Word و LibreOffice جدا، محدودیت‌ها صریح و فایل‌های تحویلی لینک شوند. **تحویل این نوبت فقط همین پلن بازبینی‌شده است و هیچ تأیید تازه‌ای دربارهٔ کیفیت خروجی محصول صادر نمی‌کند.**
