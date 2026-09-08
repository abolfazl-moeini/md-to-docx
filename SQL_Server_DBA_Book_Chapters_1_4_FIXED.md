---
lang: fa-IR
dir: rtl
---

<!-- Pandoc generates the final table of contents with --toc. -->
# فصل اول — آشنایی با SQL Server و معماری پایه

این فصل قرار است یک نقشهٔ ذهنی بسازد. پیش از آن‌که وارد Backup (نسخهٔ پشتیبان)، Monitoring (پایش)، Index Maintenance (نگه‌داری ایندکس) یا Troubleshooting (عیب‌یابی) شویم، باید بدانیم SQL Server از چه اجزایی تشکیل شده است، مرز میان Instance و Database کجاست و چرا Memory (حافظه) و Storage (فضای ذخیره‌سازی) برای یک DBA اهمیت دارند.

::: {custom-style="Chapter Overview"}
در این فصل •  مرزهای مدیریتی SQL Server؛ از Instance تا Database •  نقش Database Engine و SQL Server Agent در کنار پایگاه‌های دادهٔ سیستمی •  مدل ذهنی هویت و دسترسی با Login و User •  Editionها و تفاوت محیط‌های عملیاتی، توسعه و Lab •  مسیر کلی داده از Buffer Pool تا Storage
:::

## ۱.۱ SQL Server چیست؟

در محیط کاری، عبارت «SQL Server» گاهی با چند معنی متفاوت استفاده می‌شود. ممکن است کسی بگوید «SQL Server قطع شده است» و منظورش توقف سرویس Database Engine باشد. فرد دیگری بگوید «اطلاعات فروش در SQL Server است» و در عمل دربارهٔ یک Database مشخص صحبت کند. برای یک DBA این تفاوت فقط بحث واژه‌ها نیست، چون هرکدام دامنهٔ مدیریتی متفاوتی دارند.

Microsoft SQL Server یک سیستم مدیریت پایگاه دادهٔ رابطه‌ای است. مهم‌ترین بخش آن، Database Engine (موتور پایگاه داده)، Queryها (پرس‌وجوها) را دریافت و اجرا می‌کند، داده را در Databaseها نگه می‌دارد، Transactionها (تراکنش‌ها) را مدیریت می‌کند، دسترسی‌ها را کنترل می‌کند و برای خواندن و نوشتن داده با Memory (حافظه) و Storage (فضای ذخیره‌سازی) در ارتباط است.

پس SQL Server را نباید فقط «نرم‌افزاری برای ساخت Table» در نظر گرفت. از دید DBA، SQL Server یک سرویس سازمانی است که باید قابل دسترس، امن، قابل بازیابی و قابل پایش باشد. اگر Application پاسخ نمی‌گیرد، اگر Disk در حال پر شدن است یا اگر Backup چند روز است اجرا نشده، همهٔ این‌ها بخشی از مسئلهٔ مدیریت SQL Server هستند.

::: {custom-style="DBA Note"}
نکتهٔ DBA در این کتاب هرجا از «SQL Server» صحبت می‌کنیم، سعی می‌کنیم دقیق مشخص کنیم منظور Product (محصول)، Instance (نمونهٔ مستقل)، Service (سرویس) یا Database است. این عادت در Troubleshooting (عیب‌یابی) جلوی بسیاری از ابهام‌ها را می‌گیرد.
:::

### ۱.۱.۱ یک Query ساده، یک مسیر بزرگ‌تر

وقتی یک Application یا SSMS دستور زیر را اجرا می‌کند، چیزی که کاربر می‌بیند فقط یک نتیجه است:

**فرمان SQL**

```sql
SELECT CustomerID, CustomerName, City FROM dbo.Customers WHERE City = 'Tehran';
```

اما در پشت صحنه، Database Engine باید Connection (اتصال) را بپذیرد، Permission (مجوز دسترسی) را بررسی کند، Query را پردازش کند، Data Pageهای (صفحه‌های دادهٔ) موردنیاز را در Memory یا Storage پیدا کند و نتیجه را برگرداند. در فصل اول وارد جزئیات Query Processor (پردازشگر Query) یا Execution Plan (طرح اجرا) نمی‌شویم. فعلاً کافی است بدانیم یک Query از مجموعه‌ای از اجزای داخلی SQL Server عبور می‌کند و عملکرد آن تنها به متن دستور بستگی ندارد.

::: {custom-style="Important Note"}
SQL Server برای DBA یک «سیستم» است، نه فقط یک محل برای اجرای Query.
:::

## ۱.۲ مفاهیم پایهٔ مدیریت پایگاه داده

سه اصطلاح Database، DBMS و RDBMS در ابتدای مسیر شبیه هم به نظر می‌رسند، اما نقش یکسانی ندارند. اگر این تفاوت روشن باشد، بخش‌های بعدی کتاب بسیار ساده‌تر فهمیده می‌شوند.

### ۱.۲.۱ Database چیست؟

Database مجموعه‌ای سازمان‌یافته از داده‌ها و Objectهای مرتبط است. برای مثال، یک سامانهٔ فروش ممکن است اطلاعات مشتریان، محصولات، سفارش‌ها و پرداخت‌ها را در یک Database نگه دارد. در مدل رابطه‌ای، بخش زیادی از داده‌ها در Tableها قرار می‌گیرند و Tableها از Row و Column تشکیل می‌شوند.

| CustomerID | CustomerName | City |
|---|---|---|
| 101 | Masoud Taheri | Tehran |
| 102 | Niloofar Karimi | Shiraz |
| 103 | Amir Hosseini | Isfahan |

این جدول نمای منطقی داده است. SQL Server در Storage، Table را به‌شکل یک فایل متنی یا یک Sheet ساده ذخیره نمی‌کند. در لایهٔ پایین‌تر، داده در Fileها و Pageها مدیریت می‌شود. جزئیات Page و Allocation در فصل‌های بعدی مطرح می‌شود؛ در این فصل فقط رابطهٔ کلی را می‌سازیم.

### ۱.۲.۲ DBMS چیست؟

Database Management System (DBMS) نرم‌افزاری است که Database را مدیریت می‌کند. DBMS مسئول کارهایی مانند ذخیره و بازیابی داده، کنترل هم‌زمانی، مدیریت Transaction، اعمال Security و فراهم‌کردن سازوکار Backup و Recovery است.

اگر داده‌ها فقط در فایل‌های معمولی قرار داشتند، Application باید خودش حل می‌کرد که دو کاربر هم‌زمان چگونه یک رکورد را تغییر دهند، چه کسی اجازهٔ مشاهدهٔ اطلاعات را دارد و پس از Crash چگونه داده به وضعیت سازگار برگردد. DBMS این مسئولیت‌ها را در یک Engine تخصصی متمرکز می‌کند.

### ۱.۲.۳ RDBMS چیست؟

Relational Database Management System (RDBMS) نوعی DBMS است که بر مدل رابطه‌ای تکیه دارد. داده‌ها معمولاً در Tableهای مرتبط قرار می‌گیرند و ارتباط آن‌ها با Keyها و Constraintها مدیریت می‌شود. SQL Server در این دسته قرار می‌گیرد و زبان اصلی کار با Database Engine آن Transact-SQL (T-SQL) است.

::: {custom-style="Important Note"}
نکتهٔ مهم Database خود داده و ساختارهای مرتبط را در بر می‌گیرد؛ DBMS نرم‌افزاری است که آن Database را مدیریت می‌کند. SQL Server یک RDBMS است و هر SQL Server Instance می‌تواند چندین Database را مدیریت کند.
:::

## ۱.۳ مرزهای مدیریتی در SQL Server

این بخش یکی از پایه‌ای‌ترین قسمت‌های کتاب است. بسیاری از تنظیمات، Permissionها و عملیات DBA یا در سطح Instance انجام می‌شوند یا در سطح Database. اگر این مرز در ذهن روشن نباشد، بعداً مفاهیمی مانند Login، User، Backup، Job و Server Configuration با هم مخلوط می‌شوند.

### ۱.۳.۱ مفهوم Instance در SQL Server

یک Database Engine Instance (نمونهٔ مستقل موتور پایگاه داده) روی سیستم‌عامل اجرا می‌شود. هر Instance مجموعهٔ Databaseها، Loginها و تنظیمات Server-level (سطح Server) خودش را دارد. روی یک Windows Server می‌توان یک یا چند Instance نصب کرد، هرچند چند Instance روی یک Host (میزبان) همچنان CPU، RAM و Storage زیرساخت را با یکدیگر به اشتراک می‌گذارند.

یک Instance می‌تواند Default Instance (Instance پیش‌فرض) یا Named Instance (Instance نام‌دار) باشد. Default Instance هنگام Connection با نام Computer قابل دسترسی است و نام Instance جداگانه‌ای در Connection String (رشتهٔ اتصال) وارد نمی‌شود. Named Instance نام مشخصی دارد و معمولاً به‌شکل ServerName\InstanceName استفاده می‌شود.

::: {custom-style="Important Note"}
مثال SQLPROD01 می‌تواند اتصال به Default Instance باشد. SQLPROD01\REPORTING می‌تواند اتصال به یک Named Instance باشد.
:::

### ۱.۳.۲ Database

Database داخل Instance قرار می‌گیرد. هر Database مجموعه‌ای از Objectها مانند Table، View، Stored Procedure و Schema دارد و فایل‌های فیزیکی خودش را روی Storage نگه می‌دارد. عملیاتی مانند Full Backup معمولاً روی یک Database مشخص انجام می‌شوند، در حالی که تنظیمی مانند بعضی Server Configurationها روی کل Instance اثر دارد.

| سطح | نمونه | چند مورد از چیزهایی که در آن سطح می‌بینیم |
|---|---|---|
| Windows Server | SQLPROD01 | Serviceها، CPU، RAM، Volumeها |
| Instance | MSSQLSERVER | Loginها، Server Configuration، Databaseها |
| Database | Sales | Tableها، Viewها، Userها، Fileها |

::: {custom-style="Important Note"}
قبل از هر عملیات مدیریتی از خودتان بپرسید: این تغییر در سطح Instance است یا Database؟
:::

## ۱.۴ مؤلفه‌های اصلی SQL Server

در یک نصب معمولی SQL Server، دو نام را زیاد می‌بینید: SQL Server Database Engine و SQL Server Agent. این دو با هم کار می‌کنند، اما یک Component واحد نیستند.

### ۱.۴.۱ نقش Database Engine

Database Engine هستهٔ اصلی SQL Server است. Clientها و Applicationها به Instance مربوط به Database Engine متصل می‌شوند. Database Engine Query را اجرا می‌کند، Databaseها را مدیریت می‌کند، Security و Transactionها را اعمال می‌کند و عملیات خواندن و نوشتن داده را هماهنگ می‌کند.

### ۱.۴.۲ نقش SQL Server Agent

SQL Server Agent یک Windows Service جداگانه برای Automation (خودکارسازی) وظایف مدیریتی است. Jobها (کارهای زمان‌بندی‌شده) می‌توانند در زمان مشخص اجرا شوند یا مجموعه‌ای از Stepها (مراحل اجرا) را به‌ترتیب انجام دهند. Backupهای زمان‌بندی‌شده، Maintenance (نگه‌داری) و بعضی کارهای Monitoring (پایش) نمونه‌های رایج استفاده از Agent هستند.

خود Agent سرویس جداگانه‌ای است، اما اطلاعات Jobها و History مربوط به آن در System Database به نام msdb ذخیره می‌شود. این ارتباط مهم است: از نظر معماری، Jobs زیرمجموعهٔ Databaseهای کاربر نیستند، اما Metadata آن‌ها در msdb قرار می‌گیرد.

شکل ۱-۱. نمای مفهومی Windows Server، Database Engine Instance، SQL Server Agent، Databaseها و Clientهای متصل به Instance

::: {custom-style="DBA Note"}
نکتهٔ DBA در شکل، SSMS و Application به Database Engine Instance متصل می‌شوند. آن‌ها مستقیماً به Windows Server یا فایل‌های Database وصل نمی‌شوند. همچنین Login در این شکل یک Principal (هویت امنیتی) سطح Instance است، نه صرفاً «صفحهٔ ورود» یک نرم‌افزار.
:::

### ۱.۴.۳ معماری داخلی SQL Server Database Engine

برای درک عملکرد SQL Server، باید مسیر یک درخواست را از لحظهٔ ارسال توسط Client تا پردازش Query، دسترسی به داده، استفاده از Memory و در نهایت ارتباط با فایل‌های Database بشناسیم. Database Engine از چند مؤلفهٔ اصلی تشکیل شده است که هرکدام مسئول بخشی از چرخهٔ اجرای درخواست هستند.

شکل ۱-۲. معماری داخلی SQL Server Database Engine و مسیر ساده‌شدهٔ پردازش درخواست‌ها

در این معماری، درخواست ابتدا از طریق لایهٔ ارتباطی دریافت می‌شود. سپس Query Processor وظیفهٔ بررسی دستور، انتخاب Execution Plan و اجرای Query را بر عهده دارد. Storage Engine نیز مسئول مدیریت Pageها، Transactionها، Indexها و ارتباط با فایل‌های فیزیکی Database است. Buffer Pool میان Memory و Storage قرار می‌گیرد تا با نگه‌داری Pageهای موردنیاز در حافظه، نیاز به Physical Read کاهش پیدا کند.

## ۱.۵ پایگاه‌های دادهٔ سیستمی SQL Server

هر SQL Server Instance مجموعه‌ای از System Databaseها دارد که برای کار Engine و مدیریت Instance لازم‌اند. در این فصل قرار نیست ساختار داخلی آن‌ها را حفظ کنیم؛ هدف این است که بدانیم هرکدام در چه سناریویی اهمیت پیدا می‌کنند.

| Database | نقش اصلی | چرا برای DBA مهم است؟ |
|---|---|---|
| master | نگه‌داری اطلاعات سطح Instance و اطلاعات لازم برای راه‌اندازی و شناخت Databaseهای دیگر | خرابی آن می‌تواند Startup و مدیریت Instance را مختل کند. |
| model | Template ایجاد Databaseهای جدید | بعضی تنظیمات Database جدید از model به ارث می‌رسند. |
| msdb | اطلاعات SQL Server Agent، Jobها، Scheduleها و بخشی از Historyهای مدیریتی | برای Automation و بسیاری از عملیات DBA حیاتی است. |
| tempdb | Workspace مشترک برای Objectهای موقت و Intermediate Resultها | تقریباً همهٔ Workloadها می‌توانند به‌نوعی از آن استفاده کنند؛ با Restart دوباره ساخته می‌شود. |
| Resource | Database فقط‌خواندنی و مخفی برای System Objectهای همراه SQL Server | Objectهای سیستمی را فیزیکی نگه می‌دارد، هرچند در Databaseها به‌صورت منطقی در schemaهای سیستمی دیده می‌شوند. |

### ۱.۵.۱ چرا Resource در شکل قبل دیده نمی‌شود؟

Resource Database مانند master یا msdb برای کار روزانه در Object Explorer دیده نمی‌شود. این Database مخفی و Read-only است و System Objectهایی را نگه می‌دارد که همراه خود SQL Server ارائه می‌شوند. بنابراین نبودن Resource در شکل ۱-۱ عمدی است و به خواننده کمک می‌کند فرق Databaseهای سیستمی قابل مشاهده با Resource را بداند.

### ۱.۵.۲ tempdb را فقط «یک Database سیستمی دیگر» نبینید

tempdb یک Resource (منبع) مشترک برای همهٔ Userهای متصل به Instance است. Temporary Tableها (جدول‌های موقت)، بعضی عملیات Sort (مرتب‌سازی) و Hash و انواع Intermediate Resultها (نتایج میانی) می‌توانند از آن استفاده کنند. فعلاً وارد بحث Contention (رقابت هم‌زمان بر سر منابع) یا تعداد Data Fileهای tempdb نمی‌شویم؛ در این مرحله مهم‌تر است بدانید مشکل در tempdb می‌تواند روی چند Database و چند Application هم‌زمان اثر بگذارد.

::: {custom-style="Warning"}
هشدار System Databaseها را به چشم Databaseهای کم‌اهمیت نگاه نکنید. برای مثال، اطلاعات بسیاری از Jobهای SQL Server Agent در msdb است و اطلاعات سطح Instance در master نگه‌داری می‌شود. Strategy پشتیبان‌گیری از System Databaseها در فصل Backup بررسی خواهد شد.
:::

## ۱.۶ مدل ذهنی هویت و دسترسی

یکی از اشتباه‌های رایج Junior DBAها یکی دانستن Login و User است. برای شروع، این مدل ساده را در ذهن داشته باشید:

::: {custom-style="Important Note"}
Login معمولاً هویت ورود در سطح Instance است. User هویتی است که داخل یک Database اجازهٔ دسترسی به Objectها را پیدا می‌کند.
:::

اگر یک Login اجازه داشته باشد به Instance متصل شود، این موضوع به‌تنهایی تضمین نمی‌کند که بتواند همهٔ Databaseها را بخواند یا تغییر دهد. برای دسترسی معمول به یک Database، Login به User همان Database Map (نگاشت) می‌شود و Permissionها (مجوزهای دسترسی) به User یا Roleهای Database داده می‌شوند.

| مفهوم | سطح معمول | نمونه |
|---|---|---|
| Login | Instance | DOMAIN\Niloofar |
| User | Database | Niloofar |
| Database Role | Database | db_datareader |

این مدل استثناهایی دارد. برای مثال Contained Database User (کاربر Database مستقل از Login سطح Instance) می‌تواند بدون Login متناظر در سطح Instance ایجاد شود. فعلاً نیازی نیست وارد این جزئیات شویم. در فصل Security، Mapping (نگاشت)، Roleها (نقش‌ها) و Permissionها (مجوزهای دسترسی) را دقیق‌تر بررسی می‌کنیم.

::: {custom-style="DBA Note"}
نکتهٔ DBA برای Troubleshooting دسترسی دو سؤال جدا بپرسید: «آیا این هویت می‌تواند به Instance متصل شود؟» و «بعد از اتصال، داخل Database موردنظر چه User و Permissionهایی دارد؟»
:::

## ۱.۷ Editionهای اصلی SQL Server

Version (نسخه) و Edition (ویرایش محصول) یک چیز نیستند. Version نسل محصول را مشخص می‌کند، مانند SQL Server 2022 یا SQL Server 2025؛ در مقابل، Edition مشخص می‌کند چه مجموعه‌ای از قابلیت‌ها و محدودیت‌های Resource (منابع) و Licensing (مجوز استفاده) در اختیار آن نصب قرار دارد.

این کتاب با نگاه Enterprise نوشته می‌شود، چون هدف آن آشنایی با مدیریت SQL Server در محیط‌های سازمانی است. بااین‌حال، یک Junior DBA باید Standard، Developer و Express را هم بشناسد تا در Lab یا محیط‌های کوچک با نام‌های ناآشنا روبه‌رو نشود.

| Edition | کاربرد معمول | نکته‌ای که باید به خاطر بسپارید |
|---|---|---|
| Enterprise | Workloadهای سازمانی و سناریوهای نیازمند بیشترین ظرفیت یا قابلیت‌ها | Edition اصلی این کتاب است، اما داشتن Enterprise جای طراحی صحیح را نمی‌گیرد. |
| Standard | بسیاری از Workloadهای Production با نیاز و ظرفیت محدودتر | قبل از انتخاب باید Featureها و محدودیت‌های همان Version بررسی شوند. |
| Developer / Developer Editions | Development و Test | برای Production مجاز نیست. در SQL Server 2025، Enterprise Developer و Standard Developer جدا شده‌اند. |
| Express | Applicationهای کوچک، آموزش و سناریوهای سبک | رایگان است، اما محدودیت Resource و Feature دارد و SQL Server Agent در آن در دسترس نیست. |

### ۱.۷.۱ چرا روی شمارهٔ Version تمرکز نمی‌کنیم؟

اصول پایهٔ DBA با هر Release از نو تعریف نمی‌شوند. Instance، Database، System Database، Data File، Transaction Log، Buffer Pool و Backup همچنان مفاهیم اصلی هستند. هرجا SQL Server 2022 و SQL Server 2025 رفتار یا Editionبندی متفاوتی داشته باشند که روی کار شما اثر بگذارد، همان‌جا اشاره می‌کنیم.

نمونهٔ مهم در این فصل، Developer Edition است. در SQL Server 2022، Developer Edition از نظر Featureهای Database Engine با Enterprise هم‌سطح است ولی فقط برای Development و Test مجوز دارد. در SQL Server 2025، Microsoft دو گزینهٔ Enterprise Developer و Standard Developer ارائه کرده است تا Lab یا Test به Edition مقصد نزدیک‌تر باشد.

::: {custom-style="Lab Note"}
LAB اگر هدف شما تمرین این کتاب است، محیط Lab را بر مبنای Developer Edition مناسب Version خود بسازید. برای تمرین قابلیت‌های Enterprise در SQL Server 2025 از Enterprise Developer استفاده کنید.
:::

## ۱.۸ محیط‌های کاری SQL Server

محیطی که کاربران واقعی در آن کار می‌کنند با محیطی که برای آزمایش ساخته شده است یک سطح ریسک ندارد. تفکیک این محیط‌ها یکی از عادت‌های مهم DBA است.

| محیط | هدف | رفتار مناسب DBA |
|---|---|---|
| Production | ارائهٔ سرویس واقعی به کاربران | تغییر کنترل‌شده، Backup معتبر، Monitoring و Change Management |
| Development | توسعه و آزمون تغییرات Application و Database | آزمایش Schema و Queryها پیش از انتقال به Production |
| Lab | یادگیری، تمرین و آزمایش سناریوهای DBA | محیط قابل حذف و بازسازی، بدون وابستگی سرویس واقعی |

