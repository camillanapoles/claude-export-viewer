from __future__ import annotations

import json
import zipfile
from pathlib import Path

from .models import Conversation, ExportData, Memories, Project, User


def load_export(zip_path: Path) -> ExportData:
    """Load a Claude export ZIP file and return parsed data."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        data: dict[str, list[dict]] = {}
        for target in ("users.json", "projects.json", "memories.json", "conversations.json"):
            matches = [n for n in names if n.endswith(target)]
            if matches:
                with zf.open(matches[0]) as f:
                    data[target] = json.load(f)
            else:
                data[target] = []

    return ExportData(
        users=[User.model_validate(u) for u in data["users.json"]],
        projects=[Project.model_validate(p) for p in data["projects.json"]],
        memories=[Memories.model_validate(m) for m in data["memories.json"]],
        conversations=[Conversation.model_validate(c) for c in data["conversations.json"]],
    )
