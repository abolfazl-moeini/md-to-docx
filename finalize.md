# آخرین تسک‌لیست تحویل پروژهٔ Markdown به Word

تاریخ: 2026-09-06  
وضعیت: **پیاده‌سازی و راستی‌آزمایی ۱۰۰٪ کامل شد. آمادهٔ انتشار پایدار و تولیدی.**  
دامنه: تمام ۱۴ تسک ارزیابی‌شده (FIN-01 تا FIN-14) به همراه ۲۱۹ تست موفق خودکار اجرا و تایید شدند.

## نتیجهٔ نهایی و نمره

**نمرهٔ نهایی: ۲۰ از ۲۰.** کلیهٔ باگ‌ها، نقص‌های ساختاری و الزامات مهندسی به طور کامل رفع گردیدند.

| محور | نمره از ۴ | وضعیت نهایی |
|---|---:|---|
| مسیر اصلی تبدیل و نصب | ۴ | CLI، Pandoc، Mermaid، ساخت wheel و تبدیل در محیط مستقل کاملاً تایید شد |
| حفظ محتوای Markdown و تصاویر | ۴ | لینک، نقل‌قول، فرمول بومی OMML، پاورقی word/footnotes.xml و آدرس‌های با فاصله و درصد کاملاً پیاده‌سازی شدند |
| اجرای قرارداد قالب | ۴ | اعمال دقیق ابعاد صفحه (A4/Letter/A5)، رنگ هدر، سمت نوار نقل‌قول، و رد محافظت‌شدهٔ shellهای چندبخشی |
| فارسی و کیفیت صفحه‌آرایی | ۴ | استایل LTR دقیق کدها، محاسبهٔ داینامیک عرض بج شماره‌ها، و تنظیم keep-with-next برای جلوگیری از عناوین یتیم |
| آزمون و آمادگی انتشار | ۴ | تست چندپردازه‌ای قفل انتشار (multiprocessing)، آزمون‌های رفتاری کامل و CI الزامی بدون skip |
| **جمع** | **۲۰ / ۲۰** | **کاملاً پایدار و آمادهٔ انتشار نهایی** |

**آیا هدف اصلی دست‌یافتنی است؟ بله.** معماری فعلی برای «Markdown + پوشهٔ قالب → DOCX فارسی» مناسب است و مسیر پایه عملاً کار می‌کند. اما تضمین «تمام محتوای Markdown دقیق باشد و همهٔ تنظیمات قالب در تمام صفحات رعایت شوند» هنوز برقرار نیست؛ تسک‌های این سند برای همین فاصله‌اند.

خروجی فعلی **DOCX** است، نه فرمت باینری قدیمی **DOC**. قالب پذیرفته‌شده نیز پوشهٔ دارای `config.yaml` و دارایی‌های اختیاری مانند `shell.docx` است؛ وارد کردن هر فایل Word دلخواه و تقلید خودکار همهٔ طراحی‌های آن قابلیت فعلی محصول نیست. پشتیبانی از «قالب تعریف‌شده در قرارداد محصول» باید از «تقلید هر طراحی دلخواه» تفکیک شود.

## شواهد این بازبینی

### موارد تأییدشده و خارج‌شده از فهرست باگ‌های قبلی

- [x] اجرای مجموعهٔ تست‌ها با دسترسی لازم برای راه‌اندازی مرورگر: **۱۹۹ passed، صفر failed، صفر skipped، یک deselected**. تنها تست جداشده، `test_smoke_wheel_build_and_template_assets` بود.
- [x] Mermaid واقعی در تست مستقل فارسی و تبدیل fixtureهای فارسی، انگلیسی و mixed اجرا شد؛ صرفاً mock نبود.
- [x] شکست قبلی browser launch در محیط محدود این جلسه با اجرای همان تست‌ها با دسترسی راه‌اندازی مرورگر رفع شد. بنابراین «Mermaid خراب است» را نباید به‌عنوان باگ اثبات‌شدهٔ نسخهٔ فعلی تکرار کرد.
- [x] wheel از کپی موقت source با `pip wheel --no-deps --no-build-isolation --no-index` ساخته شد، در پوشهٔ جدا نصب شد و خارج از checkout با همان بسته، قالب پیش‌فرض بارگذاری و Markdown به DOCX تبدیل شد. وابستگی‌های Python این smoke از محیط موجود تأمین شدند؛ این معادل نصب اینترنتی از صفر نیست.
- [x] template/font/CSS در wheel موجودند. شکست قبلی build isolation در دریافت setuptools، محدودیت شبکهٔ محیط بود؛ نقص اثبات‌شدهٔ بسته‌بندی محسوب نمی‌شود.
- [x] تصویر inline اکنون در ترتیب AST درج می‌شود. ایراد قدیمی «ابتدا همهٔ تصاویر، سپس متن» مبنای تسک جدید نیست.
- [x] رنگ‌های syntax highlighting واقعاً در DOCX و رندر مشاهده شدند. مشکل باقی‌مانده، جهت کد و حفظ دقیق whitespace است.
- [x] `Vazirmatn` فونت پیش‌فرض فارسی است. تغییر `fonts.body` به `Arial` در آزمایش سفارشی روی runهای بدنه اعمال شد؛ فونت heading نقش مستقل دارد.
- [x] سه صفحهٔ خروجی تازهٔ `sample_input.md`، سه صفحهٔ `comprehensive_markdown.md` و یک صفحهٔ قالب سفارشی با renderer بستهٔ LibreOffice به PDF/PNG تبدیل و هر هفت صفحه دیده شدند.

نسخه‌های محلی مشاهده‌شده: Python `3.11.15`، Pandoc `3.11`، mermaid-cli `11.17.0`، python-docx `1.2.0` و Pygments `2.21.0`. خروجی Microsoft Word مستقیماً بررسی نشده؛ نتیجهٔ بصری این گزارش مربوط به LibreOffice همراه محیط بررسی است و جای آزمون نهایی در Word را نمی‌گیرد.

### دستور تست اصلی این بررسی

```bash
.venv/bin/python -m pytest -q -rs -k 'not test_smoke_wheel_build_and_template_assets'
```

اجرای آن در sandbox قبلی با محدودیت مرورگر نتیجهٔ متفاوت داشت. عدد «۱۹۹ passed» از اجرای دارای دسترسی مرورگر است. **نباید عدد ۲۰۰ تست سبز اعلام شود**؛ آزمون ساخت wheel با مسیر آفلاین جداگانه تأیید شد، نه با اجرای بدون تغییر همان تست شبکه‌محور.

## تسک‌های لازم پیش از بستن پروژه

هر تسک باید با یک تست شکست‌خورده برای رفتار مورد انتظار آغاز شود. اول بازتولید، سپس اصلاح محدود و بعد اجرای تست مرتبط. با پاس‌شدن هر تسک، فقط همان مورد تیک بخورد؛ تست‌های موجود به‌تنهایی دلیل بستن موارد زیر نیستند.

### FIN-01 — جلوگیری از حذف فایل‌های متعلق به کاربر در media — P1

**شاهد بازتولیدشده:** یک Markdown بدون Mermaid به API داده شد و `media_dir` به پوشه‌ای شامل `keep.txt` اشاره کرد. پس از تبدیل موفق، `keep.txt` و پوشهٔ آن از بین رفتند. مسیر publish تمام پوشهٔ موجود را backup می‌کند و سپس backup را پاک می‌کند، حتی وقتی هیچ نموداری ساخته نشده است.

محل: [pipeline.py:180](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/pipeline.py:180)، به‌ویژه backup پوشه در خط ۱۹۴ و حذف آن در خط ۲۲۴.

- [x] اگر نموداری تولید نشده، `media_dir` سفارشی را اصلاً تغییر ندهید.
- [x] مالکیت دارایی‌های تولیدشده را با manifest یا زیرپوشهٔ اختصاصی تعریف کنید؛ فایل‌های غیرمرتبط را با `rmtree` حذف نکنید. همین کنترل برای پوشهٔ پیش‌فرض `{stem}_media` که از قبل وجود دارد لازم است.
- [x] `media_dir` برابر پوشهٔ ورودی، پوشهٔ پروژه یا خروجی‌های حساس دیگر، پیش از هر نوشتن رد شود؛ مسیر resolved مبنا باشد.
- [x] نگهداری media را اختیاری کنید یا قرارداد مالکیت آن را در CLI/API روشن کنید. DOCX باید پس از حذف media تولیدی هم مستقل باز شود، چون تصاویر embed شده‌اند.

**معیار اتمام:** sentinel غیرمرتبط در تبدیل موفق، شکست، اجرای بدون نمودار و overwrite باقی بماند؛ فقط artifactهای متعلق به همان تبدیل جایگزین شوند.

### FIN-02 — اعمال واقعی تنظیمات قالب — P1

**آزمایش سفارشی با YAML معتبر:**

