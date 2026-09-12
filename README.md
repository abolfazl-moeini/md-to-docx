# md-to-docx

<p align="right">
  <a href="README_FA.md"><b>نسخه فارسی (Persian)</b></a> | <b>English</b>
</p>

**Bilingual Persian / RTL Markdown + Mermaid → Word (.docx) & PDF (.pdf)**

Transform bilingual technical Markdown into styled Microsoft Word documents and publication-ready PDFs: right-to-left (RTL) body text, mixed Persian/English inline runs, numbered heading badges, styled callout boxes, RTL tables, syntax-highlighted code blocks, and crisp high-resolution Mermaid diagrams.

<p align="center">
  <img src="sample-template/1.jpg" alt="Sample Word output: heading badges, Mermaid diagram, DBA note" width="100%">
</p>
<p align="center">
  <img src="sample-template/2.jpg" alt="Sample Word output: warning callout, quote, RTL table" width="420">
</p>

---

## TL;DR — Quick Start

Conversion pipeline summary: **Template + Markdown (File or Content) → Word Document (.docx) or PDF (.pdf)**

### 1. One-Step Environment Setup (Once)

```bash
./scripts/bootstrap.sh
source .venv/bin/activate
```

### 2. Fast Command-Line (CLI) Conversion

```bash
# Option A: Convert from Markdown file to Word (.docx)
md2docx convert input.md -o output.docx --template purple_book

# Option B: Convert directly to PDF (.pdf) via headless LibreOffice
md2docx convert input.md -o output.pdf --template purple_book

# Option C: Convert directly from standard input (pipe)
echo "# Document Title\n\nSample Markdown text with RTL content." | md2docx convert - -o output.docx --template purple_book

# Option D: Convert existing DOCX to PDF
md2docx to-pdf input.docx -o output.pdf
```

### 3. Python API

```python
from md_to_docx import convert_markdown_to_docx, convert_markdown_to_pdf, convert_docx_to_pdf

# Convert Markdown to Word (.docx)
convert_markdown_to_docx(
    input_path="document.md",
    output_path="output.docx",
    template="purple_book",  # Or custom template path: './templates/my_theme'
    overwrite=True,
)

# Convert Markdown directly to PDF (.pdf) via headless LibreOffice
convert_markdown_to_pdf(
    input_path="document.md",
    output_path="output.pdf",
    template="purple_book",
    overwrite=True,
    keep_docx=False,  # Set True to preserve intermediate output.docx
)

# Convert existing DOCX to PDF
convert_docx_to_pdf("output.docx", "output.pdf", overwrite=True)
```

| Component | Type | Description |
| :--- | :--- | :--- |
| **Input 1: Template** | Theme name or folder path | Built-in theme (`purple_book`) or any directory containing `config.yaml` with color palettes, fonts, and geometry |
| **Input 2: Markdown** | File path or string content | Markdown `.md` file path (`input_path`) or raw Markdown text (`content` in Python / `-` in CLI) |
| **Output: Word File** | Word Document | Output file with **`.docx`** extension (full RTL layout, Vazirmatn font, heading badges, tables, and embedded diagrams) |
| **Output: PDF File** | PDF Document | Output file with **`.pdf`** extension generated via headless LibreOffice with process isolation, dynamic font injection, and validation |

---

## Why This Exists

Pandoc’s default DOCX writer produces purely LTR layouts and completely ignores Mermaid diagram blocks. Furthermore, Chinese `--reference-doc` templates introduce East Asian fonts and unwanted first-line indentation that break Persian typography. 

**md-to-docx** uses Pandoc strictly as a robust Markdown AST parser, and then builds native OpenXML (OOXML) documents using `python-docx`:

- **Native RTL Document & Tables**: Injects `<w:bidi>` and `<w:bidiVisual>` so text and table columns align properly.
- **Complex Script Font Mapping**: Explicitly assigns `<w:cs>`, `<w:szCs>`, and `fa-IR` language tags for Persian runs while keeping Latin fonts distinct.
- **Source Heading Numbering**: Persian/Arabic/Latin numbers (e.g., `۱.۴.۱`) are extracted directly from headings and preserved without Word multilevel auto-renumbering distortion.
- **Callout Admonitions**: `::: note` and `::: warning` blocks are styled into beautiful container boxes with distinct accents and iconography.
- **Automated Mermaid Rendering**: Fenced `mermaid` code blocks are compiled via `mermaid-cli` and embedded directly as high-DPI PNGs.

