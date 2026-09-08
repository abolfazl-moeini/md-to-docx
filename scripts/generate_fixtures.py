#!/usr/bin/env python3
"""
Generate and validate the 61 Persian layout fixtures and manifest.yaml
as specified in persian_layout_quality_plan.md.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCE_BOOK = ROOT / "SQL_Server_DBA_Book_Chapters_1_4_FIXED.md"
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "persian_layout"

EXPECTED_BOOK_SHA = "525a3e92016a946bf36fdd5b3a2a8c8829a6e71e3e433fe52b6d9e9f3352443b"

BOOK_CAPTION_LABELS = (
    "شکل ۱-۱",
    "شکل ۱-۲",
    "شکل ۱-۳",
    "شکل ۲-۱",
    "شکل ۲-۲",
)


def caption_warnings_for(content: str) -> List[str]:
    """Slices that contain the book's image-less captions must expect those warnings."""
    return [f"caption_without_image @ {label}" for label in BOOK_CAPTION_LABELS if label in content]

# Chapter line ranges (1-indexed)
CHAPTER_RANGES = {
    "C01": (7, 368, "فصل اول — آشنایی با SQL Server و معماری پایه"),
    "C02": (369, 562, "فصل دوم — آماده‌سازی ماشین مجازی و زیرساخت برای SQL Server"),
    "C03": (563, 2289, "فصل سوم — نصب و پیکربندی اولیه SQL Server از دید DBA"),
    "C04": (2290, 3335, "فصل چهارم — مدیریت Database، فایل‌ها و رشد"),
}

# 40 Slice ranges from Table 4.2
SLICE_RANGES = {
    "R01": (15, 42, "تعریف SQL Server، متن مخلوط، SQL کوتاه و دو سبک یادداشت"),
    "R02": (73, 100, "مرزهای Instance/Database، مسیر بک‌اسلش و جدول سه‌ستونی"),
    "R03": (101, 128, "نقش مؤلفه‌ها، دو زیرنویس بدون تصویر و DBA Note"),
    "R04": (129, 152, "پایگاه‌های سیستمی، سلول پرمتن و هشدار"),
    "R05": (153, 174, "Login/User و نام‌های فنی مخلوط"),
    "R06": (175, 197, "Edition و Lab Note؛ حفظ تفاوت نقش‌ها"),
    "R07": (218, 249, "Storage، Data/Log و مسیرهای فنی"),
    "R08": (309, 362, "تمرین پایان فصل، تیترهای تو‌در‌تو و کد"),
    "R09": (395, 406, "منابع مجازی و زیرنویس بدون تصویر"),
    "R10": (407, 418, "CPU/vCPU و جهت عبارت‌های لاتین در نثر"),
    "R11": (429, 436, "لایه‌های تنظیم عملکرد و زیرنویس مستقل"),
    "R12": (457, 468, "Storage و واحدها و اصطلاحات فنی"),
    "R13": (501, 520, "طراحی Volume، جدول و هشدار"),
    "R14": (533, 562, "چک‌لیست پایان فصل دوم، Lab/Important Note"),
    "R15": (563, 636, "مقدمهٔ فصل سوم، گلوله‌های literal و جریان متنی عمودی"),
    "R16": (637, 828, "برنامهٔ نصب، زیرتیترهای متوالی و جدول"),
    "R17": (829, 960, "PowerShell، خروجی چندخطی و یادداشت‌ها"),
    "R18": (961, 1032, "Volume و مسیر Windows"),
    "R19": (1033, 1099, "console، واحد ظرفیت و هشدار"),
    "R20": (1148, 1185, "Named Instance و بک‌اسلش در متن/کد"),
    "R21": (1221, 1299, "حساب سرویس، Permission و تیترهای مخلوط بلند"),
    "R22": (1300, 1341, "احراز هویت، هشدار و کد"),
    "R23": (1342, 1419, "Collation، underscore و شناسهٔ لاتین بلند"),
    "R24": (1420, 1527, "نصب و Screenshot Recommendation؛ بدون جعل تصویر"),
    "R25": (1568, 1631, "شبکه، TCP و پورت/مسیر در متن مخلوط"),
    "R26": (1692, 1755, "محاسبهٔ حافظه، اعداد، واحد و DBA Note"),
    "R27": (1756, 1787, "MAXDOP، کد کوتاه و پاراگراف دوزبانه"),
    "R28": (1810, 2271, "اعتبارسنجی نصب؛ برش بلند عمدی برای شکست چندصفحه‌ای"),
    "R29": (2336, 2381, "معماری منطقی/فیزیکی و درخت متنی"),
    "R30": (2382, 2425, "شیت طراحی و جدول اطلاعات"),
    "R31": (2460, 2505, "Recovery Model، جدول چهارستونی، SQL و Warning"),
    "R32": (2506, 2596, "ساخت Database، SQL بلند و توصیهٔ اسکرین‌شات"),
    "R33": (2597, 2631, "نام فایل منطقی/فیزیکی و علائم مسیر"),
    "R34": (2644, 2714, "Filegroup و نویسه‌های درخت"),
    "R35": (2715, 2740, "فهرست و ظرفیت‌گذاری اولیه"),
    "R36": (2741, 2782, "Autogrowth، درصد و مقادیر SQL"),
    "R37": (2791, 2828, "درخت متنی و تشخیص خطا"),
    "R38": (2870, 2954, "Query بلند، هشدار و زیرتیترهای متوالی"),
    "R39": (2955, 3092, "Queryهای پایش چندخطی"),
    "R40": (3093, 3235, "Query با بلوک ۴۴خطی و جدول تحویل با سلول‌های خالی"),
}

