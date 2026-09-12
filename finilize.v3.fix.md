# پلن اصلاح شکاف‌های اجرای نسخهٔ ۳ — `finilize.v3.fix.md`

تاریخ بازبینی: **۲۰۲۶-۰۹-۰۹** · مرجع قرارداد: [finilize.v3.md](finilize.v3.md) · وضعیت: **پیاده‌سازی بخشی انجام شده؛ نسخهٔ ۳ هنوز قابل بستن نیست.**

این سند حاصل بازبینی مستقل کد و آزمون‌های موجود و چند بازتولید حداقلی است و **پلن اصلاح بعدی** محسوب می‌شود. در این نوبت هیچ کد محصول، تست مخزن، قالب، نمونهٔ tracked، پلن اصلی یا گزارش تاریخی اصلاح نشده است. probeها و خروجی‌های آزمایشی فقط در `/private/tmp/md2docx-v3-review-20260909/` ساخته شدند. تغییرات عامل قبلی حفظ شده‌اند.

## ۱. دامنه، snapshot و نتیجهٔ واقعی بررسی

مبنای بررسی `HEAD=4f857b6` به‌اضافهٔ working tree دارای تغییرات است؛ commit به‌تنهایی هویت این پیاده‌سازی نیست. فایل‌های `options.py`، `fonts_embed.py` و تست نسخهٔ ۳ هنوز untracked بودند. بین ثبت fingerprint و پایان probeها، محتوای هیچ‌یک از ۲۷۱ فایل tracked/untracked مبنا تغییر نکرد.

| فایل | SHA-256 در snapshot بررسی‌شده |
| --- | --- |
| `finilize.v3.md` | `d7a42ce1b1c0f9979f303f468a103bd53aadb6dfdefb316d68bbee695e36947e` |
| `src/md_to_docx/options.py` | `72d9432fda9ca99a27b9e41b8de438dd76e80e521e26cc58ae55a8921c69a337` |
| `src/md_to_docx/fonts_embed.py` | `59d670f65a08ab9bb9ec55ceb35668af2f5b6e8b738eb07b52f8673930377484` |
| `src/md_to_docx/pandoc_json.py` | `632d05e0ab426efda9bfa2a695e58e839dc38b818dcbe7fd26a28697c4d93a8b` |
| `src/md_to_docx/renderer.py` | `de51df0eb212df0ebe4fecbfd4bb5aa4cd145e27bd57543185d0aaf3bc7bb738` |

**اجرای مستقل:** Python 3.11.15، Pandoc موجود در `/opt/homebrew/bin/pandoc`، Node v22.19.0. فرمان زیر در ۲۵٫۴۳ ثانیه با exit 0 پایان یافت:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests -q -rs \
  -m 'not (mermaid or integration)' \
  -k 'not test_smoke_wheel_build_and_template_assets' -p no:cacheprovider
