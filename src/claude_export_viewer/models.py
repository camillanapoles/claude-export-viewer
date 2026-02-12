from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

# --- Users ---


class User(BaseModel):
    uuid: str
    full_name: str
    email_address: str
    verified_phone_number: str | None = None


# --- Projects ---


class ProjectDoc(BaseModel):
    uuid: str
    filename: str
    content: str = ""


class Project(BaseModel):
    uuid: str
    name: str
    description: str = ""
    is_private: bool = False
    is_starter_project: bool = False
    prompt_template: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    creator: dict[str, Any] | None = None
    docs: list[ProjectDoc] = []


# --- Memories ---


class Memories(BaseModel):
    project_memories: dict[str, str] = {}
    account_uuid: str = ""


# --- Content Blocks ---


class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str = ""
    citations: list[dict[str, Any]] = []


class ThinkingSummary(BaseModel):
    summary: str = ""


class ThinkingContent(BaseModel):
    type: Literal["thinking"] = "thinking"
    thinking: str = ""
    summaries: list[ThinkingSummary] = []
    cut_off: bool = False
    alternative_display_type: str | None = None


class ArtifactInput(BaseModel):
    command: str = "create"
    id: str = ""
    type: str | None = None
    title: str | None = None
    language: str | None = None
    content: str | None = None
    old_str: str | None = None
    new_str: str | None = None
    version_uuid: str | None = None


class ToolUseContent(BaseModel):
    type: Literal["tool_use"] = "tool_use"
    id: str | None = None
    name: str = ""
    input: dict[str, Any] | ArtifactInput = Field(default_factory=dict)
    message: str | None = None
    integration_name: str | None = None
    display_content: str | dict[str, Any] | None = None

    @property
    def is_artifact(self) -> bool:
        return self.name == "artifacts"

    @property
    def artifact_input(self) -> ArtifactInput | None:
        if not self.is_artifact:
            return None
        if isinstance(self.input, ArtifactInput):
            return self.input
        return ArtifactInput.model_validate(self.input)


class ToolResultContent(BaseModel):
    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str | None = None
    name: str = ""
    content: Any = None
    is_error: bool = False
    structured_content: dict[str, Any] | None = None
    message: str | None = None
    integration_name: str | None = None
    display_content: str | dict[str, Any] | None = None


class TokenBudgetContent(BaseModel):
    type: Literal["token_budget"] = "token_budget"


ContentBlock = Annotated[
    TextContent | ThinkingContent | ToolUseContent | ToolResultContent | TokenBudgetContent,
    Field(discriminator="type"),
]


# --- Attachments & Files ---


class Attachment(BaseModel):
    file_name: str = ""
    file_size: int = 0
    file_type: str = ""
    extracted_content: str = ""


class FileRef(BaseModel):
    file_name: str = ""


# --- Messages & Conversations ---


class ChatMessage(BaseModel):
    uuid: str
    text: str = ""
    content: list[ContentBlock] = []
    sender: Literal["human", "assistant"]
    created_at: datetime | None = None
    updated_at: datetime | None = None
    attachments: list[Attachment] = []
    files: list[FileRef] = []


class AccountRef(BaseModel):
    uuid: str


class Conversation(BaseModel):
    uuid: str
    name: str = ""
    summary: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    account: AccountRef | None = None
    project_uuid: str | None = None
    chat_messages: list[ChatMessage] = []


# --- Top-level export ---


class ExportData(BaseModel):
    users: list[User] = []
    projects: list[Project] = []
    memories: list[Memories] = []
    conversations: list[Conversation] = []