SYNTHETIC_DESCS = {
    "S01": "متن مخلوط با پرانتز، گیومه، درصد، تاریخ، IP، URL، دامنه و مسیر Windows؛ عبارت لاتین چندکلمه‌ای میان bold/link/italic",
    "S02": "تیترهای ۱ تا ۶، شماره‌های فارسی/عربی/لاتین، شمارهٔ چندبخشی بلند، عنوان دو تا چهارخطی، شناسه و لینک داخلی",
    "S03": "هر شش custom-style، calloutهای class-based، عنوان صریح/ضمنی، دو سطح nesting و نمونهٔ literal در code fence",
    "S04": "فهرست bullet و ordered، شروع عدد غیر۱، alpha/roman، tight/loose، سه سطح nesting، آیتم فقط انگلیسی کنار فارسی؛ literal bullet جدا",
    "S05": "جدول‌های دو، سه و شش‌ستونی؛ یک جدول حداقل ۶۰ردیفی با متن فارسی بلند، عدد، سرستون چندخطی و سلول خالی",
    "S06": "جدول داخل کادر، فهرست/تصویر/کد داخل سلول، quote و جدول تو‌در‌تو در syntax معتبر Pandoc",
    "S07": "SQL، PowerShell، console، Python و text؛ tab، indentation، خط خالی، توضیح فارسی و خط بیش از ۱۹۰ نویسه",
    "S08": "بلوک کد بیشتر از دو صفحه، بلوک دارای خطوط خالی ابتدا/انتها، درخت ASCII و box drawing",
    "S09": "عکس افقی و عمودی واقعی با مجوز، PNG شفاف، تصویر کوچک inline، reference image، نام فایل فارسی/فاصله/percent-encoding و caption",
    "S10": "Mermaid flowchart با جهت TB و LR، برچسب فارسی و لاتین، متن بلند داخل گره، لبهٔ دارای عنوان",
    "S11": "Mermaid sequence، state و ER با فارسی؛ نمودار عریض و بلند دارای تعداد عناصر معلوم",
    "S12": "Mermaid و تصویر داخل list، quote، Div، definition list، جدول با syntax مناسب و footnote؛ fenceهای تودرتو",
    "S13": "پاورقی چندپاراگرافی، لینک، فهرست، inlineهای غنی و فرمول‌های محدودهٔ پشتیبانی‌شدهٔ OMML",
    "S14": "مرز صفحه: تیتر، شروع کادر، تصویر/caption، جدول و کد پس از متن با طول کنترل‌شده",
    "S15": "metadata، فهرست مطالب، چهار شروع فصل، appendix، heading anchor و ارجاع داخلی",
    "S16": "کتابچهٔ بلند فارسی ترکیبی از همهٔ موارد با تصاویر و Mermaid؛ آن‌قدر محتوا که در محیط مرجع بیش از ده صفحه شود",
}

