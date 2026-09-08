def test_smoke_import():
    import md_to_docx
    assert md_to_docx is not None


def test_smoke_wheel_build_and_template_assets(tmp_path):
    """R3-06 / Packaging: Wheel build must include template assets (config.yaml, fonts, CSS)."""
    import os
    import subprocess
    import sys
    import zipfile
    from pathlib import Path
    from md_to_docx.template import PACKAGE_DIR

    # 1. Package directory contains vendored assets for all 4 templates
    templates = ["purple_book", "persian_book", "persian_compact", "persian_report"]
    for t_name in templates:
        t_dir = PACKAGE_DIR / "templates" / t_name
        assert (t_dir / "config.yaml").is_file(), f"Missing config.yaml in packaged {t_name}"
        assert (t_dir / "fonts" / "Vazirmatn-Regular.ttf").is_file(), f"Missing Regular font in {t_name}"
        assert (t_dir / "fonts" / "Vazirmatn-Bold.ttf").is_file(), f"Missing Bold font in {t_name}"
        assert (t_dir / "mermaid.css").is_file(), f"Missing mermaid.css in {t_name}"
        if t_name != "purple_book":
            assert (t_dir / "shell.docx").is_file(), f"Missing shell.docx in {t_name}"

    # 2. Build wheel into tmp_path
    wheel_dir = tmp_path / "dist"
    wheel_dir.mkdir(parents=True, exist_ok=True)
    res = subprocess.run(
        [sys.executable, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation", "-w", str(wheel_dir), "."],
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
        for t_name in templates:
            assert f"md_to_docx/templates/{t_name}/config.yaml" in names, f"Wheel missing {t_name}/config.yaml"
            assert f"md_to_docx/templates/{t_name}/fonts/Vazirmatn-Regular.ttf" in names, f"Wheel missing {t_name} Regular font"
            assert f"md_to_docx/templates/{t_name}/fonts/Vazirmatn-Bold.ttf" in names, f"Wheel missing {t_name} Bold font"
            assert f"md_to_docx/templates/{t_name}/mermaid.css" in names, f"Wheel missing {t_name} mermaid.css"
            if t_name != "purple_book":
                assert f"md_to_docx/templates/{t_name}/shell.docx" in names, f"Wheel missing {t_name} shell.docx"

    # 3. Install the wheel in a fresh venv and convert from outside the checkout (F15).
    venv_dir = tmp_path / "wheelvenv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True, timeout=60)
    pip = venv_dir / "bin" / "pip"
    py = venv_dir / "bin" / "python"
    inst = subprocess.run(
        [str(pip), "install", str(wheel_file)],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert inst.returncode == 0, inst.stderr
    outside = tmp_path / "outside"
    outside.mkdir()
    img = Path(__file__).resolve().parent / "fixtures" / "persian_layout" / "assets" / "logo.png"
    sample_md = outside / "sample.md"
    sample_md.write_text(
        "# تست بسته‌بندی\n\n::: note\nنکته بسته‌بندی\n:::\n\n"
        f"![لوگو]({img.name})\n\n```sql\nSELECT 1;\n```\n",
        encoding="utf-8",
    )
    (outside / img.name).write_bytes(img.read_bytes())
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    probe = subprocess.run(
        [
            str(py),
            "-c",
            "import md_to_docx, pathlib; p=pathlib.Path(md_to_docx.__file__).resolve(); "
            "print(p); assert 'site-packages' in str(p)",
        ],
        cwd=str(outside),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert probe.returncode == 0, probe.stdout + probe.stderr
    for t_name in templates:
        out_doc = outside / f"smoke_{t_name}.docx"
        conv = subprocess.run(
            [
                str(py),
                "-c",
                "from md_to_docx import convert_markdown_to_docx; "
                f"convert_markdown_to_docx(input_path='sample.md', output_path='{out_doc.name}', "
                f"template='{t_name}', overwrite=True)",
            ],
            cwd=str(outside),
            env=env,
            capture_output=True,
            text=True,
            timeout=90,
        )
        assert conv.returncode == 0, conv.stderr
        assert out_doc.exists()
        assert out_doc.stat().st_size > 1000

