# Claude Export Viewer

Convert a [Claude.ai](https://claude.ai) data export into a browsable static HTML website.

Claude.ai lets you export your data as a ZIP file containing your conversations, projects, and memories.
This tool takes that ZIP and generates a self-contained HTML site you can open directly in any browser.

## Features

- Renders full conversation history with human and assistant messages
- Syntax-highlighted code blocks via Pygments
- Markdown rendering for text content
- Artifact display (code, markdown, HTML, SVG, Mermaid, React)
- Collapsible thinking blocks and tool usage details
- Conversation index page sorted by date

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Installation

```bash
git clone https://github.com/lordjabez/claude-export-viewer.git
cd claude-export-viewer
uv sync
```

## Usage

### 1. Export your data from Claude.ai

Go to [Claude.ai Settings](https://claude.ai/settings) and click "Export Data". You'll receive an email with a download link for a ZIP file.

### 2. Generate the site

```bash
uv run claude-export-viewer path/to/export.zip -o path/to/output/
```

The `-o` flag sets the output directory (defaults to `site/`).

### 3. View the site

Open `path/to/output/index.html` in your browser.

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Lint
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# Auto-fix lint issues
uv run ruff check --fix src/ tests/ && uv run ruff format src/ tests/
```