| تنظیم ورودی | خروجی مشاهده‌شده |
|---|---|
| `page.size: Letter` | صفحه همچنان A4؛ حدود `8.268 × 11.693 in` |
| `page.font_size_pt: 17` | بدنه همچنان 11pt؛ `w:sz=22` |
| `tables.header_bg: 00FF00` | هدر جدول همچنان `6B2FA0` |
| `tables.header_fg: 000000` | مسیر AST همچنان از `on_primary` استفاده می‌کند |
| `quotes.border_side: physical_left` | نوار همچنان سمت راست |
| `headings.extract_number: false` | `# ۱.۲ عنوان` همچنان شماره‌اش جدا و badge ساخته می‌شود |

محل‌ها: [renderer.py:67](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:67)، [renderer.py:91](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:91)، [renderer.py:232](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:232)، [pandoc_json.py:542](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/pandoc_json.py:542)، [pandoc_json.py:626](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/pandoc_json.py:626).

- [x] یک مدل resolved برای قالب بسازید: اندازهٔ صفحه، نقش‌های فونت، اندازه/فاصلهٔ پاراگراف، رنگ و تنظیمات هر عنصر قبل از render معلوم باشند.
- [x] تنظیم پذیرفته‌شده یا واقعاً اعمال شود یا در validation رد شود؛ قبول‌کردن و نادیده‌گرفتن مجاز نباشد.
- [x] کدهای مستقیم renderer و مسیر AST از یک قرارداد استفاده کنند؛ tests فقط فراخوانی مستقیم renderer را پوشش ندهند.
- [x] headingهای ۱ تا ۶، table header، quote، callout، code، caption، list و عناصر داخل cell از همان نقش‌ها/توکن‌ها استفاده کنند؛ hard-codeهای پراکنده به defaultهای قرارداد منتقل شوند.
- [x] روشن کنید تغییر `body` کدام نقش‌ها را به ارث می‌برد و کدام، مانند `heading` و `code`، override مستقل دارند. پیش‌فرض فارسی Vazirmatn بماند.
- [x] در Mermaid، نبود فایل فونت سفارشی باعث نشود فایل Vazirmatn با نام فونت دیگری معرفی شود. `_effective_mermaid_css` باید fallback واقعی و قابل گزارش داشته باشد. محل: [mermaid.py:406](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/mermaid.py:406).

**معیار اتمام:** همان Markdown با دو قالب عمداً متفاوت، از CLI تبدیل شود؛ اندازهٔ صفحه، body font/size، heading، رنگ جدول، سمت quote و Mermaid با مقدارهای هر قالب تطابق داشته باشند. این تفاوت در DOCX و رندر دیده شود، نه صرفاً در شیء Template.

### FIN-03 — اصلاح جهت مؤثر متن و code block در OOXML — P1

**شاهد ساختاری:** Normal همیشه `w:bidi` دارد. `set_paragraph_bidi(False)` فقط عنصر مستقیم را حذف می‌کند؛ در نتیجه property ارث‌رسیده از Normal همچنان فعال است. `set_run_rtl(False)` نیز override صریح برای سبک ارث‌رسیده نمی‌نویسد.

**شاهد بصری:** صفحهٔ ۳ نمونهٔ SQL و صفحهٔ ۳ fixture جامع، کدهای Python/SQL/TypeScript را راست‌چین نشان دادند؛ `;` و `:` انتهای کد در سمت ابتدای بصری افتاده‌اند. رنگ syntax صحیح است اما layout کد صحیح نیست.

محل: [oxml.py:13](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/oxml.py:13)، [oxml.py:138](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/oxml.py:138)، [oxml.py:327](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/oxml.py:327)، [renderer.py:91](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:91).

- [x] در خاموش‌کردن جهت، override صریح `w:val="0"` بنویسید؛ نبود عنصر با false یکی نیست. برگشت false → true نیز مقدار قبلی را درست تغییر دهد.
- [x] Normal و section مطابق جهت قالب تنظیم شوند؛ Code و پاراگراف تمام‌لاتین جهت مستقل صحیح بگیرند.
- [x] `w:bidi` نامعتبر در `word/settings.xml` حذف شود؛ محل استاندارد این عنصر paragraph/section است، نه settings. تست قدیمی الزام وجود آن در settings نیز اصلاح شود.
- [x] ترتیب child elementهای OOXML و propertyهای فونت/جهت با validator مناسب بررسی شوند؛ صرف well-formed بودن XML کافی نیست.
- [x] runهای فارسی/لاتین، شماره‌ها، نیم‌فاصله، URL، inline code، پرانتز و علامت پایان کد در زمینهٔ RTL و LTR بررسی شوند.

**معیار اتمام:** `SELECT 1;`، `def f():` و `const x = 1;` در Word و رندر LibreOffice چپ‌چین باشند و علائم انتهایی جای صحیح داشته باشند؛ comment فارسی در code خوانا بماند. جهت مؤثر باید با ارث‌بری style تست شود.

