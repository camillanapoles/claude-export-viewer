import json
import zipfile
from pathlib import Path

import pytest

from claude_export_viewer.loader import load_export


@pytest.fixture()
def sample_zip(tmp_path: Path) -> Path:
    """Create a minimal valid export ZIP for testing."""
    users = [{"uuid": "u1", "full_name": "Test User", "email_address": "test@test.com"}]
    projects = [
        {
            "uuid": "p1",
            "name": "Test Project",
            "description": "",
            "is_private": False,
            "is_starter_project": False,
            "prompt_template": "",
            "docs": [],
        }
    ]
    memories = [{"project_memories": {}, "account_uuid": "u1"}]
    conversations = [
        {
            "uuid": "c1",
            "name": "Test Conversation",
            "summary": "",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "account": {"uuid": "u1"},
            "chat_messages": [
                {
                    "uuid": "m1",
                    "text": "Hello",
                    "content": [{"type": "text", "text": "Hello"}],
                    "sender": "human",
                    "attachments": [],
                    "files": [],
                },
                {
                    "uuid": "m2",
                    "text": "Hi there!",
                    "content": [
                        {"type": "thinking", "thinking": "Let me respond", "summaries": []},
                        {"type": "text", "text": "Hi there!"},
                    ],
                    "sender": "assistant",
                    "attachments": [],
                    "files": [],
                },
            ],
        }
    ]

    zip_path = tmp_path / "export.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("users.json", json.dumps(users))
        zf.writestr("projects.json", json.dumps(projects))
        zf.writestr("memories.json", json.dumps(memories))
        zf.writestr("conversations.json", json.dumps(conversations))

    return zip_path


def test_load_export(sample_zip: Path) -> None:
    data = load_export(sample_zip)
    assert len(data.users) == 1
    assert data.users[0].full_name == "Test User"
    assert len(data.projects) == 1
    assert len(data.memories) == 1
    assert len(data.conversations) == 1
    assert data.conversations[0].name == "Test Conversation"
    assert len(data.conversations[0].chat_messages) == 2


def test_load_export_nested_paths(tmp_path: Path) -> None:
    """Test loading when JSON files are in a subdirectory inside the ZIP."""
    zip_path = tmp_path / "export.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("data/users.json", json.dumps([]))
        zf.writestr("data/projects.json", json.dumps([]))
        zf.writestr("data/memories.json", json.dumps([]))
        zf.writestr("data/conversations.json", json.dumps([]))

    data = load_export(zip_path)
    assert len(data.conversations) == 0


def test_load_export_missing_files(tmp_path: Path) -> None:
    """Test loading when some JSON files are missing."""
    zip_path = tmp_path / "export.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("conversations.json", json.dumps([]))

    data = load_export(zip_path)
    assert len(data.users) == 0
    assert len(data.conversations) == 0
