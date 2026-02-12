from pathlib import Path

from claude_export_viewer.html_builder import build_site
from claude_export_viewer.models import (
    ChatMessage,
    Conversation,
    ExportData,
    TextContent,
    User,
)


def test_build_site_creates_output(tmp_path: Path) -> None:
    data = ExportData(
        users=[User(uuid="u1", full_name="Test", email_address="t@t.com")],
        conversations=[
            Conversation(
                uuid="conv-1",
                name="Test Conversation",
                created_at="2026-01-01T00:00:00Z",
                chat_messages=[
                    ChatMessage(
                        uuid="m1",
                        sender="human",
                        content=[TextContent(text="Hello")],
                    ),
                    ChatMessage(
                        uuid="m2",
                        sender="assistant",
                        content=[TextContent(text="Hi there!")],
                    ),
                ],
            ),
        ],
    )

    output_dir = tmp_path / "output"
    build_site(data, output_dir)

    assert (output_dir / "index.html").exists()
    assert (output_dir / "style.css").exists()
    assert (output_dir / "conversations" / "conv-1.html").exists()


def test_build_site_index_content(tmp_path: Path) -> None:
    data = ExportData(
        conversations=[
            Conversation(
                uuid="c1",
                name="First Chat",
                created_at="2026-01-15T00:00:00Z",
                chat_messages=[
                    ChatMessage(uuid="m1", sender="human", content=[TextContent(text="Hi")]),
                ],
            ),
            Conversation(
                uuid="c2",
                name="Second Chat",
                created_at="2026-01-10T00:00:00Z",
                chat_messages=[],
            ),
        ],
    )

    output_dir = tmp_path / "output"
    build_site(data, output_dir)

    index_html = (output_dir / "index.html").read_text()
    assert "First Chat" in index_html
    assert "Second Chat" in index_html
    assert "2 conversations" in index_html
    # First Chat should appear before Second Chat (newer first)
    assert index_html.index("First Chat") < index_html.index("Second Chat")


def test_build_site_conversation_content(tmp_path: Path) -> None:
    data = ExportData(
        conversations=[
            Conversation(
                uuid="c1",
                name="My Chat",
                created_at="2026-01-15T12:00:00Z",
                chat_messages=[
                    ChatMessage(uuid="m1", sender="human", content=[TextContent(text="What is 2+2?")]),
                    ChatMessage(uuid="m2", sender="assistant", content=[TextContent(text="The answer is **4**.")]),
                ],
            ),
        ],
    )

    output_dir = tmp_path / "output"
    build_site(data, output_dir)

    convo_html = (output_dir / "conversations" / "c1.html").read_text()
    assert "My Chat" in convo_html
    assert "message-human" in convo_html
    assert "message-assistant" in convo_html
    assert "What is 2+2?" in convo_html
    assert "<strong>4</strong>" in convo_html
    assert "../style.css" in convo_html
    assert "../index.html" in convo_html


def test_build_site_empty_conversations(tmp_path: Path) -> None:
    data = ExportData(conversations=[])
    output_dir = tmp_path / "output"
    build_site(data, output_dir)

    assert (output_dir / "index.html").exists()
    index_html = (output_dir / "index.html").read_text()
    assert "0 conversations" in index_html
