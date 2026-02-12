from __future__ import annotations

import shutil
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from .models import ExportData
from .renderer import render_message

_PACKAGE_DIR = Path(__file__).parent


def build_site(data: ExportData, output_dir: Path) -> None:
    """Generate the full static HTML site from export data."""
    env = Environment(
        loader=PackageLoader("claude_export_viewer", "templates"),
        autoescape=select_autoescape(["html.j2"]),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    convo_dir = output_dir / "conversations"
    convo_dir.mkdir(exist_ok=True)

    # Copy static assets
    shutil.copy(_PACKAGE_DIR / "static" / "style.css", output_dir / "style.css")

    # Sort conversations by date (newest first)
    conversations = sorted(
        data.conversations,
        key=lambda c: c.created_at or c.updated_at or "",
        reverse=True,
    )

    # Render index
    index_template = env.get_template("index.html.j2")
    index_html = index_template.render(conversations=conversations)
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")

    # Render each conversation
    convo_template = env.get_template("conversation.html.j2")
    for convo in conversations:
        rendered_messages = [render_message(msg) for msg in convo.chat_messages]
        convo_html = convo_template.render(
            conversation=convo,
            rendered_messages=rendered_messages,
        )
        (convo_dir / f"{convo.uuid}.html").write_text(convo_html, encoding="utf-8")