```

نتیجه: **۳۹۳ passed، ۱ skipped، ۵ deselected**. تنها skip در این انتخاب `tests/test_rtl_quality.py:149` به علت نبود LibreOffice بود؛ skip به معنی failure آزمون نیست. wheel، اجرای واقعی Mermaid، ماتریس کامل تازه و Word/LibreOffice در این بازبینی اجرا نشدند. هیچ شاهد بصری تازه‌ای صادر نشده است.

گزارش موجود عامل قبلی، `artifacts/persian-layout/run_20260909_010903/summary.md`، ۲۴۴ تبدیل و اوراکل موفق ولی **صفر صفحهٔ مرورشده** ثبت کرده است. آن گزارش شاهد اجرای همان run است؛ به‌علت کاستی oracle و fingerprint، اثبات سلامت کامل نسخهٔ ۳ نیست.

شواهد محلی این بازبینی: `before-hashes.json`، `unit.log`، `probe.py`، `probes.json`، `probe_extra.py` و `probes_extra.json` در پوشهٔ موقت بالا. این مسیر موقت است؛ شرح بازتولید و نتیجه در همین سند آمده تا برنامهٔ اصلاح به ماندگاری فایل موقت وابسته نباشد.

## ۲. موارد انجام‌شده‌ای که باید حفظ شوند

بازنویسی از صفر لازم نیست. این بخش‌ها در کد و تست‌های سبز فعلی وجود دارند:

- default فونت و تراز CLI به `None` تغییر کرده؛ flagهای heading/latin/code و center/justify اضافه شده‌اند.
- validation نوع boolean، direction، align و نام فونت و حذف هشدار عادی W05 انجام شده؛ تقدم `heading_font → font_family → template.heading` برقرار است.
- auto جهت از متن روایی اضافه شده و تعارض aliasهای metadata هشدار دارد؛ پیمایش و چند حالت کناری آن هنوز ناقص است.
- template اصلی و packaged `purple_book` به `start` تغییر کرده‌اند؛ بازسازی قالب هنوز این تغییر را برمی‌گرداند.
- جاسازی body و heading، merge اعلان font table، بررسی اولیهٔ fsType و مسیر strip افزوده شده‌اند؛ سلامت واقعی merge، font، namespace و گزارش پوشش کامل نیست.
- fallback مستقیم Bold خانوادهٔ سفارشی به Vazirmatn در دو resolver حذف شده است؛ تطبیق هویت داخلی فایل هنوز وجود ندارد.
- جهت مؤثر در گزارش CLI نمایش داده می‌شود؛ orphan check برای فونت‌های داخل `word/fonts/` به package oracle اضافه شده است.

شماره‌خط‌های بخش بعد مربوط به snapshot بالا هستند؛ با تغییر کد، از نام تابع و بازتولید استفاده شود. **P1** یعنی ایراد مهم محصول که پیش از پذیرش رفع شود؛ **P2** یعنی شکاف قرارداد/گزارش/نگهداری؛ دروازهٔ انتشار بدون شاهد بصری همچنان باز می‌ماند.

## ۳. ایرادهای بازتولیدشده و کار لازم

### V3FIX-01 — بازنویسی XML، prefixهای Markup Compatibility را خراب می‌کند · P1

**مرجع:** V3-03/V3-04، بخش ۴.۳ پلن. **کد:** `fonts_embed.py:284` مسیر settings در embed و `fonts_embed.py:457` در strip؛ `pipeline.py:346` هر دو حالت را فراخوانی می‌کند.

**شاهد:** تبدیل سادهٔ «متن فارسی و English.» هم با `embed_fonts=True` و هم False، در `word/settings.xml` مقدار `mc:Ignorable="w14"` دارد، اما namespace `w14` دیگر در scope تعریف نشده و ElementTree آن URI را با `ns5` سریال کرده است. parser معمول XML و package oracle فعلی هر دو خروجی را قبول می‌کنند. همین اشکال در **۱۰ از ۱۰ DOCX موجود در examples و سطح اول tests/fixtures** نیز مشاهده شد.

علت: namespace prefixهای به‌کاررفته در **مقدار attribute** با `ET.fromstring/tostring` حفظ/بازنویسی هماهنگ نمی‌شوند. `strip_embedded_fonts` حتی روی سند بدون فونت embedded هم به علت وجود `settings.xml` کل مسیر را اجرا می‌کند، پس default False نیز متاثر است.

**اصلاح برنامه‌ریزی‌شده:** حفظ namespace map و تمام attributeهای QName/prefix-valued در XMLهای دست‌خورده؛ حفظ extension/MC به‌جای حذف بی‌قید آن‌ها. strip وقتی هیچ تغییری لازم نیست، XML نامرتبط را دوباره serialize نکند. schema/order مستقل هم بررسی شود. معنای prefixهای `mc:Ignorable` باید با namespace متناظر هماهنگ بماند؛ نام prefix صرفاً رشتهٔ دلخواهِ بی‌ارتباط نیست. [مرجع Microsoft برای mc:Ignorable](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/advanced/mc-ignorable-attribute)

**تست قرمز و پذیرش:** سند python-docx معمولی و shell دارای `mc:Ignorable`/`AlternateContent` در true/false؛ تمام prefixهای referenced قابل resolve، extensionها محفوظ و validator مستقل سالم. Word باید روی کپی خروجی بدون Repair باز و save/reopen شود. **Repair در Word در این بازبینی مشاهده نشده**؛ یافتهٔ فعلی خرابی ارجاع namespace است. بازتولید دوبارهٔ نمونه‌های tracked فقط پس از رفع و در مرحلهٔ صریح تحویل انجام شود.

### V3FIX-02 — merge و strip بر اساس اسم پوشه عمل می‌کنند و فونت موجود را از دست می‌دهند · P1

**مرجع:** V3-03، بخش ۴.۱/۴.۳. **کد:** `fonts_embed.py:309` حذف همهٔ odttfها، `:348` نام‌گذاری از font1، `:360` بازنویسی rId موجود؛ `:444` و `:483` حذف در strip.

**بازتولید A:** در DOCX دارای فونت، ورودی فونت دیگری با `rIdLegacy → fonts/legacy.odttf` اضافه شد. package oracle قبل از embed دوباره pass بود. پس از embed، اعلان و رابطهٔ legacy باقی ماندند ولی payload حذف شد؛ oracle خطای زیر داد:

```text
Missing relationship target 'fonts/legacy.odttf' ... from word/_rels/fontTable.xml.rels
```

**بازتولید B:** یک فونت embedded معتبر به `word/custom/typeface.odttf` منتقل و relationship و Content Type Override آن تنظیم شد. پس از strip، bytes فونت همچنان در ZIP باقی بود، ولی رابطهٔ آن حذف شد؛ oracle فعلی به علت محدودبودن به `word/fonts/` همچنان pass داد. False به قرارداد «خروجی بدون payload فونت» عمل نمی‌کند.

**شکاف مرتبط در همان مسیر:** font table و settings همیشه در مسیر hardcode جست‌وجو می‌شوند؛ داشتن relationship به font table با نام دیگر کافی است تا بخش تازه در جای اشتباه نوشته شود. rId/نام جدید از ۱ شروع می‌شود و با رابطهٔ موجود برخورد می‌کند. `except Exception` هنگام parse ممکن است محتوا را با ریشهٔ خالی جایگزین کند یا strip را ناقص ولی موفق تمام کند.

**اصلاح:** مسیر partها از relationship و content type حل شود؛ merge فقط خانواده/face هدف را عوض کند. تخصیص rId و نام part با رزرو تمام نام‌های موجود؛ حذف پس از تحلیل مالکیت/reference و اصلاح Default/Override متناسب. parse نامعتبر خطای روشن و بدون publish بدهد.

**پذیرش:** بقای family/face غیرهدف از نظر بایت و رابطه؛ دوباره‌جاسازی idempotent از نظر معنایی؛ false روی shell با part/path/extension متفاوت بدون font payload و بدون orphan/dangling rel؛ اصل shell دست‌نخورده.

### V3FIX-03 — True روی تنظیم False موجود اثر نمی‌کند · P1

**مرجع:** V3-03، بخش ۴.۳. **کد:** `fonts_embed.py:289`.

**شاهد:** یک shell با `<w:embedTrueTypeFonts w:val="0"/>` ساخته شد. پس از `embed_fonts_in_docx` مقدار هنوز **0** بود، در حالی که فونت نوشته و نتیجه `embedded` اعلام شد. کد فقط در نبود عنصر آن را اضافه می‌کند و مقدار عنصر موجود را روشن نمی‌کند.

**اصلاح:** مقدار effective تنظیم صریحاً true شود؛ true/false/off/0 و تکرار ناسالم property مدیریت شوند؛ سیاست `saveSubsetFonts` و `embedSystemFonts` پوسته مطابق قرارداد باشد. قرارگیری property در ترتیب schema نیز کنترل شود، نه append به انتهای settings بدون بررسی. این تنظیم سیاست ذخیرهٔ برنامه است و با وجود payload واقعی دو شاهد جدا می‌خواهد. [مرجع EmbedTrueTypeFonts](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.embedtruetypefonts?view=openxml-3.0.1)

**پذیرش:** ورودیِ مقدار false/0، پس از درخواست true مقدار true مؤثر داشته باشد؛ false واقعاً خاموش و وضعیت CLI/report با settings نهایی منطبق باشد؛ save/reopen Word تیک و محتوای فونت را جدا تایید کند.

### V3FIX-04 — parser فونت، فایل خراب و family جعلی را معتبر می‌شمارد · P1

**مرجع:** V3-03، بخش ۴.۲/۴.۳. **کد:** `fonts_embed.py:28`، `:57` و `:137`؛ تست `tests/test_v3_features.py:764`.

**شاهد A:** فایل **۳۸‌بایتی** شامل sfnt header، یک رکورد OS/2 و ده بایت با fsType=0 به‌جای هر دو TTF قالب قرار گرفت. هیچ glyph/cmap/name/outline واقعی نداشت. validation=True، تبدیل موفق، `embedding_status=embedded` و package oracle=pass شد.

**شاهد B:** کلیدهای `Pretend-Regular` و `Pretend-Bold` به فایل‌های واقعی Vazirmatn نگاشت شدند؛ `validate_font_embedding(..., 'Pretend')` پذیرفت. تست فعلی چندخانواده نیز فایل Vazirmatn را با نام Sahel کپی می‌کند و همین اشتباه هویت را به‌عنوان موفقیت تثبیت کرده است.

**شکاف ایستا:** `read_font_fstype` نسخهٔ OS/2 را می‌خواند ولی در نتیجه/validation استفاده نمی‌کند؛ OTTO را بدون اثبات پشتیبانی CFF قبول می‌کند؛ فیلد name/weight/style و سلامت جدول‌ها سنجیده نمی‌شوند. تشخیص مجوز هنوز substring است، فقط واژه‌ها عوض شده‌اند. مجوز موجود در پوشه لزوماً متعلق به family سفارشی نیست.

**اصلاح:** parser معتبر برای نوع واقعی فونت، سلامت tableها، family/subfamily، Regular/Bold، static/variable و دامنهٔ TTF تضمین‌شده. fsType طبق نسخه و حقوق واقعی فایل بررسی شود؛ مجوز به provenance/hash خانواده متصل باشد. [مرجع OS/2 و fsType](https://learn.microsoft.com/en-us/typography/opentype/spec/os2#fstype)

**تست/پذیرش:** فایل ۳۸‌بایتی، checksum/offset/length خراب، family یا وزن اشتباه و نوع خارج قرارداد fail؛ دو family واقعی برای تست مثبت؛ مجوز غایب/نامرتبط و fsType نامعتبر/محدود رد شوند. No-subsetting با جاسازی کامل اشتباه نشود. obfuscation علاوه بر round-trip همان تابع، vector ثابت و deobfuscation با parser مستقل داشته باشد؛ GUID malformed صرفاً با حذف کاراکترهای نامعتبر معتبر نشود. در خطا DOCX/media قبلی سالم بمانند.

### V3FIX-05 — option فونت به inline code و marker فهرست نمی‌رسد · P1

**مرجع:** V3-02. **کد:** `pandoc_json.py:306`، `:1303` و `:1351`.

**شاهد:** با `font_family='ProbeBody'` و `code_font='ProbeCode'`، inline code `SELECT 1` هنوز **Courier New** داشت؛ marker فهرست مرتب و bullet همچنان **Vazirmatn** بود، در حالی که متن آیتم ProbeBody می‌گرفت. مسیر block code از option استفاده می‌کند، بنابراین یک نقش بسته به inline/block رفتار متفاوت دارد.

**اصلاح:** مصرف نقش‌های مؤثر renderer/resolver در همهٔ emitterهای فعال، شامل code داخل heading/link/callout/footnote و marker عددی/متنی؛ نام فونت مستقیماً از template دور زده نشود. فارسی داخل کد جدا با سیاست حفظ متن بررسی شود.

**پذیرش:** probe چهار نقش مستقل با assert روی run متن واقعی و marker؛ inline و block code هر دو override مربوط را بگیرند؛ `font_family` نقش‌های latin/code را بی‌دلیل تغییر ندهد.

### V3FIX-06 — auto جهت، بدنهٔ جدول را نمی‌خواند و URL را نثر حساب می‌کند · P1

**مرجع:** V3-01، بخش ۱.۱. **کد:** `pandoc_json.py:1461`؛ به‌ویژه شاخهٔ Table در `:1520`.

**بازتولید A:** جدول pipe با header انگلیسی `ID` و یک سلول طولانی فارسی. TableBody واقعی Pandoc **۴ عضو** دارد، ولی heuristic شرط `len(tbody)>4` و `tbody[4]` دارد. متن بدنه هرگز شمارش نمی‌شود؛ `detected=ltr` و جهت کل خروجی LTR شد. header/body/footer/row-head باید طبق همان AST پذیرفته‌شدهٔ adapter پیمایش شوند؛ `except Exception: pass` افت داده را پنهان می‌کند.

**بازتولید B:** نثر «متن» به‌همراه `https://example.com/very-long-english-url-and-directory` به جهت **LTR** رسید، چون متن نمایشی URL در Str/Link شمرده می‌شود؛ در قرارداد این متن فنی باید از تشخیص غالب کنار گذاشته شود.

