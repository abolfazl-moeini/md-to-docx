# md-to-docx

<p align="right">
  <a href="README_FA.md"><b>نسخه فارسی (Persian)</b></a> | <b>English</b>
</p>

**Bilingual Persian / RTL Markdown + Mermaid → Word (.docx)**

Transform bilingual technical Markdown into styled Microsoft Word documents: right-to-left (RTL) body text, mixed Persian/English inline runs, numbered heading badges, styled callout boxes, RTL tables, syntax-highlighted code blocks, and crisp high-resolution Mermaid diagrams.

<p align="center">
  <img src="sample-template/1.jpg" alt="Sample Word output: heading badges, Mermaid diagram, DBA note" width="100%">
</p>
<p align="center">
  <img src="sample-template/2.jpg" alt="Sample Word output: warning callout, quote, RTL table" width="420">
</p>

---

## TL;DR — Quick Start

Conversion pipeline summary: **Template + Markdown (File or Content) → Word Document (.docx)**

### 1. One-Step Environment Setup (Once)

```bash
./scripts/bootstrap.sh
source .venv/bin/activate
```

### 2. Fast Command-Line (CLI) Conversion

```bash
# Option A: Convert from a Markdown file
md2docx convert input.md -o output.docx --template purple_book

# Option B: Convert directly from standard input (pipe)
echo "# Document Title\n\nSample Markdown text with RTL content." | md2docx convert - -o output.docx --template purple_book
```

### 3. Python API

```python
from md_to_docx import convert_markdown_to_docx

# Option A: Convert from a Markdown file
convert_markdown_to_docx(
    input_path="document.md",
    output_path="output.docx",
    template="purple_book",  # Or custom template path: './templates/my_theme'
    overwrite=True,
)

# Option B: Convert directly from a Markdown string
convert_markdown_to_docx(
    content="# Document Title\n\nTechnical paragraphs, tables, and mermaid diagrams...",
    output_path="output.docx",
    template="purple_book",
    overwrite=True,
)
```

| Component | Type | Description |
| :--- | :--- | :--- |
| **Input 1: Template** | Theme name or folder path | Built-in theme (`purple_book`) or any directory containing `config.yaml` with color palettes, fonts, and geometry |
| **Input 2: Markdown** | File path or string content | Markdown `.md` file path (`input_path`) or raw Markdown text (`content` in Python / `-` in CLI) |
| **Output: Word File** | Word Document | Output file with **`.docx`** extension (full RTL layout, Vazirmatn font, heading badges, tables, and embedded diagrams) |

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
- **Node.js 18+** (required for `mermaid-cli`)
- **Chrome / Chromium** (required for Puppeteer headless rendering)

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

# Python environment setup
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -c constraints.txt -e ".[dev]"
npm ci || npm install

# Install Chromium for Puppeteer
npx puppeteer browsers install chrome
```

Installing the package puts the `md2docx` executable directly on your PATH.

---

## CLI Usage

```bash
# Basic conversion
md2docx convert document.md -o document.docx

# Overwrite existing output explicitly
md2docx convert document.md -o document.docx --overwrite

# Use a custom template
md2docx convert document.md -o document.docx --template purple_book
md2docx convert document.md -o document.docx --template ./templates/my_theme

# Inspect and validate templates
md2docx templates list
md2docx templates validate purple_book
```

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

The default `purple_book` theme is located under `templates/purple_book/`:

```
templates/purple_book/
├── config.yaml                 # schema_version: 1, colors, fonts, callouts
├── mermaid.json                # mermaid-cli theme configuration
├── mermaid.css                 # Custom font and CSS injection for Mermaid
├── puppeteer.json              # Headless browser runtime settings
├── fonts/Vazirmatn-Regular.ttf # SIL OFL font used during diagram rendering
└── shell.docx                  # Optional base Word document (headers and footers)
```

### Creating a Custom Theme

```bash
cp -R templates/purple_book templates/my_theme
# Edit templates/my_theme/config.yaml
md2docx templates validate my_theme
md2docx convert input.md --template my_theme -o out.docx
```

---

## Operational Specifications & Limits (v1)

- **File Formats**: Official output is `.docx`. Legacy binary Word 97-2003 `.doc` is rejected with exit code 2.
- **Input Size Cap**: Maximum supported input size is 20 MB (`MAX_INPUT_SIZE_BYTES = 20 * 1024 * 1024`).
- **Concurrent Publishing**: File write locks are serialized with stable POSIX `fcntl.flock` (`.{stem}.publish.lock`).
- **Remote Images**: Remote `http://`, `https://`, and `data:` URIs are rejected in v1; reference local images relative to your Markdown file.
- **Word Shell Contract**: A custom `shell.docx` must contain exactly one section.
- **Font Fallback**: Recipient systems without Vazirmatn will automatically fall back to their system default Arabic/Persian font.
