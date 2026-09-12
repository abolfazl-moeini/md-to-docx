# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-09-12

### Added
- **Headless LibreOffice PDF Engine (`src/md_to_docx/pdf.py`)**:
  - Direct conversion from Markdown to PDF (`md2docx convert input.md -o output.pdf`).
  - Standalone conversion from DOCX to PDF (`md2docx to-pdf input.docx -o output.pdf`).
  - Python public APIs: `convert_markdown_to_pdf`, `convert_docx_to_pdf`, `find_soffice_binary`, `is_valid_pdf`, and `LibreOfficeNotFoundError`.
- **Atomic Two-Phase Staging & Process Isolation**:
  - Two-phase staging pipeline: Markdown $\to$ AST $\to$ Staged DOCX $\to$ Headless LibreOffice $\to$ Staged PDF $\to$ Atomic Publication with backup and rollback.
  - Temporary isolated user profile generation (`-env:UserInstallation`) for LibreOffice to prevent lock collisions and configuration pollution.
  - Robust process group isolation (`start_new_session=True` / `CREATE_NEW_PROCESS_GROUP`) with guaranteed zombie cleanup (`os.killpg(SIGKILL)` / `taskkill`) on timeout.
  - Media directory hygiene: suppresses temporary Mermaid diagrams folder during PDF output unless `--keep-docx` or explicit `--media-dir` is requested.
  - File locking with `fcntl.flock` serialization (`.{stem}.pdf.publish.lock` and `.{stem}.publish.lock`).
- **Font Discovery & Injection for LibreOffice**:
  - Dynamic Fontconfig configuration (`fonts.conf`) and `SAL_FONTPATH` environment configuration passing template font directories (such as Vazirmatn) to LibreOffice.
  - XML escaping for directory paths containing special characters.
- **PDF Validation & Verification**:
  - `is_valid_pdf` verifying `%PDF-` magic header, trailer `%%EOF` marker, non-zero file existence, and minimum byte size threshold.
- **CLI Flags & Ergonomics**:
  - `--keep-docx`: Preserves intermediate `.docx` file when generating `.pdf`.
  - `--pdf-timeout` / `--timeout`: Configurable conversion timeout in seconds (default: 120s).
  - `--direction [auto|rtl|ltr]`: Explicit document direction override with automated narrative detection.
  - `--text-align [start|right|left|center|both|justify]`: Paragraph alignment override.
  - `--font, --font-family`: Font family override for body and complex script text.
  - `--heading-font`, `--latin-font`, `--code-font`: Independent font role overrides.
  - `--embed-fonts / --no-embed-fonts`: TrueType font embedding control.
  - Auto-discovery of `soffice` across standard macOS, Linux, and Windows directories, with explicit `MD2DOCX_SOFFICE` override support and friendly installation guidance on exit code 1.
- **Direction & Typography Precedence (`src/md_to_docx/options.py`)**:
  - Strict resolution hierarchy: CLI/API option $\to$ YAML metadata `dir`/`direction` $\to$ YAML metadata `lang`/`language` $\to$ AST narrative Unicode heuristic $\to$ Template fallback.
  - `detect_narrative_direction`: Automated Unicode bidirectional classifier (`R`/`AL` vs `L`) ignoring code blocks, math, and URL targets.
- **Comprehensive Test Suites**:
  - Over 50 new tests in `tests/test_pdf.py` covering binary discovery, validation, timeouts, error conditions, process tree killing, media hygiene, and CLI behaviors.
  - 30 tests in `tests/test_v3_features.py` testing typography precedence, XML generation, and options validation.

### Changed
- **Default Paragraph Alignment**:
  - `purple_book` template default `page.paragraph_align` set to `start` (ragged-right) for optimal Persian readability and prevention of awkward word-stretching.
- **Public API Exports (`src/md_to_docx/__init__.py`)**:
  - Exported `convert_markdown_to_pdf`, `convert_docx_to_pdf`, `find_soffice_binary`, `is_valid_pdf`, `LibreOfficeNotFoundError`, `GeneratorOptions`, and `DEFAULT_FONT_FAMILY`.
- **Pipeline Extensibility (`src/md_to_docx/pipeline.py`)**:
  - `convert_markdown_to_docx` and `convert_markdown_to_pdf` now accept `GeneratorOptions`, individual font overrides, and an optional diagnostic `report` dictionary.

### Fixed
- Complex script (`w:cs`, `w:eastAsia`) font inheritance across mixed inline runs, numbers, and technical terms.
- Multi-paragraph footnote alignment and bidirectional flag inheritance.
- Table visual right-to-left layout (`w:bidiVisual`) when headers or content contain mixed languages.
- CLI argument validation ensuring exit code 2 on invalid timeouts, extensions, or directory targets.

---

## [0.1.0] - 2026-08-15

### Added
- Initial release of `md-to-docx`.
- Bilingual Persian / English Markdown to DOCX conversion.
- 4 built-in templates: `purple_book`, `persian_book`, `persian_compact`, `persian_report`.
- Mermaid diagram rendering via `mermaid-cli` and headless Chromium.
- Heading number badge styling and TOC insertion.
- Callout admonitions (`::: note`, `::: warning`, GitHub alerts).
- GFM table styling with repeating headers and alternating rows.
- Pygments syntax highlighting for fenced code blocks.
- Native Word footnotes and Office Math (OMML) conversion.
- Reverse DOCX-to-Markdown extraction (`md2docx to-md`).