**اصلاح:** پیمایش کامل و مستقل nodeهای پشتیبانی‌شده؛ حذف URL/مسیر فنی از شمارش با حفظ متن نمایشی link معمولی؛ حذف فقط در مدل تشخیص، نه متن سند. TableFoot و Figure/caption/Note مطابق دامنهٔ مصوب تعیین تکلیف شوند؛ خطای ساختار AST diagnostic داشته باشد.

**پذیرش:** فارسی در body/footer جدول با header لاتین روی هر دو قالب RTL/LTR؛ URL-only و code-only از fallback قالب، نثر فارسی+URL از فارسی؛ tie/neutral، metadata صریح و option همچنان تقدم صحیح داشته باشند.

### V3FIX-07 — جهت یک متن فارسی در ظرف‌های مختلف ناسازگار است · P1

**مرجع:** V3-01. **کد:** `pandoc_json.py:1162`، شاخه‌های nested quote در `:1190`؛ `renderer.py:939` پاراگراف اول پاورقی.

**شاهد:** با `direction='ltr'`، متن فارسی بدنه `bidi=1/right` شد؛ همان متن در callout `bidi=0/left` گرفت. در پاورقی دوپاراگرافی، اولی **1/right** و دومی **0/left** شد. این حالت در سند LTR حاوی توضیح فارسی مجاز است و استثنای فارسی نباید فقط برای paragraph اول کار کند.