WRAPPER_HEADER = """---
lang: fa-IR
dir: rtl
---

"""


def _visible_in_markdown(content: str, item: str) -> bool:
    """True if item appears outside image alts/targets and code fences."""
    if not item or item not in content:
        return False
    stripped = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", content)
    stripped = re.sub(r"```[\s\S]*?```", "", stripped)
    stripped = re.sub(r"`[^`]+`", "", stripped)
    return item in stripped


def pick_sensitive_strings(content: str, preferred: Optional[List[str]] = None) -> List[str]:
    """Choose >=2 strings that actually occur in the fixture (F00)."""
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            body = parts[2]
    body = re.sub(r"\{#[^}]+\}", "", body)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    body = re.sub(r"\[[^\]]*\]\([^)]*\)", " ", body)
    body = re.sub(r"\{[^}]*custom-style[^}]*\}", " ", body, flags=re.I)
    found: List[str] = []
    for item in preferred or []:
        if _visible_in_markdown(body, item) and item not in found:
            found.append(item)
    extras = [
        r"SQLPROD01\REPORTING",
        r"D:\SQLData",
        "Buffer Pool",
        "VMware ESXi",
        "Query Processor",
        "SQL Server Database Engine",
        "Always On Availability Groups",
        r"DOMAIN\svc_sqlengine",
        "MAXDOP",
        "Collation",
        "sys.databases",
        "شکل ۱-۱",
        "شکل ۱-۲",
        "فهرست مطالب",
        "SQL Server",
    ]
    for item in extras:
        if _visible_in_markdown(body, item) and item not in found:
            found.append(item)
        if len(found) >= 5:
            break
    skip_tokens = {
        "https", "http", "lang", "true", "false", "utf-8", "assets", "mermaid",
        "flowchart", "select", "from", "where", "image", "png", "author", "title",
        "chapter", "warning", "overview",
    }
    if len(found) < 2:
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_\\.-]{5,}", body):
            low = token.lower()
            if low in skip_tokens or "/" in token or "\\" in token:
                continue
            if token.lower().endswith((".png", ".jpg", ".jpeg", ".md", ".sql", ".css")):
                continue
            if token not in found:
                found.append(token)
            if len(found) >= 2:
                break
    if len(found) < 2:
        # Last resort: distinctive Persian words of length >= 4
        for token in re.findall(r"[\u0600-\u06FF]{4,}", body):
            if token not in found:
                found.append(token)
            if len(found) >= 2:
                break
    return found[:6]


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


PANDOC_FROM = (
    "markdown+fenced_divs+pipe_tables+grid_tables+backtick_code_blocks"
    "+raw_html+markdown_in_html_blocks+lists_without_preceding_blankline"
)


