from __future__ import annotations

from contextlib import ExitStack
from importlib.resources import as_file, files
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import ExportData
from .renderer import render_message


def build_site(data: ExportData, output_dir: Path) -> None:
    """Generate the full static HTML site from export data."""
    package_root = files("claude_export_viewer")
    with ExitStack() as resources:
        template_dir = resources.enter_context(as_file(package_root / "templates"))
        style_css = resources.enter_context(as_file(package_root / "static" / "style.css"))
        env = Environment(
            loader=FileSystemLoader(Path(template_dir)),
            autoescape=select_autoescape(["html.j2"]),
        )

        output_dir.mkdir(parents=True, exist_ok=True)
        convo_dir = output_dir / "conversations"
        convo_dir.mkdir(exist_ok=True)

        shutil.copy(style_css, output_dir / "style.css")

        user_map: dict[str, str] = {u.uuid: u.full_name for u in data.users}
        all_projects = {p.uuid: p.name for p in data.projects}
        referenced = {c.project_uuid for c in data.conversations if c.project_uuid}
        project_map: dict[str, str] = {k: v for k, v in all_projects.items() if k in referenced}

        conversations = sorted(
            data.conversations,
            key=lambda c: c.created_at or c.updated_at or "",
            reverse=True,
        )

        index_template = env.get_template("index.html.j2")
        index_html = index_template.render(
            conversations=conversations,
            user_map=user_map,
            project_map=project_map,
        )
        (output_dir / "index.html").write_text(index_html, encoding="utf-8")

        convo_template = env.get_template("conversation.html.j2")
        for convo in conversations:
            rendered_messages = [render_message(msg) for msg in convo.chat_messages]
            convo_html = convo_template.render(
                conversation=convo,
                rendered_messages=rendered_messages,
            )
            (convo_dir / f"{convo.uuid}.html").write_text(convo_html, encoding="utf-8")
