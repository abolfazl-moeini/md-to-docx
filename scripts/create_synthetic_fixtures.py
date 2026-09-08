#!/usr/bin/env python3
"""
Create synthetic test fixtures S01 to S16 for Persian layout quality testing.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYN_DIR = ROOT / "tests" / "fixtures" / "persian_layout" / "synthetic"
SYN_DIR.mkdir(parents=True, exist_ok=True)

# S01: Mixed text with brackets, quotes, percentage, date, IP, URL, domain, Windows paths
S01 = """---
lang: fa-IR
dir: rtl
---

# بررسی جامع متن دوزبانه و فنی در محیط SQL Server

این سند برای بررسی رفتارهای متن مخلوط (Mixed-Direction Text) در زبان فارسی آماده شده است. هنگامی که یک مدیر پایگاه داده (Database Administrator) متنی فنی می‌نویسد، عبارات انگلیسی مانند **SQL Server Management Studio (SSMS)** یا عبارت‌های چندکلمه‌ای نظیر *Always On Availability Groups* به وفور در میان جملات فارسی ظاهر می‌شوند.

مسیرهای پیش‌فرض نصب در ویندوز مانند `C:\\Program Files\\Microsoft SQL Server\\MSSQL16.MSSQLSERVER\\MSSQL\\DATA` و مسیرهای داده در درایو `D:\\SQLData` باید بدون وارونگی بک‌اسلش یا تغییر جهت نویسه‌ها نمایش داده شوند.

سرور هدف در این سناریو دارای آدرس شبکه `192.168.1.100:1433` در دامنهٔ سازمانی `corp.local` است و نسخهٔ نصب‌شده بر روی کلاستر `SQLPROD01\\REPORTING` قرار دارد. نرخ رشد سالانه ۲۵٪ (یا 25%) محاسبه شده و تاریخ بازبینی پیکربندی در روز ۱۴۰۳/۰۶/۱۷ ثبت گردیده است.

