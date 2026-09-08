"""
Unit tests for Persian layout quality fixtures and manifest (Q01).
"""

import hashlib
import json
import subprocess
from pathlib import Path
import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "persian_layout"
MANIFEST_PATH = FIXTURE_ROOT / "manifest.yaml"
EXPECTED_BOOK_SHA = "525a3e92016a946bf36fdd5b3a2a8c8829a6e71e3e433fe52b6d9e9f3352443b"


def test_manifest_exists_and_has_61_fixtures():
    assert MANIFEST_PATH.exists(), f"Manifest not found at {MANIFEST_PATH}"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert data["total_fixtures"] == 61
    assert data["source_book_sha256"] == EXPECTED_BOOK_SHA
    fixtures = data["fixtures"]
    assert len(fixtures) == 61

    ids = [f["id"] for f in fixtures]
    assert len(set(ids)) == 61, "Fixture IDs must be completely unique"
    assert "B00" in ids
    for c in ["C01", "C02", "C03", "C04"]:
        assert c in ids
    for r in range(1, 41):
        assert f"R{r:02d}" in ids
    for s in range(1, 17):
        assert f"S{s:02d}" in ids


def test_fixture_files_exist_and_sha_matches():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    fixtures = data["fixtures"]

    for fix in fixtures:
        path = FIXTURE_ROOT / fix["rel_path"]
        assert path.exists(), f"Fixture file missing: {path}"
        with open(path, "rb") as f:
            actual_sha = hashlib.sha256(f.read()).hexdigest()
        assert actual_sha == fix["sha256"], f"SHA mismatch for {fix['id']}: expected {fix['sha256']}, got {actual_sha}"


def test_all_fixtures_parse_cleanly_with_pandoc():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    fixtures = data["fixtures"]

    for fix in fixtures:
        path = FIXTURE_ROOT / fix["rel_path"]
        content = path.read_text(encoding="utf-8")

        # Fences and Divs must be balanced
        fence_count = content.count("```")
        assert fence_count % 2 == 0, f"Unbalanced code fence in {fix['id']}"
        div_count = content.count(":::")
        assert div_count % 2 == 0, f"Unbalanced Div in {fix['id']}"

        cmd = [
            "pandoc",
            "-f", "markdown+fenced_divs+pipe_tables+grid_tables+backtick_code_blocks+raw_html+markdown_in_html_blocks",
            "-t", "json"
        ]
        res = subprocess.run(cmd, input=content, text=True, capture_output=True)
        assert res.returncode == 0, f"Pandoc parse failure on {fix['id']}: {res.stderr}"


def test_b00_captions_without_images():
    b00_path = FIXTURE_ROOT / "source" / "B00.md"
    content = b00_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # The 5 caption lines in the plan: 115, 125, 262, 401, 435 (1-indexed)
    expected_captions = {
        115: "شکل ۱-۱",
        125: "شکل ۱-۲",
        262: "شکل ۱-۳",
        401: "شکل ۲-۱",
        435: "شکل ۲-۲",
    }
    for l_num, prefix in expected_captions.items():
        line = lines[l_num - 1]
        assert line.startswith(prefix), f"Expected caption at line {l_num} to start with {prefix}, got: {line}"
