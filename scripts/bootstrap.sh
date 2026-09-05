#!/usr/bin/env bash
set -e

# ==============================================================================
# Bootstrap Script for md-to-docx
# Sets up Python virtualenv, Node dependencies, Chromium browser, and checks Pandoc.
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Bootstrapping md-to-docx environment ==="
echo "Project Root: ${ROOT_DIR}"
cd "${ROOT_DIR}"

# 1. Check Python
PYTHON_BIN=""
for cmd in python3.11 python3.12 python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
        PY_VER=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        PY_MAJOR=$("$cmd" -c 'import sys; print(sys.version_info.major)')
        PY_MINOR=$("$cmd" -c 'import sys; print(sys.version_info.minor)')
        if [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 11 ]; then
            PYTHON_BIN="$cmd"
            echo "✔ Found compatible Python: $cmd (v${PY_VER})"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "✖ Error: Python >= 3.11 is required. Please install Python 3.11 or later."
    exit 1
fi

# 2. Virtual Environment Setup
if [ ! -d ".venv" ]; then
    echo "Creating Python virtualenv at .venv..."
    "$PYTHON_BIN" -m venv .venv
fi

echo "Activating virtualenv and installing Python dependencies..."
VENV_PIP=".venv/bin/pip"
"$VENV_PIP" install --upgrade pip setuptools wheel
if [ -f "constraints.txt" ]; then
    "$VENV_PIP" install -c constraints.txt -e ".[dev]"
else
    "$VENV_PIP" install -e ".[dev]"
fi
echo "✔ Python dependencies installed."

# 3. Check and setup Node.js & npm
if command -v npm >/dev/null 2>&1; then
    echo "Installing Node.js dependencies via npm..."
    npm ci || npm install
    echo "✔ Node.js dependencies installed."

    # Install Chromium browser for Puppeteer if not available
    echo "Checking Puppeteer Chromium installation..."
    npx puppeteer browsers install chrome || echo "Notice: System Chrome/Chromium can be used as fallback."
else
    echo "⚠ Warning: 'npm' not found in PATH. Mermaid rendering via mmdc requires Node.js."
fi

# 4. Check Pandoc
if command -v pandoc >/dev/null 2>&1; then
    PANDOC_VER=$(pandoc --version | head -n 1)
    echo "✔ Pandoc is installed: ${PANDOC_VER}"
else
    echo "⚠ Warning: 'pandoc' not found in PATH. Install via: 'brew install pandoc' (macOS) or 'apt install pandoc' (Ubuntu)."
fi

echo ""
echo "=== Bootstrap Complete ==="
echo "Run tests: ./.venv/bin/python -m pytest"
echo "Convert fixtures: ./.venv/bin/python scripts/convert_fixtures.py"