def count_ast_elements(markdown_text: str) -> Dict[str, Any]:
    cmd = [
        "pandoc",
        "-f", PANDOC_FROM,
        "-t", "json"
    ]
    res = subprocess.run(cmd, input=markdown_text, text=True, capture_output=True, check=True)
    ast = json.loads(res.stdout)
    blocks = ast.get("blocks", [])

    counts = {
        "headings": 0,
        "code_blocks": 0,
        "tables": 0,
        "images": 0,
        "mermaid_blocks": 0,
        "callouts": 0,
        "custom_styles": 0,
    }

    def walk_inlines(inlines):
        if not isinstance(inlines, list):
            return
        for inl in inlines:
            if not isinstance(inl, dict):
                continue
            it = inl.get("t")
            ic = inl.get("c")
            if it == "Image":
                counts["images"] += 1
            elif it == "Note" and isinstance(ic, list):
                for child in ic:
                    if isinstance(child, dict):
                        walk_block(child)
            elif it in ("Emph", "Strong", "Strikeout", "Superscript", "Subscript", "Underline", "SmallCaps") and isinstance(ic, list):
                walk_inlines(ic)
            elif it in ("Link", "Span", "Quoted", "Cite") and isinstance(ic, list) and len(ic) > 1 and isinstance(ic[1], list):
                walk_inlines(ic[1])

    def walk_block(b: dict):
        t = b.get("t")
        c = b.get("c", [])
        if t == "Header":
            counts["headings"] += 1
            if isinstance(c, list) and len(c) > 2:
                walk_inlines(c[2])
        elif t == "CodeBlock":
            attr = c[0] if isinstance(c, list) and len(c) > 0 else []
            classes = attr[1] if isinstance(attr, list) and len(attr) > 1 else []
            if "mermaid" in classes:
                counts["mermaid_blocks"] += 1
            else:
                counts["code_blocks"] += 1
        elif t == "Table":
            counts["tables"] += 1
            thead = c[3] if isinstance(c, list) and len(c) > 3 else []
            tbodies = c[4] if isinstance(c, list) and len(c) > 4 else []
            def walk_rows(rows):
                if not isinstance(rows, list):
                    return
                for row in rows:
                    if isinstance(row, list) and len(row) > 1 and isinstance(row[1], list):
                        for cell in row[1]:
                            if isinstance(cell, list) and len(cell) > 4 and isinstance(cell[4], list):
                                for child in cell[4]:
                                    if isinstance(child, dict):
                                        walk_block(child)
            if isinstance(thead, list) and len(thead) > 1:
                walk_rows(thead[1])
            if isinstance(tbodies, list):
                for body in tbodies:
                    if isinstance(body, list):
                        if len(body) > 2:
                            walk_rows(body[2])
                        if len(body) > 3:
                            walk_rows(body[3])
        elif t == "Note" and isinstance(c, list):
            for child in c:
                if isinstance(child, dict):
                    walk_block(child)
        elif t == "DefinitionList" and isinstance(c, list):
            for item in c:
                if isinstance(item, list) and len(item) > 1 and isinstance(item[1], list):
                    if isinstance(item[0], list):
                        walk_inlines(item[0])
                    for def_blocks in item[1]:
                        if isinstance(def_blocks, list):
                            for child in def_blocks:
                                if isinstance(child, dict):
                                    walk_block(child)
        elif t == "Figure":
            if len(c) > 2 and isinstance(c[2], list):
                for child in c[2]:
                    if isinstance(child, dict):
                        walk_block(child)
        elif t == "Div":
            attr = c[0] if isinstance(c, list) and len(c) > 0 else []
            classes = attr[1] if isinstance(attr, list) and len(attr) > 1 else []
            kvs = {k: v for k, v in attr[2]} if isinstance(attr, list) and len(attr) > 2 else {}
            if "custom-style" in kvs:
                counts["custom_styles"] += 1
            known_callout = any(cls in ("note", "warning", "important", "tip", "caution") for cls in classes)
            if known_callout or "custom-style" in kvs:
                counts["callouts"] += 1
            for child in c[1] if len(c) > 1 and isinstance(c[1], list) else []:
                if isinstance(child, dict):
                    walk_block(child)
        elif t == "BlockQuote":
            for child in c if isinstance(c, list) else []:
                if isinstance(child, dict):
                    walk_block(child)
        elif t in ("Para", "Plain"):
            walk_inlines(c if isinstance(c, list) else [])
        elif t in ("BulletList", "OrderedList"):
            items = c[1] if t == "OrderedList" and len(c) > 1 else c
            for item in items if isinstance(items, list) else []:
                for child in item if isinstance(item, list) else []:
                    if isinstance(child, dict):
                        walk_block(child)

    for b in blocks:
        if isinstance(b, dict):
            walk_block(b)

    return counts