ممکن است از نظر فنی Production و Development را روی Instanceهای جدا در یک Host قرار دهید، اما این کار الزاماً جداسازی واقعی ایجاد نمی‌کند. اگر هر دو Instance از یک CPU، RAM، Storage یا Hypervisor استفاده کنند، Failure Domain (دامنهٔ خرابی) و Resource Domain (دامنهٔ منابع) همچنان مشترک است. برای کتاب مقدماتی همین نکته کافی است: «جدا بودن نام Instance» با «جدا بودن زیرساخت» یکسان نیست.

### ۱.۸.۱ مسیر امن یادگیری

هر دستور یا تنظیمی که اثر آن را نمی‌شناسید ابتدا در Lab آزمایش کنید. بعد از فهم نتیجه، می‌توان همان تغییر را در Development بررسی کرد. انتقال به Production باید همراه با برنامهٔ اجرا، روش بازگشت و در صورت نیاز Backup یا Restore Plan باشد.

::: {custom-style="Important Note"}
Production محل یادگیری با آزمون‌وخطا نیست.
:::

## ۱.۹ فایل‌ها و Storage در یک نگاه

Database فقط یک نام در SSMS نیست. دادهٔ آن در فایل‌های فیزیکی روی Storage نگه‌داری می‌شود. یک Database معمولی حداقل یک Data File و یک Transaction Log File دارد.

### ۱.۹.۱ Data File

Data Fileها Data Pageها و ساختارهای مربوط به Database را نگه می‌دارند. فایل Primary معمولاً با پسوند .mdf و Data Fileهای اضافه معمولاً با .ndf دیده می‌شوند. این Extensionها قرارداد رایج SQL Server هستند و به DBA کمک می‌کنند نوع فایل را سریع تشخیص دهد.

### ۱.۹.۲ Transaction Log File

Transaction Log سابقهٔ تغییرات لازم برای مدیریت Transaction و Recovery را نگه می‌دارد و فایل آن معمولاً پسوند .ldf دارد. Data File و Log File هدف و الگوی I/O یکسانی ندارند. Data Fileها برای خواندن و نوشتن Pageهای Database استفاده می‌شوند، در حالی که Log برای ثبت تغییرات Transactionها طراحی شده است.

| نوع فایل | پسوند متعارف | کار اصلی |
|---|---|---|
| Primary Data File | .mdf | Data File اصلی Database |
| Secondary Data File | .ndf | Data File اضافه در طراحی‌های نیازمند چند فایل |
| Transaction Log File | .ldf | ثبت Log Recordهای لازم برای Transaction و Recovery |

### ۱.۹.۳ Drive Letter با Storage واقعی یکی نیست

در یک طراحی ساده ممکن است Data روی D:، Log روی E: و Backup روی F: قرار گیرد. این جداسازی برای مدیریت و جلوگیری از پر شدن درایو سیستم مفید است، اما داشتن سه Drive Letter لزوماً به معنی سه مجموعه Disk مستقل نیست. در VM، SAN یا Storage Array ممکن است چند Volume در نهایت روی Backend مشترک قرار داشته باشند.

برای همین DBA باید علاوه بر مسیر فایل، ظرفیت، Latency (تأخیر)، Throughput (توان عملیاتی)، Failure Domain (دامنهٔ خرابی) و معماری واقعی Storage را بشناسد. جزئیات طراحی Storage در فصل زیرساخت و بخش‌های بعدی کتاب بررسی می‌شود.

**فرمان SQL**

```sql
SELECT name, type_desc, physical_name, size * 8.0 / 1024 AS SizeMB FROM sys.database_files;
```

ستون size در Catalog View بالا بر حسب Pageهای ۸ KB ذخیره می‌شود. ضرب در ۸ و تقسیم بر ۱۰۲۴، اندازهٔ تقریبی فایل را بر حسب MB نشان می‌دهد. همین جزئیات کوچک نمونه‌ای از چیزی است که DBA باید هنگام خواندن Metadata (فراداده) به آن توجه کند.

## ۱.۱۰ مسیر خواندن داده از Memory و Storage

خواندن از Memory (حافظه) بسیار سریع‌تر از خواندن از Storage (فضای ذخیره‌سازی) است. SQL Server برای کاهش I/O فیزیکی، Data Pageهایی (صفحه‌های داده) را که نیاز دارد در Memory و در ناحیه‌ای مانند Buffer Pool (ناحیهٔ اصلی نگه‌داری Pageها در حافظه) نگه می‌دارد.

### ۱.۱۰.۱ Logical Read

هر بار Database Engine یک Page را از Buffer Pool درخواست می‌کند، یک Logical Read (خواندن منطقی) در نظر گرفته می‌شود. اگر Page از قبل در Buffer Pool باشد، درخواست بدون نیاز به خواندن آن Page از Storage پاسخ داده می‌شود.

### ۱.۱۰.۲ Physical Read

اگر Page موردنیاز در Buffer Pool نباشد، SQL Server باید آن Page را از Data File روی Storage به Memory بیاورد. این بخش نیازمند Physical Read (خواندن فیزیکی) است. پس Physical Read در این مدل به معنی مراجعه به Storage برای وارد کردن Page به Buffer Pool است.

شکل ۱-۳. مدل ساده‌شدهٔ مسیر Data Page میان Buffer Pool و Storage و مسیر جداگانهٔ Transaction Log

شکل ۱-۳ عمداً ساده است. در دنیای واقعی، Query ممکن است تعداد زیادی Logical Read و تعدادی Physical Read داشته باشد. بنابراین نباید یک Query را فقط «Logical» یا فقط «Physical» بدانیم. این مفاهیم در سطح درخواست Pageها معنا پیدا می‌کنند.

همچنین مسیر Transaction Log در شکل از مسیر Read داده جداست. Log File منبع Physical Read معمول Data Page نیست. این جداسازی برای فهم فصل‌های Backup، Recovery و Performance اهمیت زیادی خواهد داشت.

::: {custom-style="DBA Note"}
نکتهٔ DBA اگر Query کند است، اولین پاسخ نباید «CPU کم است» باشد. CPU، Memory و Storage هر سه می‌توانند در رفتار SQL Server نقش داشته باشند. فصل Monitoring به شما یاد می‌دهد چطور با Metric و شواهد سراغ علت بروید.
:::

## ۱.۱۱ SQL Server از دید یک DBA

Developer معمولاً از SQL Server می‌خواهد Query درست اجرا شود و Application نتیجهٔ صحیح بگیرد. DBA همین موضوع را می‌بیند، اما چند سؤال دیگر هم به آن اضافه می‌کند: آیا Database در دسترس است؟ آیا Backup قابل Restore داریم؟ چه کسی دسترسی دارد؟ آیا Storage در حال پر شدن است؟ آیا یک Job شکست خورده؟ آیا Performance نسبت به Baseline تغییر کرده است؟

| حوزه | سؤال سادهٔ DBA |
|---|---|
| Availability | Database و Service زمانی که Application نیاز دارد در دسترس‌اند؟ |
| Backup & Recovery | اگر داده یا Server از دست رفت، تا چه نقطه‌ای و در چه زمانی می‌توانیم برگردیم؟ |
| Security | چه کسی به Instance و Database دسترسی دارد و چه Permissionهایی دارد؟ |
| Performance | کندی از Query، Blocking، CPU، Memory، I/O یا عامل دیگری است؟ |
| Monitoring | چطور قبل از تماس کاربر متوجه Failed Job، Full Disk یا Error شویم؟ |
| Maintenance | چه کارهای دوره‌ای واقعاً لازم‌اند و کدام کارها صرفاً عادت قدیمی‌اند؟ |

### ۱.۱۱.۱ DBA خوب تنظیمات را حفظ نمی‌کند، رابطه‌ها را می‌فهمد

هدف این کتاب ساختن Checklistهای کور نیست. برای مثال، وقتی می‌گوییم Data و Log رفتار متفاوتی دارند، قرار نیست همیشه بدون بررسی آن‌ها را روی هر Drive متفاوتی قرار دهید. باید بفهمید Storage واقعی چگونه طراحی شده است. وقتی دربارهٔ Index Maintenance صحبت می‌کنیم، قرار نیست هر شب تمام Indexها Rebuild شوند. باید بدانید چه مشکلی را حل می‌کنید.

این نوع نگاه از همین فصل شروع می‌شود: تشخیص سطح Instance از Database، تشخیص Data File از Log File و تشخیص Memory access از Physical I/O.

### ۱.۱۱.۲ یک Health Check (بررسی سلامت) ذهنی ساده

وقتی وارد یک SQL Server جدید می‌شوید، لازم نیست در ده دقیقه همه‌چیز را Tune کنید. ابتدا چند سؤال پایه بپرسید:

•  این Server چه محیطی است: Production، Development یا Lab؟

•  Version و Edition چیست؟

•  چند Database دارد و وضعیت آن‌ها چیست؟

•  Backupها کجا هستند و آخرین Backup موفق چه زمانی بوده است؟

•  SQL Server Agent فعال است و Jobهای مهم چه وضعی دارند؟

•  Data و Log روی چه Volumeهایی هستند و فضای آزاد چقدر است؟

این سؤال‌ها در فصل‌های بعدی به Query و روال عملی تبدیل می‌شوند. هدف این است که بررسی سلامت Server به‌تدریج از یک چک ذهنی به یک روش قابل تکرار و قابل اندازه‌گیری تبدیل شود.

## ۱.۱۲ تمرین پایان فصل

تمرین‌های این فصل برای Lab طراحی شده‌اند. هدف آن‌ها حفظ‌کردن Syntax نیست؛ باید بتوانید ساختار Instance را ببینید و مفاهیم این فصل را به یک SQL Server واقعی وصل کنید.

### تمرین ۱: Version، Edition و Instance را پیدا کنید

**فرمان SQL**

```sql
SELECT SERVERPROPERTY('ProductVersion') AS ProductVersion, SERVERPROPERTY('Edition') AS Edition, SERVERPROPERTY('InstanceName') AS InstanceName, SERVERPROPERTY('MachineName') AS MachineName;
```

توضیح دهید کدام ستون به Version، کدام به Edition، کدام به Instance و کدام به Windows Server مربوط است. اگر InstanceName برابر NULL بود، دربارهٔ Default Instance تحقیق کنید و دلیل آن را بنویسید.

### تمرین ۲: Databaseهای Instance را فهرست کنید

**فرمان SQL**

```sql
SELECT name, database_id, state_desc, recovery_model_desc FROM sys.databases ORDER BY database_id;
```

System Databaseها را از User Databaseها جدا کنید. بررسی کنید آیا Resource در خروجی دیده می‌شود یا خیر.

### تمرین ۳: نقش System Databaseها را بدون نگاه‌کردن به متن توضیح دهید

برای master، model، msdb، tempdb و Resource هرکدام یک جمله بنویسید. اگر توضیح شما بیش از دو جمله شد، احتمالاً وارد جزئیات غیرضروری شده‌اید.

### تمرین ۴: فایل‌های یک Database را بررسی کنید

یک User Database آزمایشی انتخاب کنید و Query بخش ۱.۹ را اجرا کنید. نام منطقی، نوع فایل، مسیر فیزیکی و اندازهٔ فایل را ثبت کنید. سپس توضیح دهید چرا size مستقیماً MB نیست.

### تمرین ۵: Login و User را روی کاغذ Map کنید

فرض کنید Login با نام DOMAIN\Niloofar.Karimi به Instance متصل می‌شود و در Database فروش User با نام Niloofar.Karimi دارد. مسیر «اتصال به Instance» و «دسترسی داخل Database» را در دو مرحله رسم کنید. این تمرین عمداً Query ندارد.

### تمرین ۶: شکل ۱-۳ را با زبان خودتان توضیح دهید

برای دو حالت زیر توضیح کوتاه بنویسید:

•  Page موردنیاز از قبل در Buffer Pool است.

•  Page موردنیاز در Buffer Pool نیست.

در پاسخ مشخص کنید Logical Read و Physical Read در کدام بخش رخ می‌دهند و چرا Transaction Log مسیر جداگانه‌ای دارد.

### تمرین ۷: یک Mini Inventory برای Lab بسازید

در یک صفحه اطلاعات زیر را برای Lab خود ثبت کنید: نام Windows Server، نام Instance، Version، Edition، نام User Database آزمایشی، مسیر Data File، مسیر Log File و وضعیت SQL Server Agent. این Inventory را در فصل‌های بعدی تکمیل می‌کنیم.

::: {custom-style="Important Note"}
اگر این فصل را درست یاد گرفته‌اید باید بتوانید بدون حفظ‌کردن Wizard نصب توضیح دهید SQL Server با Database چه تفاوتی دارد، Instance چیست، Agent چه نقشی دارد، System Databaseها چرا مهم‌اند، Login و User در چه سطحی قرار می‌گیرند، Data و Log چه تفاوتی دارند و چرا Buffer Pool و Storage روی رفتار Query اثر می‌گذارند.
:::

## جمع‌بندی فصل

در این فصل یک مدل پایه ساختیم: Windows Server میزبان Serviceهای SQL Server است؛ Database Engine در قالب Instance، Databaseها و Loginهای سطح Server را مدیریت می‌کند؛ SQL Server Agent برای Automation کارهای مدیریتی استفاده می‌شود؛ System Databaseها بخشی از زیرساخت Instance هستند؛ Databaseها Data File و Transaction Log دارند؛ Buffer Pool دسترسی Pageها از Memory را ممکن می‌کند و در صورت نبودن Page در Memory، Physical Read از Storage لازم می‌شود.

در فصل بعدی این مدل را به زیرساخت واقعی وصل می‌کنیم و می‌بینیم یک ماشین مجازی یا سرور مناسب SQL Server از نظر CPU، RAM و Storage باید چه ویژگی‌هایی داشته باشد، بدون اینکه وارد جزئیات غیرضروری طراحی دیتاسنتر شویم.

# فصل دوم — آماده‌سازی ماشین مجازی و زیرساخت برای SQL Server

در فصل اول، SQL Server را از داخل Instance تا Database، فایل‌ها و Buffer Pool دنبال کردیم. این فصل زاویهٔ دید را عوض می‌کند و یک لایه عقب‌تر می‌رود: زیرساختی که Windows Server و SQL Server روی آن اجرا می‌شوند. برای یک DBA تازه‌کار، مهم‌ترین نکته این نیست که همهٔ جزئیات VMware را بداند؛ مهم این است که بداند vCPU، RAM و Diskهایی که داخل VM می‌بیند، در نهایت از منابع فیزیکی Host تأمین می‌شوند و ممکن است با Workloadهای دیگر مشترک باشند.

::: {custom-style="Chapter Overview"}
در این فصل •  اجرای SQL Server روی سرور فیزیکی و ماشین مجازی •  نقش Hypervisor و منابع مشترک Host •  Right-sizing اولیهٔ CPU و RAM و مفهوم Resource Contention •  مدیریت توان از Firmware تا ESXi و Windows Server •  مبانی Storage شامل IOPS، Throughput و Latency •  Disk Provisioning، PVSCSI و طراحی Volumeهای SQL Server •  مرز میان VMware HA و High Availability در سطح SQL Server
:::

مبنای فصل: SQL Server Enterprise Edition روی Windows Server است و VMware ESXi نمونهٔ اصلی محیط مجازی این فصل است. مطالب به سال خاصی وابسته نشده‌اند؛ تفاوت نسخه‌ها فقط زمانی مطرح می‌شود که روی تصمیم DBA اثر واقعی داشته باشد.

## ۲.۱ اجرای SQL Server روی سرور فیزیکی یا ماشین مجازی

SQL Server می‌تواند مستقیماً روی Physical Server یا داخل Virtual Machine اجرا شود. Database Engine در هر دو حالت همان مسئولیت اصلی را دارد: دریافت Query، استفاده از Memory، دسترسی به فایل‌های Database و ثبت تغییرات در Transaction Log. تفاوت اصلی زیر این لایه اتفاق می‌افتد.

در Physical Server، Windows Server مستقیماً با سخت‌افزار همان سرور کار می‌کند. در محیط مجازی، Windows Server سخت‌افزار مجازی دریافت می‌کند و Hypervisor (لایهٔ مجازی‌سازی) این منابع را روی CPU، RAM و Storage واقعی Host مدیریت می‌کند. همین واسطه باعث می‌شود DBA هنگام بررسی Performance فقط به Task Manager و SQL Server نگاه نکند.

::: {custom-style="Important Note"}
دام مجازی‌سازی اگر داخل Windows Server عدد ۸ vCPU دیده می‌شود، نتیجه نگیرید که هشت Core فیزیکی به‌صورت دائمی و انحصاری در اختیار SQL Server است. Hypervisor باید زمان پردازش این vCPUها را روی منابع واقعی Host فراهم کند.
:::

## ۲.۲ Hypervisor چیست؟

Hypervisor نرم‌افزاری است که ماشین‌های مجازی را ایجاد و منابع آن‌ها را مدیریت می‌کند. در مراکز داده معمولاً با Hypervisorهای Type 1 روبه‌رو هستیم؛ یعنی لایهٔ مجازی‌سازی مستقیماً روی سخت‌افزار Host اجرا می‌شود. VMware ESXi و Microsoft Hyper-V نمونه‌های شناخته‌شدهٔ این مدل هستند.

Type 2 روی یک سیستم‌عامل میزبان اجرا می‌شود و بیشتر برای Desktop، آموزش یا Lab مناسب است. برای ادامهٔ این فصل، ESXi را به‌عنوان نمونهٔ عملی در نظر می‌گیریم، اما هدف آموزش پنل VMware نیست. DBA باید رابطهٔ منابع را بفهمد و بداند برای هر مسئله از تیم Virtualization چه اطلاعاتی بخواهد.

## ۲.۳ لایه‌های منابع از SQL Server تا زیرساخت

درون VM، SQL Server با vCPU، vRAM و Virtual Disk کار می‌کند. این‌ها برای Guest OS واقعی به نظر می‌رسند، اما هرکدام نمایی از منابع زیرساخت هستند: vCPU روی Physical CPU زمان‌بندی می‌شود، vRAM از RAM فیزیکی Host تأمین می‌شود و vDisk از مسیری مانند VMDK، Datastore و Storage فیزیکی عبور می‌کند.

اگر Host چند VM پرمصرف داشته باشد، Resource Contention (رقابت بر سر منابع) ممکن است به SQL Server برسد. بنابراین افزایش vCPU یا ساخت یک Drive جدید همیشه معادل افزایش منبع فیزیکی نیست.

شکل ۲-۱. رابطهٔ منابع مجازی SQL Server با Hypervisor و زیرساخت فیزیکی مشترک

::: {custom-style="DBA Note"}
نکتهٔ DBA در Troubleshooting یک SQL Server مجازی، سه محدوده را جدا ببینید: داخل SQL Server، داخل Windows Server و زیرساخت VMware/Storage. مشکل می‌تواند در هرکدام از این سه لایه باشد.
:::

## ۲.۴ CPU؛ بیشتر همیشه بهتر نیست

در VM، vCPU با Physical Core یک مفهوم نیست. Hypervisor باید هر vCPU آمادهٔ اجرا را روی CPUهای فیزیکی زمان‌بندی کند. اگر VM بدون دلیل بزرگ شود، تعداد vCPU بیشتر می‌تواند زمان‌بندی را پیچیده‌تر کند و الزاماً Performance را بهتر نکند.

یکی از معیارهای VMware، CPU Ready است؛ یعنی زمانی که VM آمادهٔ اجراست اما هنوز نوبت CPU فیزیکی به آن نرسیده است. این عدد به‌تنهایی تشخیص نهایی نیست، ولی در کنار کندی Workload، CPU Usage و وضعیت Host می‌تواند سرنخ مهمی باشد.

برای Junior DBA یک اصل کافی است: VM را Right-size کنید؛ یعنی اندازهٔ آن را بر اساس Baseline و Peak واقعی Workload انتخاب کنید، نه بر اساس حدس یا شعار «هرچه CPU بیشتر، بهتر».

vNUMA را فعلاً در حد یک هشدار بشناسید

در VMهای بزرگ، چیدمان vCPU و Memory با معماری NUMA در Host ارتباط پیدا می‌کند. در این کتاب وارد تنظیم NUMA نمی‌شویم. همین را بدانید که تغییر تعداد vCPU، Hot Add و اندازهٔ VM می‌تواند روی این توپولوژی اثر بگذارد و برای VMهای بزرگ باید با تیم Virtualization بررسی شود.

## ۲.۵ RAM و فشار حافظه در محیط مجازی

SQL Server از Memory برای Cache کردن Pageهای داده و ساختارهای داخلی استفاده می‌کند. در فصل اول دیدیم که وجود Page در Buffer Pool می‌تواند نیاز به Physical Read را کاهش دهد. در محیط مجازی، علاوه بر مقدار RAM داخل Windows، وضعیت Memory در سطح Host نیز اهمیت دارد.

اگر Host با Memory Pressure (فشار حافظه) روبه‌رو شود، Hypervisor می‌تواند از مکانیزم‌هایی مانند Ballooning یا Swapping استفاده کند. برای SQL Serverهای حساس، چنین شرایطی می‌تواند Latency را بالا ببرد. Reservation (رزرو منبع) یکی از ابزارهای VMware برای تضمین بخشی از Memory است، اما مقدار آن باید با ظرفیت Cluster و سیاست زیرساخت هماهنگ باشد.

