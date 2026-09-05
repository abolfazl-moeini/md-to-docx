from pathlib import Path
import zipfile
import pytest
from lxml import etree
from md_to_docx.pipeline import convert_markdown_to_docx

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
FIXTURES_DIR = Path(__file__).parent / "fixtures"

REQUIRED_FIXTURES = [
    "sample_input.md",
    "persian_technical_doc.md",
    "english_technical_doc.md",
    "mixed_doc.md",
]


def test_sample_input_fixture_locked():
    fixture_path = FIXTURES_DIR / "sample_input.md"
    assert fixture_path.exists(), "sample_input.md must exist"
    content = fixture_path.read_text(encoding="utf-8")
    
    # Must contain exact headings with Persian numbers
    assert "# ۱.۵ پایگاه‌های دادهٔ سیستمی SQL Server" in content
    assert "## ۱.۴.۱ نقش Database Engine" in content
    assert "## ۱.۴.۲ نقش SQL Server Agent" in content
    assert "::: note نکتهٔ DBA" in content
    assert "## ۱.۴.۳ معماری داخلی SQL Server Database Engine" in content
    assert "```mermaid" in content
    assert "شکل ۲-۱. معماری داخلی SQL Server Database Engine" in content
    assert "::: warning هشدار" in content
    assert "## ۱.۶ مدل ذهنی هویت و دسترسی" in content
    assert "> Login معمولاً هویت ورود در سطح Instance است." in content
    assert "| مفهوم | سطح معمول | نمونه |" in content
    assert "| Login | Instance | DOMAIN\\Niloofar |" in content


def test_diverse_fixtures_exist():
    for name in REQUIRED_FIXTURES:
        p = FIXTURES_DIR / name
        assert p.exists(), f"Fixture file '{name}' must exist"
        assert p.stat().st_size > 100, f"Fixture file '{name}' must not be empty"

    assert (FIXTURES_DIR / "1.jpg").exists(), "1.jpg asset must exist in fixtures"
    assert (FIXTURES_DIR / "2.jpg").exists(), "2.jpg asset must exist in fixtures"


@pytest.mark.pandoc
@pytest.mark.mermaid
@pytest.mark.integration
def test_convert_all_fixtures_and_retain_on_disk(tmp_path):
    """Converts all diverse fixtures to DOCX using default template in tmp_path to avoid modifying tracked files."""
    import shutil
    from md_to_docx.mermaid import probe_mermaid_renderer
    if not shutil.which("pandoc"):
        pytest.skip("pandoc is not installed")
    can_render, reason = probe_mermaid_renderer()
    if not can_render:
        pytest.skip(f"Mermaid renderer not operational: {reason}")

    # Copy shared image assets
    for img in ["1.jpg", "2.jpg", "diagram-stub.png"]:
        src_img = FIXTURES_DIR / img
        if src_img.exists():
            (tmp_path / img).write_bytes(src_img.read_bytes())

    for name in REQUIRED_FIXTURES:
        src_md = FIXTURES_DIR / name
        md_file = tmp_path / name
        md_file.write_text(src_md.read_text(encoding="utf-8"), encoding="utf-8")
        docx_file = md_file.with_suffix(".docx")

        # Convert using default purple_book template
        saved_path = convert_markdown_to_docx(md_file, docx_file)

        # 1. Output must match target path on disk right beside the md file
        assert saved_path == docx_file.resolve()
        assert docx_file.exists(), f"Output DOCX '{docx_file.name}' must exist on disk"
        assert docx_file.is_file(), f"Output DOCX '{docx_file.name}' must be a regular file"
        assert docx_file.stat().st_size > 20_000, f"Output DOCX '{docx_file.name}' too small ({docx_file.stat().st_size} bytes)"

        # 2. Must be a valid zip / OOXML package
        with zipfile.ZipFile(docx_file, "r") as z:
            namelist = z.namelist()
            assert "word/document.xml" in namelist
            assert "word/settings.xml" in namelist
            assert "[Content_Types].xml" in namelist


def test_persian_docx_structure():
    docx_file = FIXTURES_DIR / "persian_technical_doc.docx"
    assert docx_file.exists(), "persian_technical_doc.docx must exist on disk"

    with zipfile.ZipFile(docx_file, "r") as z:
        # Check media contains at least 3 images (1 mermaid + 2 photos)
        media_pngs = [n for n in z.namelist() if n.startswith("word/media/")]
        assert len(media_pngs) >= 3, f"Expected at least 3 images in docx, found {len(media_pngs)}"

        doc_xml = z.read("word/document.xml")
        tree = etree.fromstring(doc_xml)
        all_text = "".join(tree.xpath("//w:t/text()", namespaces=NS))

        # Check Persian headings and numbers
        assert "راهنمای جامع معماری داده" in all_text
        assert "۱.۰" in all_text
        assert "۱.۱" in all_text

        # Check callout titles
        assert "نکتهٔ کلیدی پایگاه داده" in all_text
        assert "هشدار مهاجرت داده" in all_text

        # Check RTL tables (bidiVisual)
        bidi_tables = tree.xpath("//w:tbl[.//w:bidiVisual]", namespaces=NS)
        assert len(bidi_tables) >= 1, "Persian doc must contain RTL bidiVisual tables"

        # Check table data content
        assert "احراز هویت (Auth)" in all_text
        assert "تسویه حساب و پرداخت" in all_text

        # Check caption
        assert "شکل ۱-۱." in all_text

        # Check code blocks and syntax highlighting (json, sql, typescript, python)
        code_blocks = tree.xpath("//w:tc[.//w:shd[@w:fill='F6F8FA']]", namespaces=NS)
        assert len(code_blocks) >= 4, f"Expected at least 4 code blocks, found {len(code_blocks)}"
        assert "OutboxMessages" in all_text
        assert "processOrderMessage" in all_text
        assert "OrderCreated" in all_text
        assert "dispatch_order_notification" in all_text


def test_english_docx_structure():
    docx_file = FIXTURES_DIR / "english_technical_doc.docx"
    assert docx_file.exists(), "english_technical_doc.docx must exist on disk"

    with zipfile.ZipFile(docx_file, "r") as z:
        # Check media has at least 2 images (mermaid sequence + photo)
        media_pngs = [n for n in z.namelist() if n.startswith("word/media/")]
        assert len(media_pngs) >= 2, f"Expected at least 2 images in docx, found {len(media_pngs)}"

        doc_xml = z.read("word/document.xml")
        tree = etree.fromstring(doc_xml)
        all_text = "".join(tree.xpath("//w:t/text()", namespaces=NS))

        # Check English heading
        assert "Distributed Cache and Persistence Architecture" in all_text

        # Check callout titles
        assert "Replication Lag Considerations" in all_text
        assert "Eviction Policy Notice" in all_text

        # Check code block content
        assert "fetch_order_details" in all_text
        assert "OrderCacheClient" in all_text
        assert "IX_Orders_Pending" in all_text
        assert "redis-cluster-eu-west-1" in all_text

        # Check code blocks
        code_blocks = tree.xpath("//w:tc[.//w:shd[@w:fill='F6F8FA']]", namespaces=NS)
        assert len(code_blocks) >= 4, f"Expected at least 4 code blocks, found {len(code_blocks)}"

        # Check LTR data table exists and does NOT have bidiVisual
        tables = tree.xpath("//w:tbl", namespaces=NS)
        data_table = None
        for tbl in tables:
            tbl_text = "".join(tbl.xpath(".//w:t/text()", namespaces=NS))
            if "Node Identifier" in tbl_text and "redis-master-01" in tbl_text:
                data_table = tbl
                break

        assert data_table is not None, "English data table must exist in document"
        assert len(data_table.xpath(".//w:bidiVisual", namespaces=NS)) == 0, "English table must be LTR (no bidiVisual)"

        # Check caption
        assert "Figure 1." in all_text


def test_mixed_docx_structure():
    docx_file = FIXTURES_DIR / "mixed_doc.docx"
    assert docx_file.exists(), "mixed_doc.docx must exist on disk"

    with zipfile.ZipFile(docx_file, "r") as z:
        media_pngs = [n for n in z.namelist() if n.startswith("word/media/")]
        assert len(media_pngs) >= 3, f"Expected at least 3 images in docx, found {len(media_pngs)}"

        doc_xml = z.read("word/document.xml")
        tree = etree.fromstring(doc_xml)
        all_text = "".join(tree.xpath("//w:t/text()", namespaces=NS))

        # Check bilingual content
        assert "بررسی عملکرد پایگاه داده" in all_text
        assert "Database Performance Benchmark" in all_text
        assert "Throughput" in all_text
        assert "Apache Kafka" in all_text

        # Check code blocks (sql, json, python, typescript)
        code_blocks = tree.xpath("//w:tc[.//w:shd[@w:fill='F6F8FA']]", namespaces=NS)
        assert len(code_blocks) >= 4, f"Expected at least 4 code blocks, found {len(code_blocks)}"
        assert "dm_hadr_database_replica_states" in all_text
        assert "OLTP-Throughput-Test" in all_text
        assert "calculate_latency_metrics" in all_text
        assert "checkFragmentation" in all_text

        # Check caption
        assert "شکل ۲-۱." in all_text
