from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field

from ..models import SessionState, TodoItem, TodoStatus, ToolResult
from .base import Tool


class TodoParams(BaseModel):
    action: Literal["create", "list", "get", "update"] = Field(
        ..., description="Todo operation to run."
    )
    title: str | None = Field(None, description="Task title for create.")
    task_id: str | None = Field(None, description="Task id for get or update.")
    status: TodoStatus | None = Field(None, description="New task status.")
    notes: str | None = Field(None, description="Optional task notes.")


class TodoTool(Tool):
    name = "todo"
    description = "Create, list, get, and update todo tasks in the current session."
    params_model = TodoParams

    def _run(self, params: BaseModel, state: SessionState) -> ToolResult:
        p = params
        if p.action == "create":  # type: ignore[attr-defined]
            return self._create(p, state)  # type: ignore[arg-type]
        if p.action == "list":  # type: ignore[attr-defined]
            return self._list(state)
        if p.action == "get":  # type: ignore[attr-defined]
            return self._get(p, state)  # type: ignore[arg-type]
        if p.action == "update":  # type: ignore[attr-defined]
            return self._update(p, state)  # type: ignore[arg-type]
        return ToolResult("unsupported todo action", is_error=True)

    def _create(self, params: TodoParams, state: SessionState) -> ToolResult:
        if not params.title:
            return ToolResult("title is required for create", True, "missing title")
        item = TodoItem(
            id=uuid.uuid4().hex[:8],
            title=params.title,
            status=params.status or "todo",
            notes=params.notes or "",
        )
        state.todos.append(item)
        return ToolResult(
            output=(
                f"Created task id={item.id}, title={item.title}, "
                f"status={item.status}"
            )
        )

    def _list(self, state: SessionState) -> ToolResult:
        if not state.todos:
            return ToolResult("No tasks in this session.")
        return ToolResult(output="\n".join(self._format_item(t) for t in state.todos))

    def _get(self, params: TodoParams, state: SessionState) -> ToolResult:
        item = self._find(params.task_id, state)
        if item is None:
            return ToolResult("task not found", True, "task not found")
        return ToolResult(output=self._format_item(item))

    def _update(self, params: TodoParams, state: SessionState) -> ToolResult:
        item = self._find(params.task_id, state)
        if item is None:
            return ToolResult("task not found", True, "task not found")
        if params.status is None and params.notes is None and params.title is None:
            return ToolResult(
                "status, notes, or title is required for update",
                True,
                "missing update field",
            )
        if params.status is not None:
            item.status = params.status
        if params.notes is not None:
            item.notes = params.notes
        if params.title is not None:
            item.title = params.title
        return ToolResult(output=f"Updated task: {self._format_item(item)}")

    def _find(self, task_id: str | None, state: SessionState) -> TodoItem | None:
        if not task_id:
            return None
        for item in state.todos:
            if item.id == task_id:
                return item
        return None

    def _format_item(self, item: TodoItem) -> str:
        notes = f", notes={item.notes}" if item.notes else ""
        return f"id={item.id}, title={item.title}, status={item.status}{notes}"