::: {custom-style="DBA Note"}
نکتهٔ DBA وقتی می‌گویند «برای SQL Server مقدار ۶۴ GB RAM تعریف شده»، یک سؤال دیگر هم بپرسید: این Memory هنگام فشار Host چه تضمینی دارد و سیاست Reservation چیست؟
:::

## ۲.۶ مدیریت توان در لایه‌های زیرساخت

Power Management فقط یک گزینه در Windows Server نیست. رفتار CPU می‌تواند در Firmware یا BIOS سرور، در ESXi و در Power Plan سیستم‌عامل Guest کنترل شود. اگر این لایه‌ها با هدف Workload هم‌راستا نباشند، ممکن است CPU در زمان بار سنگین به فرکانس مورد انتظار نرسد یا زمان پاسخ ناپایدار شود.

برای Workloadهای حساس به Latency، معمولاً سیاست‌های Performance-oriented بررسی می‌شوند. این به معنی فعال‌کردن کورکورانهٔ High Performance در همه‌جا نیست؛ باید Power Profile سخت‌افزار، ESXi و Windows Server با راهنمای Vendor و نیاز واقعی Workload هماهنگ باشد.

شکل ۲-۲. لایه‌های اصلی تنظیم Performance از Firmware تا SQL Server Workload

## ۲.۷ تنظیمات Firmware و رفتار CPU

Turbo Boost

Turbo Boost به CPU اجازه می‌دهد در شرایط مناسب بالاتر از فرکانس پایه کار کند. Queryهای CPU-bound می‌توانند از این ظرفیت استفاده کنند، اما نتیجه به محدودیت توان، دما، تعداد Coreهای فعال و Power Profile بستگی دارد. برای DBA مهم است مطمئن شود این قابلیت ناخواسته توسط یک Profile محدودکننده از کار نیفتاده است.

C-State

C-State برای کاهش مصرف انرژی، بخش‌هایی از CPU را در زمان بیکاری وارد حالت کم‌مصرف می‌کند. در بعضی Workloadهای بسیار حساس به Latency، خروج از حالت‌های عمیق‌تر می‌تواند قابل توجه باشد؛ با این حال خاموش‌کردن C-State یک قانون عمومی برای همهٔ SQL Serverها نیست. نسل CPU و توصیهٔ سازندهٔ Server تعیین‌کننده‌اند.

::: {custom-style="Warning"}
هشدار تنظیم BIOS یک Server قدیمی را به‌عنوان Template برای Server جدید کپی نکنید. نام گزینه‌ها ممکن است مشابه باشد، اما رفتار Power Management با نسل CPU و Firmware تغییر می‌کند.
:::

## ۲.۸ Hot Add در ماشین مجازی

Hot Add امکان افزودن CPU یا Memory به VM روشن را فراهم می‌کند. این قابلیت جذاب است، اما فعال‌بودن آن می‌تواند روی نحوهٔ ارائهٔ توپولوژی CPU و Memory به Guest OS اثر بگذارد و رفتار دقیق آن به نسخهٔ vSphere، Virtual Hardware و Guest OS وابسته است.

برای این سطح از کتاب یک تصمیم ساده کافی است: Hot Add را فقط به این دلیل که «شاید روزی لازم شود» فعال نکنید. اگر واقعاً به افزایش Online منابع نیاز دارید، سازگاری ESXi، Hardware Version و Windows Server را با تیم Virtualization بررسی کنید.

## ۲.۹ Storage فقط ظرفیت نیست

وقتی DBA می‌پرسد «Storage این Server چقدر است؟» پاسخ «دو ترابایت» فقط ظرفیت را توضیح می‌دهد. برای Performance باید دست‌کم سه مفهوم را بشناسیم: IOPS، Throughput و Latency.

| مفهوم | معنی ساده | نمونهٔ سؤال DBA |
|---|---|---|
| IOPS | تعداد عملیات I/O در هر ثانیه | آیا Storage می‌تواند تعداد درخواست‌های ریز و زیاد OLTP را پاسخ دهد؟ |
| Throughput | حجم داده‌ای که در واحد زمان منتقل می‌شود | برای Backup، Restore یا Scanهای بزرگ پهنای باند کافی داریم؟ |
| Latency | زمان انتظار هر درخواست I/O | Data File یا Log File برای پاسخ Storage چقدر منتظر می‌ماند؟ |

هیچ‌کدام از این معیارها به‌تنهایی کافی نیستند. Workload ممکن است IOPS بالا ولی Transfer Size کوچک داشته باشد، یا برعکس در Backup و Scanهای بزرگ بیشتر به Throughput وابسته باشد. Latency نیز تجربهٔ واقعی SQL Server از مسیر I/O را نشان می‌دهد.

## ۲.۱۰ مسیر I/O در VMware

در یک SQL Server مجازی، درخواست I/O مسیر طولانی‌تری از یک Drive Letter دارد. مدل ساده‌شده چنین است: SQL Server File ← Windows Volume ← VMDK ← Virtual SCSI Controller ← Datastore ← LUN یا Storage Array. در هر لایه Queue، Limit یا رقابت می‌تواند وجود داشته باشد.

به همین دلیل جدا کردن D:\SQLData و E:\SQLLog از نظر مدیریت بسیار مفید است، اما از روی Drive Letter نمی‌توان نتیجه گرفت مسیر فیزیکی آن‌ها جداست. ممکن است هر دو VMDK در یک Datastore و در نهایت روی یک Storage Pool مشترک باشند.

::: {custom-style="Important Note"}
دام مجازی‌سازی دو Drive جدا در Windows الزاماً دو Storage مستقل نیستند. هنگام طراحی یا Troubleshooting، مسیر VMDK تا Datastore و Storage را هم مستند کنید.
:::

## ۲.۱۱ روش‌های تخصیص VMDK

Disk Provisioning (روش تخصیص فضای دیسک مجازی) مشخص می‌کند Blockهای VMDK چه زمانی تخصیص داده و Zero می‌شوند. این انتخاب هم بر مدیریت ظرفیت اثر دارد و هم در بعضی الگوهای Write روی Performance اولیهٔ دیسک اثر می‌گذارد.

| نوع VMDK | رفتار کلی | برداشت مناسب برای DBA |
|---|---|---|
| Thin Provisioned | فضا با مصرف Blockها تخصیص پیدا می‌کند. | مصرف Capacity بهینه‌تر است؛ Datastore باید دقیق پایش شود. |
| Thick / Lazy Zeroed | فضا از ابتدا تخصیص می‌یابد؛ Zero شدن Block در اولین Write انجام می‌شود. | ظرفیت از ابتدا رزرو می‌شود؛ اولین Write روی Block جدید می‌تواند هزینه داشته باشد. |
| Eager Zeroed Thick | فضا و Zero شدن Blockها از ابتدا انجام می‌شود. | در بعضی Workloadهای حساس یا سناریوهای خاص مناسب است؛ الزام عمومی برای همهٔ SQL Serverها نیست. |

در بسیاری از Workloadهای معمول، تفاوت روزمرهٔ این سه نوع کمتر از چیزی است که بعضی Checklistها القا می‌کنند؛ تفاوت بزرگ‌تر معمولاً هنگام Write روی Blockهای جدید یا در نیازمندی‌های خاص دیده می‌شود. بنابراین انتخاب را با Storage Platform و سیاست Capacity هماهنگ کنید.

## ۲.۱۲ PVSCSI در SQL Server

PVSCSI یا VMware Paravirtual SCSI یک Virtual SCSI Controller با تمرکز بر Throughput بالا و سربار CPU پایین است. برای VMهای دارای I/O زیاد، از جمله بسیاری از SQL Serverهای Production، انتخاب رایجی است.

VMware امکان استفاده از چند PVSCSI Controller را فراهم می‌کند. در Workloadهای سنگین، توزیع Diskهای پرترافیک میان چند Controller می‌تواند Queueهای بیشتری در اختیار سیستم قرار دهد. با این حال قانون «هر Disk یک Controller» را به‌صورت عمومی اجرا نکنید؛ شدت I/O و معماری Storage باید تصمیم را هدایت کنند.

::: {custom-style="DBA Note"}
نکتهٔ DBA اگر Storage Array سریع است اما Windows Server هنوز Disk Latency بالایی نشان می‌دهد، فقط Array را مقصر ندانید. Queue در Controller مجازی و Datastore نیز بخشی از مسیر I/O است.
:::

## ۲.۱۳ طراحی Volumeهای SQL Server

برای مدیریت ساده‌تر، معمولاً Data، Transaction Log، TempDB و Backup روی Volumeهای جدا قرار می‌گیرند. این جداسازی به Capacity Planning، Permission، Monitoring و Troubleshooting کمک می‌کند. برای Performance باید بررسی شود این Volumeها در لایهٔ VMware و Storage نیز چگونه پیاده‌سازی شده‌اند.

| کاربرد | نمونهٔ مسیر | هدف |
|---|---|---|
| Windows Server و SQL Server | C:\ | سیستم‌عامل و Program Files |
| Data Files | D:\SQLData | فایل‌های .mdf و .ndf |
| Transaction Log | E:\SQLLog | فایل‌های .ldf |
| TempDB | F:\TempDB | فایل‌های Data و Log مربوط به tempdb |
| Backup Stage | G:\SQLBackup | فضای موقت/محلی Backup؛ نسخهٔ اصلی باید Strategy مستقل داشته باشد. |

Allocation Unit Size برابر ۶۴ KB

برای Volumeهای اختصاصی SQL Server، ۶۴ KB Allocation Unit Size انتخاب رایجی است و در بسیاری از راهنماهای عملی Microsoft نیز دیده می‌شود. این مقدار را «عدد جادویی» در نظر نگیرید؛ Storage مناسب، Latency و طراحی مسیر I/O مهم‌ترند. در فصل نصب، روش Format و بررسی Allocation Unit Size را عملی انجام می‌دهیم.

::: {custom-style="Warning"}
هشدار اگر مسیر Backup روی همان Datastore و همان Storage اصلی Database باشد، در برابر خرابی همان Failure Domain محافظت مستقلی ایجاد نمی‌کند. Backup باید بخشی از Strategy بازیابی باشد، نه فقط یک Folder دیگر.
:::

## ۲.۱۴ RAID را کجا ببینیم؟

در سرورهای محلی ممکن است RAID مستقیماً روی Controller سرور تعریف شود؛ در SAN، All-Flash Array یا HCI ممکن است این لایه کاملاً از DBA پنهان باشد. بنابراین سؤال درست فقط «RAID چند است؟» نیست. باید بدانیم Storage چه Latency، Throughput، Redundancy و Failure Domainی دارد.

در سطح مقدماتی کافی است بدانیم RAID 10 با Mirroring و Striping معمولاً Write Penalty کمتری از RAIDهای Parity-based دارد. RAID 5 یا RAID 6 ظرفیت مفید بیشتری می‌دهند، اما Write و Rebuild هزینهٔ متفاوتی دارند. Controller Cache و معماری Array می‌تواند رفتار واقعی را تغییر دهد؛ بنابراین RAID 10 را به‌عنوان «بهترین انتخاب همیشگی» حفظ نکنید.

## ۲.۱۵ مرز HA در VMware و SQL Server

VMware HA در خرابی Host می‌تواند VM را روی Host دیگری Restart کند. این قابلیت دربارهٔ سلامت Transaction Log، وضعیت Database یا نقش Primary و Secondary در SQL Server تصمیم نمی‌گیرد. در مقابل، فناوری‌هایی مانند Failover Cluster Instance و Availability Group برای Availability سرویس SQL Server و Database طراحی می‌شوند.

برای Junior DBA همین مرز کافی است: Hypervisor HA از VM محافظت می‌کند؛ SQL Server HA در سطح سرویس و داده مسئلهٔ دیگری را حل می‌کند. این دو می‌توانند مکمل هم باشند، اما جای یکدیگر را نمی‌گیرند.

## ۲.۱۶ چک‌لیست تحویل VM به DBA و تمرین پایان فصل

قبل از نصب SQL Server بهتر است DBA و تیم Virtualization یک چک‌لیست مشترک داشته باشند. هدف این نیست که DBA به VMware Administrator تبدیل شود؛ هدف این است که ابهام‌های اصلی قبل از ورود Workload واقعی برطرف شوند.

☐  تعداد vCPU و RAM بر اساس نیاز Workload مشخص شده و VM بدون دلیل Oversize نشده است.

☐  Power Profile در Firmware، ESXi و Windows Server بررسی شده است.

☐  وضعیت CPU Hot Add و Memory Hot Add آگاهانه انتخاب شده است.

☐  نوع VMDK و PVSCSI Controller برای Diskهای SQL Server مشخص شده است.

☐  Datastore و Storage Path مربوط به Data، Log و TempDB مستند شده است.

☐  هدف IOPS، Throughput و Latency یا حداقل Baseline موجود مشخص است.

☐  روش Monitoring فضای Datastore و Volumeهای Windows مشخص شده است.

☐  مسئولیت Troubleshooting میان DBA، Windows، Virtualization و Storage Team روشن است.

::: {custom-style="Lab Note"}
تمرین: تمرین پایان فصل یک VM آزمایشگاهی را انتخاب کنید و برای آن یک نقشهٔ یک‌صفحه‌ای بنویسید: تعداد vCPU و RAM چقدر است؟ Diskها روی کدام Datastore قرار دارند؟ نوع Controller چیست؟ Power Policy در ESXi و Windows چگونه است؟ اگر SQL Server کند شود، چه اطلاعاتی را از تیم Virtualization درخواست می‌کنید؟
:::

::: {custom-style="Important Note"}
مهم‌ترین خروجی این فصل یک تنظیم خاص نیست؛ یک مدل ذهنی است.
:::

SQL Server مجازی روی زنجیره‌ای از منابع اجرا می‌شود و هر لایه می‌تواند روی Performance اثر بگذارد. در فصل بعد، با همین دید وارد نصب SQL Server و تنظیمات اولیهٔ Windows Server و Database Engine می‌شویم.

# فصل سوم — نصب و پیکربندی اولیه SQL Server از دید DBA

از تحویل Windows Server تا Instance قابل بهره‌برداری؛ تصمیم‌هایی که پیش از Setup گرفته می‌شوند و تنظیماتی که بعد از آن اعمال می‌گردند.

در فصل اول، SQL Server را از داخل Instance تا Database، فایل‌ها و Buffer Pool دنبال کردیم. در فصل دوم یک لایه عقب‌تر رفتیم و دیدیم CPU، RAM و Diskهایی که Windows Server در اختیار SQL Server قرار می‌دهد، در یک محیط مجازی چگونه به منابع Host و Storage وابسته‌اند.

حالا وقت آن است که این دو تصویر را به هم وصل کنیم.

فرض کنید تیم Infrastructure یک Windows Server جدید در اختیار DBA قرار داده و اعلام کرده است:

«Server آماده است؛ SQL Server را نصب کنید.»

در نگاه اول کار ساده به نظر می‌رسد. Setup را اجرا می‌کنیم، چند گزینه را انتخاب می‌کنیم و منتظر پیام موفقیت می‌مانیم.

اما از دید DBA، نصب SQL Server خیلی قبل‌تر از فشردن دکمهٔ Install آغاز می‌شود و با بسته‌شدن Wizard نیز تمام نمی‌شود.

DBA باید بداند چه Serverی تحویل گرفته است، Instance قرار است چه نقشی داشته باشد، Data و Transaction Log کجا قرار می‌گیرند، tempdb چگونه آماده می‌شود، Serviceها با چه هویتی اجرا می‌شوند، چه مقدار Memory در اختیار Database Engine قرار می‌گیرد و Applicationها از چه مسیری به Instance متصل خواهند شد.

ممکن است Setup بدون خطا تمام شود، اما Data و Log روی مسیر نامناسب قرار گرفته باشند. ممکن است Database Engine اجرا شود، ولی SQL Server آن‌قدر Memory مصرف کند که برای Windows و Agentهای دیگر Headroom کافی باقی نماند. ممکن است Serviceها در وضعیت Running باشند، اما Application از شبکه نتواند به Instance متصل شود.

::: {custom-style="Important Note"}
● نکتهٔ مهم

صفحهٔ سبز پایان Setup فقط می‌گوید نصب SQL Server به پایان رسیده است؛ نمی‌گوید Server برای بهره‌برداری آماده است.

در این فصل، نصب را به شکل یک فرایند می‌بینیم:
:::

```text
Server Verification
        ↓
Installation Design
        ↓
SQL Server Setup
        ↓
Initial Configuration
        ↓
Validation
        ↓
Documentation & Handover
```

هدف این نیست که صفحه‌های Wizard را حفظ کنیم. ظاهر Setup با Versionهای مختلف تغییر می‌کند. چیزی که باید باقی بماند، منطق تصمیم‌گیری DBA است.

در این فصل

• بررسی Windows Server و منابع تحویل‌شده

• طراحی مسیرهای Data، Log، tempdb و Backup

• انتخاب Version، Edition، Instance و Featureهای لازم

• انتخاب Service Account و Authentication Mode

• شناخت Collation و اثر آن

• اجرای Setup با نگاه DBA

• پیکربندی اولیهٔ tempdb

• بررسی Build و Update

• تنظیم Network Protocol و Port

• آشنایی عملی با IFI و LPIM

• تعیین اولیهٔ max server memory و MAXDOP

• ساخت Day-Zero Baseline

• مستندسازی و Handover

Microsoft نیز Installation را صرفاً اجرای Wizard نمی‌بیند و Requirement، Security، Configuration و وضعیت سیستم‌عامل را بخشی از فرایند آماده‌سازی می‌داند. برای SQL Server 2022 و بعد از آن روی Windows Server 2022 و جدیدتر، وجود Pending Restart نیز پیش از نصب یا Upgrade باید جدی گرفته شود.

## ۳.۱ قبل از نصب SQL Server چه چیزهایی باید مشخص باشد؟

در Lab می‌توان Setup را اجرا کرد، چند گزینه را امتحان کرد و در صورت نیاز VM را دوباره ساخت. Production چنین جایی نیست.

همان اصلی که در فصل اول مطرح شد اینجا شکل عملی پیدا می‌کند:

Production محل یادگیری با آزمون‌وخطا نیست.

بخش مهمی از Installation باید پیش از بازشدن Wizard تصمیم‌گیری شده باشد. Version، Edition، Instance Type، Service Account، Authentication Mode، Collation و محل فایل‌ها از همین دسته‌اند.

اگر هنگام رسیدن به صفحهٔ Data Directories تازه بپرسیم «Data را روی کدام Drive قرار دهیم؟»، Setup زودتر از Design شروع شده است.

خروجی این مرحله بهتر است یک Installation Plan ساده باشد؛ سندی که تصمیم‌های اصلی را پیش از نصب ثبت کند.

### ۳.۱.۱ ابتدا نقش Server را مشخص کنید

اولین سؤال این نیست:

«Enterprise نصب کنیم یا Standard؟»

سؤال اول این است:

این Server قرار است چه کاری انجام دهد؟

فرض کنید VM زیر تحویل داده شده است:

| مورد | مقدار |
|---|---|
| CPU | 8 vCPU |
| RAM | 64 GB |
| Environment | Production |
| Application | Sales ERP |
| Workload | OLTP |

بدون شناخت Workload نمی‌توان گفت ۸ vCPU زیاد است یا کم، ۶۴ GB RAM مناسب است یا خیر، یا Storage چه ظرفیتی باید داشته باشد.

یک تعریف کوتاه می‌تواند چنین باشد:

«این VM میزبان Instance اصلی SQL Server سامانهٔ فروش است و Workload تراکنشی Production روی آن اجرا خواهد شد.»

برای Server دیگری ممکن است تعریف این باشد:

«این Instance برای Reporting داخلی استفاده می‌شود و Transactionهای اصلی سامانه روی آن اجرا نمی‌شوند.»

همین چند خط زمینهٔ بسیاری از تصمیم‌های بعدی را می‌سازد.

::: {custom-style="DBA Note"}
◆ نکتهٔ DBA

دو Server با CPU و RAM یکسان الزاماً به Configuration یکسان نیاز ندارند. Resource بخشی از داستان است؛ نوع Workload و نقش Server بخش دیگر آن است.
:::

### ۳.۱.۲ Version، Edition و Build را از هم جدا کنید

در فصل اول تفاوت Version و Edition را شناختیم. اینجا سؤال عملی‌تر است:

دقیقاً چه محصولی قرار است نصب شود؟

| مشخصه | Production | Lab |
|---|---|---|
| Product | SQL Server | SQL Server |
| Version | SQL Server 2025 | SQL Server 2025 |
| Edition | Enterprise | Developer مناسب Lab |
| Environment | Production | Lab |

Version و Edition باید با Requirementهای Application، Licensing، Featureهای لازم و Support Policy سازمان هماهنگ باشند.

اما مشخصهٔ دیگری نیز وجود دارد: Build.

عبارت SQL Server 2025 Enterprise برای شناخت محصول کافی است، ولی برای Inventory فنی کافی نیست. دو Server ممکن است هر دو SQL Server 2025 باشند اما Build متفاوتی داشته باشند.

پس بعد از نصب باید Build دقیق را نیز ثبت کنیم.

```sql
SELECT
    SERVERPROPERTY('ProductVersion')       AS ProductVersion,
    SERVERPROPERTY('ProductLevel')         AS ProductLevel,
    SERVERPROPERTY('ProductUpdateLevel')   AS ProductUpdateLevel,
    SERVERPROPERTY('Edition')              AS Edition;
```