---

## Key Features

| Input | Output |
| :--- | :--- |
| `# ۱.۵ Section Title` | Purple number badge on the right + bottom accent line |
| Mixed `Clientها` / `SQL Server` | Script-segmented runs to ensure Latin words do not flip direction |
| `::: note DBA Tip` | Dark purple header with `◆` bullet and shaded body |
| `::: warning Warning` | Warm amber box with clear title styling |
| `> Blockquote` | Thick purple **physical-right** accent bar with `#ECE4F1` background fill |
| GFM Table | Purple header row with white text, visual-RTL column alignment |
| ` ```mermaid ` + `شکل ۲-۱. …` | Centered diagram image with standard figure caption beneath |
| ` ```python ` / `sql` / `ts` | Monospaced shaded LTR code box with Pygments syntax highlighting |

Also supports modern GitHub alerts (`> [!NOTE]`, `> [!WARNING]`), bullet and numbered lists, local images, internal and external hyperlinks, native Word footnotes, and Office Math equations (`m:oMath`).

---

## System Requirements

- **Python 3.11+**
- **[Pandoc](https://pandoc.org) 3.x** (used as AST parser only; it does not write the DOCX)
- **Node.js >= 22.12.0** (required for `mermaid-cli`)
- **Chrome / Chromium** (required for Puppeteer headless rendering)
- **[LibreOffice](https://www.libreoffice.org)** (required for PDF conversion: `brew install --cask libreoffice` on macOS, `sudo apt install libreoffice` on Ubuntu/Debian, `sudo dnf install libreoffice` on Fedora; or set `MD2DOCX_SOFFICE` to your `soffice` binary path)

> [!TIP]
> For optimal viewing, install the [Vazirmatn](https://github.com/rastikerdar/vazirmatn) font on the client machine that will view the resulting Word file.

---

## Quick Start & Setup

Run the automated one-step setup script to configure Python virtual environment, dependencies, Puppeteer Chromium, and verify Pandoc:

```bash
./scripts/bootstrap.sh
```

Or configure manually:

```bash
# On macOS:
brew install pandoc
brew install --cask libreoffice    # Required for PDF conversion

# Python environment setup
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -c constraints.txt -e ".[dev]"
npm ci

# Install the managed Puppeteer browser (not system Chrome)
npx puppeteer browsers install chrome-headless-shell
```

Installing the package puts the `md2docx` executable directly on your PATH.

---

## CLI Usage

### Basic Conversion Commands

```bash
# Convert Markdown to Word (.docx)
md2docx convert document.md -o document.docx

# Convert Markdown directly to PDF (.pdf) via headless LibreOffice
md2docx convert document.md -o document.pdf

# Convert Markdown to PDF and keep intermediate DOCX
md2docx convert document.md -o document.pdf --keep-docx

# Convert Markdown to PDF with custom timeout (default: 120s)
md2docx convert document.md -o document.pdf --pdf-timeout 180

# Convert existing DOCX to PDF
md2docx to-pdf document.docx -o document.pdf --pdf-timeout 120

# Overwrite existing output explicitly
md2docx convert document.md -o document.docx --overwrite

# Use a custom template
md2docx convert document.md -o document.docx --template purple_book
md2docx convert document.md -o document.docx --template ./templates/my_theme

# Inspect and validate templates
md2docx templates list
md2docx templates validate purple_book

# Convert DOCX back to Markdown and extract media
md2docx to-md document.docx -o document.md
```

### CLI Options & Flags

#### `md2docx convert` Options & Styling Flags

The `convert` command handles Markdown to DOCX or PDF conversion with comprehensive layout and typography controls:

| Flag | Description | Values / Default |
| :--- | :--- | :--- |
| `-o, --output` | Output file path (`.docx` or `.pdf`) | Defaults to `{input}.docx` |
| `-t, --template` | Template name or directory path | Defaults to `purple_book` |
| `-f, --overwrite` | Overwrite existing output file | `False` |
| `--keep-docx` | Preserve intermediate DOCX when generating PDF | `False` |
| `--pdf-timeout` | LibreOffice execution timeout in seconds | `120` |
| `--direction, --dir` | Document text direction | `auto` (default), `rtl`, `ltr` |
| `--text-align, --align` | Body paragraph text alignment | `start` (ragged-right), `right`, `left`, `center`, `both` (justified) |
| `--font, --font-family` | Font family for body and complex script text | Defaults to template font (`Vazirmatn`) |
| `--heading-font` | Font family override for headings | Defaults to template heading font |
| `--latin-font` | Font family override for Latin text runs | Defaults to template latin font (`Segoe UI`) |
| `--code-font` | Monospace code block and inline code font | Defaults to template code font (`Courier New`) |
| `--embed-fonts / --no-embed-fonts` | Embed TrueType font files inside the DOCX package | `--no-embed-fonts` |

#### `md2docx to-pdf` Options

The `to-pdf` command converts an existing `.docx` file into a `.pdf` file via headless LibreOffice:

| Flag | Description | Values / Default |
| :--- | :--- | :--- |
| `-o, --output` | Output PDF file path | Defaults to `{input}.pdf` |
| `-f, --overwrite` | Overwrite existing output PDF file | `False` |
| `--timeout, --pdf-timeout` | LibreOffice execution timeout in seconds | `120` |

### CLI Exit Codes

- `0`: Successful execution.
- `1`: Operational failure (e.g. conversion error, permission issue).
- `2`: Usage error, missing input, invalid options, or unconfirmed file collision.

---

## Pandoc AST Support Matrix

| Category | Node Types | Output Behavior |
| :--- | :--- | :--- |
| **Inlines** | `Str`, `Space`, `SoftBreak`, `LineBreak` | Bidi-segmented runs, Complex Script (Vazirmatn) & Latin font matching |
| | `Strong`, `Emph` | Bold (`w:b`, `w:bCs`), Italic (`w:i`, `w:iCs`) |
| | `Strikeout` | Strikethrough (`w:strike`) |
| | `Superscript`, `Subscript` | Vertical alignment (`w:vertAlign`) |
| | `Underline` | Single underline (`w:u`) |
| | `SmallCaps` | Small capitals (`w:smallCaps`) |
| | `Code` | Inline monospace code (`Courier New`), strictly LTR |
| | `Link`, `Quoted`, `Span` | True Word hyperlinks (`w:hyperlink`), quotation marks (« »), formatted spans |
| | `Note` | Real Word footnotes (`word/footnotes.xml`) |
| | `Math` | Native Office Math (`m:oMath`) for common TeX equations (fractions, sums, powers) |
| **Blocks** | `Header` (1–6) | Level-specific size, bottom border, or RTL number badge table |
| | `Para`, `Plain` | Justified RTL/LTR body paragraphs with line spacing |
| | `BlockQuote` | Shaded box (`#ECE4F1`) with physical right border (`6B2FA0`) |
| | `Div` (Callouts) | `::: note`, `::: warning`, and GFM alerts preserving rich child formatting |
| | `Div` (Mermaid) | Compiled via mermaid-cli to high-res PNG and centered |
| | `Table` | Multi-tbody support, repeating header row (`6B2FA0`), visual-RTL (`w:bidiVisual`) |
| | `CodeBlock` | LTR shaded container with syntax highlighting token styles |
| | `BulletList`, `OrderedList`| Indented list items with text markers |
| | `DefinitionList` | Bolded terms with indented definition descriptions |
| | `HorizontalRule` | Subtle horizontal dividing rule |

---

## Templates

`md-to-docx` includes 4 built-in production templates tailored for different document formats:

| Template | Page Size | Paragraph Alignment | Description |
| :--- | :--- | :--- | :--- |
| `purple_book` | A4 | `start` (ragged-right) | Default theme with purple styling, decorative heading badges, and ragged-right edge for optimal Persian typography. |
| `persian_book` | A4 | `start` (ragged-right) | Technical Persian book layout with page breaks before H1, clean neutral headers/footers, and ragged-right edge for optimal Persian readability. |
| `persian_compact`| A5 | `start` (ragged-right) | Pocket handbook layout with compact margins and page breaks before H1. |
| `persian_report` | Letter | `start` (ragged-right) | Formal organizational report with continuous H1 headings, embedded emblem logo header, and dynamic PAGE field footer. |

### Template Configuration Options (`config.yaml`)

- `page.paragraph_align`: Set to `start` (recommended for Persian technical text to prevent awkward justification word-stretching) or `both` (full justification).
- `page.space_after_pt`: Body paragraph trailing space in points (default: `6.0`).
- `caption.size_pt`: Font size for figure and table captions (e.g. `10.0`).
- `custom_styles`: Map custom Pandoc fenced div style names to callout roles. Put `strict` inside this mapping (it is not a top-level template key):
  ```yaml
  custom_styles:
    strict: false  # If true, unmapped custom styles raise ConvertError
    "Field Note": note
    "Security Alert": warning
  ```
- Code blocks keep **Courier New** in all four templates. DejaVu Sans Mono is not bundled. Whether Courier New is actually installed on a review machine must be checked in that environment.

### Typography & Font Roles

- **Persian Text (`fonts.body`, `fonts.heading`)**: Defaults to `Vazirmatn`. Both regular and bold weights (`Vazirmatn-Regular.ttf`, `Vazirmatn-Bold.ttf`) are bundled in all 4 templates.
- **Latin Text (`fonts.latin`)**: Configured to `Segoe UI` (or `Vazirmatn`).
- **Code Blocks & Monospace (`fonts.code`)**: Defaults to `Courier New`.
  > **Design Decision**: `Courier New` is the configured code font. Presence on a given Word/LibreOffice host is an environment fact, not a guarantee; check the review machine if monospace looks substituted. To use another font, set `fonts.code` in `config.yaml`. DejaVu Sans Mono is not bundled.

### Creating a Custom Theme

```bash
cp -R templates/persian_book templates/my_theme
# Edit templates/my_theme/config.yaml
md2docx templates validate my_theme
md2docx convert input.md --template my_theme -o out.docx
```

---

## Persian Layout Quality Matrix & Verification

A comprehensive automated matrix suite tests 61 representative fixtures across all 4 templates (244 conversion pairs) with independent structural and content oracles:

```bash
python scripts/matrix_runner.py
# Or run for specific fixtures:
python scripts/matrix_runner.py --fixtures S01,S05,S11,B00
```

Invalid fixture names, an empty selection, or a non-empty output directory without `--overwrite-run` exit with code 2. Failed/blocked pairs exit with code 1.

Mermaid diagrams need Node `>=22.12.0`, `npm ci`, and a Puppeteer-managed browser (`npx puppeteer browsers install chrome-headless-shell` or `chrome`). System Chrome/Edge are not used unless `MD2DOCX_ALLOW_SYSTEM_BROWSER=1`. After a launch failure the process stops retrying (`MD2DOCX_MERMAID_HEALTH_FILE` can share that lock across workers). Page rendering uses `MD2DOCX_SOFFICE` or `soffice` on PATH; a user cache path is never hardcoded.

Detailed reports are generated under `artifacts/persian-layout/run_<timestamp>/` (`matrix.csv`, `run.json`, `reviews.json`, `summary.md`, and `index.html`). Visual review stays `pending` until LibreOffice/Word page renders are actually produced and reviewed.

---

## Operational Specifications & Limits
 
- **File Formats**: Official outputs are Word documents (`.docx`) and publication-ready PDFs (`.pdf`). Legacy binary Word 97-2003 `.doc` is rejected with exit code 2.
- **PDF Engine**: PDF generation uses headless LibreOffice (`soffice`) with isolated temporary user profiles, robust process group management, font directory injection, and output integrity validation.
- **Input Size Cap**: Maximum supported input size is 20 MB (`MAX_INPUT_SIZE_BYTES = 20 * 1024 * 1024`).
- **Concurrent Publishing**: File write locks are serialized with stable POSIX `fcntl.flock` (`.{stem}.publish.lock` and `.{stem}.pdf.publish.lock`).
- **Remote Images**: Remote `http://`, `https://`, and `data:` URIs are rejected in v1; reference local images relative to your Markdown file.
- **Word Shell Contract**: A custom `shell.docx` must contain exactly one section.
- **Font Fallback**: Recipient systems without Vazirmatn will automatically fall back to their system default Arabic/Persian font. TrueType fonts can optionally be embedded using `--embed-fonts`.
