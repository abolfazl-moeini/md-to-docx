def test_smoke_import():
    import md_to_docx
    assert md_to_docx is not None


def test_smoke_wheel_build_and_template_assets(tmp_path):
    """R3-06 / Packaging: Wheel build must include template assets (config.yaml, fonts, CSS)."""
    import subprocess
    import sys
    import zipfile
    from pathlib import Path
    from md_to_docx.template import PACKAGE_DIR

    # 1. Package directory contains vendored assets
    packaged_tmpl = PACKAGE_DIR / "templates" / "purple_book"
    assert (packaged_tmpl / "config.yaml").is_file()
    assert (packaged_tmpl / "fonts" / "Vazirmatn-Regular.ttf").is_file()
    assert (packaged_tmpl / "mermaid.css").is_file()

    # 2. Build wheel into tmp_path
    wheel_dir = tmp_path / "dist"
    wheel_dir.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(
        [sys.executable, "-m", "pip", "wheel", "--no-deps", "-w", str(wheel_dir), "."],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert res.returncode == 0, f"pip wheel failed: {res.stderr}"

    wheels = list(wheel_dir.glob("*.whl"))
    assert len(wheels) == 1, "Expected exactly 1 built wheel"
    wheel_file = wheels[0]

    with zipfile.ZipFile(wheel_file, "r") as z:
        names = z.namelist()
        assert "md_to_docx/templates/purple_book/config.yaml" in names
        assert "md_to_docx/templates/purple_book/fonts/Vazirmatn-Regular.ttf" in names
        assert "md_to_docx/templates/purple_book/mermaid.css" in names