شمارهٔ CU را در کتاب به‌عنوان یک عدد دائمی حفظ نمی‌کنیم. DBA باید Build نصب‌شده را پیدا کند، آن را با فهرست Buildهای جاری Microsoft و Target سازمان مقایسه کند و Patch را بر اساس Change Process خود سازمان انجام دهد. این روش عمداً Evergreen است؛ برای مثال فهرست SQL Server 2025 تا سپتامبر ۲۰۲۶ نیز چندین بار تغییر کرده و CUهای تازه منتشر شده‌اند.

### ۳.۱.۳ منابع تحویل‌شده را ثبت کنید

فصل دوم یک نکتهٔ مهم داشت:

چیزی که Windows می‌بیند الزاماً تمام داستان زیرساخت نیست.

اینجا همان مفهوم را عملی می‌کنیم.

| مورد | نمونه |
|---|---|
| Server Name | SQLPROD01 |
| Environment | Production |
| CPU | 8 vCPU |
| RAM | 64 GB |
| OS Volume | C: |
| Data Volume | D: |
| Log Volume | E: |
| TempDB Volume | F: |
| Backup Stage | G: |
| Virtualization | VMware ESXi |

این جدول نمی‌گوید منابع مناسب‌اند؛ فقط مشخص می‌کند چه چیزی تحویل شده است.

اگر Design اولیه ۸ vCPU و ۶۴ GB RAM بوده ولی Windows چهار vCPU و ۳۲ GB RAM می‌بیند، زمان کشف اختلاف قبل از Setup است، نه بعد از ورود کاربران.

### ۳.۱.۴ نام Server و Instance را پیش از Setup مشخص کنید

Default Instance معمولاً با نام Server قابل اتصال است:

```text
SQLPROD01
```

Named Instance نام Instance را نیز وارد Connection String می‌کند:

```text
SQLPROD01\ERP
```

Instance Name بعدها در Connection String، Monitoring، Documentation، Scriptها، Jobها و Troubleshooting دیده خواهد شد.

نامی مانند:

```text
TEST2_NEW_FINAL
```

شاید امروز بی‌ضرر به نظر برسد، اما ممکن است سال‌ها در Configuration سازمان باقی بماند.

نام‌گذاری باید تابع Naming Convention باشد، نه تصمیم لحظه‌ای.

### ۳.۱.۵ مسیر فایل‌ها باید از قبل مشخص باشد

یک Design ساده ممکن است چنین باشد:

```text
C:\              Windows + SQL Server binaries
D:\SQLData\      User Database Data Files
E:\SQLLog\       Transaction Log Files
F:\TempDB\       tempdb
G:\SQLBackup\    Local Backup Stage
```

این یک نمونه است، نه قانون.

در محیط دیگری ممکن است Mount Point استفاده شود یا چند Volume برای Data وجود داشته باشد. اصل مهم این است که برای هر مسیر بتوانیم پاسخ دهیم:

«این Volume چرا وجود دارد و قرار است چه چیزی روی آن قرار بگیرد؟»

### ۳.۱.۶ تصمیم‌های Security را به آخر Setup موکول نکنید

پیش از Setup حداقل این سه سؤال باید پاسخ داشته باشند:

• SQL Server Database Engine با چه Service Accountی اجرا می‌شود؟

• Authentication Mode چیست؟

• Server Collation چه خواهد بود؟

این‌ها شبیه انتخاب محل Shortcut نیستند. روی Security و رفتار Instance اثر دارند و بعضی از آن‌ها بعداً تغییر ساده‌ای ندارند. Microsoft نیز Service Identity، Authentication و Collation را بخشی از تصمیم‌های اصلی Installation می‌داند.

### ۳.۱.۷ Installation Sheet بسازید

| تصمیم | مقدار |
|---|---|
| Server Name | SQLPROD01 |
| Environment | Production |
| SQL Server Version | تعیین شود |
| Edition | تعیین شود |
| Instance Type | Default / Named |
| Instance Name | در صورت Named |
| Engine Service Account | تعیین شود |
| Agent Service Account | تعیین شود |
| Authentication Mode | Windows / Mixed |
| SQL Administrators | ترجیحاً AD Group |
| Server Collation | تعیین شود |
| Data Path | `D:\SQLData` |
| Log Path | `E:\SQLLog` |
| TempDB Path | `F:\TempDB` |
| Backup Stage | `G:\SQLBackup` |
| TCP Port | تعیین شود |
| Target Build | تعیین شود |

::: {custom-style="DBA Note"}
◆ نکتهٔ DBA

§۳.۱ جای ثبت تصمیم‌ها است. در بخش‌های بعدی—Version/Edition، Instance، Service Account، Authentication و Collation—می‌بینیم این تصمیم‌ها چگونه گرفته می‌شوند. این تکرار نیست؛ حرکت از Design Sheet به Implementation است.
:::

## ۳.۲ بررسی Windows Server و زیرساخت تحویل‌شده

وقتی Infrastructure می‌گوید Server آماده است، DBA قرار نیست VMware یا Storage را از صفر طراحی کند.

اما باید مطمئن شود چیزی که تحویل گرفته با چیزی که برای SQL Server درخواست شده هم‌خوانی دارد.

هدف Benchmark کامل نیست. هنوز Workload واقعی نداریم.

سؤال این است:

آیا Server تحویل‌شده همان Serverی است که انتظار داشتیم؟

### ۳.۲.۱ CPU و RAM را تأیید کنید

یک بررسی سریع PowerShell:

```powershell
$cs = Get-CimInstance Win32_ComputerSystem

[pscustomobject]@{
    ComputerName      = $env:COMPUTERNAME
    LogicalProcessors = $cs.NumberOfLogicalProcessors
    MemoryGB          = [math]::Round($cs.TotalPhysicalMemory / 1GB, 1)
    Domain            = $cs.Domain
}
```

Win32_ComputerSystem اطلاعاتی مانند تعداد Logical Processorها و Memory قابل‌مشاهدهٔ Windows را در اختیار می‌گذارد.

اگر Specification برابر ۸ vCPU و ۶۴ GB RAM بوده، خروجی باید با Handover مقایسه شود.

در VM نیز مشاهدهٔ ۸ Logical Processor به این معنی نیست که هشت Core فیزیکی به‌صورت اختصاصی در اختیار VM هستند. همان مرزبندی فصل دوم همچنان برقرار است.

### ۳.۲.۲ Volumeها را یکی‌یکی بررسی کنید

```powershell
Get-Volume |
    Where-Object DriveLetter |
    Select-Object DriveLetter, FileSystemLabel, FileSystem, AllocationUnitSize,
        @{Name='SizeGB';Expression={[math]::Round($_.Size / 1GB, 1)}},
        @{Name='FreeGB';Expression={[math]::Round($_.SizeRemaining / 1GB, 1)}}
```

Get-Volume اطلاعات Volumeهایی را که Windows می‌بیند برمی‌گرداند.

برای هر Volume حداقل این موارد باید روشن باشند:

| ویژگی | دلیل بررسی |
|---|---|
| Capacity | فضای کل |
| Free Space | فضای آزاد هنگام تحویل |
| File System | مطابق Design |
| Allocation Unit Size | تنظیم File System |
| Purpose | Data / Log / TempDB / Backup |
| Storage Mapping | در صورت نیاز، ارتباط با زیرساخت |

::: {custom-style="DBA Note"}
◆ نکتهٔ DBA

چهار Drive Letter لزوماً به معنی چهار مجموعه Disk مستقل نیست.

D: و E: می‌توانند از دید Windows جدا باشند اما در Backend روی Storage مشترک قرار گرفته باشند.
:::

PowerShell می‌گوید Windows چه Volumeهایی می‌بیند؛ نمی‌گوید چرا ساخته شده‌اند و در زیرساخت به کجا متصل‌اند.

### ۳.۲.۳ Free Space را بدون Growth تفسیر نکنید

فرض کنید D: دارای ۳۰۰ GB فضای آزاد است.

آیا کافی است؟

به‌تنهایی نمی‌دانیم.

اگر Database اولیه ۲۰ GB باشد، ممکن است مدت زیادی کافی باشد. اگر قرار است Database یک‌ترابایتی Restore شود، همین Volume برای شروع نیز کافی نیست.

پس Capacity را در کنار این‌ها ببینید:

```text
Current / Initial Size
        +
Expected Growth
        +
Operational Headroom
```

Capacity Planning کامل در فصل مناسب خودش انجام می‌شود؛ اما DBA باید پیش از نصب بداند چه چیزی قرار است روی Volume بنشیند.

### ۳.۲.۴ Pending Restart را نادیده نگیرید

Windows ممکن است ظاهراً سالم باشد ولی Update یا Component نصب‌شده‌ای منتظر Restart باشد.

برای SQL Server 2022 و بعد از آن روی Windows Server 2022 و جدیدتر، Microsoft تأکید می‌کند که Pending Restart پیش از Install/Upgrade برطرف شود.

در سازمان‌ها روش تشخیص Pending Restart ممکن است متفاوت باشد؛ Group Policy، Endpoint Management، DSC یا فرایند Windows Team ممکن است مرجع باشد. یک Registry Script تصادفی از اینترنت را به‌عنوان حقیقت قطعی Server در کتاب استاندارد نمی‌کنیم.

قاعدهٔ عملی:

وضعیت Restart پیش از Setup باید معلوم باشد.

### ۳.۲.۵ موارد زیرساخت را حدس نزنید؛ تأیید کنید

☐ CPU و RAM تحویل‌شده مطابق Specification هستند؟

☐ Power Policy مطابق Baseline سازمان است؟

☐ Volumeها Purpose مشخص دارند؟

☐ Mapping Storage در صورت نیاز تأیید شده است؟

☐ Free Space برای Initial Deployment کافی است؟

☐ Time Synchronization وضعیت مشخصی دارد؟

☐ Server عضو Domain مورد انتظار است؟

☐ Pending Restart تعیین تکلیف شده است؟

☐ Firewall Policy مشخص است؟

☐ Antivirus/EDR Policy برای SQL Server بررسی شده است؟

☐ Monitoring Agent یا Backup Agent دیگری روی OS وجود دارد؟

::: {custom-style="DBA Note"}
◆ نکتهٔ DBA

«این تنظیم مسئولیت تیم دیگری است» با «این تنظیم روی SQL Server اثر ندارد» یکسان نیست.

DBA لازم نیست VMware Administrator، Storage Engineer و Windows Administrator باشد؛ اما باید Dependencyهای SQL Server را بشناسد.
:::

## ۳.۳ طراحی Volumeها و مسیر فایل‌های SQL Server

در فصل اول Data File و Transaction Log را از نظر نقش شناختیم. در فصل دوم دیدیم این فایل‌ها از VM تا Storage چه مسیری طی می‌کنند.

حالا باید محل واقعی آن‌ها را مشخص کنیم.

```text
C:\              Windows + SQL Server binaries
D:\SQLData\      User Database Data Files
E:\SQLLog\       Transaction Log Files
F:\TempDB\       tempdb
G:\SQLBackup\    Local Backup Stage
```

باز هم: این نمونهٔ Design است، نه قانون.

### ۳.۳.۱ چرا همه‌چیز را روی C: نمی‌گذاریم؟

مسئله این نیست که SQL Server روی C: اجرا نمی‌شود.

مسئله این است که در Production معمولاً نمی‌خواهیم رشد User Database، Transaction Log یا tempdb مستقیماً OS Volume را مصرف کند.

اگر Transaction Log به‌صورت غیرمنتظره رشد کند و روی Volume سیستم‌عامل باشد، یک مشکل Database می‌تواند به مشکل Windows تبدیل شود.

تفکیک منطقی همچنین Capacity Monitoring را ساده‌تر می‌کند.

### ۳.۳.۲ Data و Log رفتار یکسانی ندارند

Data File محل نگه‌داری Pageهای Database است.

Transaction Log رکوردهای لازم برای Transaction و Recovery را ثبت می‌کند.

پس جدا دیدن آن‌ها فقط Convention نام‌گذاری نیست.

این تفکیک کمک می‌کند:

• Capacity هرکدام مستقل‌تر دیده شود؛

• Autogrowth جداگانه پایش شود؛

• پرشدن یک Volume الزاماً دیگری را پر نکند؛

• نوع I/O هنگام Troubleshooting واضح‌تر باشد.

اما:

جداسازی Path با جداسازی Storage فیزیکی یکسان نیست.

### ۳.۳.۳ tempdb را از روز اول جدی بگیرید

tempdb Workspace مشترک Instance است. Temporary Objectها، Sort، Hash و بسیاری از عملیات داخلی می‌توانند از آن استفاده کنند.

در این فصل Tuning کامل tempdb انجام نمی‌دهیم؛ اما Path، تعداد Data Fileهای اولیه، Size و Growth آن بخشی از Installation است. Setup نیز امکان Configuration اولیهٔ tempdb را فراهم می‌کند.

### ۳.۳.۴ Backup Stage با Backup Strategy یکی نیست

وجود:

```text
G:\SQLBackup
```

به معنی داشتن Backup Strategy نیست.

ممکن است G: فقط Stage موقت باشد و Backup بعداً به Repository دیگری منتقل شود.

اگر Database و Backup در یک Failure Domain باشند، از دست رفتن همان زیرساخت می‌تواند هر دو را از بین ببرد.

Backup Path یک آدرس است؛ Backup Strategy یک طرح Recovery است.

جزئیات Backup و Restore در فصل مربوط به خودش بررسی می‌شود.

## ۳.۴ File System و Allocation Unit Size

SQL Server فایل‌های Database را روی File System قرار می‌دهد. بنابراین DBA باید حداقل بداند Volume چگونه Format شده است.

### ۳.۴.۱ Allocation Unit Size چیست؟

NTFS فضای Volume را در واحدهایی به نام Cluster تخصیص می‌دهد.

این مفهوم را با Page هشت‌کیلوبایتی SQL Server یکی نکنید:

```text
SQL Server layer : 8 KB Data Page
File-system layer: Allocation Unit / Cluster
Storage layer    : Block / Chunk / Backend layout
```

هرکدام متعلق به لایهٔ خودش است.

### ۳.۴.۲ 64 KB را قانون مطلق نکنید

در بسیاری از Designهای اختصاصی SQL Server، 64 KB به‌عنوان Allocation Unit Size رایج دیده می‌شود.

اما جملهٔ مناسب برای کتاب این نیست:

«SQL Server حتماً باید 64 KB باشد.»

بلکه:

64 KB یک Baseline رایج برای بسیاری از Volumeهای اختصاصی SQL Server است؛ عدد جادویی Performance نیست.

Cluster Size نامناسب تنها یکی از متغیرهاست. Storage Latency، Queueing، Controller، Hypervisor و Workload می‌توانند اثر بسیار بزرگ‌تری داشته باشند.

### ۳.۴.۳ Allocation Unit Size را مشاهده کنید

برای NTFS:

```console
cmd
```

```console
fsutil fsinfo ntfsinfo D:
```

به‌دنبال مقدار مشابه زیر باشید:

```text
Bytes Per Cluster : 65536
```

برای Volumeهای دیگر نیز جداگانه بررسی کنید:

```console
cmd
```

```console
fsutil fsinfo ntfsinfo E:
fsutil fsinfo ntfsinfo F:
```

::: {custom-style="Warning"}
▲ هشدار

فقط برای رسیدن به یک عدد، Volume Production را بدون Design و Backup/Recovery Plan دوباره Format نکنید.
:::

## ۳.۵ انتخاب Version، Edition و Media

در فصل اول Version و Edition را شناختیم. اینجا تصمیم Installation را می‌گیریم.

Version باید با موارد زیر هماهنگ باشد:

• Support Matrix Application

• Operating System

• Feature Requirements

• Lifecycle Policy

• Licensing

• استاندارد سازمان

Edition نیز باید Feature و Capacity موردنیاز را فراهم کند.

Enterprise داشتن به‌تنهایی Architecture خوب ایجاد نمی‌کند؛ Standard نیز الزاماً انتخاب ضعیفی نیست. مسئله Fit است.

### ۳.۵.۱ Lab را به Production نزدیک کنید، نه اینکه Production را شبیه Lab مدیریت کنید

Developer Edition برای Development/Test طراحی شده است، نه Production. در SQL Server 2025 نیز Developer گزینه‌های متفاوتی برای شبیه‌سازی بهتر Edition مقصد دارد. نسخه و Edition باید با مستندات جاری Microsoft و License سازمان تطبیق داده شوند.

### ۳.۵.۲ Media و Build را مستند کنید

در Installation Sheet فقط ننویسید:

```text
SQL Server 2025
```

ثبت کنید:

```text
Product:
Edition:
Installation Media:
Initial Build:
Target Build:
Patch Date:
Change/Ticket:
```

این اطلاعات در Troubleshooting بعدی ارزش زیادی دارند.

## ۳.۶ Default Instance یا Named Instance؟

Default Instance معمولاً با نام Host شناخته می‌شود:

```text
SQLPROD01
```

Named Instance:

```text
SQLPROD01\ERP
```

Named Instance می‌تواند در سناریوهای چند Instance یا جداسازی منطقی مفید باشد، اما باید هزینهٔ عملیاتی آن را هم دید:

• Naming پیچیده‌تر

• Port Management

• Monitoring بیشتر

• Serviceهای بیشتر

• Patch/Change Coordination

• Resource Sharing روی Host

::: {custom-style="DBA Note"}
◆ نکتهٔ DBA

دو Instance روی یک Windows Server از نظر SQL Server مرزهای مدیریتی جدا دارند، اما CPU، RAM، OS و Storage آن‌ها همچنان می‌تواند مشترک باشد.

Instance Isolation ≠ Infrastructure Isolation
:::

این همان مرزبندی فصل اول و دوم است.

## ۳.۷ Feature Selection: هر چیزی که قابل نصب است، لازم نیست نصب شود

صفحهٔ Feature Selection جای این سؤال نیست:

«این گزینه چیست؟ شاید بعداً لازم شود، پس تیک بزنیم.»

هر Feature هزینه دارد:

• Binary و Component بیشتر

• Service بیشتر

• Patch Surface بیشتر

• Security Surface بیشتر

• Complexity بیشتر

برای یک Database Server معمولی ممکن است Database Engine Services و بعضی Featureهای واقعاً موردنیاز کافی باشند.

Featureهایی مانند Analysis Services یا Integration Services باید وقتی نصب شوند که Requirement واقعی وجود دارد.

### ۳.۷.۱ SSMS را با Database Engine یکی ندانید

SQL Server Management Studio ابزار Client/Administration است. نبود SSMS روی خود Production Server به معنی نبود Database Engine نیست.

در بسیاری از محیط‌ها DBA از Workstation یا Management Server به Instance متصل می‌شود.

این مرز مهم است:

```text
SQL Server Database Engine = Server workload
SSMS                       = Management client
```

## ۳.۸ Service Accountها

در فصل اول Service را از Login جدا کردیم. اینجا این مرز اهمیت عملی پیدا می‌کند.

Service Account هویتی است که Windows Service مربوط به SQL Server با آن اجرا می‌شود.

Login هویتی است که برای اتصال به SQL Server استفاده می‌شود.

این دو مفهوم یکی نیستند.

### ۳.۸.۱ برای Engine و Agent هویت را آگاهانه انتخاب کنید

SQL Server می‌تواند بسته به Design با Virtual Account، Managed Service Account، gMSA یا Domain Account مناسب اجرا شود. انتخاب Account باید تابع Security Standard، نیازهای شبکه و Operational Model سازمان باشد. Microsoft نیز Least Privilege و استفاده از Identity مناسب هر Service را توصیه می‌کند.

نمونه:

```text
Database Engine Service : DOMAIN\svc_sqlengine
SQL Server Agent        : DOMAIN\svc_sqlagent
```

این صرفاً نمونه است، نه الزام برای همهٔ سازمان‌ها.

### ۳.۸.۲ Service Account را Local Administrator نکنید فقط چون «کار را راه می‌اندازد»

مشکل Permission باید در همان Boundary حل شود.

اگر SQL Server به Folder خاصی نیاز دارد، Permission همان Folder را درست کنید؛ پاسخ استاندارد این نیست که Service Account را عضو Administrators کنیم.

### ۳.۸.۳ تغییر Service Account را با ابزار مناسب انجام دهید

SQL Server Configuration Manager علاوه بر تغییر Credential، تنظیمات SQL Server-specific لازم را نیز مدیریت می‌کند. تغییر دستی در services.msc برای Serviceهای SQL Server روش ترجیحی نیست. Microsoft این موضوع را در مستندات Service Accounts تصریح می‌کند.

### ۳.۸.۴ Service Account و Login را دوباره جدا کنید

```text
Windows Service Identity
        ↓
SQL Server Database Engine process

User / Application Identity
        ↓
SQL Server Login
        ↓
Database User / Permissions
```

این دقیقاً همان مرزبندی فصل اول است.

### ۳.۸.۵ مسیر سفارشی فقط با ساخت Folder آماده نمی‌شود

فرض کنید Data Path این است:

```text
D:\SQLData
```

ساخت Folder کافی نیست. Database Engine باید Permission لازم را داشته باشد.

SQL Server برای Serviceها Service SID دارد. برای Default Instance:

```text
NT SERVICE\MSSQLSERVER
```

برای Named Instance مانند ERP:

```powershell
NT SERVICE\MSSQL$ERP
```

Microsoft برای Folderهای سفارشی، اعطای Permission لازم به Service Identity/Service SID مربوط را مستند کرده است.

::: {custom-style="DBA Note"}
◆ نکتهٔ DBA

Service Account، Service SID و SQL Login سه Identity متفاوت‌اند. در Troubleshooting Permission ابتدا مشخص کنید مشکل در کدام Boundary است.
:::

## ۳.۹ Authentication Mode و SQL Administrators