def main():
    print(f"Checking source book at {SOURCE_BOOK}...")
    if not SOURCE_BOOK.exists():
        raise FileNotFoundError(f"Source book {SOURCE_BOOK} not found!")

    book_sha = sha256_of_file(SOURCE_BOOK)
    print(f"Book SHA256: {book_sha}")
    if book_sha != EXPECTED_BOOK_SHA:
        raise ValueError(f"Book SHA256 mismatch! Expected {EXPECTED_BOOK_SHA}, got {book_sha}")

    with open(SOURCE_BOOK, "r", encoding="utf-8") as f:
        book_lines = f.readlines()

    # Create directories
    for sub in ["source", "chapters", "extracted", "synthetic", "assets"]:
        (FIXTURE_ROOT / sub).mkdir(parents=True, exist_ok=True)

    manifest_entries: List[Dict[str, Any]] = []

    # 1. B00 (Source book)
    b00_path = FIXTURE_ROOT / "source" / "B00.md"
    shutil.copy2(SOURCE_BOOK, b00_path)
    b00_counts = count_ast_elements(b00_path.read_text(encoding="utf-8"))
    manifest_entries.append({
        "id": "B00",
        "category": "source",
        "rel_path": "source/B00.md",
        "sha256": book_sha,
        "title": "کتاب کامل مدیریت پایگاه داده SQL Server (فصل‌های ۱ تا ۴)",
        "source_range": "1-3335",
        "wrapper": False,
        "counts": b00_counts,
        "sensitive_strings": pick_sensitive_strings(
            b00_path.read_text(encoding="utf-8"),
            [
                r"SQLPROD01\REPORTING",
                r"D:\SQLData",
                "Buffer Pool",
                "VMware ESXi",
                "Query Processor",
            ],
        ),
        "expected_warnings": caption_warnings_for(b00_path.read_text(encoding="utf-8")),
    })
    print("B00 registered.")

    # 2. Chapters C01 - C04
    for c_id, (start_l, end_l, title) in CHAPTER_RANGES.items():
        c_path = FIXTURE_ROOT / "chapters" / f"{c_id}.md"
        content = WRAPPER_HEADER + "".join(book_lines[start_l - 1:end_l])
        c_path.write_text(content, encoding="utf-8")
        counts = count_ast_elements(content)
        manifest_entries.append({
            "id": c_id,
            "category": "chapters",
            "rel_path": f"chapters/{c_id}.md",
            "sha256": sha256_of_file(c_path),
            "title": title,
            "source_range": f"{start_l}-{end_l}",
            "wrapper": True,
            "counts": counts,
            "sensitive_strings": pick_sensitive_strings(content),
            "expected_warnings": caption_warnings_for(content),
        })
    print("C01-C04 registered.")

    # 3. Slices R01 - R40
    for r_id, (start_l, end_l, desc) in sorted(SLICE_RANGES.items()):
        r_path = FIXTURE_ROOT / "extracted" / f"{r_id}.md"
        content = WRAPPER_HEADER + "".join(book_lines[start_l - 1:end_l])
        r_path.write_text(content, encoding="utf-8")
        counts = count_ast_elements(content)
        manifest_entries.append({
            "id": r_id,
            "category": "extracted",
            "rel_path": f"extracted/{r_id}.md",
            "sha256": sha256_of_file(r_path),
            "title": f"برش {r_id}: {desc}",
            "source_range": f"{start_l}-{end_l}",
            "wrapper": True,
            "counts": counts,
            "sensitive_strings": pick_sensitive_strings(content),
            "expected_warnings": caption_warnings_for(content),
        })
    print("R01-R40 registered.")

    # 4. Synthetic S01 - S16
    for s_idx in range(1, 17):
        s_id = f"S{s_idx:02d}"
        s_path = FIXTURE_ROOT / "synthetic" / f"{s_id}.md"
        if not s_path.exists():
            raise FileNotFoundError(f"Synthetic fixture {s_path} not found!")
        content = s_path.read_text(encoding="utf-8")
        counts = count_ast_elements(content)
        manifest_entries.append({
            "id": s_id,
            "category": "synthetic",
            "rel_path": f"synthetic/{s_id}.md",
            "sha256": sha256_of_file(s_path),
            "title": f"نمونه ساختگی {s_id}: {SYNTHETIC_DESCS.get(s_id, '')}",
            "source_range": None,
            "wrapper": False,
            "counts": counts,
            "sensitive_strings": pick_sensitive_strings(content),
            "expected_warnings": caption_warnings_for(content),
        })
    print("S01-S16 registered.")

    assert len(manifest_entries) == 61, f"Expected 61 entries, got {len(manifest_entries)}"

    manifest_data = {
        "version": 1,
        "total_fixtures": len(manifest_entries),
        "source_book_sha256": book_sha,
        "fixtures": manifest_entries
    }

    manifest_path = FIXTURE_ROOT / "manifest.yaml"
    with open(manifest_path, "w", encoding="utf-8") as f:
        yaml.dump(manifest_data, f, allow_unicode=True, sort_keys=False)

    print(f"Successfully wrote manifest with {len(manifest_entries)} fixtures to {manifest_path}")


if __name__ == "__main__":
    main()
