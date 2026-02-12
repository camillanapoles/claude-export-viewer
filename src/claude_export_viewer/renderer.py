from __future__ import annotations

import html
from typing import Any

import mistune
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer

from .models import (
    Attachment,
    ChatMessage,
    FileRef,
    TextContent,
    ThinkingContent,
    TokenBudgetContent,
    ToolResultContent,
    ToolUseContent,
)

# --- Markdown renderer with Pygments code highlighting ---

_pygments_formatter = HtmlFormatter(nowrap=True)


def _highlight_code(code: str, lang: str | None) -> str:
    try:
        if lang:
            lexer = get_lexer_by_name(lang, stripall=True)
        else:
            lexer = guess_lexer(code)
    except Exception:
        return f"<code>{html.escape(code)}</code>"
    return highlight(code, lexer, _pygments_formatter)


class _HighlightRenderer(mistune.HTMLRenderer):
    """Extends the default HTML renderer to use Pygments for code blocks."""

    def block_code(self, code: str, info: str | None = None, **attrs: Any) -> str:
        lang = info.split()[0] if info else None
        highlighted = _highlight_code(code, lang)
        lang_class = f' class="language-{html.escape(lang)}"' if lang else ""
        return f"<pre><code{lang_class}>{highlighted}</code></pre>\n"

    def link(self, text: str, url: str, title: str | None = None) -> str:
        title_attr = f' title="{html.escape(title)}"' if title else ""
        return f'<a href="{html.escape(url)}"{title_attr} target="_blank" rel="noopener">{text}</a>'


_md = mistune.create_markdown(
    renderer=_HighlightRenderer(),
    plugins=["strikethrough", "table"],
)


def render_markdown(text: str) -> str:
    """Render markdown text to HTML."""
    return _md(text)


# --- Content block renderers ---


def _render_text(block: TextContent) -> str:
    if not block.text:
        return ""
    return f'<div class="content-text">{render_markdown(block.text)}</div>'


def _render_thinking(block: ThinkingContent) -> str:
    if not block.thinking:
        return ""
    summary = block.summaries[-1].summary if block.summaries else "Thinking..."
    return (
        f'<details class="thinking">'
        f"<summary>{html.escape(summary)}</summary>"
        f'<div class="thinking-content">{render_markdown(block.thinking)}</div>'
        f"</details>"
    )


# Artifact type → human label mapping
_ARTIFACT_TYPE_LABELS: dict[str, str] = {
    "text/markdown": "Document",
    "text/html": "HTML",
    "application/vnd.ant.code": "Code",
    "application/vnd.ant.react": "React Component",
    "application/vnd.ant.mermaid": "Mermaid Diagram",
    "image/svg+xml": "SVG",
}


def _render_artifact(block: ToolUseContent) -> str:
    ai = block.artifact_input
    if ai is None:
        return ""

    # Only render create/rewrite commands (they have full content)
    if ai.command not in ("create", "rewrite"):
        return ""

    title = html.escape(ai.title or "Untitled")
    artifact_type = ai.type or ""
    type_label = _ARTIFACT_TYPE_LABELS.get(artifact_type, artifact_type)
    content = ai.content or ""

    # Render content based on type
    if artifact_type in ("text/markdown",):
        rendered = render_markdown(content)
    elif artifact_type in ("application/vnd.ant.code", "application/vnd.ant.mermaid"):
        lang = ai.language or ""
        rendered = f"<pre><code>{_highlight_code(content, lang or None)}</code></pre>"
    elif artifact_type in ("text/html", "application/vnd.ant.react", "image/svg+xml"):
        # Show as highlighted code — rendering raw HTML/React would be unsafe
        lang = "html" if artifact_type != "application/vnd.ant.react" else "jsx"
        rendered = f"<pre><code>{_highlight_code(content, lang)}</code></pre>"
    else:
        rendered = render_markdown(content)

    return (
        f'<div class="artifact">'
        f'<div class="artifact-header">'
        f'<span class="artifact-title">{title}</span>'
        f'<span class="artifact-type">{html.escape(type_label)}</span>'
        f"</div>"
        f'<div class="artifact-content">{rendered}</div>'
        f"</div>"
    )


def _render_tool_use(block: ToolUseContent) -> str:
    if block.is_artifact:
        return _render_artifact(block)

    name = html.escape(block.name)
    summary = html.escape(block.message or f"Used {block.name}")
    return f'<details class="tool-use"><summary>{summary}</summary><div class="tool-name">Tool: {name}</div></details>'


def _render_tool_result(block: ToolResultContent) -> str:
    # Skip artifact results (usually just "OK")
    if block.name == "artifacts":
        return ""

    content_text = ""
    if isinstance(block.content, str):
        content_text = block.content
    elif isinstance(block.content, list):
        parts = []
        for item in block.content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        content_text = "\n".join(parts)

    if not content_text or len(content_text.strip()) == 0:
        return ""

    # Truncate very long tool results
    display = content_text if len(content_text) <= 2000 else content_text[:2000] + "\n... (truncated)"

    name = html.escape(block.name or "tool")
    error_class = " tool-error" if block.is_error else ""
    return (
        f'<details class="tool-result{error_class}">'
        f"<summary>Result from {name}</summary>"
        f"<pre>{html.escape(display)}</pre>"
        f"</details>"
    )


def _render_attachment(att: Attachment) -> str:
    name = html.escape(att.file_name or "Untitled")
    file_type = html.escape(att.file_type) if att.file_type else "file"
    size_kb = att.file_size / 1024 if att.file_size else 0
    size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb / 1024:.1f} MB"

    parts = ['<div class="attachment">']
    parts.append(f'<span class="attachment-pill">{name} ({file_type}, {size_str})</span>')

    if att.extracted_content:
        if len(att.extracted_content) <= 3000:
            preview = att.extracted_content
        else:
            preview = att.extracted_content[:3000] + "\n..."
        parts.append(
            f'<details class="attachment-content">'
            f"<summary>View content</summary>"
            f"<pre>{html.escape(preview)}</pre>"
            f"</details>"
        )

    parts.append("</div>")
    return "".join(parts)


def _render_file(f: FileRef) -> str:
    name = html.escape(f.file_name or "Unknown file")
    return f'<span class="file-pill">{name}</span>'


def render_message(msg: ChatMessage) -> str:
    """Render a full chat message to HTML."""
    parts: list[str] = []

    # Render attachments first (they appear above the message)
    for att in msg.attachments:
        parts.append(_render_attachment(att))

    # Render file references
    if msg.files:
        file_html = " ".join(_render_file(f) for f in msg.files)
        parts.append(f'<div class="files">{file_html}</div>')

    # Render content blocks
    for block in msg.content:
        if isinstance(block, TextContent):
            parts.append(_render_text(block))
        elif isinstance(block, ThinkingContent):
            parts.append(_render_thinking(block))
        elif isinstance(block, ToolUseContent):
            parts.append(_render_tool_use(block))
        elif isinstance(block, ToolResultContent):
            parts.append(_render_tool_result(block))
        elif isinstance(block, TokenBudgetContent):
            pass  # Skip

    rendered = "\n".join(p for p in parts if p)

    sender = msg.sender
    return f'<div class="message message-{sender}">\n<div class="message-bubble">\n{rendered}\n</div>\n</div>'