SQL Server دو مدل اصلی Authentication در Windows Deployment دارد:

• Windows Authentication

• Mixed Mode، یعنی Windows + SQL Authentication

در بیشتر محیط‌های Domain-based، Windows Authentication برای حساب‌های انسانی و Service Identityهای Domain مزایای مدیریتی و امنیتی مهمی دارد.

Mixed Mode زمانی لازم می‌شود که Application یا Requirement مشخصی SQL Login بخواهد.

### ۳.۹.۱ Mixed Mode را فقط برای اینکه «شاید لازم شود» فعال نکنید

در Mixed Mode باید Credentialهای SQL Authentication را نیز مدیریت کنید.

اگر Requirement وجود ندارد، Feature اضافی را فقط به‌خاطر احتمال آینده وارد Design نکنید.

### ۳.۹.۲ دربارهٔ sa تصمیم آگاهانه بگیرید

اگر Windows Authentication هنگام Setup انتخاب شود، Login شناخته‌شدهٔ sa غیرفعال می‌ماند. حتی در Mixed Mode نیز صرف داشتن sa به معنی این نیست که باید برای کار روزمره استفاده شود. Microsoft توصیه می‌کند آن را بدون Requirement روشن فعال نکنید.

### ۳.۹.۳ SQL Administrators را با Group مدیریت کنید

به‌جای اضافه‌کردن تعداد زیادی حساب فردی به sysadmin، در محیط Domain معمولاً Group مدیریت‌شدهٔ AD عملیاتی‌تر است.

مثلاً:

```text
DOMAIN\SQL-DBA-Admins
```

اما عضویت در همان Group نیز باید تحت Governance و Audit سازمان باشد.

::: {custom-style="Warning"}
▲ هشدار

sysadmin یک Role معمولی برای راحتی کار نیست. عضو آن عملاً اختیار کامل روی Instance دارد.

جزئیات Security در فصل مربوط به خودش بررسی خواهد شد.
:::

## ۳.۱۰ Collation؛ تصمیمی کوچک در Wizard با اثر بلندمدت

Collation مجموعهٔ Ruleهایی است که SQL Server برای مقایسه و Sort داده‌های Character استفاده می‌کند.

برای مثال Collation می‌تواند مشخص کند:

• حروف بزرگ و کوچک متفاوت‌اند یا نه؛

• Accent متفاوت در نظر گرفته شود یا نه؛

• Sort و Comparison بر چه Ruleهایی انجام شوند.

Microsoft Collation را در سطح Server، Database، Column و Expression پشتیبانی می‌کند.

### ۳.۱۰.۱ CI، CS، AI و AS چه هستند؟

در Collation Name معمولاً علامت‌هایی شبیه این‌ها دیده می‌شود:

| علامت | مفهوم |
|---|---|
| CI | Case Insensitive |
| CS | Case Sensitive |
| AI | Accent Insensitive |
| AS | Accent Sensitive |

مثلاً در یک Collation دارای CI:

```text
ABC
abc
```

از نظر Case ممکن است برابر مقایسه شوند.

در CS این رفتار متفاوت است.

### ۳.۱۰.۲ Server Collation چرا برای DBA مهم است؟

Server Collation روی Environment سیستم و Defaultهایی که هنگام ساخت Databaseها و Objectهای مختلف وجود دارند اثر می‌گذارد.

System Databaseها نیز بخشی از این داستان‌اند.

tempdb در هر Startup دوباره ساخته می‌شود و Collation آن بر اساس model تعیین می‌شود. اگر User Database Collation متفاوتی داشته باشد، Queryهایی که Data متنی User Database را با Temporary Objectهای tempdb ترکیب می‌کنند می‌توانند با Collation Conflict روبه‌رو شوند. Microsoft به‌طور مشخص این Boundary را مستند کرده است.

این بدان معنا نیست که همهٔ Databaseها باید همیشه Collation یکسان داشته باشند. یعنی اختلاف باید آگاهانه باشد.

### ۳.۱۰.۳ Collation را مشاهده کنید

```sql
SELECT SERVERPROPERTY('Collation') AS ServerCollation;
```

Databaseها:

```sql
SELECT
    name,
    collation_name
FROM sys.databases
ORDER BY database_id;
```

برای دیدن model و tempdb:

```sql
SELECT
    name,
    collation_name
FROM sys.databases
WHERE name IN (N'model', N'tempdb');
```

::: {custom-style="DBA Note"}
◆ نکتهٔ DBA

Collation را فقط به‌خاطر اینکه «این گزینه Default است» انتخاب نکنید. Application Compatibility، Databaseهای موجود و استاندارد سازمان را بررسی کنید.
:::

## ۳.۱۱ اجرای SQL Server Setup با نگاه DBA

وقتی Installation Sheet کامل است، Setup باید بیشتر شبیه اجرای Design باشد تا جلسهٔ تصمیم‌گیری.

صفحه‌های دقیق Wizard ممکن است با Version تغییر کنند؛ بنابراین تمرکز روی تصمیم‌هاست.

### ۳.۱۱.۱ قبل از Install یک توقف کوتاه داشته باشید

پیش از شروع:

☐ Version/Edition تأیید شده؟

☐ Media معتبر است؟

☐ Windows Requirementها بررسی شده‌اند؟

☐ Pending Restart تعیین تکلیف شده؟

☐ Service Accountها آماده‌اند؟

☐ Folderها و Permissionها آماده‌اند؟

☐ Data/Log/tempdb Path مشخص است؟

☐ Collation مشخص است؟

☐ Authentication Mode مشخص است؟

☐ SQL Admin Group مشخص است؟

☐ Change/Ticket در صورت نیاز ثبت شده است؟

### ۳.۱۱.۲ Featureها را مطابق Requirement انتخاب کنید

Database Engine را چون لازم است نصب کنید؛ Feature دیگر را چون Requirement دارد.

Setup نباید به Component Warehouse تبدیل شود.

### ۳.۱۱.۳ Instance Configuration را با Installation Sheet تطبیق دهید

Default یا Named Instance همان چیزی باشد که Design شده است.

در Named Instance، نام را دقیقاً با Naming Convention مقایسه کنید.

### ۳.۱۱.۴ Service Accountها را همان‌جا بازبینی کنید

Engine و Agent Identityها را با Plan تطبیق دهید.

Startup Type نیز باید آگاهانه باشد.

### ۳.۱۱.۵ Collation را قبل از عبور از صفحه بررسی کنید

اشتباه Collation از آن تصمیم‌هایی نیست که دوست داشته باشیم بعد از Go-Live متوجه آن شویم.

### ۳.۱۱.۶ Database Engine Configuration

در این مرحله معمولاً موارد مهمی مانند Authentication، SQL Administrators، Data Directories و tempdb مطرح می‌شوند.

مسیرها را با Installation Sheet تطبیق دهید:

```text
Data   : D:\SQLData
Log    : E:\SQLLog
TempDB : F:\TempDB
Backup : G:\SQLBackup
```

### ۳.۱۱.۷ tempdb: Baseline، نه افسانه

برای SQL Server 2016 و بعد از آن، Microsoft توصیه می‌کند Data Fileهای tempdb Initial Size و Growth یکسان داشته باشند. برای شروع، اگر Logical Processorها هشت یا کمتر باشند می‌توان یک Data File برای هر Logical Processor در نظر گرفت؛ اگر بیشتر از هشت باشند، هشت Data File شروع رایجی است. افزایش بیشتر باید با Evidence از Allocation Contention انجام شود، نه صرفاً با Core Count.

برای Server نمونه با ۸ Logical Processor:

```text
tempdb Data Files : 8
Initial Size      : Equal
Autogrowth        : Equal
Data Path         : F:\TempDB
```

این Baseline اولیه است، نه وعدهٔ Performance.

::: {custom-style="Warning"}
▲ هشدار

قاعدهٔ «برای هر Core یک tempdb File بساز» را بدون سقف و بدون مشاهدهٔ Contention اجرا نکنید.
:::

### ۳.۱۱.۸ نتیجهٔ Setup را ثبت کنید

بعد از Setup فقط روی Close کلیک نکنید.

Microsoft Setup Logها را در مسیر Setup Bootstrap نگه می‌دارد و Summary.txt نمای کلی نتیجه را ارائه می‌کند.

مسیر معمول:

```text
%ProgramFiles%\Microsoft SQL Server\<nnn>\Setup Bootstrap\Log\
```

در صورت Failure، Error Message را با Summary و Detail Logها بررسی کنید.

::: {custom-style="Screenshot Recommendation"}
▣ اسکرین‌شات پیشنهادی

صفحهٔ نهایی Setup با قسمت Status/Feature Result، بدون نمایش اطلاعات حساس.
:::

## ۳.۱۲ پیکربندی اولیه بعد از Setup

SQL Server نصب شده است؛ حالا باید Instance را به وضعیت Operational برسانیم.

این قسمت عمداً Performance Tuning کامل نیست. هدف Day-Zero Configuration است.

### ۳.۱۲.۱ Build را ثبت و با Target مقایسه کنید

```sql
SELECT
    SERVERPROPERTY('ProductVersion')      AS ProductVersion,
    SERVERPROPERTY('ProductLevel')        AS ProductLevel,
    SERVERPROPERTY('ProductUpdateLevel')  AS ProductUpdateLevel,
    SERVERPROPERTY('Edition')             AS Edition;
```

سه چیز را ثبت کنید:

```text
Installed Build
Approved Target Build
Patch / Change Reference
```

Book نباید بگوید «همیشه CU شمارهٔ X را نصب کنید»، چون آن شماره عمر کوتاهی دارد. Build History رسمی Microsoft مرجع جاری است.

### ۳.۱۲.۲ Serviceها را بررسی کنید

```sql
SELECT
    servicename,
    startup_type_desc,
    status_desc,
    service_account,
    last_startup_time
FROM sys.dm_server_services;
```

این Query به DBA کمک می‌کند Engine و Agent و Identityهای آن‌ها را ثبت کند.

### ۳.۱۲.۳ Network را از سه لایه ببینید

برای Remote Connection فقط یک سؤال نپرسید:

«SQL Server بالا هست؟»

زنجیره را ببینید:

```text
Database Engine
      ↓
TCP/IP enabled
      ↓
Listening Port
      ↓
Windows / Network Firewall
      ↓
DNS / Server Name
      ↓
Client
```

SQL Server Configuration Manager ابزار اصلی مدیریت Protocolها و تنظیم Port در Windows است. بعد از تغییر بعضی Network Settingها، Restart Database Engine لازم می‌شود.

Default Instance معمولاً با Port ثابت مانند TCP 1433 دیده می‌شود، ولی این قانون نیست. Named Instanceها ممکن است Dynamic Port داشته باشند. SQL Server Browser نیز می‌تواند در Resolution نام Instance به Port نقش داشته باشد.

برای اتصال مستقیم به Port:

```text
tcp:SQLPROD01,51433
```

### ۳.۱۲.۴ TCP Port را از Client واقعی Test کنید

مثلاً:

```powershell
Test-NetConnection SQLPROD01 -Port 1433
```

یا Port واقعی Design:

```powershell
Test-NetConnection SQLPROD01 -Port 51433
```

نتیجهٔ موفق این دستور فقط می‌گوید Client توانسته TCP Connection به آن Host/Port برقرار کند.

نمی‌گوید SQL Login درست است، Database Permission وجود دارد یا Application Query سالم است.

پس سه Test جدا داریم:

```text
Network Reachability
SQL Authentication
Database Authorization
```

::: {custom-style="DBA Note"}
◆ نکتهٔ DBA

ping موفق به‌تنهایی SQL Connectivity را اثبات نمی‌کند.
:::

### ۳.۱۲.۵ Instant File Initialization یا IFI

وقتی SQL Server یک Data File ایجاد یا بزرگ می‌کند، بدون IFI لازم است فضای جدید ابتدا Zero-initialize شود.

IFI به Data Fileها اجازه می‌دهد در بسیاری از سناریوها بدون آن Zeroing کامل اولیه رشد کنند و در نتیجه File Creation/Growth سریع‌تر شود.

برای IFI معمول Data File، Database Engine Service باید Privilege مناسب Windows یعنی SE_MANAGE_VOLUME_NAME را داشته باشد. Microsoft توصیه می‌کند در صورت طراحی مناسب این Privilege به Database Engine Service SID داده شود تا تغییر Service Account الزاماً آن را از بین نبرد.

وضعیت را می‌توان مشاهده کرد:

```sql
SELECT
    servicename,
    instant_file_initialization_enabled
FROM sys.dm_server_services
WHERE servicename LIKE 'SQL Server (%';
```

Data File و Transaction Log را در IFI یکی نکنید.

در SQL Server 2022 و بعد از آن، Transaction Log Autogrowthهایی با اندازهٔ تا 64 MB می‌توانند از Instant Initialization جدید استفاده کنند؛ Growthهای بزرگ‌تر Log همچنان Zero-initialize می‌شوند. این رفتار کوچک Log Growth نیز به Privilege معمول IFI Data File وابسته نیست.

بنابراین:

```text
Data File IFI                 → feature اصلی IFI
Log growth ≤ 64 MB (2022+)   → رفتار ویژهٔ جدید
Large Log growth             → همچنان Zero Initialization
```

::: {custom-style="Warning"}
▲ هشدار

IFI جای Capacity Planning و Pre-sizing را نمی‌گیرد. سریع‌ترشدن Growth به معنی خوب‌بودن Autogrowth مکرر نیست.
:::

### ۳.۱۲.۶ Lock Pages in Memory یا LPIM

LPIM اجازه می‌دهد بخشی از Memory مورد استفادهٔ SQL Server در برابر Paging معمول Windows محافظت شود.

سال‌ها این توصیه زیاد تکرار می‌شد:

«روی هر SQL Server حتماً LPIM را Enable کن.»

برای یک کتاب آموزشی، این جمله بیش از حد مطلق است.

راهنمای فعلی Microsoft توصیه می‌کند LPIM را برای مسئلهٔ واقعی Memory Trimming/Paging و همراه با Memory Configuration مناسب در نظر بگیریم، نه اینکه بدون Evidence روی همهٔ Instanceها فعال شود.

پس Workflow بهتر:

```text
Establish max server memory
        ↓
Leave OS headroom
        ↓
Observe memory behavior
        ↓
Use LPIM when policy/evidence supports it
```

### ۳.۱۲.۷ max server memory را عمداً تعیین کنید

SQL Server برای Cache و اجرای Workload از Memory استفاده می‌کند و می‌تواند مصرف خود را افزایش دهد.

اما Windows نیز Memory لازم دارد.

Agentها، Backup Software، Monitoring، Antivirus و Componentهای دیگر نیز Consumer هستند.

پس مدل ذهنی این است:

```text
Physical RAM
   ↓
Windows + Drivers
   ↓
Other Services / Agents
   ↓
SQL Server Memory
   ↓
Operational Headroom
```

max server memory برای بخش مهمی از SQL Server Memory یک سقف ایجاد می‌کند؛ با این حال کل Working Set/Committed Memory پردازش sqlservr.exe می‌تواند به دلایل Allocationهایی که خارج از این Limit هستند از همان مقدار بیشتر باشد. Microsoft به همین دلیل توصیه می‌کند Headroom واقعی OS را در نظر بگیرید، نه اینکه صرفاً کل RAM منهای یک عدد ثابت را وارد کنید.

برای مشاهده:

```text
EXEC sys.sp_configure 'max server memory (MB)';
```

تغییر نمونه در Lab:

```text
EXEC sys.sp_configure 'show advanced options', 1;
RECONFIGURE;

EXEC sys.sp_configure 'max server memory (MB)', 49152;
RECONFIGURE;
```

در Server دارای ۶۴ GB RAM، مقدار 49152 MB فقط یک Worked Example برای فهم Budget است.

این توصیهٔ عمومی نیست.

برای Server واقعی باید بپرسیم:

• OS چه مقدار Memory لازم دارد؟

• Agentها چه مصرفی دارند؟

• چند Instance روی Host وجود دارد؟

• Edition/Workload چه محدودیتی دارد؟

• آیا Component دیگری روی Server اجرا می‌شود؟

• رفتار واقعی Memory بعد از Go-Live چیست؟

::: {custom-style="DBA Note"}
◆ نکتهٔ DBA

قاعدهٔ «همیشه ۸۰٪ RAM را بده» را حفظ نکنید. Memory Budget بسازید.
:::

### ۳.۱۲.۸ MAXDOP؛ نقطهٔ شروع، نه عدد جادویی

MAXDOP حداکثر Degree of Parallelism را برای بعضی Queryهای Parallel محدود می‌کند.

مقدار مناسب به Processor Topology، NUMA و Workload وابسته است.

SQL Server Setup در Versionهای جدید Recommendation اولیه ارائه می‌کند، اما همان مقدار باید به‌عنوان Baseline دیده شود، نه حکم نهایی.

Microsoft برای سیستم‌های دارای یک NUMA Node با حداکثر هشت Logical Processor، MAXDOP حداکثر تا تعداد Logical Processorها را پیشنهاد می‌کند؛ در Topologyهای بزرگ‌تر معمولاً Recommendation به NUMA و Processor Count وابسته می‌شود.

مشاهده:

```text
EXEC sys.sp_configure 'max degree of parallelism';
```

مدل درست:

```text
CPU / NUMA Topology
        +
Setup Recommendation
        +
Workload
        +
Evidence
        =
MAXDOP Decision
```

در این فصل وارد Waitها، Execution Plan Analysis، DOP Feedback و Tuning پیشرفته نمی‌شویم. آن‌ها متعلق به فصل Performance هستند.

### ۳.۱۲.۹ Snapshot اولیهٔ Configuration بسازید

حداقل این موارد را ثبت کنید:

```text
SQL Version / Edition / Build
Server Collation
Authentication Mode
Service Accounts
Data / Log / tempdb paths
tempdb file count / size / growth
TCP Port
IFI status
LPIM status
max server memory
MAXDOP
```

هدف این Snapshot این است که چند ماه بعد بتوانید پاسخ دهید:

«Server در Day Zero چگونه تحویل داده شد؟»

## ۳.۱۳ Validation و Handover

Configuration تمام شده است؛ حالا باید ثابت کنیم آن چیزی که Design کردیم همان چیزی است که واقعاً اجرا شده است.

### ۳.۱۳.۱ Service Health

```sql
SELECT
    servicename,
    status_desc,
    startup_type_desc,
    service_account,
    last_startup_time
FROM sys.dm_server_services;
```

Engine باید در وضعیت مورد انتظار باشد. Agent نیز بر اساس Operational Design بررسی شود.

### ۳.۱۳.۲ ERRORLOG را بخوانید

SQL Server ERRORLOG برای DBA فقط زمانی نیست که Server خراب شده باشد.

بعد از Installation، Startup Messageها اطلاعات مفیدی مانند Listening، Build، Startup Optionها و Errorهای اولیه نشان می‌دهند.

به‌دنبال موارد غیرمنتظره باشید:

• Error در Startup

• File Path نامعتبر

• Permission Problem

• Network Listener مشکل‌دار

• Database Recovery Error

• Startup Warning غیرمنتظره

### ۳.۱۳.۳ System Databaseها را بررسی کنید

```sql
SELECT
    name,
    state_desc,
    recovery_model_desc,
    collation_name
FROM sys.databases
WHERE database_id <= 4
ORDER BY database_id;
```

master، model، msdb و tempdb باید وضعیت مورد انتظار داشته باشند.

### ۳.۱۳.۴ مسیر واقعی Databaseها را با Design مقایسه کنید

```sql
SELECT
    DB_NAME(database_id) AS DatabaseName,
    type_desc,
    physical_name
FROM sys.master_files
ORDER BY database_id, file_id;
```

این Query به شما می‌گوید فایل‌ها واقعاً کجا هستند.

Documentation نباید از Installation Sheet کپی شود بدون اینکه Implementation بررسی شده باشد.

### ۳.۱۳.۵ tempdb را از داخل SQL Server بررسی کنید

```sql
USE tempdb;
GO

SELECT
    file_id,
    name,
    type_desc,
    size / 128.0 AS SizeMB,
    growth,
    is_percent_growth,
    physical_name
FROM sys.database_files
ORDER BY file_id;
GO
```

بررسی کنید:

• Data File Count

• Equal Initial Size

• Growth Setting

• Path

• Log File

### ۳.۱۳.۶ Collation را Verify کنید

```sql
SELECT
    SERVERPROPERTY('Collation') AS ServerCollation;

SELECT
    name,
    collation_name
FROM sys.databases
WHERE name IN (N'master', N'model', N'msdb', N'tempdb');
```

اگر Application Database از قبل وجود دارد، Collation آن نیز جداگانه ثبت شود.

### ۳.۱۳.۷ Connection را در چند Boundary آزمایش کنید

Test اول: Local DBA Connection.

Test دوم: Remote DBA Connection.

Test سوم: Application Connection با Identity و Connection String واقعی یا معادل Test آن.

یک اتصال موفق SSMS با حساب sysadmin از خود Server، اثبات نمی‌کند Application از Subnet دیگر با Service Account خودش موفق خواهد بود.

### ۳.۱۳.۸ Build را با Target Patch مقایسه کنید

ثبت کنید:

```text
Installed Build:
Approved Build:
Patch Applied:
Reboot Required:
Validation Result:
```

Patch بدون Validation نهایی کامل نیست.

### ۳.۱۳.۹ Day-Zero Baseline بسازید

Baseline قبل از Workload کامل، Benchmark Production نیست.

اما Snapshot اولیه بسیار ارزشمند است.

ثبت کنید:

| حوزه | نمونه |
|---|---|
| CPU | Logical Processor Count |
| Memory | Physical RAM، max server memory |
| Storage | Volume Size / Free Space |
| SQL | Version / Edition / Build |
| tempdb | File Count / Size / Growth |
| Network | Protocol / Port |
| Security | Service Accounts / Auth Mode |
| Configuration | MAXDOP / IFI / LPIM |
| Logs | Startup ERRORLOG وضعیت اولیه |

Baseline بعداً به یک سؤال بسیار مهم کمک می‌کند:

«چه چیزی نسبت به Day Zero تغییر کرده است؟»

Baseline مفهوم اصلی Monitoring و Performance Troubleshooting است و Microsoft نیز برای ارزیابی عملکرد، داشتن Snapshot/Metricهای اولیهٔ CPU، Memory، I/O و Workload را مبنای مقایسه می‌داند.

### ۳.۱۳.۱۰ As-Built Document بسازید

Installation Plan می‌گوید قرار بود چه کاری انجام شود.

As-Built می‌گوید در نهایت چه چیزی ساخته شد.

نمونه:

| مورد | مقدار واقعی |
|---|---|
| Server | SQLPROD01 |
| Instance | MSSQLSERVER |
| Version | SQL Server 2025 |
| Edition | Enterprise |
| Build | ثبت شود |
| Engine Account | ثبت شود |
| Agent Account | ثبت شود |
| Authentication | ثبت شود |
| Collation | ثبت شود |
| Data Path | `D:\SQLData` |
| Log Path | `E:\SQLLog` |
| TempDB Path | `F:\TempDB` |
| Backup Stage | `G:\SQLBackup` |
| TCP Port | ثبت شود |
| IFI | Enabled / Disabled |
| LPIM | Enabled / Disabled |
| max server memory | ثبت شود |
| MAXDOP | ثبت شود |

### ۳.۱۳.۱۱ Checklist نهایی تحویل

☐ Windows Resourceها با Design تطبیق داده شده‌اند.

☐ Pending Restart تعیین تکلیف شده است.

☐ Volumeها و Free Space بررسی شده‌اند.

☐ Allocation Unit Size ثبت شده است.

☐ Version، Edition و Build ثبت شده‌اند.

☐ Instance Name مطابق Naming Convention است.

☐ Featureهای غیرضروری نصب نشده‌اند.

☐ Service Accountها تأیید شده‌اند.

☐ Permission مسیرهای سفارشی بررسی شده است.

☐ Authentication Mode مطابق Requirement است.

☐ SQL Administrator Group ثبت شده است.

☐ Server Collation تأیید شده است.

☐ Data/Log/tempdb Paths تأیید شده‌اند.

☐ tempdb File Count، Size و Growth بررسی شده‌اند.

☐ TCP/IP و Port بررسی شده‌اند.

☐ Remote Connection Test موفق است.

☐ Application Connection Test انجام شده است.

☐ IFI وضعیت مشخصی دارد.

☐ LPIM در صورت نیاز و با دلیل پیکربندی شده است.

☐ max server memory عمداً تعیین شده است.

☐ MAXDOP Baseline ثبت شده است.

☐ ERRORLOG بررسی شده است.

☐ Setup Logها در صورت نیاز بررسی شده‌اند.

☐ Day-Zero Baseline ثبت شده است.

☐ As-Built Document کامل شده است.

::: {custom-style="DBA Note"}
◆ نکتهٔ DBA

Server زمانی تحویل‌پذیر است که DBA بتواند توضیح دهد:

چه چیزی نصب شده، چرا این‌گونه نصب شده، اکنون در چه وضعیتی است و نفر بعدی چگونه می‌تواند آن را بفهمد.
:::

این همان نقطه‌ای است که Installation از «نصب نرم‌افزار» به عملیات DBA تبدیل می‌شود.

سناریوی Production اول — ERP تراکنشی

یک VM با این مشخصات تحویل شده است:

```text
16 vCPU
128 GB RAM
Production OLTP
Default Instance
Dedicated Data / Log / tempdb volumes
```

اشتباه این است که فقط به‌خاطر ۱۶ vCPU شانزده tempdb Data File بسازیم، max server memory را با فرمول اینترنتی تعیین کنیم و MAXDOP را بدون توجه به Topology روی عددی ثابت بگذاریم.

روش بهتر:

```text
Verify resources
→ confirm storage mapping
→ start tempdb with evidence-based baseline
→ create memory budget
→ review Setup MAXDOP recommendation/topology
→ validate after workload arrives
```

سناریوی Production دوم — Reporting Server

Server دوم همان ۱۶ vCPU و ۱۲۸ GB RAM را دارد، اما Workload آن Reporting و Queryهای طولانی است.

Resource مساوی به معنی Configuration مساوی نیست.

Memory Demand، Parallelism Behavior، tempdb Usage و I/O Pattern ممکن است با OLTP کاملاً متفاوت باشند.

فصل Performance بعداً این تفاوت را عمیق‌تر بررسی می‌کند. در Chapter 3 فقط یاد می‌گیریم Configuration اولیه را قابل اندازه‌گیری و قابل بازنگری بسازیم.

سناریوی Production سوم — Named Instance پشت Firewall

Application باید به:

```text
SQLAPP01\ERP
```

متصل شود، اما Security Team فقط Port ثابت را در Firewall باز می‌کند.

Design بهتر می‌تواند استفاده از TCP Port ثابت باشد:

```text
tcp:SQLAPP01,51433
```

سپس:

```powershell
Test-NetConnection SQLAPP01 -Port 51433
```

و در مرحلهٔ بعد، Connection واقعی SQL/Application Test می‌شود.

این سناریو نشان می‌دهد:

Instance Name، Browser، TCP Port، Firewall و Authentication یک مسئله نیستند؛ چند Boundary متوالی‌اند.

تمرین عملی اول — Installation Plan

برای Server زیر Installation Sheet بسازید:

```text
Server: SQLLAB01
CPU: 8 vCPU
RAM: 64 GB
Environment: Lab
Workload: OLTP Training
```

این موارد را تعیین کنید:

• Version/Edition

• Instance Type

• Service Accounts

• Authentication

• Collation

• Data/Log/tempdb Paths

• TCP Port

• Target Build

سپس توضیح دهید کدام تصمیم قطعی است و کدام هنوز به اطلاعات Application یا Infrastructure نیاز دارد.

تمرین عملی دوم — Pre-install Verification

دستورهای زیر را اجرا کنید:

```powershell
$cs = Get-CimInstance Win32_ComputerSystem

[pscustomobject]@{
    ComputerName      = $env:COMPUTERNAME
    LogicalProcessors = $cs.NumberOfLogicalProcessors
    MemoryGB          = [math]::Round($cs.TotalPhysicalMemory / 1GB, 1)
    Domain            = $cs.Domain
}
```

و:

```powershell
Get-Volume |
    Where-Object DriveLetter |
    Select-Object DriveLetter, FileSystemLabel, FileSystem, AllocationUnitSize,
        @{Name='SizeGB';Expression={[math]::Round($_.Size / 1GB, 1)}},
        @{Name='FreeGB';Expression={[math]::Round($_.SizeRemaining / 1GB, 1)}}
```

برای Volume آزمایش:

```console
cmd
```

```console
fsutil fsinfo ntfsinfo D:
```

خروجی را با Installation Sheet مقایسه کنید.

تمرین عملی سوم — SQL Validation

بعد از Installation، این Queryها را در یک Script ذخیره و اجرا کنید:

```sql
SELECT
    SERVERPROPERTY('ProductVersion')      AS ProductVersion,
    SERVERPROPERTY('ProductLevel')        AS ProductLevel,
    SERVERPROPERTY('ProductUpdateLevel')  AS ProductUpdateLevel,
    SERVERPROPERTY('Edition')             AS Edition,
    SERVERPROPERTY('Collation')           AS ServerCollation;
```

```sql
SELECT
    servicename,
    startup_type_desc,
    status_desc,
    service_account,
    instant_file_initialization_enabled
FROM sys.dm_server_services;
```

```sql
SELECT
    name,
    collation_name
FROM sys.databases
ORDER BY database_id;
```

```sql
USE tempdb;
GO

SELECT
    file_id,
    name,
    type_desc,
    size / 128.0 AS SizeMB,
    growth,
    is_percent_growth,
    physical_name
FROM sys.database_files
ORDER BY file_id;
```

خروجی را به As-Built Document تبدیل کنید.

تمرین عملی چهارم — Day-Zero Handover

یک Handover Package بسازید که حداقل شامل این موارد باشد:

```text
Installation Sheet
As-Built Configuration
SQL Build
Service Accounts
Collation
Data / Log / tempdb paths
tempdb configuration
Network port
IFI status
LPIM decision
max server memory
MAXDOP
ERRORLOG review result
Connection test
Day-Zero resource snapshot
```

فرض کنید DBA دیگری شش ماه بعد Server را تحویل می‌گیرد. سند شما باید بدون حضور شما پاسخ دهد:

«این Instance چگونه ساخته شده و وضعیت اولیهٔ مورد انتظارش چه بوده است؟»

## جمع‌بندی فصل

در این فصل دیدیم نصب SQL Server از دید DBA یک Wizard نیست؛ یک زنجیرهٔ تصمیم و Verification است.

پیش از Setup نقش Server، Resourceها، Storage Pathها، Version/Edition، Instance، Service Identity، Authentication و Collation مشخص می‌شوند.

حین Setup، Design پیاده‌سازی می‌شود؛ Featureها، Serviceها، Data Directoryها و tempdb کنترل می‌شوند.

بعد از Setup، Build، Network، IFI، LPIM، Memory و MAXDOP بررسی می‌شوند.

در پایان، Serviceها، ERRORLOG، System Databaseها، File Pathها، tempdb، Collation، Connection و Build اعتبارسنجی می‌شوند و Day-Zero Baseline و As-Built Document ساخته می‌شود.

اگر بخواهیم کل فصل را در یک جمله خلاصه کنیم:

نصب SQL Server زمانی تمام شده است که Instance نه‌فقط Running، بلکه قابل توضیح، قابل بررسی و قابل تحویل باشد.

در فصل بعد، از سطح Instance یک لایه پایین‌تر می‌رویم و به خود Database می‌رسیم: فایل‌ها، Filegroupها، Initial Size، Growth و تصمیم‌هایی که مشخص می‌کنند Database چگونه روی Storage زندگی خواهد کرد.

# فصل چهارم — مدیریت Database، فایل‌ها و رشد

در فصل اول دیدیم که Database یک شیء منطقی برای نگه‌داری و پردازش داده است، نه یک پوشهٔ ساده در Windows. در فصل دوم مسیر I/O را از Windows Volume تا VMware و Storage دنبال کردیم و در فصل سوم یاد گرفتیم که پیش از نصب SQL Server باید مسیرهای Data، Transaction Log و tempdb را آگاهانه انتخاب و سپس نتیجه را Verify کنیم. این فصل همان نگاه را یک سطح پایین‌تر ادامه می‌دهد: حالا یک Database مشخص را طراحی می‌کنیم، می‌سازیم، ظرفیت آن را اندازه می‌گیریم و برای تحویل عملیاتی مستند می‌کنیم.

دیدن Database در Object Explorer به‌تنهایی نشانهٔ آماده‌بودن آن نیست. ممکن است Database در SSMS ظاهر شود، اما Data File با اندازهٔ اولیهٔ نامناسب ساخته شده باشد، Log روی Volume اشتباه قرار گرفته باشد، Collation با نیاز Application هماهنگ نباشد، Recovery Model انتخاب‌شده Backup Strategy نداشته باشد یا فایل در آستانهٔ پرشدن باشد.

یک نمونهٔ واقعی را تصور کنید: تیم Application یک Database جدید را در چند دقیقه می‌سازد. چند هفته بعد، Import بزرگ اجرا می‌شود؛ Data File بارها Grow می‌کند، Log Backup Job از کار افتاده است و D: نیز به Datastore مشترکی متصل است که فضای آزاد کمی دارد. Database هنوز در SSMS Online دیده می‌شود، اما اولین Transaction بزرگ با خطای کمبود فضا متوقف می‌شود. مسئله یک Setting منفرد نیست؛ مسئله نبودن Design، ظرفیت‌سنجی و Verification است.

مدل ذهنی این فصل چنین است:

```text
Database Requirement
        ↓
Database Design
        ↓
CREATE DATABASE
        ↓
Initial Configuration
        ↓
File and Capacity Validation
        ↓
Monitoring Baseline
        ↓
Documentation & Handover
```

در این فصل

- رابطهٔ Database، Filegroup، Data File و Transaction Log را می‌بینید.

- پیش از ایجاد Database یک Database Design Sheet تهیه می‌کنید.

- Database را با SSMS و T-SQL می‌سازید و تنظیمات واقعی را Verify می‌کنید.

- Collation، Recovery Model، model، Initial Size، FILEGROWTH و MAXSIZE را عملیاتی بررسی می‌کنید.

- Data File، Filegroup، Log و Windows Volume Full را از هم تشخیص می‌دهید.

- فضای آزاد داخلی Data File، مصرف Log و ظرفیت Volume را اندازه می‌گیرید.

- دلیل واقعی استفاده از چند Data File یا Filegroup را می‌سنجید.

- File و Filegroup را با پیش‌شرط، هشدار و Verification مدیریت می‌کنید.

- Database As-Built و Handover Checklist می‌سازید.

## ۴.۱ Database از دید منطقی و فیزیکی

در SSMS، SalesDB یک نام زیر شاخهٔ Databases است؛ اما Database Engine برای نگه‌داری آن از فایل‌های فیزیکی استفاده می‌کند. حداقل، یک Database معمولی به Data File و Transaction Log File نیاز دارد.

```text
SalesDB (logical database)
├── PRIMARY Filegroup
│   ├── SalesDB_Data  →  D:\SQLData\SalesDB.mdf
│   └── SalesDB_Data2 →  D:\SQLData\SalesDB_02.ndf
└── Transaction Log
    └── SalesDB_Log   →  E:\SQLLog\SalesDB_log.ldf
```

Data Fileها Pageهای داده و Objectهایی مانند Table، Index، View و Stored Procedure را نگه می‌دارند. Data Fileها عضو Filegroup هستند. Transaction Log File تغییرات لازم برای Transaction Management، Durability و Recovery را ثبت می‌کند و عضو هیچ Filegroupی نیست.

```text
Database
 ├─ Filegroup
 │   └─ Data File(s)
 └─ Transaction Log File(s)

Data File → Windows Volume → VMDK/Virtual Disk → VMware Datastore → Storage Backend
Log File  → Windows Volume → VMDK/Virtual Disk → VMware Datastore → Storage Backend
```

حرف درایو، مانند D: یا E:, فقط نام یک Windows Volume است. همان‌طور که در فصل دوم دیدیم، دو Volume جدا ممکن است پشت‌صحنه روی یک Datastore یا آرایهٔ Storage مشترک باشند. بنابراین جداسازی منطقی مسیرها مفید است، اما به‌خودی‌خود IOPS مستقل ایجاد نمی‌کند.

### ۴.۱.۱ سه لایهٔ فضا

برای هر Data File سه عدد متفاوت مهم است:

```text
Windows Volume capacity
        └── Physical Data File size
                ├── Used space inside file
                └── Free internal space
```

Free internal space قبلاً از Windows گرفته شده و آمادهٔ Allocation داخل File است. Free space روی Volume هنوز به File تعلق ندارد و SQL Server فقط با Grow کردن File یا ساختن File جدید می‌تواند آن را وارد Database کند.

::: {custom-style="DBA Note"}
◆ نکتهٔ DBA برای این بخش، مقدار واقعی را با Design Sheet و نتیجهٔ Verification تطبیق دهید.
:::

هر بار که کسی گفت «فضای Database کم است»، سؤال بعدی باید این باشد: فضای داخل Data File، فضای Filegroup، فضای Transaction Log یا فضای Windows Volume؟ پاسخ این چهار سؤال یکسان نیست.

## ۴.۲ Database Design Sheet پیش از ایجاد

ساخت Database باید نتیجهٔ یک تصمیم باشد، نه شروع تصمیم‌گیری. Design Sheet زیر را پیش از CREATE تکمیل کنید. مقدارها نمونه نیستند؛ محل ثبت تصمیم واقعی پروژه‌اند.

| فیلد | مقدار طراحی |
|---|---|
| Database Name | `SalesDB` |
| Purpose / Application | سامانهٔ فروش و سفارش |
| Environment | Production / Test / Development |
| Workload | OLTP، گزارش‌گیری، Import دوره‌ای |
| Owner | تیم یا Login مسئول |
| Data Path | `D:\SQLData` |
| Log Path | `E:\SQLLog` |
| Initial Data Size | بر پایهٔ حجم فعلی و Import اولیه |
| Initial Log Size | بر پایهٔ بزرگ‌ترین Transaction و عملیات نگه‌داری |
| Data FILEGROWTH | Increment ثابت و قابل پایش |
| Log FILEGROWTH | جداگانه، متناسب با Log Workload |
| MAXSIZE | سقف هر File طبق ظرفیت و سیاست سازمان |
| Filegroup Design | `PRIMARY` یا گروه‌های دارای دلیل مشخص |
| Default Filegroup | Filegroup هدف برای Allocationهای بدون مقصد صریح |
| Recovery Model | `SIMPLE`، `FULL` یا `BULK_LOGGED` |
| Database Collation | نیاز Application و زبان داده |
| RPO | حداکثر دادهٔ قابل از دست رفتن |
| RTO | زمان هدف برای بازگشت سرویس |
| Backup Responsibility | تیم، Job و محل Backup |
| Monitoring Thresholds | رشد، فضای Volume، Log و Jobها |
| Change / Ticket Reference | شمارهٔ Change یا Ticket |

Size و Growth از جدول‌های اینترنتی کپی نمی‌شوند. آن‌ها به Workload، اندازهٔ فعلی Database، نرخ رشد، ظرفیت فعلی همهٔ Databaseها، مدت عملیات Maintenance، RPO/RTO و زمان لازم برای تهیهٔ Storage جدید وابسته‌اند. اگر این داده‌ها موجود نیستند، Design Sheet باید «نیازمند اندازه‌گیری» را ثبت کند، نه یک عدد ساختگی.

### ۴.۲.۱ پرسش‌هایی که پیش از CREATE باید پاسخ داشته باشند

- چه Applicationهایی به Database وصل می‌شوند و آیا Collation یا Compatibility Requirement دارند؟

- حجم فعلی، حجم Import اولیه و رشد ماهانه چقدر است؟

- بزرگ‌ترین Transaction، Index Rebuild یا Batch چه مقدار Log تولید می‌کند؟

- Backup در کجا ذخیره و چه کسی موفقیت آن را کنترل می‌کند؟

- Data و Log در کدام Volume قرار می‌گیرند و ظرفیت واقعی آن Volume چیست؟

- آیا Filegroup اضافی یک نیاز عملیاتی است یا صرفاً یک نام تزئینی؟

## ۴.۳ Database Collation و ارتباط آن با فصل سوم

Server Collation ویژگی سطح Instance است؛ Database Collation ویژگی خود Database. وقتی Collation را هنگام CREATE DATABASE صریحاً تعیین نمی‌کنید، Database معمولاً Collation را از model می‌گیرد؛ و model نیز در محیط عادی تحت تأثیر Collation Instance قرار می‌گیرد. این زنجیره به معنی آن نیست که DBA می‌تواند بدون بررسی فرض کند نتیجه درست است.

Collation روی مقایسه و مرتب‌سازی رشته‌ها، حساسیت به حروف، و رفتار برخی عملیات متنی اثر دارد. اگر Application یا دادهٔ واردشونده نیاز مشخصی دارد، آن نیاز باید پیش از CREATE معلوم باشد. تغییر Collation بعداً ممکن است به بازسازی ستون‌ها، Indexها و Constraintها، حل Conflictهای داده و Downtime نیاز داشته باشد.

```sql
SELECT
    name,
    collation_name
FROM sys.databases
WHERE name = N'SalesDB';
```

برای دیدن Collationهای Server و model:

```sql
SELECT
    SERVERPROPERTY('Collation') AS ServerCollation;
GO

SELECT
    name,
    collation_name
FROM sys.databases
WHERE name IN (N'model', N'SalesDB');
```

::: {custom-style="Important Note"}
● نکتهٔ مهم برای این بخش، مقدار واقعی را با Design Sheet و نتیجهٔ Verification تطبیق دهید.
:::

model یک الگوی عملیاتی برای Databaseهای جدید است، نه جایگزین Verification. قبل از تحویل، Collation خود Database را از sys.databases بخوانید و با Design Sheet مقایسه کنید.

## ۴.۴ Recovery Model

Recovery Model تعیین می‌کند SQL Server چگونه Log را برای Truncation و Backup مدیریت کند و چه نوع Recoveryای در دسترس باشد. این Property جای Backup را نمی‌گیرد.

| Recovery Model | Log Backup | Point-in-time Recovery | کاربرد معمول |
|---|---|---|---|
| `SIMPLE` | ندارد | ندارد | داده‌هایی که از دست‌رفتن تغییرات بین Backupها پذیرفتنی است |
| `FULL` | دارد | دارد، با زنجیرهٔ Log Backup | Production با RPO محدود |
| `BULK_LOGGED` | دارد | محدود هنگام برخی Bulk Operationها | انتخاب تخصصی و موقت در شرایط کنترل‌شده |

در SIMPLE نیز Transaction Log وجود دارد و برای Recovery داخلی و Transactionهای جاری ضروری است. تفاوت اصلی این است که SQL Server پس از Checkpoint می‌تواند بخش‌هایی از Log را برای استفادهٔ مجدد علامت‌گذاری کند و Log Backup برای حفظ زنجیرهٔ Recovery وجود ندارد.