علت: مسیر root/پاراگراف اول از `resolve_paragraph_bidi` استفاده می‌کند، اما مسیر container از `contains_persian(text) if effective_direction == 'rtl' else False`.

**اصلاح:** resolver بافت/نقش مشترک برای بدنه، cell، quote، callout و تمام paragraphهای footnote؛ حفظ اندازه و فونت یک نقش در پاراگراف‌های متوالی. section LTR با paragraph فارسی RTL تناقض نیست.

**پذیرش:** یک fixture با همان متن در همهٔ ظرفها، روی هر دو جهت پایه و با runهای لاتین؛ جهت و تراز مطابق نقش، فونت/اندازهٔ پاورقی یکنواخت و copy/search محفوظ؛ رندر Word جدا.

### V3FIX-08 — فهرست و جدول تماماً لاتین، جهت صریح ظرف RTL را کنار می‌گذارند · P1

**مرجع:** V3-01، بخش‌های ۱ و ۲. **کد:** `pandoc_json.py:962`، `:825` و مسیر مشابه `renderer.py::render_table`.

**شاهد:** `direction='rtl'` با فهرست دو آیتم تماماً انگلیسی، هر دو paragraph marker را `bidi=0` می‌سازد. جدول `Name/Value` در همین جهت، **هیچ `bidiVisual`** ندارد، با وجود اینکه config آن را فعال می‌خواهد.

علت: `_resolve_list_rtl` به متن ترکیبی فهرست رجوع می‌کند و parent=False را هم قبل از تشخیص متن قطعی نمی‌کند؛ جدول نیز با `if not has_persian: is_rtl_table=False` سیاست ظرف را خنثی می‌کند.

**اصلاح:** جهت ساختاری marker/continuation و ترتیب ستون‌ها از ظرفِ مؤثر بیاید؛ run لاتین و paragraph محتوایی سلول مستقل باقی بمانند. برای برگشت جدول RTLِ inherited به LTR helper باید false مؤثر تولید کند، نه فقط نبود عنصر جدید.

**پذیرش:** RTL با آیتم/جدول انگلیسی، LTR با متن فارسی، فهرست چندسطحی با parent true/false، continuation و header/data قابل تمایز؛ بدون reverse دوبارهٔ داده و بدون جابه‌جایی marker با تغییر زبان آیتم.

### V3FIX-09 — shell/header/footer و ارث‌بری فونت/وزن کامل اعمال نمی‌شوند · P1

**مرجع:** V3-01/V3-02/V3-06. **کد:** `renderer.py:212` `_setup_page`، `:233` `_setup_normal_style`؛ `oxml.py::set_run_cs_font`.

**شاهد A:** shell با run سرصفحه دارای `cs=WrongHeaderFont` و جدول داخل header با paragraph فارسی `bidi=0` ساخته شد. با `font_family='ProbeBody', direction='rtl'`، فونت مستقیم سرصفحه **WrongHeaderFont** و جهت جدول **0** باقی ماندند. فقط paragraphهای سطح اول header/footer پیمایش می‌شوند.

**شاهد B:** `Normal` پوسته با `w:bCs` و theme font متعارض ساخته شد. بعد از override، theme attribute و bold موروثی همچنان وجود داشتند و run نثر عادی هیچ false برای bCs نداشت. تنظیم نام فونت/عدم نوشتن bold به‌تنهایی خنثی‌کردن ارث‌بری نیست.

**اصلاح:** پیمایش storyهای موجود و container nested، resolver font/size/direction و مدیریت theme/explicit formatting متعارض؛ defaults/Normal/role styles و paragraph mark با آزمون واقعی. طراحی center/PAGE/logo/چرخش عمدی را تغییر نده؛ part first/even خالی فقط بر اثر inspection تولید نشود.

**پذیرش:** default/first/even هر دو story، جدول nested، field result، run بدون text و custom style؛ falseِ bold/italic و LTR در برابر inheritance واقعاً مؤثر؛ Word پس از Enter و update field به فونت/جهت قبلی برنگردد. وجود tag مستقیم در همهٔ paragraphها الزام بی‌دلیل نیست؛ رفتار effective سنجیده شود.

### V3FIX-10 — resolver و CSS Mermaid هنوز با option فونت یک قرارداد ندارند · P1

**مرجع:** V3-02/V3-05. **کد:** `mermaid.py:590` تا `:655` و resolver جدا در `fonts_embed.py:65`.

**شاهد A، بدون launch مرورگر:** `font_files['Custom-Regular']='fonts/Vazirmatn-Regular.ttf'` و کلید Bold به `_effective_mermaid_css` داده شد. resolver Mermaid کلید `Family-Regular` را نمی‌خواند؛ warning نبود فایل صادر کرد و CSS قدیمی **Vazirmatn با مسیر نسبی** را نگه داشت. وجود نام فایل Regular در متن CSS شاهد بارگذاری family انتخابی نیست. resolver embedding همین ساختار کلید را می‌پذیرد.

**شاهد B:** family معتبر از نظر رشته مانند `O'Brien` مستقیماً به `font-family: 'O'Brien';` تبدیل می‌شود؛ CSS string صحیح escape نشده است. XML-string escaping اصلاح‌شده به معنی CSS escaping نیست.

**اصلاح:** resolver مشترک family/face/path، escape صحیح CSS و URI، font-ready، عدم نگه‌داشتن CSS خانوادهٔ قبلی در fallback پنهان؛ diagnostic به warnings/report عمومی برسد. family/weight واقعی با V3FIX-04 کنترل شود.

**پذیرش:** نام فارسی/فاصله/apostrophe/quote، مسیر سفارشی regular/bold و family دوم واقعی؛ assert CSS فقط مرحلهٔ اول است، smoke Chromium با font استفاده‌شده و PNG/SVG و خوانایی در A5 لازم است. دو subprocess PNG/SVG فعلی بدون fingerprint کافی همچنان شاهد «همان فرایند» نیستند.

### V3FIX-11 — oracleها تغییر معنای فرمول، مقصد پاورقی و جهت را تشخیص نمی‌دهند · P1

**مرجع:** V3-04. **کد:** `scripts/semantic_oracle.py:723` تا `:747`؛ `scripts/package_oracle.py` بخش media/font و reference validation.

**شاهد:** سند دارای دو پاورقی با متن متمایز و فرمول `x+1` ابتدا pass شد. روی کپی خروجی، ID دو `footnoteReference` جابه‌جا شد، عدد فرمول به 9 تغییر کرد و bidi پاراگراف‌های فارسی false شد. **semantic و package هر دو دوباره `(True, [])` دادند.** خرابی‌ها هم‌زمان تزریق شدند و هیچ‌کدام diagnostic نداشت؛ در تست رگرسیون آینده هرکدام جدا نیز باید fail شود.

package oracle همچنین namespace خراب V3FIX-01، فونت ۳۸‌بایتی V3FIX-04 و payload یتیم خارج `word/fonts/` در V3FIX-02 را ندید. تصویر بدنه با base_dir قابل resolve اکنون hash می‌شود؛ این قابلیت موجود را دوباره «صرفاً شمارشی» گزارش نکن. اما تصاویر/لینک‌ها/math پاورقی عمدتاً count می‌شوند و اتصال reference به story مقصد سنجیده نمی‌شود.

**اصلاح:** مدل مستقل جهت/فونت مؤثر، معنای عملگر/عملوند OMML، mapping هر footnoteRef به محتوای مربوط، target/text لینک و image occurrence/hash در تمام storyهای پشتیبانی‌شده؛ schema/MC/fontKey/payload و رابطه‌های فونت مستقل از مسیر دلخواه پوشه. unresolved asset به pass خاموش تبدیل نشود.

**پذیرش:** mutationهای تک‌علتی و ترکیبی برای موارد بالا + حذف جمله/قطع کد/جابه‌جایی cell و media هم‌اندازه؛ failure با محل و انتظار/واقعیت. خروجی مثبت سالم در هر چهار قالب pass بماند؛ clipping فقط با لایهٔ تصویری بسته شود.

### V3FIX-12 — عرض جدول می‌تواند از ظرف فراتر برود · P1

**مرجع:** V3-06. **کد:** `pandoc_json.py:855` تا `:865`، تخصیص widthهای AST.

**شاهد:** AST جدول بومی دو ستونی با `ColWidth=0.75` برای هر ستون روی `persian_compact`، عرض ظرف **۶۵۷۷ twip** و grid **۴۹۳۳+۴۹۳۳=۹۸۶۶ twip** تولید کرد؛ نه normalize و نه diagnostic. در diff فعلی تنظیم نهایی مجموع عرض حذف شده است. این probe مستقیم AST است؛ ادعای بازتولید با Markdown عادی یا مشاهدهٔ clipping در Word نشده است.

**اصلاح:** اعتبارسنجی مجموع explicit widths و حداقل‌ها، تخصیص deterministic برای explicit/default و rounding؛ اگر درخواست در ظرف نمی‌گنجد، قرارداد روشن normalize یا خطای صریح، نه خروجی سرریز خاموش. padding/indent از عرض قابل استفاده کم شوند.

**پذیرش:** explicit مجموع زیر/برابر/بیش از ۱، ستون‌های auto، مجموع حداقل‌ها بیش از A5 و جدول nested؛ مجموع grid و tcW از ظرف فراتر نرود و داده/سرستون حفظ شود؛ fixtureهای مثبت S05/S06 و جدول چندصفحه‌ای با رندر تایید شوند.

## ۴. شکاف‌های باقی‌ماندهٔ قرارداد، گزارش و پذیرش

### V3FIX-13 — گزارش embedding و گزینهٔ مؤثر ناقص است · P2

**مرجع:** V3-02/V3-03/V3-07. **کد:** `fonts_embed.py:419`، `pipeline.py:351` و `cli.py:137`/`:238`؛ `matrix_runner.py:618` و `:659`.

**شاهد:** تبدیل پیش‌فرض purple_book با true تنها body/heading Vazirmatn را embed کرد، اما نتیجهٔ کل `embedded` بود و Segoe UI/Courier New به‌عنوان referenced_only گزارش نشدند. CLI همچنان `embedded: yes/no` را از **درخواست** می‌سازد. report مؤثر چهار family و جهت را دارد ولی per-face/per-role، partial، علت، hash، size delta، requested/effective align و منشأ resolution ندارد. runner اصلاً این report را به خروجی ماتریس متصل نکرده است.

**کار:** نتیجهٔ مشترک مطابق بخش ۴.۴ پلن؛ body/heading ضروری، latin/code مستقل با فایل معتبر اختیاری، Italic/BoldItalic یا synthetic با وضعیت صریح. True بودن option به معنی embedding همهٔ faceها نباشد. `report` پیش از publish به‌عنوان نتیجهٔ موفق نهایی مصرف نشود؛ failure و استفادهٔ مجدد ظرف گزارش تعریف شود. aliasهای مسطح heading/latin/code و `report=` تازهٔ API نیز مستند شوند.

**پذیرش:** خروجی API همچنان Path، warnings سازگار، بدون sidecar اجباری؛ CLI و runner با نتیجهٔ واقعی یکسان و hash خانواده‌ها قابل ممیزی. با family/face ناقص در دامنهٔ ضروری failure بدون publish؛ نقش‌های اختیاری reference باعث ادعای all-embedded نشوند.

### V3FIX-14 — validation کناری و metadata نامعتبر هنوز diagnostic یکسان ندارند · P2

**مرجع:** V3-01/V3-02. **کد:** `options.py:98`، `pandoc_json.py:1598` و `:1628`.

**بازتولید:** `options={1: True}` به TypeError در join و `{1: True, 'oops': True}` به TypeError در sort می‌رسند؛ قرارداد خواسته ValueError روشن برای کلید نامعتبر است. ورودی metadata `dir: sideways` بی‌هیچ warning ردگیری‌شدنی کنار گذاشته شد و خروجی موفق بود؛ تشخیص تعارض دو alias جای validation مقدار را نمی‌گیرد.