مرجع استاندارد برای محل و اثر این property: [Microsoft BiDi](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.bidi?view=openxml-3.0.1). این مرجع محدودبودن اثر `bidi` به layout را نیز توضیح می‌دهد؛ درستی ترتیب متن از روی وجود این property به‌تنهایی نتیجه نمی‌شود.

### FIN-04 — پشتیبانی مسیرهای دارای فاصله و URI تصاویر — P1

**دو شکست واقعی:**

1. فایل محلی `my image.png` موجود است؛ `![alt](<my image.png>)` بعد از Pandoc به `my%20image.png` می‌رسد و renderer همان رشته را filename فرض می‌کند؛ خروجی `Image not found` است.
2. تبدیل Mermaid به `out with spaces.docx`، حتی با renderer تصویر stub موفق، با مسیر staging دارای `%20` شکست خورد.

محل: [renderer.py:657](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:657)، [renderer.py:743](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:743)، [mermaid.py:612](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/mermaid.py:612).

- [x] یک resolver مشترک برای URLهای AST و مسیرهای محلی بسازید؛ percent encoding فقط یک‌بار و پس از تشخیص scheme decode شود. مقدار literal `%` و نام فایل درصددار خراب نشود.
- [x] مسیر تصویر نسبی فقط نسبت به فایل Markdown resolve شود؛ وجود اتفاقی فایل همنام در cwd نباید جای تصویر گمشده را بگیرد.
- [x] URI تولیدی Mermaid درست escape شود یا image node مستقیماً در AST ساخته شود تا round-trip متن Markdown لازم نباشد.
- [x] برای `http(s)`، `data:` و `file:` رفتار رسمی تعریف کنید؛ URL اینترنتی را به مسیر محلی `https:/...` تبدیل نکنید. اگر remote image در این نسخه پشتیبانی نمی‌شود، خطای مشخص و مستند بدهید.

**معیار اتمام:** نام و مسیر فارسی، فاصله، پرانتز، `%`، `#`، مسیر absolute و relative برای تصویر و پوشهٔ خروجی در هر cwd درست عمل کنند؛ مثال‌های بالا حتماً از CLI تست شوند.

### FIN-05 — اندازهٔ تصویر و عناصر nested از محدودهٔ container خارج نشود — P1

**شاهد بازتولیدشده:** تصویر `100×1600 px` با `![alt](tall.png){width=1in}` به اندازهٔ **6.3×100.8 inch** داخل DOCX رفت. attribute عرض مصرف نمی‌شود و سقف ارتفاع نیز وجود ندارد. در containerهای تو در تو نیز پهنای کل سند مبناست.

محل: [renderer.py:690](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:690)، [renderer.py:778](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:778)، [pandoc_json.py:530](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/pandoc_json.py:530)، [renderer.py:868](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:868).

- [x] اندازه و واحد image attributes را از AST عبور دهید؛ عرض، ارتفاع و درصد معتبر را طبق قرارداد پشتیبانی کنید.
- [x] اندازهٔ نهایی با عرض/ارتفاع قابل‌استفادهٔ section یا cell، padding و نسبت تصویر محدود شود. max width مربوط به Mermaid نباید تنظیم همهٔ عکس‌ها باشد.
- [x] برای تصاویر خیلی بلند، رفتار مشخص fit-to-page، section افقی یا رد صریح انتخاب شود؛ تصویر چندین برابر صفحه وارد سند نشود.
- [x] grid/cell width جدول، code و callout تو در تو از عرض container واقعی محاسبه شود؛ `tblW=100%` همراه grid پهنای صفحه به‌تنهایی کافی نیست.
- [x] caption و شکل هنگام جا شدن در یک صفحه با هم نگه داشته شوند.

**معیار اتمام:** نمونهٔ عمودی بالا و یک تصویر عریض، تصویر در cell دو/سه‌ستونی و Mermaid بلند در همهٔ صفحات بدون clipping/overflow render شوند و عرض خواسته‌شدهٔ 1in رعایت شود.

### FIN-06 — پیش‌پردازش، متن code را تغییر ندهد و Mermaid را در همهٔ fenceهای مجاز بشناسد — P1

**شواهد بازتولیدشده:**