در FULL، تغییر Property به‌تنهایی طراحی Recovery را کامل نمی‌کند. پس از تغییر به FULL، برای شروع زنجیرهٔ مناسب باید یک Full Database Backup تهیه شود و سپس Log Backupها با برنامهٔ متناسب با RPO اجرا و موفقیتشان پایش شوند. اگر Log Backup Job متوقف شود، LOG_BACKUP می‌تواند مانع Reuse شود و Log به رشد ادامه دهد.

BULK_LOGGED برای کاهش حجم Log برخی عملیات Bulk طراحی شده، اما در صورت وجود Bulk-logged Changes، Point-in-time Restore درون Log Backup مربوط ممکن نیست. این گزینه باید با طرح Backup/Restore و پنجرهٔ عملیاتی هماهنگ باشد.

```sql
USE master;
GO

ALTER DATABASE SalesDB
SET RECOVERY FULL;
GO
```

```sql
SELECT
    name,
    recovery_model_desc,
    log_reuse_wait_desc
FROM sys.databases
WHERE name = N'SalesDB';
```

FULL بدون Log Backup، محافظت خودکار نیست. RPO می‌گوید چه مقدار داده قابل از دست رفتن است و RTO می‌گوید سرویس باید در چه مدتی بازگردد؛ انتخاب Recovery Model باید هر دو را در نظر بگیرد. جزئیات کامل Backup Chain و Restore در فصل Backup و Restore بررسی می‌شود.

### ۴.۴.۱ اثر model بر Recovery Model

ویژگی‌هایی مانند Recovery Model و برخی تنظیمات File هنگام ساخت Database از model اثر می‌پذیرند. پس از CREATE، مقدار واقعی Database را بررسی کنید. تغییر model، Databaseهای موجود را بازپیکربندی نمی‌کند؛ تغییر روی Database موجود باید صریحاً روی همان Database انجام شود.

::: {custom-style="Warning"}
▲ هشدار برای این بخش، مقدار واقعی را با Design Sheet و نتیجهٔ Verification تطبیق دهید.
:::

برای Production فقط به این دلیل که model روی FULL است، Recovery را آماده فرض نکنید. وجود Full Backup، زنجیرهٔ Log Backup، Job موفق و مسئول مشخص باید اثبات شود.

## ۴.۵ ایجاد Database با SSMS و T-SQL

### ۴.۵.۱ ساخت با SSMS

در Object Explorer مسیر زیر را باز کنید:

Databases ← کلیک راست ← New Database...

در پنجرهٔ New Database، نام، جدول Database Files، Logical Name، File Type، Initial Size، مسیر Physical File، Autogrowth، MAXSIZE و Filegroup را بررسی کنید. سپس در Options، Collation، Recovery Model و Owner را با Design Sheet مقایسه کنید. Wizard برای Lab مفید است، اما نتیجهٔ آن باید به Script یا As-Built قابل بازبینی تبدیل شود.

::: {custom-style="Screenshot Recommendation"}
▣ اسکرین‌شات پیشنهادی برای این بخش، مقدار واقعی را با Design Sheet و نتیجهٔ Verification تطبیق دهید.
:::

از صفحهٔ Database Properties در بخش Files، فقط زمانی تصویر بگیرید که برای آموزش جای کنترل‌ها مهم است؛ تصویر نباید جای توضیح Design و Verification را بگیرد.

### ۴.۵.۲ ساخت با T-SQL

پیش‌شرط: پوشه‌های D:\SQLData و E:\SQLLog باید از قبل وجود داشته باشند و هویت سرویس Database Engine روی آن‌ها مجوز مناسب داشته باشد. همان‌طور که در فصل سوم دربارهٔ Service SID و Permission مسیرها دیدیم، مجوز حساب کاربر شما با مجوز Service Identity یکی نیست.

```sql
USE master;
GO

CREATE DATABASE SalesDB
ON PRIMARY
(
    NAME = N'SalesDB_Data',
    FILENAME = N'D:\SQLData\SalesDB.mdf',
    SIZE = 512MB,
    MAXSIZE = 100GB,
    FILEGROWTH = 256MB
)
LOG ON
(
    NAME = N'SalesDB_Log',
    FILENAME = N'E:\SQLLog\SalesDB_log.ldf',
    SIZE = 256MB,
    MAXSIZE = 50GB,
    FILEGROWTH = 128MB
);
GO
```

اعداد این مثال آموزشی‌اند و برای همهٔ Productionها Standard نیستند. قبل از اجرا، مسیر، ظرفیت، اندازهٔ Import، Workload و Change/Ticket را بررسی کنید.

### ۴.۵.۳ پیکربندی و Verification پس از CREATE

```sql
USE master;
GO

ALTER DATABASE SalesDB
SET RECOVERY FULL;
GO

ALTER AUTHORIZATION ON DATABASE::SalesDB TO [sa];
GO
```

تغییر Owner باید مطابق سیاست امنیتی سازمان باشد؛ استفاده از sa در اینجا فقط نمونهٔ آموزشی است و نباید بدون بررسی به‌عنوان سیاست عمومی کپی شود.

```sql
SELECT
    d.name,
    d.state_desc,
    SUSER_SNAME(d.owner_sid) AS owner_name,
    d.recovery_model_desc,
    d.collation_name,
    d.log_reuse_wait_desc
FROM sys.databases AS d
WHERE d.name = N'SalesDB';
GO

USE SalesDB;
GO

SELECT
    file_id,
    name AS logical_file_name,
    type_desc,
    physical_name,
    size * 8.0 / 1024 AS size_mb,
    growth,
    is_percent_growth,
    max_size,
    state_desc
FROM sys.database_files
ORDER BY file_id;
```

## ۴.۶ Logical File Name و Physical File Name

Logical File Name نامی است که SQL Server برای شناسایی File در Metadata استفاده می‌کند. Physical File Name مسیر واقعی فایل در Windows است.

```text
Logical File Name:  SalesDB_Data
Physical File Name: D:\SQLData\SalesDB.mdf
```

نمونهٔ نادرست:

```text
SalesDB\_Data
sys.database\_files
```

نمونهٔ درست:

```sql
SalesDB_Data
sys.database_files
```

در Markdown یا متن فارسی، Underscore نباید با Backslash جعلی نمایش داده شود. در دستورهای مدیریتی مانند ALTER DATABASE ... MODIFY FILE، مقدار NAME باید Logical File Name باشد، نه مسیر Windows.

```sql
USE SalesDB;
GO

SELECT
    name,
    physical_name
FROM sys.database_files;
```

## ۴.۷ MDF، NDF و LDF

پسوندها قراردادهای رایج‌اند، نه تعریف معماری:

| نوع | پسوند رایج | نقش |
|---|---|---|
| Primary Data File | `.mdf` | یک Data File اصلی با اطلاعات ساختاری Database |
| Secondary Data File | `.ndf` | Data File اضافی در یک یا چند Filegroup |
| Transaction Log File | `.ldf` | ثبت Log و عملیات Recovery |

هر Database یک Primary Data File دارد، اما یک Filegroup می‌تواند چند Data File داشته باشد. افزودن .ndf به‌خودی‌خود سرعت را افزایش نمی‌دهد؛ سود احتمالی به Filegroup، Allocation Contention، ظرفیت Volume و محل واقعی Storage بستگی دارد. چند .ldf نیز معمولاً Scaling عملکردی ایجاد نمی‌کند، چون Log به‌صورت ترتیبی در چرخهٔ Log استفاده می‌شود. Log File عضو Filegroup نیست.

## ۴.۸ Filegroup

Filegroup یک Container منطقی برای گروه‌بندی Data Fileها و هدایت Allocation است.

```text
SalesDB
├── PRIMARY
│   └── SalesDB_Data.mdf
├── FG_History
│   └── SalesDB_History01.ndf
└── Transaction Log
    └── SalesDB_Log.ldf
```

PRIMARY در همهٔ Databaseهای عادی وجود دارد. Primary Data File در آن قرار می‌گیرد و Objectهایی که مقصد دیگری ندارند، معمولاً به Default Filegroup می‌روند.

این گزاره غلط است:

```text
PRIMARY Filegroup = MDF
```

PRIMARY یک Filegroup و MDF یک Data File است. یک Filegroup می‌تواند چند Data File داشته باشد. ساختن Filegroup، Objectهای موجود را جابه‌جا نمی‌کند و افزودن Data File نیز داده‌های قبلی را خودکار توزیع مجدد نمی‌کند. FG_History فقط یک نام است و تا وقتی Objectها صریحاً در آن ساخته یا منتقل نشوند، دادهٔ تاریخی در آن قرار نمی‌گیرد.

```sql
USE master;
GO

ALTER DATABASE SalesDB
ADD FILEGROUP FG_History;
GO

ALTER DATABASE SalesDB
ADD FILE
(
    NAME = N'SalesDB_History01',
    FILENAME = N'D:\SQLData\SalesDB_History01.ndf',
    SIZE = 512MB,
    MAXSIZE = 200GB,
    FILEGROWTH = 256MB
)
TO FILEGROUP FG_History;
GO
```

برای قرار دادن Object جدید:

```sql
USE SalesDB;
GO

CREATE TABLE dbo.SalesHistory
(
    HistoryID bigint NOT NULL,
    SaleDate date NOT NULL,
    Amount decimal(19, 4) NOT NULL
)
ON FG_History;
GO
```

Default Filegroup فقط روی Allocationهای آینده‌ای اثر می‌گذارد که Filegroup صریحی ندارند؛ Objectهای موجود را جابه‌جا نمی‌کند.

```sql
ALTER DATABASE SalesDB
MODIFY FILEGROUP FG_History DEFAULT;
GO
```

Partitioning می‌تواند Allocation را بر اساس Range یا معیار دیگر مدیریت کند، اما به Filegroup بیشتر، طراحی Index و سیاست Maintenance نیاز دارد. جزئیات Partitioning پیشرفته خارج از محدودهٔ این فصل است.

## ۴.۹ Initial Size و Pre-sizing

Initial Size مقدار فضایی است که File هنگام ایجاد از Windows می‌گیرد. Pre-sizing یعنی فضای موردنیاز قابل پیش‌بینی را پیش از آنکه Database مجبور به Growth شود، رزرو کنیم.

برای انتخاب Initial Size این عوامل را کنار هم بگذارید:

- حجم فعلی Database یا حجم Import اولیه؛

- رشد پیش‌بینی‌شده در دورهٔ مورد توافق؛

- Headroom برای رشد عادی و خطاهای کوتاه‌مدت؛

- فضای سایر Databaseها و Backup/Staging؛

- ظرفیت Volume و زمان لازم برای افزودن Storage؛

- بزرگ‌ترین Transaction، Index Maintenance و Batch؛

- زمان قابل‌تحمل برای Initialization و Growth.

Data و Log جداگانه Size می‌شوند. Log باید بتواند Transactionهای معمول، بزرگ‌ترین Transaction برنامه‌ریزی‌شده و فاصلهٔ بین Log Backupها را پوشش دهد. اندازهٔ Log برابر با اندازهٔ Data نیست.

Pre-sizing به معنی گرفتن کل فضای پنج سال آینده از روز اول نیست. اگر Storage محدود است، رشد مرحله‌ای و پایش‌شده منطقی‌تر است. اگر Migration فردا انجام می‌شود، شروع از File بسیار کوچک و ایجاد ده‌ها Growth در زمان Import، ریسک و زمان غیرضروری ایجاد می‌کند.

IFI برای Zero Initialization Data File می‌تواند زمان برخی عملیات را کاهش دهد؛ این نکته در فصل سوم معرفی شد. Log رفتار جداگانه‌ای دارد. در SQL Server 2022، رشدهای Transaction Log تا ۶۴ MB می‌توانند از بهبود مربوط به IFI بهره ببرند؛ این نکته جای Pre-sizing و انتخاب Growth مناسب را نمی‌گیرد.

## ۴.۱۰ Autogrowth، FILEGROWTH و MAXSIZE

Autogrowth یک Safety Mechanism است: اگر Allocation به فضای بیشتری نیاز داشته باشد، SQL Server در صورت وجود شرایط لازم File را بزرگ می‌کند. Autogrowth Capacity Strategy نیست؛ Capacity Strategy باید بر پیش‌بینی، پایش و رشد برنامه‌ریزی‌شده بنا شود.

FILEGROWTH می‌تواند ثابت یا درصدی باشد:

```sql
ALTER DATABASE SalesDB
MODIFY FILE
(
    NAME = N'SalesDB_Data',
    FILEGROWTH = 1024MB
);
GO

ALTER DATABASE SalesDB
MODIFY FILE
(
    NAME = N'SalesDB_Log',
    FILEGROWTH = 512MB
);
GO
```

Growth درصدی با بزرگ‌شدن File، Increment بزرگ‌تری تولید می‌کند و ممکن است ناگهان چند ده گیگابایت فضا بخواهد. Increment بسیار کوچک، Growthهای پرتعداد و وقفه‌های مکرر ایجاد می‌کند. Increment بسیار بزرگ نیز می‌تواند یک‌باره فضای زیادی از Volume بگیرد، مدت طولانی‌تری Initialization ایجاد کند و فضای Databaseهای دیگر را تحت فشار قرار دهد. Data و Log باید جداگانه ارزیابی شوند.

خاموش‌کردن Autogrowth (FILEGROWTH = 0) بدون کنترل جایگزین خطرناک است؛ Allocation بعدی ممکن است با خطا متوقف شود. اگر سیاست سازمان رشد خودکار را محدود می‌کند، باید قبل از آن Manual Growth، Alert و مسئول مشخص داشته باشید.

MAXSIZE سقف هر File است، نه سقف کل Database و نه برنامهٔ ظرفیت. UNLIMITED نیز بی‌نهایت واقعی نیست: Data File در SQL Server حداکثر فنی خود را دارد و در هر حال نمی‌تواند از فضای Volume بیشتر شود؛ برای Log نیز محدودیت فنی جداگانه وجود دارد. MAXSIZE روی تک‌تک Fileها اعمال می‌شود.

```sql
ALTER DATABASE SalesDB
MODIFY FILE
(
    NAME = N'SalesDB_Data',
    MAXSIZE = 500GB
);
GO
```

MAXSIZE از پرشدن خارج از سیاست جلوگیری می‌کند، اما جای Alert ظرفیت Volume، Trend رشد، Manual Growth و Change Management را نمی‌گیرد.

## ۴.۱۱ رشد Transaction Log و راهنمای مقدماتی VLF

Physical Log File از بخش‌های داخلی‌ای به نام Virtual Log File یا VLF تشکیل می‌شود. رشدهای بسیار کوچک می‌توانند تعداد زیادی VLF کوچک بسازند و عملیات‌هایی مانند Recovery را دشوارتر کنند. رشدهای بسیار بزرگ نیز ممکن است زمان Initialization و وقفهٔ قابل‌توجه ایجاد کنند.

Log Size باید با بزرگ‌ترین Transaction، Index Maintenance، Batch، مدت Backup و فاصلهٔ Log Backupها هماهنگ باشد. Growth ممکن است در لحظهٔ تخصیص فضای جدید Workload را متوقف یا کند کند؛ به همین دلیل Log را پیش از عملیات بزرگ Pre-size کنید و از Growthهای اضطراری در ساعات پرترافیک دوری کنید.

چند Log File معمولاً Performance Scaling نیست. اگر Log پر شده، ابتدا علت Reuse نشدن را پیدا کنید. افزودن .ldf دوم فقط در شرایط خاص و با هدف Capacity یا Recovery اضطراری بررسی می‌شود، نه به‌عنوان درمان عادی.

## ۴.۱۲ Data File Full، Filegroup Full، Log Full و Volume Full

عبارت «Database پر است» برای عیب‌یابی کافی نیست. این تصمیم‌گیری را انجام دهید:

```text
Write/Allocation fails
        ↓
Is the failing space Data or Log?
   ├─ Data → Is internal free space available?
   │          ├─ Yes → why did allocation fail?
   │          └─ No  → can this file grow?
   │                    ├─ Yes → check Volume and MAXSIZE
   │                    └─ No  → File/Filegroup capacity problem
   └─ Log  → check log utilization and log_reuse_wait_desc
              ├─ LOG_BACKUP → repair Log Backup chain/job
              └─ ACTIVE_TRANSACTION → find/resolve long transaction
```

### ۴.۱۲.۱ Data File Full

ممکن است یک Data File فضای داخلی نداشته باشد، اما با Autogrowth، MAXSIZE و Volume مناسب بتواند Grow کند. در این حالت File به‌طور مطلق «غیرقابل استفاده» نیست؛ باید شرایط Growth را بررسی کرد.

### ۴.۱۲.۲ یک File پر، اما Filegroup دارای ظرفیت

وقتی چند Data File در Filegroup وجود دارد، وضعیت همهٔ آن‌ها را ببینید. یک File ممکن است به MAXSIZE رسیده باشد، در حالی که File دیگر ظرفیت دارد؛ یا تنظیمات Growth فایل‌ها هماهنگ نباشد. Allocation رفتار Proportional Fill دارد، پس صرف دیدن نام یک File برای نتیجه‌گیری کافی نیست.

### ۴.۱۲.۳ Filegroup Full و Error 1105

اگر Filegroup نتواند فضای لازم برای Allocation فراهم کند، خطاهایی مانند 1105 ممکن است رخ دهد. علت می‌تواند رسیدن همهٔ Fileها به MAXSIZE، نبودن فضای Volume، خاموش بودن Growth یا نداشتن Permission باشد.

### ۴.۱۲.۴ Volume Full

ممکن است Data File فضای داخلی داشته باشد و هنوز خطایی رخ نداده باشد، اما Volume برای Growth بعدی جا نداشته باشد. UNLIMITED نیز در این وضعیت نمی‌تواند فضا ایجاد کند. Windows-visible Volumeهای جدا هم الزاماً Backend فیزیکی جدا ندارند.

### ۴.۱۲.۵ Log Full و Error 9002

Log Full به معنی نبودن فضای قابل Reuse در Log یا ناتوانی در Growth است. Error 9002 برای پرشدن Transaction Log مرتبط است. برخی Readها ممکن است ادامه پیدا کنند، اما Transaction یا Allocation وابسته به Log می‌تواند Fail شود؛ Database الزاماً بلافاصله Offline نمی‌شود.

## ۴.۱۳ Log Truncation، Reuse و Shrinking

Log Truncation یعنی بخش‌هایی از Log که دیگر برای نیازهای فعلی Recovery لازم نیستند، برای Reuse علامت‌گذاری شوند. Truncation اندازهٔ فیزیکی .ldf را کم نمی‌کند. ممکن است Used Log پایین بیاید، اما File در Windows همچنان ۵۰ GB باشد؛ این رفتار عادی است.

Shrink اندازهٔ فیزیکی File را کاهش می‌دهد، اما اگر علت رشد باقی باشد، File دوباره Grow می‌کند و مشکل تکرار می‌شود. Shrink باید اقدام استثنایی پس از یک رشد غیرعادی و با برنامهٔ مشخص باشد، نه Job روزانه.

```sql
SELECT
    name,
    recovery_model_desc,
    log_reuse_wait_desc
FROM sys.databases
WHERE name = N'SalesDB';
```

مقدارهای مهم شامل LOG_BACKUP، ACTIVE_TRANSACTION، AVAILABILITY_REPLICA و REPLICATION هستند. هر مقدار مسیر بررسی متفاوتی دارد. تغییر فوری به SIMPLE ممکن است زنجیرهٔ Log Backup را بشکند و RPO را نقض کند. افزودن Log File یا Shrink نیز علت LOG_BACKUP را برطرف نمی‌کند.

## ۴.۱۴ چند Data File و Proportional Fill

چند Data File زمانی قابل دفاع است که یک نیاز قابل اندازه‌گیری وجود داشته باشد:

- ظرفیت لازم باید روی چند Volume تأمین شود؛

- Filegroup یا طراحی Lifecycle/Partitioning به جداسازی نیاز دارد؛

- Database بسیار بزرگ است و Allocation Contention با شواهد دیده می‌شود؛

- سیاست Backup/Restore یا مدیریت ظرفیت چنین جداسازی‌ای را توجیه می‌کند.

چند File روی همان Storage، IOPS جدید ایجاد نمی‌کند. حتی دو Drive Letter متفاوت ممکن است VMDKهایی روی یک Datastore مشترک باشند. قبل از File Design، نقشهٔ واقعی Storage فصل دوم را دوباره بررسی کنید.

در Filegroup چندفایلی، Proportional Fill باعث می‌شود Allocation بر اساس فضای آزاد نسبی Fileها توزیع شود؛ SQL Server لزوماً File اول را تا انتها پر نمی‌کند و سپس سراغ File دوم نمی‌رود.

::: {custom-style="Warning"}
▲ هشدار برای این بخش، مقدار واقعی را با Design Sheet و نتیجهٔ Verification تطبیق دهید.
:::

Baseline تعداد Data Fileهای tempdb را به User Database تعمیم ندهید. راهنمایی‌های فصل سوم دربارهٔ tempdb برای مسئلهٔ خاص Allocation Contention آن است و نسخهٔ عمومی طراحی User Database نیست.

در صورت استفاده از AUTOGROW_ALL_FILES، رشد همهٔ Fileهای Filegroup به‌صورت هماهنگ انجام می‌شود. این گزینه باید فقط وقتی انتخاب شود که مدل Allocation و ظرفیت همهٔ Fileها آگاهانه طراحی شده باشد؛ در این فصل صرفاً به‌عنوان یک قابلیت پیشرفته معرفی می‌شود.