**کار:** کلیدهای option پیش از sort/join نوع‌سنجی؛ مقدار invalid metadata با code/identity روشن و precedence مستند؛ canonicalization alias زبان/جهت یکسان. انتخاب script subtag با primary language متعارض نیز تست شود؛ این قسمت فراتر از نمونه‌های محدود فعلی است و بدون تست «BCP47 کامل» ادعا نشود.

**پذیرش:** dict/شیء/alias، کلید غیررشته، None/empty/false، whitespace/case و metadata invalid/conflict با exception/exit/warning مشخص؛ پیش از اجرای ابزار خارجی برای option نامعتبر؛ ورودی‌های valid و شیء کاربر بدون mutation.

### V3FIX-15 — بازسازی قالب و مستندات هنوز قرارداد قدیمی را برمی‌گردانند · P2

**مرجع:** V3-06/V3-08. **کد:** `scripts/setup_templates.py:93`، `README.md:204`، `README_FA.md:196` و بخش API/فونت AGENTS.

**شاهد ایستا:** دو config purple_book روی start هستند، اما setup همچنان `cfg['page']['paragraph_align']='both'` می‌نویسد. هر دو README هنوز purple_book را justified معرفی می‌کنند؛ AGENTS می‌گوید flag فونت وجود ندارد و embedding انجام نمی‌شود. docstring option نیز default فونت/align را نادقیق توصیف می‌کند.

**کار:** یکسان‌کردن generator تنظیم قالب، نسخهٔ packaged، READMEها، AGENTS، help و docstring با رفتار نهایی. تراز start و تغییر ظاهر عمدی purple_book، auto جهت، نقش‌ها، precedence و دامنه/محدودیت embedding و گزارش روشن شوند.

**پذیرش:** بازسازی فقط در کپی موقت قالب config مورد انتظار را بازتولید کند؛ نمونه‌های مستند در محیط تمیز اجرا شوند. بدون مجوز بازتولید، فایل‌های نمونه و قالب‌های کاربر بازنویسی نشوند.

### V3FIX-16 — دروازه‌های کامل v3 هنوز شاهد و پوشش اجرایی ندارند · الزامی برای انتشار

**مرجع:** V3-00/V3-04/V3-05/V3-06/V3-07/V3-08 و بخش ۹ پلن.

کارهای باز باید در گزارش بعدی با وضعیت جدا ثبت شوند، نه در یک تیک «v3 انجام شد»:

| حوزه | شکاف و کار لازم |
| --- | --- |
| TDD | تست‌های اضافه‌شده green هستند، اما شاهد red-before/green-after برای همهٔ تغییرات ارائه نشده. تست family جعلی و round-trip همان تابع نیز انتظار مستقل نیست. برای اصلاح‌های این سند red واقعی ثبت شود؛ فقدان log تاریخی به معنی اثبات «TDD انجام نشده» نیست. |
| runtime Mermaid | guardها موجودند؛ smoke واقعی این بازبینی اجرا نشده. font-ready، label/occurrence nested، fingerprint مشترک PNG/SVG، theme و خوانایی A5 بعد از اصلاح فونت دوباره اثبات شوند. شکست launch blocked ثبت شود؛ مرورگر دسکتاپ جایگزین خودکار نباشد. |
| رندر/Word | run قبلی صفر review دارد. همهٔ ۲۴۴ DOCX باید در هر دو موتور رندر شوند؛ review تمام صفحات و مرزها، مرور انسانی هدفمند، Word بدون فونت نصب‌شده برای embedding، save/reopen و TOC/PAGE/Enter هنوز بازند. نبود ابزار یا پاسخ انسانی pending/blocked است. |
| runner | mode پذیرش release، ثبت/مصرف review صفحه‌به‌صفحه و engine، exit ناموفق برای gate الزامی pending و گزارش گزینه‌ها کامل نیستند. `visual_pages_reviewed` در writer فعلی ثابت 0 است؛ این صداقتِ نبود مرور است، نه workflow تکمیل‌شدهٔ مرور. |
| fingerprint | code_snapshot فعلی فقط چند فایل renderer/adapter/Mermaid/runner را hash می‌کند؛ options/fonts_embed/pipeline/oxml، تمام دارایی/فونت‌ها و منشأ config مؤثر در fingerprint نهایی لازم‌اند. |
| wheel/CI | تست wheel فعلی چهار قالب را می‌سازد ولی سناریوهای v3 شامل embed on/off، shell دارای embed، optionهای فونت و validation در wheel نیستند. نصب مستقل، مسیر فارسی/فاصله، API/CLI/stdin و ابزار integration با skip الزامی صفر لازم است. این بازبینی wheel تازه اجرا نکرد. |
| layout و محتوا | شکست سالم جدول/کد/callout، badge بلند، caption/image/EXIF، نقش/اندازهٔ nested، TOC/navigation و template چهارگانه تا review تصاویر بسته نیستند؛ سبزشدن XML جای آن نیست. |
| assets و خروجی‌های موجود | DOCXهای نمونه عامل قبلی بازتولید شده‌اند، اما V3FIX-01 در همهٔ ده نمونه دیده شد. پس از اصلاح package، خروجی‌های متاثر با قصد صریح و روی snapshot ثابت دوباره ساخته و review شوند؛ اصلاح دستی Word جای اصلاح renderer نیست. |

