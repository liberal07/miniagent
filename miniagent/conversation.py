from __future__ import annotations

import json
from typing import Any

from .models import AgentAction, Message, SessionState


class ConversationManager:
    def __init__(self, messages: list[Message] | None = None) -> None:
        self.messages = list(messages or [])

    @classmethod
    def from_session_state(cls, state: SessionState) -> "ConversationManager":
        return cls(state.messages)

    def to_session_messages(self) -> list[Message]:
        return list(self.messages)

    def add_user(self, content: str) -> None:
        self.messages.append(Message(role="user", content=content))

    def add_assistant(
        self,
        content: str,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> None:
        self.messages.append(
            Message(role="assistant", content=content, tool_calls=tool_calls or [])
        )

    def add_assistant_tool_call(self, action: AgentAction) -> None:
        tool_call_id = action.tool_call_id or "tool_call"
        tool_name = action.tool_name or ""
        self.add_assistant(
            content="",
            tool_calls=[
                {
                    "id": tool_call_id,
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": json.dumps(
                            action.arguments, ensure_ascii=False
                        ),
                    },
                }
            ],
        )

    def add_tool_result(
        self, tool_call_id: str, tool_name: str, content: str
    ) -> None:
        self.messages.append(
            Message(
                role="tool",
                content=content,
                tool_call_id=tool_call_id,
                tool_name=tool_name,
            )
        )

    def to_llm_messages(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for message in self.messages:
            if message.role == "tool":
                out.append(
                    {
                        "role": "tool",
                        "tool_call_id": message.tool_call_id,
                        "name": message.tool_name,
                        "content": message.content,
                    }
                )
                continue

            item: dict[str, Any] = {
                "role": message.role,
                "content": message.content,
            }
            if message.tool_calls:
                item["tool_calls"] = message.tool_calls
            out.append(item)
        return out