اصطلاحاتی نظیر «تراکنش‌های توزیع‌شده» (Distributed Transactions) و مفاهیم حافظه مانند (Buffer Pool Extension) باید پرانتزها و گیومه‌های خود را در سمت صحیح متن فارسی حفظ کنند. برای اطلاعات تکمیلی می‌توانید به [مستندات رسمی مایکروسافت](https://learn.microsoft.com/sql) مراجعه فرمایید.
"""

# S02: Headings 1-6, Persian/Arabic/Latin digits, bookmarks, multiline heading
S02 = """---
lang: fa-IR
dir: rtl
---

# فصل اول: راهنمای جامع معماری و ذخیره‌سازی داده {#ch1-intro}

این فصل به بررسی معماری لایه‌ای می‌پردازد. می‌توانید برای مراجعه به بخش‌های بعدی از لینک‌های داخلی استفاده کنید:
- [مراجعه به مبانی پایه](#sec-basics)
- [مراجعه به ساختار پیج‌ها](#sec-pages)

## ۱.۱ مبانی پایه و ساختار پردازش کوئری {#sec-basics}

در این بخش، جریان اجرای دستورات در موتور رابطه بررسی می‌شود.

### ۱.۱.۱ بررسی ساختار Data Pageها در حافظه و دیسک {#sec-pages}

هر پیج داده دارای اندازهٔ دقیق ۸ کیلوبایت است.

#### ۱.۱.۱.۱ جزئیات فیزیکی سرفصل صفحه (Page Header)

سرفصل صفحه حاوی ۹۶ بایت اطلاعات مدیریتی است.

##### ۱.۱.۱.۱.۱ بایت‌های کنترلی Slot Array در انتهای صفحه

آرایهٔ اسلات تعیین‌کنندهٔ آفست رکوردهای داده در صفحه است.

###### ۱.۱.۱.۱.۱.۱ فلگ‌های وضعیت رکورد و تخصیص فضا در حافظه

وضعیت رکورد مشخص می‌کند که آیا داده از نوع متغیر است یا ثابت.

# این یک عنوان بسیار طولانی سطح یک است که برای آزمون رفتار شکست چندخطی تیتر در سند بدون پوشانده شدن بج شماره یا خروج متن از حاشیه صفحه و رعایت فاصله از پاراگراف بعدی طراحی شده است {#long-heading}

متن پاراگراف پس از عنوان طولانی برای بررسی فاصله‌گذاری و عدم تداخل بصری.
"""

# S03: All six custom-styles, class-based callouts, nested divs, literal code
S03 = """---
lang: fa-IR
dir: rtl
---

# بررسی رفتارهای شش استایل سفارشی و کادرهای اعلان

::: {custom-style="Chapter Overview"}
در این فصل • ساختار معماری پایگاه داده • نحوه مدیریت منابع پردازنده و حافظه • تفکیک دسترسی‌های ورود و پایگاه داده • راهکارهای نگه‌داری و بهینه‌سازی عملکرد مورد بحث قرار می‌گیرند.
:::

متن عادی میان کادرها برای تفکیک بخش‌ها.

::: {custom-style="DBA Note"}
نکتهٔ DBA اتصال کاربران همواره باید از طریق کانال‌های رمزنگاری‌شده با گواهی دیجیتال معتبر صورت پذیرد و پورت پیش‌فرض ۱۴۳۳ در محیط‌های عمومی مسدود باشد.
:::

::: {custom-style="Important Note"}
توجه مهم: پیش از اعمال هرگونه تغییر بر روی پارامترهای سرور در محیط عملیاتی، حتماً نسخهٔ پشتیبان کامل از دیتابیس master تهیه فرمایید.
:::

::: {custom-style="Warning"}
هشدار امنیتی: استفاده از حساب کاربری sa در زنجیرهٔ اتصال نرم‌افزارهای کاربردی خطری بحرانی محسوب می‌شود.
:::

::: {custom-style="Lab Note"}
یادداشت تمرین: این سناریو را ابتدا در محیط آزمایشی (Lab) با حداقل دو ماشین مجازی پیاده‌سازی و رفتار Failover را بسنجید.
:::

::: {custom-style="Screenshot Recommendation"}
پیشنهاد تصویر: از پنجرهٔ پیکربندی حافظه در Server Properties تصویر تهیه کنید تا حد Max Server Memory مستند باشد.
:::

::: note
این یک کادر اعلان مبتنی بر کلاس استاندارد note است.
:::

::: warning
این یک کادر هشدار مبتنی بر کلاس استاندارد warning است.
:::

::: note
کادر اعلان تودرتو - سطح بیرونی
::: warning
کادر هشدار تودرتو - سطح درونی
:::
:::

کد زیر نحوه نوشتن اعلان‌ها را نشان می‌دهد و نباید تبدیل به کادر واقعی شود:

```markdown
::: {custom-style="DBA Note"}
این یک کد نمونه است و نباید به کادر Word تبدیل شود.
:::
```
"""

# S04: Lists: bullet, ordered, start != 1, roman/alpha, tight/loose, 3-level nesting, English item
S04 = """---
lang: fa-IR
dir: rtl
---

# راهنمای چک‌لیست و بررسی فهرست‌های چندسطحی

در زیر چک‌لیست اقدامات اولیه ارائه شده است:

* اقدامات پیش از نصب سیستم‌عامل
    * بررسی نیازمندی‌های سخت‌افزاری سرور
        * تعداد Coreهای فیزیکی پردازنده
        * میزان حافظه RAM با قابلیت ECC
    * تنظیمات BIOS و Firmware سرور
* پیکربندی لایه مجازی‌سازی
    * تنظیمات کارت شبکه مجازی
    * Windows Server Failover Clustering (WSFC)
* نصب و راه‌اندازی پایگاه داده

فهرست ترتیبی با شروع از عدد پنج:

5. مرحلهٔ پنجم: اعمال آخرین Cumulative Update (CU)
6. مرحلهٔ ششم: تنظیم Service Accountها با دسترسی‌های حداقل
7. مرحلهٔ هفتم: راه‌اندازی مکانیزم پایش (Monitoring)

فهرست با حروف الفبای انگلیسی:

a. مرحله اولیه تست ارتباط شبکه
b. مرحله اعتبارسنجی پورت‌های باز
c. مرحله نهایی پذیرش سرویس

متن حاوی نشانه‌های گلوله‌ای درون نثر:
در این روش • ابتدا لاگ ثبت می‌شود • سپس داده‌ها در بافر نوشته می‌شوند • و در نهایت تغییرات اعمال می‌گردند.
"""

# S05: Tables: 2, 3, 6-col, 60+ rows
def build_s05():
    lines = [
        "---",
        "lang: fa-IR",
        "dir: rtl",
        "---",
        "",
        "# جداول داده، مشخصات سیستم و پارامترهای پایگاه داده",
        "",
        "## جدول دو ستونی",
        "",
        "| نام مؤلفه | مسیر پیشنهادی |",
        "| :--- | :--- |",
        "| فایل داده اصلی | `D:\\SQLData\\master.mdf` |",
        "| فایل لاگ تراکنش | `L:\\SQLLog\\mastlog.ldf` |",
        "",
        "## جدول سه ستونی",
        "",
        "| پارامتر | مقدار پیش‌فرض | توضیحات فنی |",
        "| :--- | :--- | :--- |",
        "| Max Server Memory | ۲۱۴۷۴۸۳۶۴۷ مگابایت | باید بر اساس فرمول سیستم‌عامل محدود شود |",
        "| Cost Threshold for Parallelism | ۵ | برای سیستم‌های OLTP مدرن به ۵۰ افزایش یابد |",
        "| Max Degree of Parallelism | ۰ | بر اساس تعداد Coreهای هر NUMA Node تنظیم شود |",
        "",
        "## جدول شش ستونی با ۶۲ ردیف",
        "",
        "| شناسه | نام دیتابیس | وضعیت | تعداد فایل | حجم (GB) | مدل بازیابی |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for i in range(1, 63):
        lines.append(f"| {i} | DB_Production_{i:02d} | Online | {2 + (i % 3)} | {10.5 * i:.1f} | Full |")
    return "\n".join(lines) + "\n"

S05 = build_s05()

# S06: Nested structures: table in callout, list/code/image in cell, blockquote
S06 = """---
lang: fa-IR
dir: rtl
---

# ساختارهای تودرتو و ترکیبی در اسناد فنی

::: note
در زیر جدول خلاصه وضعیت درون کادر یادداشت قرار گرفته است:

| سرویس | پورت | وضعیت |
| :--- | :--- | :--- |
| SQL Database Engine | ۱۴۳۳ | در حال اجرا |
| SQL Server Agent | - | متوقف |
:::

> نقل‌قول مهم از مدیر ارشد پایگاه داده:
> همواره باید اصل حداقل اختیارات (Principle of Least Privilege) در تمامی اجزای سیستم رعایت شود.
> 
> ```sql
> DENY ALTER ANY LOGIN TO [AppUser];
> ```

جدول حاوی لیست و کد در سلول:

| بخش | توضیحات و دستورات |
| :--- | :--- |
| تنظیمات اولیه | دستور پیکربندی: `sp_configure 'show advanced options', 1;` |
| نیازمندی‌ها | * دسترسی sysadmin<br>* راه‌اندازی مجدد سرویس |
"""

# S07: Code blocks: SQL, PowerShell, Console, Python, text, long line
S07 = """---
lang: fa-IR
dir: rtl
---

# اسکریپت‌ها و کدهای فنی با رنگ‌بندی نحوی

## اسکریپت T-SQL

```sql
-- بررسی جلسات کاری فعال و جزئیات مصرف منابع پردازنده
SELECT 
    session_id,
    login_name,
    status,
    cpu_time,
    total_elapsed_time
FROM sys.dm_exec_sessions
WHERE is_user_process = 1
ORDER BY cpu_time DESC;
```

## اسکریپت PowerShell

```powershell
# بررسی وضعیت سرویس‌های مرتبط با SQL Server در سرور محلی
Get-Service -Name "MSSQL*" | Select-Object -Property Name, DisplayName, Status | Format-Table -AutoSize
```

## دستور خط فرمان (Console)

```console
netstat -ano | findstr :1433
sqlcmd -S SQLPROD01 -E -Q "SELECT @@VERSION;"
```

## اسکریپت Python

```python
# اسکریپت پایش و اتصال به دیتابیس
import pyodbc

conn_str = "Driver={ODBC Driver 18 for SQL Server};Server=SQLPROD01;Database=master;Trusted_Connection=yes;"
print("Connecting to SQL Server instance...")
```

## دستور تک‌خطی بسیار بلند (بیش از ۱۹۰ نویسه)

```sql
SELECT [SessionID], [LoginName], [HostName], [ProgramName], [DatabaseName], [Command], [CPU_Time_MS], [Total_Elapsed_Time_MS], [Reads], [Writes], [LogicalReads], [Status] FROM [sys].[dm_exec_sessions] WHERE [is_user_process] = 1;
```
"""

# S08: Long code block (2+ pages) and ASCII tree
def build_s08():
    lines = [
        "---",
        "lang: fa-IR",
        "dir: rtl",
        "---",
        "",
        "# اسکریپت بلند پایگاه داده و ساختار درختی فایل‌ها",
        "",
        "## ساختار درختی پوشه‌ها و فایل‌های دیتابیس",
        "",
        "```text",
        "D:\\SQLData\\",
        "├── Primary_Data.mdf",
        "├── Secondary_Data_1.ndf",
        "│   ├── Partitions_2024.ndf",
        "│   └── Partitions_2025.ndf",
        "└── Logs\\",
        "    └── Transaction_Log.ldf",
        "```",
        "",
        "## اسکریپت جامع نگه‌داری ایندکس‌ها (بیش از ۱۰۰ خط)",
        "",
        "```sql",
        "-- اسکریپت جامع دیفرگمنت و بازسازی ایندکس‌ها",
    ]
    for i in range(1, 105):
        lines.append(f"EXEC dbo.sp_MaintainIndex @DatabaseID = {i}, @FragmentationThreshold = 30.0, @LogOutput = 1; -- گام عملیاتی شماره {i}")
    lines.append("```")
    return "\n".join(lines) + "\n"

S08 = build_s08()

# S09: Real images: horizontal, vertical, transparent, with spaces, persian name, captions
S09 = """---
lang: fa-IR
dir: rtl
---

# تصاویر و نمودارهای معماری پایگاه داده

در این بخش انواع تصاویر با ابعاد و فرمت‌های مختلف آزمایش می‌شوند.

![نمودار افقی معماری SQL Server](../assets/horizontal_sample.png)
شکل ۱-۱. نمای افقی مؤلفه‌های سرور و اتصالات شبکه

![سلسله‌مراتب عمودی لایه‌های حافظه](../assets/vertical_sample.png)
شکل ۱-۲. معماری عمودی ساختار بافر و سلسله‌مراتب دسترسی

![نشان شفاف سیستم](../assets/transparent_sample.png)

![تصویر با فاصله در نام](../assets/sample%20with%20spaces.png)

![تصویر با نام فارسی](../assets/تصویر_نمونه_فارسی.png)
"""

# S10: Mermaid Flowchart TB & LR with Persian/Latin labels
S10 = """---
lang: fa-IR
dir: rtl
---

# نمودارهای جریان فرآیندها (Mermaid Flowchart)

## دیاگرام افقی جریان پردازش کوئری

```mermaid
flowchart LR
    A[درخواست کلاینت / Client Request] -->|ارسال کوئری| B[پردازشگر پرس‌وجو / Query Processor]
    B -->|تولید پلن اجرایی| C[موتور ذخیره‌سازی / Storage Engine]
    C -->|بررسی بافر| D[Buffer Pool]
    D -->|واکشی داده| E[VMware ESXi Hypervisor]
    E -->|دسترسی به دیسک| F[Physical Storage Device]
```
شکل ۲-۱. مسیر جریان داده از کلاینت تا دیسک فیزیکی

## دیاگرام عمودی لایه‌های امنیتی

```mermaid
flowchart TB
    A[کاربر نهایی] --> B[احراز هویت در سطح ویندوز]
    B --> C[بررسی لاگین در سطح Instance]
    C --> D[بررسی نقش‌ها و دسترسی به Database]
    D --> E[اجازه خواندن و نوشتن جداول]
```
شکل ۲-۲. لایه‌های سلسله‌مراتبی امنیت و دسترسی
"""

# S11: Mermaid Sequence, State, ER diagrams
S11 = """---
lang: fa-IR
dir: rtl
---

# نمودارهای پیشرفته توالی، وضعیت و موجودیت-رابطه

## نمودار توالی ثبت تراکنش در Transaction Log

```mermaid
sequenceDiagram
    autonumber
    actor Client as کلاینت
    participant Engine as موتور دیتابیس
    participant BP as بافر پول
    participant Log as لاگ تراکنش

    Client->>Engine: ارسال دستور INSERT
    Engine->>BP: نوشتن رکورد در پیج حافظه (Dirty Page)
    Engine->>Log: ثبت رکورد تراکنش در فایل لاگ (WAL)
    Log-->>Engine: تأیید ثبت فیزیکی بر روی دیسک
    Engine-->>Client: ارسال پیام موفقیت تراکنش
```

## نمودار وضعیت چرخه حیات تراکنش

```mermaid
stateDiagram-v2
    [*] --> فعال: شروع تراکنش
    فعال --> آماده_تعهد: پایان دستورات
    آماده_تعهد --> متعهد: نوشتن در لاگ
    فعال --> لغو_شده: بروز خطا در اجرا
    آماده_تعهد --> لغو_شده: خطای سیستم
    متعهد --> [*]
    لغو_شده --> [*]
```

## نمودار موجودیت-رابطه (ER Diagram)

```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEM : contains
    CUSTOMER {
        int CustomerID PK
        string FullName
        string EmailAddress
    }
    ORDER {
        int OrderID PK
        int CustomerID FK
        date OrderDate
        decimal TotalAmount
    }
```
"""

# S12: Mermaid & Image nested in list, quote, div, footnote
S12 = """---
lang: fa-IR
dir: rtl
---

# دیاگرام‌ها و تصاویر در ظروف تودرتو

::: note
دیاگرام درون کادر اعلان:

```mermaid
flowchart LR
    A[ورودی یادداشت] --> B[پردازش داخلی]
    B --> C[خروجی اعلان]
```
:::

> نقل‌قول حاوی تصویر:
> ![نشان سیستم](../assets/logo.png)
> تصویر کوچک در بالا نمونه‌ای از جاسازی دارایی در بلوک نقل‌قول است.

فهرست حاوی دیاگرام:

* مرحله اول: دریافت درخواست
* مرحله دوم: بررسی گرافیکی فرآیند:
  ```mermaid
  flowchart LR
      X[شروع بررسی] --> Y[تأیید مجوز]
  ```
* مرحله سوم: تکمیل فرآیند
"""

# S13: Footnotes, Links, Rich Formatting, Math
S13 = """---
lang: fa-IR
dir: rtl
---

# پاورقی‌های پیشرفته، فرمول‌های ریاضی و پیوندها

مدیریت حافظه در SQL Server نیازمند محاسبه دقیق فضای کاری است[^mem_calc]. همچنین برای پایش لاگ‌ها باید نرخ رشد تراکنش‌ها را محاسبه نمود[^trans_rate].

فرمول محاسبه اندازه کل بافر در مدل ریاضی به صورت $E = mc^2$ یا رابطه زیر تعریف می‌شود:

$$\\sum_{i=1}^{n} X_i = \\frac{n(n+1)}{2}$$

فرمول کسر و توان در محاسبات دیتابیس:

$$Memory_{allocated} = \\frac{RAM_{total} - OS_{reserved}}{Num_{instances}}$$

برای کسب اطلاعات بیشتر به [سایت مایکروسافت](https://learn.microsoft.com) مراجعه فرمایید.

[^mem_calc]: این یک پاورقی چندپاراگرافی است. در این پاراگراف اول مفاهیم اولیه تشریح شده است.

    پاراگراف دوم پاورقی شامل جزئیات بیشتر و پیوند به مستندات رسمی مایکروسافت می‌باشد.

[^trans_rate]: نرخ تولید لاگ بر حسب مگابایت بر ثانیه محاسبه می‌شود.
"""

# S14: Page boundaries stress test
S14 = """---
lang: fa-IR
dir: rtl
---

# آزمون مرزهای صفحه و شکست کنترل‌شده

این بخش برای بررسی رفتار شکست صفحه قبل از تیترها و کادرها طراحی شده است.

پاراگراف اول با متنی که بخشی از فضای صفحه را پر می‌کند تا عنصر بعدی درست در نزدیکی انتهای صفحه قرار گیرد. این پاراگراف شامل توضیحات پیرامون نگه‌داری ایندکس‌ها و لزوم بازسازی منظم آنها برای جلوگیری از قطعه‌قطعه شدن حافظه است.

پاراگراف دوم برای افزایش ارتفاع محتوا پیش از رسیدن به جدول یا کادر اعلان بعدی. عملکرد مناسب در شرایط مرزی صفحه نشان‌دهندهٔ عملکرد صحیح قواعد keepNext در موتور رندر است.

::: {custom-style="DBA Note"}
نکتهٔ DBA در انتهای صفحه: این کادر باید به صورت یکپارچه با سرفصل و بدنه در صفحه نمایش داده شود و سرفصل به تنهایی در انتهای صفحه رها نگردد.
:::

## تیتر نزدیک به مرز صفحه

این تیتر نباید بدون حداقل دو خط از پاراگراف بعدی خود در انتهای صفحه قرار گیرد (جلوگیری از ایجاد تیتر یتیم).

| ردیف | نام سرویس | وضعیت |
| :--- | :--- | :--- |
| ۱ | SQL Engine | فعال |
| ۲ | SQL Agent | فعال |
| ۳ | SQL Browser | متوقف |
"""

# S15: Document Shell, TOC, Headings, Internal References
S15 = """---
title: راهنمای جامع مدیریت پایگاه داده
author: تیم راهبری داده‌ها
lang: fa-IR
dir: rtl
---

# فهرست مطالب

<!-- Pandoc generates the final table of contents with --toc. -->

# فصل اول: معماری سرور پایگاه داده {#ch-arch}

معماری اولیه در این بخش تشریح شده است. برای مشاهده پیکربندی به [فصل دوم](#ch-config) بروید.

# فصل دوم: پیکربندی و راه‌اندازی سرویس {#ch-config}

تنظیمات پیشرفته سرور در این بخش قرار دارد.

# فصل سوم: بهینه‌سازی و خطایابی {#ch-tuning}

راهکارهای پایش کارایی و شناسایی گلوگاه‌ها.

# پیوست: پرس‌وجوهای پرکاربرد {#ch-appendix}

پرس‌وجوهای مفید برای عیب‌یابی سریع.
"""

# S16: Comprehensive Persian Booklet (> 10 pages equivalent)
def build_s16():
    parts = [
        "---",
        "title: کتابچه راهنمای جامع مدیران پایگاه داده SQL Server",
        "author: دپارتمان فناوری اطلاعات و زیرساخت داده",
        "lang: fa-IR",
        "dir: rtl",
        "---",
        "",
        "# پیش‌گفتار و راهنمای مطالعه",
        "",
        "این کتابچه راهنمای عملیاتی جامع برای مدیران پایگاه داده (DBA) است که تمامی مفاهیم از نصب و پیکربندی اولیه تا پایش و نگه‌داری را پوشش می‌دهد.",
        "",
        "::: {custom-style=\"Chapter Overview\"}",
        "در این سند راهنما • ساختار پایگاه داده و فایل‌ها • پیکربندی بهینه سخت‌افزار • تنظیمات امنیتی لاگین‌ها • دستورات پایش کارایی مورد بررسی قرار گرفته است.",
        ":::",
        "",
        "## ۱. مفاهیم پایه و معماری حافظه",
        "",
        "موتور رابطه (Relational Engine) و موتور ذخیره‌سازی (Storage Engine) دو بخش اساسی در پردازش درخواست‌ها هستند.",
        "",
        "![معماری افقی](../assets/horizontal_sample.png)",
        "شکل ۱-۱. معماری درونی موتور پایگاه داده",
        "",
        "```mermaid",
        "flowchart LR",
        "    A[درخواست کلاینت] --> B[موتور پردازش کوئری]",
        "    B --> C[موتور ذخیره‌سازی]",
        "    C --> D[بافر پول / حافظه]",
        "    D --> E[فایل‌های فیزیکی دیسک]",
        "```",
        "شکل ۱-۲. دیاگرام جریان درخواست‌ها در لایه‌های مختلف",
        "",
        "::: {custom-style=\"DBA Note\"}",
        "نکتهٔ DBA در خصوص حافظه: همواره سقف Max Server Memory را مشخص کنید تا سیستم‌عامل دچار کمبود حافظه نگردد.",
        ":::",
        "",
        "## ۲. پارامترهای پیکربندی سرور",
        "",
        "| ردیف | نام پارامتر | مقدار پیشنهادی | ضرورت |",
        "| :--- | :--- | :--- | :--- |",
        "| ۱ | Max Server Memory | محاسبه بر اساس فرمول | الزامی |",
        "| ۲ | Cost Threshold for Parallelism | ۵۰ | پیشنهادی |",
        "| ۳ | Max Degree of Parallelism | بر اساس Core | الزامی |",
        "| ۴ | Backup Compression Default | ۱ (فعال) | پیشنهادی |",
        "| ۵ | Remote Admin Connections | ۱ (فعال) | الزامی |",
        "",
        "## ۳. اسکریپت‌های مدیریت و نگه‌داری",
        "",
        "```sql",
        "-- استخراج مشخصات دیتابیس‌ها و فایل‌های آنها",
        "SELECT ",
        "    d.name AS DatabaseName,",
        "    f.name AS LogicalFileName,",
        "    f.physical_name AS PhysicalFilePath,",
        "    f.size * 8 / 1024 AS SizeMB",
        "FROM sys.databases d",
        "JOIN sys.master_files f ON d.database_id = f.database_id;",
        "```",
        "",
        "## ۴. دستورالعمل‌های تکمیلی و سناریوهای پایش",
        "",
        "چک‌لیست بررسی دوره‌ای:",
        "* بررسی لاگ‌های خطا (SQL Server Error Logs)",
        "* پایش فضای خالی دیسک‌ها",
        "* بررسی اجرای موفق کارهای زمان‌بندی‌شده (Agent Jobs)",
        "* بررسی شاخص‌های تکه‌تکه‌شدگی ایندکس‌ها",
        "",
        "::: {custom-style=\"Important Note\"}",
        "توجه مهم: گزارشات هفتگی باید توسط مدیر سیستم تأیید و مستندات به‌روزرسانی شوند.",
        ":::",
        "",
    ]
    for sec_idx in range(5, 16):
        parts.extend([
            f"## {sec_idx}. بخش تخصصی شماره {sec_idx}: مستندات تکمیلی عملیات",
            "",
            f"در این بخش جزئیات تکمیلی عملیات نگه‌داری سطح {sec_idx} ارائه می‌شود. مفاهیم امنیتی و پیکربندی شبکه در این مرحله دارای اهمیت اساسی هستند.",
            "",
            "::: {custom-style=\"DBA Note\"}",
            f"نکتهٔ DBA در بخش {sec_idx}: کلیه اتصالات باید رمزنگاری TLS 1.3 داشته باشند.",
            ":::",
            "",
            "```sql",
            f"-- بررسی وضعیت سلامت دیتابیس شماره {sec_idx}",
            f"DBCC CHECKDB (N'Production_DB_{sec_idx}') WITH NO_INFOMSGS, ALL_ERRORMSGS;",
            "```",
            "",
            "| مؤلفه | مقدار کنونی | مقدار هدف | وضعیت |",
            "| :--- | :--- | :--- | :--- |",
            f"| CPU Utilization | {20 + sec_idx}% | < 70% | مناسب |",
            f"| Memory Usage | {40 + sec_idx}% | < 85% | مناسب |",
            f"| Disk IO Latency | {sec_idx} ms | < 15 ms | عالی |",
            "",
        ])
    return "\n".join(parts) + "\n"

S16 = build_s16()

ALL_SYN = {
    "S01": S01,
    "S02": S02,
    "S03": S03,
    "S04": S04,
    "S05": S05,
    "S06": S06,
    "S07": S07,
    "S08": S08,
    "S09": S09,
    "S10": S10,
    "S11": S11,
    "S12": S12,
    "S13": S13,
    "S14": S14,
    "S15": S15,
    "S16": S16,
}


def main():
    for sid, content in ALL_SYN.items():
        p = SYN_DIR / f"{sid}.md"
        p.write_text(content.strip() + "\n", encoding="utf-8")
        print(f"Wrote {p.name} ({len(content)} chars)")


if __name__ == "__main__":
    main()