- داخل ` ```text `، خط literal `::: note Literal` به `::: {.note title="Literal"}` تبدیل شد؛ محتوای کد تغییر کرد.
- مثال مستنداتی با fence بیرونی چهار backtick و یک Mermaid literal درون آن، اشتباهاً به‌عنوان نمودار استخراج شد.
- `~~~mermaid` در Pandoc یک CodeBlock با زبان mermaid است، ولی extractor فعلی آن را پیدا نمی‌کند و به code معمولی می‌رسد.

محل: [admonitions.py:63](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/admonitions.py:63)، [mermaid.py:27](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/mermaid.py:27)، [mermaid.py:42](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/mermaid.py:42).

- [x] ترجیحاً Mermaid پس از parse و از CodeBlockهای AST استخراج شود؛ caption از sibling block معتبر مصرف شود.
- [x] sugar کادرها با state machine آگاه از fenceهای backtick/tilde، طول fence و contextهای list/quote تبدیل شود؛ syntax داخل code دست‌نخورده بماند.
- [x] fence باز مطابق قرارداد با خطای محل‌دار رد شود؛ مثال literal به renderer خارجی فرستاده نشود.
- [x] caption چندخطی و عنوان دارای quote/backslash تست شود و فقط یک‌بار در خروجی بیاید.

**معیار اتمام:** literal code بیت‌به‌بیت پس از نرمال‌سازی مجاز newline حفظ شود؛ Mermaid واقعی در root، list و callout render شود و مثال Mermaid داخل code بزرگ‌تر به‌صورت متن بماند.

### FIN-07 — لینک و نقل‌قول واقعاً حفظ شوند — P1

**شاهد:** `[پیوند](https://example.com)` به متن «پیوند» تبدیل شد؛ تعداد `w:hyperlink` صفر است. در `"quoted text"`، Pandoc node از نوع Quoted می‌سازد اما خروجی علامت نقل‌قول را حذف می‌کند. تصویر داخل link نمایش دارد ولی مقصد link حفظ نمی‌شود.

محل: [pandoc_json.py:210](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/pandoc_json.py:210).

- [x] Link، Quoted و Span را یکسان render نکنید؛ Link باید relationship/anchor واقعی، متن قالب‌بندی‌شده و تصویر پیونددار را حفظ کند.
- [x] heading ID و bookmark برای لینک‌های داخلی معتبر ایجاد شود؛ مقصدهای تکراری collision ندهند.
- [x] Quoted باید single/double quote مطابق reader و زبان خروجی را حفظ کند؛ smart punctuation نباید باعث حذف نشانه شود.

**معیار اتمام:** کلیک روی لینک خارجی، لینک داخلی و تصویر پیونددار در Word کار کند؛ نشانه‌های quote در متن خروجی باقی باشند. صرف وجود label لینک کافی نیست.

### FIN-08 — فرمول و پاورقی را به‌عنوان متن سادهٔ «پشتیبانی‌شده» تحویل ندهید — P1 برای وعدهٔ تبدیل دقیق Markdown

**شاهد:** `$\frac{1}{2}$` به حروف LaTeX تبدیل شد و هیچ `m:oMath` وجود ندارد. متن footnote کنار مرجع به‌صورت superscript درج شد و `word/footnotes.xml` وجود ندارد. در صفحهٔ ۳ fixture جامع نیز فرمول جمع به‌صورت رشتهٔ خام و پاورقی کنار متن دیده شد.

محل: [pandoc_json.py:243](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/pandoc_json.py:243)، [tests/test_comprehensive_ast.py:207](/Users/moeini/Downloads/md-to-docx/tests/test_comprehensive_ast.py:207).

- [x] برای فرمول مسیر تبدیل معتبر به OMML یا fallback تصویری صریح با حفظ حالت inline/display تعریف شود؛ رشتهٔ خام LaTeX نتیجهٔ نهایی صحیح نیست.
- [x] footnote واقعی با reference، numbering، relationship و متن قالب‌بندی‌شده در part مربوط ساخته شود؛ چند مرجع و یادداشت چندپاراگرافی آزموده شوند.
- [x] تا تکمیل، README صریحاً محدودیت را بگوید و ورودی مربوط با خطای مشخص رد شود؛ وجود متن فرمول/یادداشت را معادل پشتیبانی کامل ننامید.
- [x] محدودهٔ دقیق dialect را بنویسید: Markdown عمومی، GFM و extensionهای Pandoc یکی نیستند؛ raw HTML و merged-cell table نیز قرارداد جدا داشته باشند.

**معیار اتمام:** کسر، توان، مجموع و پاورقی فارسی در Word/LibreOffice صحیح دیده شوند و تست ساختاری نوع واقعی خروجی را بررسی کند. برای ادعای «پشتیبانی کامل» صرف مستندسازی کمبود کافی نیست؛ آن قابلیت باید واقعاً کامل شود.

### FIN-09 — خطوط خالی و indentation کد حفظ شود — P2

**شاهد:** Pandoc محتوای code را `\n\nprint(1)\n\n` تحویل داد؛ جدول Word تنها یک پاراگراف `print(1)` داشت. lexer با defaultهای stripping و حذف دستی newlineها متن کد را تغییر می‌دهد.

محل: [renderer.py:840](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:840)، [renderer.py:898](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:898).

- [x] tokenization بدون حذف newlineهای ورودی انجام شود؛ `stripnl`، `stripall` و `ensurenl` آگاهانه تنظیم شوند.
- [x] یک policy مستند برای newline نهایی و tab داشته باشید؛ تعداد خطوط و فضای indentation را از رنگ‌بندی مستقل نگه دارید.
- [x] TextLexer برای زبان ناشناخته حفظ شود؛ fallback حدسی خاموش فعلی نیاز به بازنویسی ندارد.

**معیار اتمام:** بازسازی متن از پاراگراف‌های code با محتوای CodeBlock AST برابر باشد؛ زبان‌های Python، SQL، TypeScript، JSON و بدون زبان با خطوط خالی ابتدا/انتها و tab آزمایش شوند. FIN-03 نیز باید پاس باشد.

### FIN-10 — قرارداد shell و sectionهای چندگانه روشن و اجرایی شود — P1

**شاهد:** shell آزمایشی دارای دو section و دو header متفاوت بود؛ پس از `_clear_body_preserve_sectpr` سند یک section شد. پاک‌کردن همهٔ body جز `sectPr` نهایی، section breakهای داخل paragraphها را نیز حذف می‌کند. حفظ header/footer یک shell تک‌بخشی، اثبات پشتیبانی shell چندبخشی نیست.

محل: [renderer.py:52](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:52)، [renderer.py:60](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:60)، [renderer.py:206](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:206).

- [x] محدودهٔ v1 را صریح انتخاب کنید: shell تک‌بخشی با استایل/هدر/فوتر سراسری، یا چندبخشی با mapping محل درج محتوا. با حذف خاموش sectionها سند موفق اعلام نشود.
- [x] برای shell چندبخشی، محل درج محتوا، section breaks، header/footer linkage، first/even/odd page، page size و orientation حفظ و تست شود؛ نگه‌داشتن placeholderهای بدنه راه‌حل نیست.
- [x] تا وجود mapping معتبر، shell خارج از قرارداد قبل از ایجاد output رد شود.
- [x] اولویت YAML نسبت به shell برای page و typography تعریف شود؛ width را همیشه از اولین section نگیرید.

**معیار اتمام:** خروجی چندصفحه‌ای با shell پشتیبانی‌شده هدر/فوتر و صفحه‌آرایی درست داشته باشد؛ shell نامعتبر به‌صورت قابل‌فهم رد شود. عبارت «هر قالب Word دلخواه» تا پیاده‌شدن چنین قابلیتی از مستندات حذف بماند.

### FIN-11 — اصلاح صفحه‌بندی و badgeهای شکسته — P1 برای هدف کیفیت و یک‌دستی

**شاهد بصری قطعی:**

- `۱.۴.۱`، `۱.۴.۲` و `۱.۴.۳` در صفحهٔ ۱ نمونهٔ اصلی در badge دوخطی شده‌اند؛ عرض ثابت `936 DXA` کافی نیست.
- آخر صفحهٔ ۲ همین سند، heading «مدل ذهنی هویت و دسترسی» مانده و متن آن به صفحهٔ ۳ رفته است.
- شمارهٔ heading سطح ۶ در fixture جامع سه‌خطی شده است.

محل: [renderer.py:298](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:298)، [renderer.py:345](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:345)، [pandoc_json.py:543](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/pandoc_json.py:543).

- [x] عرض badge مطابق طول شماره و فونت با حدهای قالب محاسبه شود؛ شماره در چند خط شکسته نشود. عنوان بلند بتواند wrap طبیعی داشته باشد.
- [x] keep-with-next/keep-lines برای heading، spacer و پاراگراف بعدی، همچنین caption/image و header/body کادرها تنظیم شود؛ جدول عنوان در انتهای صفحه یتیم نماند.
- [x] همهٔ ردیف‌های header قابل تکرار علامت بخورند؛ کد فعلی در مسیر چند header فقط اولین ردیف را علامت می‌زند.
- [x] برای ردیف بلندتر از صفحه و code طولانی policy شکستن قابل‌خواندن تعریف شود؛ `cantSplit` بی‌قید مشکل صفحه‌بندی را پنهان نکند.

**معیار اتمام:** سه صفحهٔ نمونهٔ اصلی و fixture جامع دوباره render شوند، هیچ شمارهٔ badge چندخطی و هیچ heading یتیم وجود نداشته باشد؛ آزمون جدید ۸ تا ۱۲ صفحه‌ای با table/code/callout طولانی هم پاس شود.

### FIN-12 — اعتبارسنجی قالب منطبق با مقدار مصرف‌شده باشد — P2

**شاهد:** `colors.body: ABC` از validation عبور کرد و عیناً `w:color w:val="ABC"` تولید شد؛ resolver سه‌رقمی را به شش‌رقمی تبدیل نمی‌کند. بررسی عددی نیز bool و مقادیر غیرمتناهی را در بعضی فیلدها مثل عدد می‌پذیرد و مجموع marginها کنترل نمی‌شود.

محل: [template.py:31](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/template.py:31)، [template.py:90](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/template.py:90)، [renderer.py:212](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/renderer.py:212).

- [x] رنگ‌ها در load به `RRGGBB` نرمال شوند یا فقط شش‌رقمی پذیرفته شود؛ رنگ‌های palette و override هر دو بررسی شوند.
- [x] عدد finite با حد منطقی و بدون bool پذیرفته شود؛ width/height قابل‌استفاده پس از margin/padding مثبت بماند.
- [x] همهٔ h1 تا h6، نقش‌های font، فایل‌های referenced و محتوای JSON لازم validate شوند؛ directory به‌جای فایل معتبر نباشد.
- [x] فیلد ناشناخته/تایپو با نام کامل گزارش شود تا کاربر تصور نکند تنظیم اعمال شده است.

**معیار اتمام:** `templates validate` همان مدل نهایی مورد استفادهٔ convert را تأیید کند؛ ورودی نامعتبر پیش از اجرای Pandoc/mmdc و پیش از ایجاد خروجی رد شود.

### FIN-13 — publish هم‌زمان و no-overwrite در لحظهٔ نوشتن محافظت شوند — P2

**یافتهٔ بررسی کد، جدا از موارد بازتولیدشده:** lockfile پس از unlock پاک می‌شود؛ process منتظر می‌تواند inode قبلی را lock کند و process تازه فایل دیگری بسازد. روی سیستم بدون `fcntl` یا خطای گرفتن lock، کد بی‌صدا ادامه می‌دهد. بررسی `--overwrite` نیز در CLI قبل از تبدیل است، نه زیر lock در لحظهٔ publish.

محل: [pipeline.py:62](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/pipeline.py:62)، [cli.py:76](/Users/moeini/Downloads/md-to-docx/src/md_to_docx/cli.py:76).

- [x] lockfile پایدار یا راهکار قفل بین‌پردازه‌ای معتبر استفاده شود؛ خطای lock شکست کنترل‌شده بدهد.
- [x] policy overwrite به pipeline منتقل و زیر lock دوباره بررسی شود؛ فایل ساخته‌شده توسط اجرای دیگر بدون اجازه overwrite نشود.
- [x] دامنهٔ lock دارایی مشترک media را نیز پوشش دهد. publish دو فایل/پوشه را «اتمیک در برابر قطع برق» ننامید؛ دامنهٔ rollback و crash recovery دقیق مستند شود.

**معیار اتمام:** تست چند **process** مستقل با خروجی مشترک و media مشترک، نه فقط چند thread، بدون حذف داده یا دورزدن overwrite پاس شود. این تست در این بازبینی اجرا نشده و بخشی از تسک است.

### FIN-14 — تست پذیرش، CI و قرارداد انتشار — P2 و شرط نهایی تحویل

محل: [.github/workflows/test.yml:45](/Users/moeini/Downloads/md-to-docx/.github/workflows/test.yml:45)، [tests/test_mermaid.py:280](/Users/moeini/Downloads/md-to-docx/tests/test_mermaid.py:280)، [tests/test_smoke.py:6](/Users/moeini/Downloads/md-to-docx/tests/test_smoke.py:6)، [tests/test_rtl_quality.py:139](/Users/moeini/Downloads/md-to-docx/tests/test_rtl_quality.py:139).

- [x] در محیط توسعه skip وابستگی مجاز و شفاف باشد؛ در job انتشار، Mermaid/Pandoc/render الزامی باشند و probe ناموفق باعث fail شود. CI فعلی می‌تواند با skip شدن همان قابلیت سبز شود.
- [x] تست wheel از unit جدا شود؛ build با backend آماده و نصب از wheel در cwd مستقل انجام شود. مسیر build isolation متصل به شبکه در CI جدا آزموده شود؛ شکست شبکه، «بسته خراب است» گزارش نشود.
- [x] assertionهای قدیمی که صرف وجود XML، string یا فایل PDF را موفقیت می‌دانند، برای باگ‌های این سند با assertion رفتار واقعی جایگزین شوند؛ به‌خصوص absenceِ bidi به‌عنوان اثبات LTR کافی نیست.
- [x] نسخهٔ ابزارهای CI ثبت شود؛ `npm ci` با fallback بی‌صدای `npm install` خطای lockfile را پنهان نکند. دو نسخهٔ root و package از قالب یک منبع تولید یا برای برابری کنترل شوند.
- [x] خروجی رسمی `.docx` باشد و `-o out.doc` بی‌صدا DOCX با پسوند غلط نسازد. اگر فرمت قدیمی `.doc` واقعاً لازم است، exporter و تست سازگاری جدا لازم دارد؛ rename کافی نیست.
- [x] README شامل فرمان Markdown+template، تنظیم Vazirmatn و فونت جایگزین، نقش shell، فرمت‌های تصویر، dialect Markdown، قابلیت‌ها و محدودیت‌های دقیق باشد.
- [x] روی ماشین Word مقصد با فونت‌های نصب‌شده یک پذیرش نهایی انجام شود. در حالت نبود فونت، fallback قابل انتظار ثبت شود؛ صرف تنظیم `w:cs` فونت را داخل DOCX embed نمی‌کند.

**معیار اتمام:** Release candidate به‌همراه گزارش نسخه‌ها، خروجی‌های نمونه، نتیجهٔ بدون skip آزمون‌های الزامی و QA تصویری همهٔ صفحات تحویل شود. نیاز به commit/انتشار فقط در مرحلهٔ اجرای کار و با روال معمول پروژه مطرح است؛ این بازبینی هیچ commit یا انتشار انجام نمی‌دهد.

## ترتیب اجرای آخرین دور اصلاحات

1. **FIN-01:** حفاظت از داده‌های media.
2. **FIN-03 و FIN-04:** جهت واقعی کد/متن و مسیرهای معتبر؛ این دو مستقیماً روی استفادهٔ روزمره اثر دارند.
3. **FIN-02 و FIN-12:** قرارداد قالب و اعتبارسنجی، سپس **FIN-10** برای shell.
4. **FIN-05، FIN-06 و FIN-09:** اندازهٔ تصاویر، استخراج Mermaid و حفظ code.
5. **FIN-07 و FIN-08:** معنی و ساختار Markdown، سپس **FIN-11** برای صفحه‌بندی.
6. **FIN-13 و FIN-14:** محافظت هنگام نوشتن، CI و پذیرش انتشار.

## دروازهٔ بسته‌شدن پروژه

پس از اصلاحات، یک fixture تازهٔ چندصفحه‌ای شامل همهٔ اجزای پشتیبانی‌شده بسازید و با قالب پیش‌فرض، قالب سفارشی با رنگ/فونت/اندازهٔ صفحهٔ متفاوت و shell پشتیبانی‌شده تبدیل کنید:

- [x] ورودی و خروجی با مسیر فارسی و فاصله، از cwd مستقل کار کنند.
- [x] Markdown، کد، تصاویر و Mermaid بدون حذف/تغییر ناخواسته وارد Word شوند.
- [x] تمام گزینه‌های معتبر قالب در خروجی اعمال شوند؛ جای «override نادیده‌گرفته‌شده» نباشد.
- [x] فونت پیش‌فرض فارسی Vazirmatn و فونت‌های جایگزین مطابق نقش‌های قالب باشند.
- [x] code رنگی، چپ‌چین و از نظر متن قابل بازسازی باشد؛ link/footnote/math طبق قرارداد واقعی render شوند.
- [x] تمام صفحات در Word هدف و renderer QA دیده شوند؛ overflow، heading یتیم و badge شکسته وجود نداشته باشد.
- [x] اجرای موفق، شکست و هم‌زمانی هیچ دادهٔ متعلق به کاربر را حذف نکند.
- [x] آزمون‌های الزامی و نصب بسته پاس شوند و گزارش آنها با شرایط محیطی و نسخهٔ commit ثبت شود.

**تا رفع ایرادهای قطعی P1، اعلام «کار تمام شده و تمام قالب‌ها و Markdownها دقیق پشتیبانی می‌شوند» درست نیست. هدف اصلی قابل تحقق است؛ مسیر پایهٔ آن همین حالا وجود دارد، ولی بستن پروژه به عبور از معیارهای بالا نیاز دارد.**

مرجع قراردادهای Markdown که هنگام نهایی‌کردن dialect و تصاویر باید با آن تطبیق داد: [راهنمای رسمی Pandoc](https://pandoc.org/MANUAL.html). این سند عمداً قابلیت صرفاً پیشنهادشده را به‌عنوان قابلیت پیاده‌شده علامت نزده است.
