# برنامهٔ اصلاحات باقی‌مانده پس از بازبینی سوم

تاریخ بازبینی: 2026-09-05
وضعیت فعلی: `166 passed, 1 skipped` در venv؛ با این حال مسیر واقعی Mermaid در این ماشین هنوز شکست می‌خورد. موارد حل‌شدهٔ بازبینی قبلی از این فهرست حذف شده‌اند.

## الزامی برای قابلیت‌های درخواستی

### R3-01 — Mermaid هنوز end-to-end سبز نیست (P0)

با وجود نصب Chrome for Testing، اجرای fixture واقعی با `mmdc` با خطای `Failed to launch the browser process` شکست می‌خورد. probe فعلی فقط مسیر executable را پیدا می‌کند و موفقیت launch را ثابت نمی‌کند؛ بنابراین ادعای «امکان استفاده از Mermaid» هنوز اثبات نشده است.

**برنامهٔ اصلاح:** probe را با همان command/config واقعی mmdc اجرا کنید، executable را به شکل صریح به Puppeteer بدهید، علت‌های sandbox/architecture/permission را تفکیک کنید و در CI یک job واقعی با یک Mermaid فارسی و assertion روی PNG و DOCX داشته باشید. تست integration فقط بر اساس probe موفق اجرا شود؛ تست unit مستقل بماند.

### R3-02 — تصاویر inline ترتیب Markdown را حفظ نمی‌کنند (P1)

در مسیر `Para/Plain` وقتی تصویر همراه متن است، ابتدا همهٔ تصاویر render می‌شوند و سپس متن باقی‌مانده render می‌شود؛ در نتیجه ورودی‌ای مثل `قبل ![عکس](a.png) بعد` به ترتیب دیگری در DOCX می‌رسد. Alt text نیز بدون توجه به semantics به‌عنوان caption استفاده می‌شود.

**برنامهٔ اصلاح:** inline dispatcher را به‌صورت ترتیبی render کنید تا تصویر دقیقاً در جای خود قرار گیرد، title/caption را از alt جدا کنید و برای تصاویر standalone/inline قرارداد مشخص داشته باشید. تست‌های چند تصویر، متن قبل/بعد، لینک‌دار و caption واقعی اضافه شود.

### R3-03 — پشتیبانی «کامل Markdown» هنوز کامل نیست (P1)

AST adapter برای برخی nodeها هنوز رفتار ناسازگار دارد: `blocks_to_text` در مسیرهای کمکی بخشی از nodeها را حذف می‌کند، nested ساختارها در بعضی contextها تخت می‌شوند، و Raw HTML/RawInline به متن خام تبدیل می‌شود. بنابراین ادعای پشتیبانی کامل README بیش از رفتار اثبات‌شده است.

**برنامهٔ اصلاح:** ماتریس پشتیبانی را دقیقاً با Pandoc version قفل کنید؛ dispatcher بازگشتی واحد را در تمام contextها استفاده کنید؛ برای nodeهای unsupported خطای مسیر‌دار بدهید یا صریحاً آن‌ها را در README محدود کنید. fixture جامع برای headings، paragraphs، emphasis/strike/sup/sub, links, images, lists, blockquotes, tables, code, footnotes, math و raw HTML اضافه کنید.

### R3-04 — Syntax highlighting فقط در تست ساختاری تأیید شده است (P1)

کد از Pygments token color استفاده می‌کند، اما تست end-to-end مستقل که زبان‌های Python/SQL/TypeScript/JSON را از Markdown تا DOCX بررسی کند و وجود رنگ‌های متفاوت/فونت monospaced را assert کند، کافی نیست. تشخیص lexer ناشناخته نیز silently به `guess_lexer` می‌رود و ممکن است خروجی غلط بدهد.

**برنامهٔ اصلاح:** برای هر زبان fixture و assertion روی `w:color`, `w:rFonts` و LTR بودن code table اضافه کنید؛ رفتار زبان ناشناخته را مستند و قابل‌کنترل کنید (fallback صریح یا خطا). یک تست بازکردن DOCX و بررسی چند token رنگی/چند خطی اجرا شود.

### R3-05 — Mermaid و image artifactها هنوز cleanup/atomicity کامل ندارند (P1)

اگر Pandoc یا renderer بعد از تولید تصویر شکست بخورد، media directory پایدار می‌تواند باقی بماند و اجرای بعدی را آلوده کند؛ publish هم‌زمان DOCX و media اتمیک نیست.

**برنامهٔ اصلاح:** staging یکتا، publish اتمیک، rollback در شکست و تست crash در هر مرحله. media قبلی نباید بدون policy صریح overwrite یا reuse شود.

## کیفیت خروجی و قراردادها

### R3-06 — اعتبارسنجی بصری RTL/تصاویر هنوز ناکافی است (P1)

تست‌ها عمدتاً XPath هستند و وجود تصویر را می‌سنجند، اما ترتیب بصری badge/جدول، جای تصویر، اندازه‌گذاری، page break و خوانایی Mermaid در Word/LibreOffice اثبات نشده است.

**برنامهٔ اصلاح:** DOCXهای golden را به PDF/PNG render کنید و checks بصری/دستی برای RTL، تصاویر standalone/inline، caption، table و Mermaid اضافه کنید. معیار اندازهٔ تصویر و fallback فونت را ثبت کنید.

### R3-07 — محدودیت‌های محیط و اجرای تست باید شفاف‌تر شود (P2)

اجرای `pytest` از PATH سیستم به interpreter حذف‌شده اشاره می‌کند و فقط `.venv/bin/pytest` سالم است. یک تست skip نیز می‌تواند به‌علت تفاوت محیطی پنهان شود.

**برنامهٔ اصلاح:** README/CI را به `python -m pytest` از محیط ساخته‌شده مقید کنید، smoke install از صفر اجرا کنید و گزارش skipها را در CI قابل مشاهده نگه دارید.

## ترتیب اجرا

1. R3-01 و R3-05 برای اثبات و پایدارسازی Mermaid.
2. R3-02 تا R3-04 برای تصاویر، Markdown و code highlighting.
3. R3-06 و R3-07 برای پذیرش بصری و reproducibility.

هر مورد باید با تست قرمز آغاز شود و پس از اصلاح، unit، integration و در موارد DOCX/RTL، بررسی PDF/PNG اجرا شود. این فایل فقط برنامهٔ اصلاح است؛ هیچ کدی در این بازبینی تغییر نکرده است.