## ۵. ترتیب اجرا و نگاشت به پلن اصلی

۱. **V3FIX-01 تا 04:** ابتدا سلامت package و فونت؛ یک probe کوچک Word برای جلوگیری از تولید انبوه خروجی ناسالم. V3FIX-11 برای همین خرابی‌ها هم‌زمان تست محافظ مستقل بگیرد.
۲. **V3FIX-05 تا 10 و 14:** قرارداد فونت/جهت در همهٔ ظرفها و metadata؛ fixture حداقلی و TDD با تمرکز روی RTL.
۳. **V3FIX-12 و 13:** عرض و نتیجهٔ گزارش‌شده؛ سپس تکمیل باقی‌ماندهٔ oracle در V3FIX-11.
۴. **V3FIX-15 و 16:** قالب/مستندات، wheel/CI، ماتریس تازه، دو موتور رندر و review. ابزار غایب فقط دروازهٔ وابسته را باز نگه دارد؛ کار مستقل متوقف نشود.

| تسک اصلی | موارد این پلن |
| --- | --- |
| V3-00 | snapshot و شواهد بخش ۱، V3FIX-16 |
| V3-01 | V3FIX-06/07/08/09/14 |
| V3-02 | V3FIX-05/09/10/13/14 |
| V3-03 | V3FIX-01/02/03/04/13 |
| V3-04 | V3FIX-01/02/04/11 و آزمون‌های خرابی همهٔ موارد |
| V3-05 | V3FIX-10/16 |
| V3-06 | V3FIX-09/12/15/16 |
| V3-07 | V3FIX-11/13/16 |
| V3-08 | V3FIX-13/15/16 |

## ۶. راه بازتولید شواهد کلیدی

probeهای ذخیره‌شده برای اجرای یک‌باره در پوشهٔ خالی نوشته شده‌اند و `overwrite=False` دارند؛ اجرای دوباره در همان مسیرِ پر انتظار FileExistsError دارد. برای تکرار، مسیر تازهٔ اختصاصی در کپی probe تعیین شود؛ پوشهٔ شواهد قبلی پاک نشود.

**نمونهٔ مستقل نقص namespace؛ خروجی فقط موقت:**

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from lxml import etree
from md_to_docx import convert_markdown_to_docx

mc = '{http://schemas.openxmlformats.org/markup-compatibility/2006}'
with TemporaryDirectory(prefix='v3-review-') as directory:
    for enabled in (False, True):
        out = Path(directory) / f'{enabled}.docx'
        convert_markdown_to_docx(
            content='متن فارسی', output_path=out,
            embed_fonts=enabled, overwrite=False,
        )
        with ZipFile(out) as z:
            root = etree.fromstring(z.read('word/settings.xml'))
        unresolved = [prefix for el in root.iter()
                      for prefix in el.get(mc + 'Ignorable', '').split()
                      if prefix not in el.nsmap]
        print(enabled, unresolved)  # snapshot فعلی: هر دو ['w14']
```

**ورودی حداقلی جهت جدول:**

```markdown
| ID |
|---|
| این یک متن بسیار طولانی فارسی برای آزمایش جهت کل سند است |
```

با `report={}` و `direction='auto'`، مقدار `report['effective_direction']` اکنون ltr می‌شود؛ انتظار rtl است.

**ساخت bytes فونت خراب برای تست منفی، فقط در کپی موقت قالب:**

```python
import struct
fake_font = (
    struct.pack('>4sHHHH', b'\x00\x01\x00\x00', 1, 0, 0, 0)
    + struct.pack('>4sIII', b'OS/2', 0, 28, 10)
    + struct.pack('>HHHHH', 3, 0, 400, 5, 0)
)
assert len(fake_font) == 38
```

این داده صرفاً header و بخشی از OS/2 دارد. در probe جای Regular/Bold کپی قالب گذاشته شد و validation و تبدیل فعلی آن را پذیرفتند؛ تست اصلاح باید آن را رد کند.

## ۷. تعریف پایان کار اصلاحی

هر V3FIX فقط با شاهد بسته شود: تست مستقل قرمز قبل از اصلاح، نتیجهٔ سبز بعد، عدم رگرسیون نزدیک، artifact مربوط و برای رفتار بصری Word/LO مشاهدهٔ واقعی. وجود ۳۹۳ تست سبز فعلی یا ۲۴۴ pass تاریخی جای این شرط نیست.

برای بستن کل نسخه، دروازه‌های `finilize.v3.md` باقی‌اند: snapshot واحد، صحت معنایی و package، option/فونت/embedding روشن و خاموش، ماتریس کامل، Mermaid واقعی، wheel مستقل، رندر همهٔ صفحات و مرور لازم. هیچ fail/blocked/pending الزامی با نمره یا تیک تاریخی پوشانده نشود.

**تحویل این بازبینی فقط این پلن اصلاحی است. هیچ‌یک از ایرادهای فوق در کد این نوبت رفع نشده‌اند.**

