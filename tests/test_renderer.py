from claude_export_viewer.models import (
    Attachment,
    ChatMessage,
    FileRef,
    TextContent,
    ThinkingContent,
    ThinkingSummary,
    TokenBudgetContent,
    ToolResultContent,
    ToolUseContent,
)
from claude_export_viewer.renderer import render_markdown, render_message


def test_render_markdown_basic() -> None:
    result = render_markdown("Hello **world**")
    assert "<strong>world</strong>" in result
    assert "<p>" in result


def test_render_markdown_code_block() -> None:
    result = render_markdown("```python\nprint('hello')\n```")
    assert "<pre>" in result
    assert "<code" in result


def test_render_markdown_table() -> None:
    md = "| A | B |\n|---|---|\n| 1 | 2 |"
    result = render_markdown(md)
    assert "<table>" in result
    assert "<th" in result


def test_render_markdown_link() -> None:
    result = render_markdown("[click](https://example.com)")
    assert 'target="_blank"' in result
    assert 'rel="noopener"' in result


def test_render_message_human() -> None:
    msg = ChatMessage(
        uuid="m1",
        sender="human",
        content=[TextContent(text="Hello")],
    )
    result = render_message(msg)
    assert "message-human" in result
    assert "message-bubble" in result
    assert "Hello" in result


def test_render_message_assistant_text() -> None:
    msg = ChatMessage(
        uuid="m1",
        sender="assistant",
        content=[TextContent(text="**Bold response**")],
    )
    result = render_message(msg)
    assert "message-assistant" in result
    assert "<strong>Bold response</strong>" in result


def test_render_message_thinking() -> None:
    msg = ChatMessage(
        uuid="m1",
        sender="assistant",
        content=[
            ThinkingContent(
                thinking="Let me think about this...",
                summaries=[ThinkingSummary(summary="Considering the options")],
            ),
            TextContent(text="Here's my answer"),
        ],
    )
    result = render_message(msg)
    assert "<details" in result
    assert "thinking" in result
    assert "Considering the options" in result
    assert "Here&#x27;s my answer" in result or "Here's my answer" in result


def test_render_message_thinking_no_summary() -> None:
    msg = ChatMessage(
        uuid="m1",
        sender="assistant",
        content=[ThinkingContent(thinking="Thinking...", summaries=[])],
    )
    result = render_message(msg)
    assert "Thinking..." in result


def test_render_message_artifact_create() -> None:
    msg = ChatMessage(
        uuid="m1",
        sender="assistant",
        content=[
            ToolUseContent(
                name="artifacts",
                input={
                    "command": "create",
                    "id": "my-doc",
                    "type": "text/markdown",
                    "title": "My Document",
                    "content": "# Hello\n\nThis is a document.",
                },
            ),
        ],
    )
    result = render_message(msg)
    assert "artifact" in result
    assert "My Document" in result
    assert "Document" in result  # type label


def test_render_message_artifact_code() -> None:
    msg = ChatMessage(
        uuid="m1",
        sender="assistant",
        content=[
            ToolUseContent(
                name="artifacts",
                input={
                    "command": "create",
                    "id": "code-1",
                    "type": "application/vnd.ant.code",
                    "title": "My Script",
                    "language": "python",
                    "content": "print('hello')",
                },
            ),
        ],
    )
    result = render_message(msg)
    assert "artifact" in result
    assert "My Script" in result
    assert "Code" in result


def test_render_message_artifact_update_skipped() -> None:
    msg = ChatMessage(
        uuid="m1",
        sender="assistant",
        content=[
            ToolUseContent(
                name="artifacts",
                input={"command": "update", "id": "my-doc", "old_str": "foo", "new_str": "bar"},
            ),
        ],
    )
    result = render_message(msg)
    assert "artifact-header" not in result


def test_render_message_tool_use_non_artifact() -> None:
    msg = ChatMessage(
        uuid="m1",
        sender="assistant",
        content=[
            ToolUseContent(name="web_search", input={"query": "test"}, message="Searching the web"),
        ],
    )
    result = render_message(msg)
    assert "<details" in result
    assert "Searching the web" in result


def test_render_message_tool_result_artifact_skipped() -> None:
    msg = ChatMessage(
        uuid="m1",
        sender="assistant",
        content=[ToolResultContent(name="artifacts", content="OK")],
    )
    result = render_message(msg)
    assert "OK" not in result or "tool-result" not in result


def test_render_message_tool_result_with_content() -> None:
    msg = ChatMessage(
        uuid="m1",
        sender="assistant",
        content=[
            ToolResultContent(name="web_search", content="Search results here", is_error=False),
        ],
    )
    result = render_message(msg)
    assert "tool-result" in result
    assert "Search results here" in result


def test_render_message_tool_result_error() -> None:
    msg = ChatMessage(
        uuid="m1",
        sender="assistant",
        content=[
            ToolResultContent(name="web_fetch", content="403 Forbidden", is_error=True),
        ],
    )
    result = render_message(msg)
    assert "tool-error" in result


def test_render_message_tool_result_empty_skipped() -> None:
    msg = ChatMessage(
        uuid="m1",
        sender="assistant",
        content=[ToolResultContent(name="some_tool", content="")],
    )
    result = render_message(msg)
    assert "tool-result" not in result


def test_render_message_token_budget_skipped() -> None:
    msg = ChatMessage(
        uuid="m1",
        sender="assistant",
        content=[TokenBudgetContent(), TextContent(text="Response")],
    )
    result = render_message(msg)
    assert "token_budget" not in result
    assert "Response" in result


def test_render_message_attachment() -> None:
    msg = ChatMessage(
        uuid="m1",
        sender="human",
        content=[TextContent(text="See attached")],
        attachments=[
            Attachment(file_name="report.docx", file_size=34382, file_type="docx", extracted_content="Some text"),
        ],
    )
    result = render_message(msg)
    assert "attachment-pill" in result
    assert "report.docx" in result
    assert "docx" in result
    assert "33.6 KB" in result
    assert "View content" in result


def test_render_message_files() -> None:
    msg = ChatMessage(
        uuid="m1",
        sender="human",
        content=[TextContent(text="Check these files")],
        files=[FileRef(file_name="image.png"), FileRef(file_name="doc.pdf")],
    )
    result = render_message(msg)
    assert "file-pill" in result
    assert "image.png" in result
    assert "doc.pdf" in result
