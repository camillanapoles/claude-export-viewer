# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Python CLI tool that converts a Claude.ai data export ZIP into a browsable static HTML website. The export ZIP contains `users.json`, `projects.json`, `memories.json`, and `conversations.json`. The output is a flat directory with `index.html`, `style.css`, and `conversations/{uuid}.html`.

## Commands

```bash
# Setup
uv venv && uv pip install -e "."

# Run against a real export
.venv/bin/claude-export-viewer exports/data-*.zip -o site/

# Tests
.venv/bin/pytest tests/ -v
.venv/bin/pytest tests/test_renderer.py::test_render_message_artifact_create  # single test

# Lint
.venv/bin/ruff check src/ tests/
.venv/bin/ruff format --check src/ tests/
.venv/bin/ruff check --fix src/ tests/ && .venv/bin/ruff format src/ tests/  # auto-fix
```

## Architecture

The data flows in one direction: **ZIP → models → renderer → templates → HTML files**.

- **`models.py`** — Pydantic v2 models for all four JSON files. Content blocks use a `ContentBlock` discriminated union on the `type` field (`text`, `thinking`, `tool_use`, `tool_result`, `token_budget`). The `ToolUseContent` model has special handling for artifacts via `is_artifact` / `artifact_input` properties — artifact tool_use blocks have `name="artifacts"` and their `input` dict contains `command`, `type`, `title`, `content`, etc.

- **`loader.py`** — Opens the ZIP, finds JSON files by suffix (handles nested paths), and returns an `ExportData` instance.

- **`renderer.py`** — Converts each `ChatMessage` into an HTML string. The key function is `render_message()` which dispatches to per-block-type renderers. Markdown rendering uses mistune v3 with a custom `_HighlightRenderer` that extends `mistune.HTMLRenderer` (not `BaseRenderer` — this matters because `HTMLRenderer.render_token` unpacks token dicts into method args). Pygments handles code highlighting at build time.

- **`html_builder.py`** — Loads Jinja2 templates, renders index + each conversation page, copies `style.css`. Templates use `{{ message_html | safe }}` since message HTML is pre-rendered by the renderer.

- **`cli.py`** — Thin argparse wrapper.

## Rendering Rules

| Content type | How it renders |
| --- | --- |
| `text` | Full markdown via mistune + Pygments |
| `thinking` | Collapsible `<details>`, last summary as label |
| `tool_use` (artifacts, create/rewrite) | Bordered card with title bar; markdown artifacts rendered, code highlighted |
| `tool_use` (artifacts, update) | Skipped (no full content) |
| `tool_use` (other tools) | Collapsible with message text |
| `tool_result` (artifacts) | Skipped |
| `tool_result` (other) | Collapsible with pre-formatted output, truncated at 2000 chars |
| `token_budget` | Skipped |

## Export Data Quirks

These were discovered by validating against real export data:

- `ThinkingContent.summaries` contains `[{summary: str}]` objects, not plain strings
- `ToolUseContent.id` and `ToolResultContent.tool_use_id` can be `None`
- `display_content` on both tool_use and tool_result can be either a string or a dict (rich_link objects)
- Artifact `input` has `command` field: `create` has full content, `update` has `old_str`/`new_str`, `rewrite` has full content
- Artifact types seen: `text/markdown`, `text/html`, `application/vnd.ant.code`, `application/vnd.ant.react`, `application/vnd.ant.mermaid`, `image/svg+xml`
