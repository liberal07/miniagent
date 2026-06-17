from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


ActionType = Literal["final", "tool_call"]
MessageRole = Literal["system", "user", "assistant", "tool"]
TodoStatus = Literal["todo", "doing", "done"]
WireAPI = Literal["chat_completions", "responses"]


@dataclass
class AgentConfig:
    model: str
    api_key: str
    base_url: str | None
    wire_api: WireAPI
    max_steps: int
    max_tool_result_chars: int
    data_dir: Path
    session_id: str


@dataclass
class Message:
    role: MessageRole
    content: str = ""
    tool_call_id: str | None = None
    tool_name: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "role": self.role,
            "content": self.content,
        }
        if self.tool_call_id is not None:
            data["tool_call_id"] = self.tool_call_id
        if self.tool_name is not None:
            data["tool_name"] = self.tool_name
        if self.tool_calls:
            data["tool_calls"] = self.tool_calls
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        return cls(
            role=data["role"],
            content=data.get("content") or "",
            tool_call_id=data.get("tool_call_id"),
            tool_name=data.get("tool_name"),
            tool_calls=list(data.get("tool_calls") or []),
        )


@dataclass
class AgentAction:
    type: ActionType
    content: str = ""
    tool_call_id: str | None = None
    tool_name: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass
class ToolResult:
    output: str
    is_error: bool = False
    error: str | None = None


@dataclass
class TraceRecord:
    session_id: str
    step: int
    tool_call_id: str
    tool_name: str
    arguments: dict[str, Any]
    result: str
    success: bool
    error: str | None
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "step": self.step,
            "tool_call_id": self.tool_call_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": self.result,
            "success": self.success,
            "error": self.error,
            "created_at": self.created_at,
        }


@dataclass
class TodoItem:
    id: str
    title: str
    status: TodoStatus = "todo"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TodoItem":
        return cls(
            id=str(data["id"]),
            title=str(data["title"]),
            status=data.get("status", "todo"),
            notes=data.get("notes", ""),
        )


@dataclass
class SessionState:
    session_id: str
    messages: list[Message] = field(default_factory=list)
    todos: list[TodoItem] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "messages": [m.to_dict() for m in self.messages],
            "todos": [t.to_dict() for t in self.todos],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionState":
        return cls(
            session_id=str(data["session_id"]),
            messages=[Message.from_dict(m) for m in data.get("messages", [])],
            todos=[TodoItem.from_dict(t) for t in data.get("todos", [])],
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )
