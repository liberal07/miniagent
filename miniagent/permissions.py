from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    reason: str = ""


class PermissionChecker:
    """Small local policy gate before tool execution."""

    _allowed_tools = {"calculator", "search", "todo"}
    _allowed_todo_actions = {"create", "list", "get", "update"}

    def check(self, tool_name: str, arguments: dict[str, Any]) -> PermissionDecision:
        if tool_name not in self._allowed_tools:
            return PermissionDecision(False, f"tool is not allowed: {tool_name}")

        if tool_name == "todo":
            action = arguments.get("action")
            if action not in self._allowed_todo_actions:
                return PermissionDecision(
                    False,
                    "todo action must be one of create, list, get, update",
                )

        return PermissionDecision(True)
