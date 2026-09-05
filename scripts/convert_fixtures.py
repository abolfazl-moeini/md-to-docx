#!/usr/bin/env python3
"""Convenience script to convert all fixture and example markdown documents to DOCX."""

import sys
from pathlib import Path
from md_to_docx.pipeline import convert_markdown_to_docx

def main():
    root = Path(__file__).parent.parent
    targets = [
        root / "tests" / "fixtures",
        root / "examples",
    ]

    converted_count = 0
    for target_dir in targets:
        if not target_dir.exists():
            continue
        print(f"\nProcessing directory: {target_dir}")
        for md_file in sorted(target_dir.glob("*.md")):
            docx_file = md_file.with_suffix(".docx")
            print(f"  Converting {md_file.name} -> {docx_file.name} ...", end=" ", flush=True)
            try:
                out = convert_markdown_to_docx(md_file, docx_file)
                size_kb = out.stat().st_size / 1024.0
                print(f"OK ({size_kb:.1f} KB)")
                converted_count += 1
            except Exception as e:
                print(f"FAILED: {e}")
                sys.exit(1)

    print(f"\nSuccessfully generated {converted_count} DOCX files on disk.")

if __name__ == "__main__":
    main()