## ۴.۱۵ افزودن، تغییر، خالی‌کردن و حذف Fileها

### ۴.۱۵.۱ افزودن Filegroup و Data File

```sql
USE master;
GO

ALTER DATABASE SalesDB
ADD FILEGROUP FG_Archive;
GO

ALTER DATABASE SalesDB
ADD FILE
(
    NAME = N'SalesDB_Archive01',
    FILENAME = N'D:\SQLData\SalesDB_Archive01.ndf',
    SIZE = 1024MB,
    MAXSIZE = 500GB,
    FILEGROWTH = 512MB
)
TO FILEGROUP FG_Archive;
GO
```

پیش‌شرط: مسیر موجود، Permission سرویس، ظرفیت Volume، Change تأییدشده و Backup معتبر را بررسی کنید. پس از اجرا، sys.database_files و sys.filegroups را Verify کنید.

### ۴.۱۵.۲ تغییر Size، Growth و MAXSIZE

```sql
ALTER DATABASE SalesDB
MODIFY FILE
(
    NAME = N'SalesDB_Archive01',
    SIZE = 4096MB,
    FILEGROWTH = 512MB,
    MAXSIZE = 500GB
);
GO
```

این دستور File را کوچک نمی‌کند؛ Size جدید باید بزرگ‌تر از Size فعلی باشد. برای تغییر Default Filegroup:

```sql
ALTER DATABASE SalesDB
MODIFY FILEGROUP FG_Archive DEFAULT;
GO
```

این تغییر Objectهای موجود را منتقل نمی‌کند.

### ۴.۱۵.۳ آماده‌سازی File برای حذف

حذف File، حذف نام آن از یک فهرست نیست. ابتدا باید بفهمید چه Allocationهایی در آن وجود دارد. EMPTYFILE تلاش می‌کند Allocationها را به Fileهای دیگر همان Filegroup منتقل کند؛ این کار می‌تواند I/O و زمان زیادی مصرف کند.

```sql
USE SalesDB;
GO

DBCC SHRINKFILE
(
    N'SalesDB_Archive01',
    EMPTYFILE
);
GO

SELECT
    name,
    type_desc,
    physical_name,
    size * 8.0 / 1024 AS size_mb
FROM sys.database_files;
GO

ALTER DATABASE SalesDB
REMOVE FILE SalesDB_Archive01;
GO
```

::: {custom-style="Warning"}
▲ هشدار برای این بخش، مقدار واقعی را با Design Sheet و نتیجهٔ Verification تطبیق دهید.
:::

پیش از EMPTYFILE و REMOVE FILE، Backup، پنجرهٔ Maintenance، ظرفیت Fileهای مقصد، Objectهای وابسته و امکان Rollback عملیاتی را بررسی کنید. اگر File خالی نشد، آن را حذف نکنید و علت Allocation باقی‌مانده را پیدا کنید. هرگز .mdf، .ndf یا .ldf را با File Explorer حذف نکنید؛ این اقدام می‌تواند Database را خراب یا غیرقابل‌دسترس کند. برای Primary Data File و Log، محدودیت‌ها و ملاحظات ویژه وجود دارد.

## ۴.۱۶ اندازه‌گیری ظرفیت با T-SQL

### ۴.۱۶.۱ وضعیت Database

```sql
SELECT
    d.name,
    d.state_desc,
    SUSER_SNAME(d.owner_sid) AS owner_name,
    d.recovery_model_desc,
    d.collation_name,
    d.log_reuse_wait_desc
FROM sys.databases AS d
WHERE d.name = N'SalesDB';
```

### ۴.۱۶.۲ Inventory کامل Fileها و Filegroup

```sql
USE SalesDB;
GO

SELECT
    DB_NAME() AS database_name,
    df.file_id,
    df.name AS logical_file_name,
    df.physical_name,
    df.type_desc,
    fg.name AS filegroup_name,
    CAST(df.size * 8.0 / 1024 AS decimal(19, 2)) AS size_mb,
    df.growth,
    df.is_percent_growth,
    CASE
        WHEN df.is_percent_growth = 1
            THEN CONCAT(df.growth, '%')
        ELSE CONCAT(CAST(df.growth * 8.0 / 1024 AS decimal(19, 2)), ' MB')
    END AS growth_display,
    CASE
        WHEN df.max_size = -1 THEN 'UNLIMITED'
        ELSE CONCAT(CAST(df.max_size * 8.0 / 1024 AS decimal(19, 2)), ' MB')
    END AS max_size_display,
    df.state_desc
FROM sys.database_files AS df
LEFT JOIN sys.filegroups AS fg
    ON df.data_space_id = fg.data_space_id
ORDER BY df.file_id;
```

sys.database_files Fileهای Database جاری را نشان می‌دهد. برای Inventory همهٔ Databaseهای Instance از sys.master_files استفاده کنید:

```sql
SELECT
    DB_NAME(database_id) AS database_name,
    file_id,
    name AS logical_file_name,
    type_desc,
    physical_name,
    size * 8.0 / 1024 AS size_mb,
    growth,
    is_percent_growth,
    max_size,
    state_desc
FROM sys.master_files
ORDER BY database_id, file_id;
```

### ۴.۱۶.۳ فضای داخلی Data File

```sql
USE SalesDB;
GO

SELECT
    name AS logical_file_name,
    CAST(size * 8.0 / 1024 AS decimal(19, 2)) AS file_size_mb,
    CAST(FILEPROPERTY(name, 'SpaceUsed') * 8.0 / 1024 AS decimal(19, 2)) AS used_mb,
    CAST((size - FILEPROPERTY(name, 'SpaceUsed')) * 8.0 / 1024 AS decimal(19, 2)) AS free_inside_file_mb
FROM sys.database_files
WHERE type = 0;
```

FILEPROPERTY(name, 'SpaceUsed') برای Data File جاری استفاده می‌شود. نتیجهٔ آن با فضای آزاد Windows Volume یکی نیست و این Query برای Log File به‌کار نمی‌رود.

### ۴.۱۶.۴ مصرف Transaction Log

در SQL Server جدید، DMV زیر Snapshot مصرف Log Database جاری را می‌دهد:

```sql
USE SalesDB;
GO

SELECT
    total_log_size_in_bytes / 1024.0 / 1024 AS total_log_mb,
    used_log_space_in_bytes / 1024.0 / 1024 AS used_log_mb,
    used_log_space_in_percent
FROM sys.dm_db_log_space_usage;
```

برای علت Reuse نشدن نیز Query بخش ۴.۱۳ و sys.databases.log_reuse_wait_desc را اجرا کنید. مجوزهای لازم برای DMVها بر اساس Version و سطح دسترسی Login متفاوت است؛ در Production حداقل Permission موردنیاز Version نصب‌شده را مطابق مستندات همان Version بررسی کنید.

### ۴.۱۶.۵ ظرفیت Windows Volume

```sql
USE SalesDB;
GO

SELECT DISTINCT
    vs.volume_mount_point,
    vs.total_bytes / 1024.0 / 1024 / 1024 AS total_volume_gb,
    vs.available_bytes / 1024.0 / 1024 / 1024 AS available_volume_gb,
    vs.available_bytes * 100.0 / NULLIF(vs.total_bytes, 0) AS available_percent
FROM sys.database_files AS df
CROSS APPLY sys.dm_os_volume_stats(DB_ID(), df.file_id) AS vs;
```

این Query ظرفیت Volumeهایی را نشان می‌دهد که Fileهای Database جاری روی آن‌ها قرار دارند. sys.dm_os_volume_stats ممکن است به Permission سطح Instance مانند VIEW SERVER STATE یا Permission متناظر Version نیاز داشته باشد؛ در صورت خطا، Permission را مطابق SQL Server 2022/2025 بررسی کنید.

### ۴.۱۶.۶ بررسی مقدماتی Backup

این Query وجود سابقهٔ Backup را نشان می‌دهد، اما جای Restore Test و بررسی کامل Backup Strategy را نمی‌گیرد:

```sql
SELECT TOP (10)
    bs.database_name,
    bs.type,
    bs.backup_start_date,
    bs.backup_finish_date,
    bs.is_copy_only,
    bmf.physical_device_name
FROM msdb.dbo.backupset AS bs
LEFT JOIN msdb.dbo.backupmediafamily AS bmf
    ON bs.media_set_id = bmf.media_set_id
WHERE bs.database_name = N'SalesDB'
ORDER BY bs.backup_finish_date DESC;
```

وجود یک Row در msdb موفقیت فعلی Job، قابل Restore بودن Backup یا رعایت RPO را تضمین نمی‌کند.

## ۴.۱۷ Build و Capacity Validation

پس از CREATE، فرآیند را با این الگو تمام کنید:

```text
Create → Configure → Verify → Document
```

### ۴.۱۷.۱ فهرست Verification

- Database وجود دارد و نام آن با Design Sheet برابر است.

- state_desc برابر ONLINE است.

- Owner مورد انتظار است و مسئول آن مشخص است.

- Recovery Model درست است و Backup Strategy دارد.

- Collation با نیاز Application برابر است.

- Logical File Nameها دقیق‌اند.

- Physical Pathها وجود دارند و Permission سرویس بررسی شده است.

- نوع Fileها Data یا Log و Filegroup membership درست است.

- Default Filegroup درست است.

- Initial Size، Growth و MAXSIZE مطابق Change هستند.

- فضای داخلی هر Data File معلوم است.

- Total و Used Log و log_reuse_wait_desc ثبت شده‌اند.

- فضای آزاد Volumeها معلوم است.

- Backup Responsibility و Monitoring Thresholdها مکتوب‌اند.

### ۴.۱۷.۲ اسکریپت تجمیعی کوتاه

```sql
SELECT
    d.name,
    d.state_desc,
    SUSER_SNAME(d.owner_sid) AS owner_name,
    d.recovery_model_desc,
    d.collation_name,
    d.log_reuse_wait_desc
FROM sys.databases AS d
WHERE d.name = N'SalesDB';
GO

USE SalesDB;
GO

SELECT
    df.file_id,
    df.name AS logical_file_name,
    df.type_desc,
    df.physical_name,
    fg.name AS filegroup_name,
    df.size * 8.0 / 1024 AS size_mb,
    df.growth,
    df.is_percent_growth,
    df.max_size,
    df.state_desc
FROM sys.database_files AS df
LEFT JOIN sys.filegroups AS fg
    ON df.data_space_id = fg.data_space_id;
GO

SELECT
    name,
    size * 8.0 / 1024 AS file_size_mb,
    FILEPROPERTY(name, 'SpaceUsed') * 8.0 / 1024 AS used_mb,
    (size - FILEPROPERTY(name, 'SpaceUsed')) * 8.0 / 1024 AS free_inside_file_mb
FROM sys.database_files
WHERE type = 0;
GO

SELECT
    total_log_size_in_bytes / 1024.0 / 1024 AS total_log_mb,
    used_log_space_in_bytes / 1024.0 / 1024 AS used_log_mb,
    used_log_space_in_percent
FROM sys.dm_db_log_space_usage;
```

## ۴.۱۸ Database As-Built و Handover

As-Built باید نشان دهد چه چیزی واقعاً ساخته شده است، نه اینکه چه چیزی قرار بود ساخته شود.

| مورد | مقدار واقعی |
|---|---|
| Database Name / Purpose |  |
| Environment / Owner / State |  |
| Recovery Model / Collation |  |
| Data Path / Log Path |  |
| Logical و Physical File Names |  |
| File Type و Filegroup |  |
| Current Size و Initial Size |  |
| FILEGROWTH و MAXSIZE |  |
| Default Filegroup |  |
| Additional Filegroups |  |
| Internal Data File Free Space |  |
| Log Size / Used Percent / Reuse Wait |  |
| Volume Total و Available Capacity |  |
| Backup Job / Responsibility |  |
| Monitoring Thresholds |  |
| Change / Ticket Reference |  |
| Validation Date / DBA |  |

### ۴.۱۸.۱ Handover Checklist

این Checklist باید با Evidence تکمیل شود:

- ☐ Database با نام صحیح ایجاد و در ONLINE بودن آن Verify شد.

- ☐ Owner، Collation و Recovery Model با Design Sheet تطبیق داده شد.

- ☐ Full Backup اولیه در Recovery Model لازم تهیه شد.

- ☐ Log Backup Job در صورت نیاز ایجاد، فعال و با اجرای موفق Verify شد.

- ☐ همهٔ Fileها با Logical Name، Physical Path، Type و Filegroup ثبت شدند.

- ☐ مسیرها، Permission سرویس و وجود Folderها بررسی شد.

- ☐ Initial Size، FILEGROWTH و MAXSIZE هر File ثبت و تأیید شد.

- ☐ فضای داخلی Data File و ظرفیت Volume Snapshot شد.

- ☐ Log utilization و log_reuse_wait_desc ثبت شد.

- ☐ Default Filegroup و Object placement مورد انتظار Verify شد.

- ☐ Alertهای Growth، Volume، Log و Backup Job به Owner معرفی شد.

- ☐ RPO، RTO، Backup Responsibility و Change Reference مکتوب شد.

- ☐ Script ایجاد، Script Verification و As-Built در محل مورد توافق تحویل شد.

- ☐ مسئول تحویل‌گیرنده وجود مستندات و نتیجهٔ Verification را تأیید کرد.

## سناریوهای عملیاتی

### سناریوی ۱: OLTP Production با FULL

Application فروش در Production به Point-in-time Recovery نیاز دارد. DBA در Design Sheet مقدار RPO را محدود ثبت می‌کند، FULL را انتخاب می‌کند، Full Backup اولیه می‌گیرد و Log Backup را در بازهٔ سازگار با RPO زمان‌بندی می‌کند. Alert Job Failure، Log Used Percent، LOG_BACKUP و فضای Volume فعال می‌شوند. در Handover، RPO/RTO و مسئول بررسی Job ثبت می‌شوند. اگر فقط Recovery Model به FULL تغییر کند اما Full Backup اولیه و Log Backup وجود نداشته باشد، طرح Recovery ناقص است.

### سناریوی ۲: Data File نمی‌تواند Grow کند

Insert با خطای Allocation مواجه شده است. بررسی نشان می‌دهد Data File فضای داخلی ندارد، Volume هنوز ۱۰۰ GB آزاد دارد، اما File به MAXSIZE رسیده است. نتیجه «Volume پر است» غلط است. DBA با Change تأییدشده MAXSIZE را اصلاح یا File/Volume مناسب اضافه می‌کند، ظرفیت Filegroup را Verify می‌کند و سپس عملیات را در پنجرهٔ کنترل‌شده تکرار می‌کند.

### سناریوی ۳: Log Full به‌علت LOG_BACKUP

Database روی FULL است و Log Backup Job از شب گذشته Fail شده است. sys.databases.log_reuse_wait_desc مقدار LOG_BACKUP را نشان می‌دهد. علت، نبودن Log Backup موفق و امکان Reuse نشدن Log است. افزودن Log File دوم یا Shrink، Job را تعمیر نمی‌کند. DBA علت Job Failure، مقصد Backup، Permission و فضای Volume را اصلاح، یک Log Backup موفق اجرا و سپس مصرف Log را Verify می‌کند.

### سناریوی اختیاری ۴: ACTIVE_TRANSACTION

Log Backupها موفق‌اند، اما log_reuse_wait_desc = ACTIVE_TRANSACTION است. یک Transaction طولانی یا Rollback در حال اجرا بخش‌های Log را فعال نگه داشته است. DBA باید Session و Transaction را با احتیاط شناسایی کند و بدون Kill کردن کورکورانه، اثر توقف یا Rollback را با Owner Application هماهنگ کند.

## تمرین‌های فصل

### تمرین ۱: تکمیل Database Design Sheet

برای یک Database با نام SalesDB، هدف Application، Environment، Owner، مسیر Data و Log، حجم فعلی، Import اولیه، Initial Size، Data/Log Growth، MAXSIZE، Filegroup، Default Filegroup، Recovery Model، Collation، RPO، RTO، Backup Responsibility و Thresholdهای Monitoring را تعیین کنید. برای هر عدد یک دلیل عملیاتی بنویسید و اگر داده کافی ندارید، فرض خود را صریح ثبت کنید.

### تمرین ۲: ایجاد و Verify کردن

SalesDB را با T-SQL ایجاد کنید. سپس Database State، Owner، Recovery Model، Collation، Logical/Physical File Name، File Type، Filegroup، Size، Growth و MAXSIZE را Query کنید. نتیجه را با Design Sheet مقایسه کنید و هر اختلاف را به‌عنوان Finding ثبت کنید.

### تمرین ۳: تشخیص ظرفیت

برای هر وضعیت زیر تعیین کنید مشکل در کدام لایه است و اولین Query شما چیست:

- Data File فضای داخلی ندارد، اما می‌تواند Grow کند.

- یک File به MAXSIZE رسیده و Filegroup چند File دارد.

- همهٔ Fileهای Filegroup به سقف رسیده‌اند؛ Error 1105 گزارش شده است.

- Volume فضای آزاد ندارد.

- Log روی FULL است و LOG_BACKUP دیده می‌شود.

- Log روی FULL است و ACTIVE_TRANSACTION دیده می‌شود.

برای هر پاسخ، یک اقدام اشتباه را نیز بنویسید که نباید انجام شود؛ مانند Shrink برای حل LOG_BACKUP یا افزودن File دوم برای درمان Volume Full.

### تمرین ۴: Database Handover

یک بستهٔ تحویل برای SalesDB آماده کنید که شامل این موارد باشد:

```text
Database Design Sheet
Creation Script
Validation Script
File and Filegroup Inventory
Recovery Configuration
Capacity Snapshot
Database As-Built
Handover Checklist
```

هیچ بخش را با عبارت «بررسی شد» خالی تحویل ندهید؛ برای هر مورد مقدار، زمان، Query یا Evidence ثبت کنید.

## جمع‌بندی فصل

Database از یک نام منطقی، Filegroupهای دارای هدف، Data Fileهای فیزیکی و Transaction Log تشکیل می‌شود. Data و Log را باید جداگانه طراحی و پایش کرد. model می‌تواند بر Database جدید اثر بگذارد، اما DBA باید مقدار واقعی Collation و Recovery Model را Verify کند. Initial Size و Pre-sizing رشد عادی را کنترل‌پذیرتر می‌کنند؛ Autogrowth فقط Safety Mechanism است و MAXSIZE نیز جای Capacity Strategy را نمی‌گیرد.

در عیب‌یابی، Data File Full، Filegroup Full، Log Full و Volume Full را یکی ندانید. برای هرکدام فضای داخلی File، تنظیمات Growth، سقف File، ظرفیت Volume و log_reuse_wait_desc را در لایهٔ درست بخوانید. چند Data File یا Filegroup فقط با دلیل عملیاتی و شواهد قابل دفاع‌اند و چند Log File درمان عمومی Performance یا Log Full نیست.

اصل راهنمای فصل این است: مدیریت Database زمانی کامل است که ساختار فایل، Recovery، ظرفیت، رشد و وضعیت عملیاتی آن قابل مشاهده، قابل توضیح و قابل تحویل باشد.

## گذار به فصل بعد

در فصل بعدی، این Database ساخته‌شده را در کنار موضوعات عملیاتی بعدی کتاب دنبال می‌کنیم؛ تمرکز باید بر زنجیره‌ای باشد که در ادامهٔ Outline کتاب تأیید شده است. تا آن زمان، هیچ Databaseای را فقط با دیدن نام آن در SSMS آماده فرض نکنید: Design Sheet، Verification و As-Built باید سه شاهد اصلی آماده‌بودن آن باشند.

## منابع فنی منتخب

1. [Database Files and Filegroups — Microsoft Learn](https://learn.microsoft.com/en-us/sql/relational-databases/databases/database-files-and-filegroups?view=sql-server-ver17)

2. [ALTER DATABASE — File and Filegroup Options](https://learn.microsoft.com/en-us/sql/t-sql/statements/alter-database-transact-sql-file-and-filegroup-options?view=sql-server-ver17)

3. [Manage the Size of the Transaction Log File](https://learn.microsoft.com/en-us/sql/relational-databases/logs/manage-the-size-of-the-transaction-log-file?view=sql-server-ver17)

4. [SQL Server Transaction Log Architecture and Management Guide](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-log-architecture-and-management-guide?view=sql-server-ver17)

5. [The Transaction Log — SQL Server](https://learn.microsoft.com/en-us/sql/relational-databases/logs/the-transaction-log-sql-server?view=sql-server-ver17)

6. [Recovery Models — SQL Server](https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/recovery-models-sql-server?view=sql-server-ver17)

7. [Back Up and Restore of SQL Server Databases](https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/back-up-and-restore-of-sql-server-databases?view=sql-server-ver17)

8. [Add Data or Log Files to a Database](https://learn.microsoft.com/en-us/sql/relational-databases/databases/add-data-or-log-files-to-a-database?view=sql-server-ver17)

9. [Database Properties — Files Page](https://learn.microsoft.com/en-us/sql/relational-databases/databases/database-properties-files-page?view=sql-server-ver17)

10. [Considerations for the Autogrow and Autoshrink](https://learn.microsoft.com/en-us/troubleshoot/sql/database-engine/database-file-operations/considerations-autogrow-autoshrink)

11. [What's New in SQL Server 2022 — Improved VLF Algorithm](https://learn.microsoft.com/en-us/sql/sql-server/what-s-new-in-sql-server-2022?view=sql-server-ver17)

12. [SQL Server Storage Guide](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-storage-guide?view=sql-server-ver17)
