from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ValidationError

from ..models import SessionState, ToolResult, ToolSpec


class Tool(ABC):
    name: str
    description: str
    params_model: type[BaseModel]

    def get_schema(self) -> ToolSpec:
        schema = self.params_model.model_json_schema()
        schema.pop("title", None)
        return ToolSpec(
            name=self.name,
            description=self.description,
            parameters=schema,
        )

    def execute(self, arguments: dict[str, Any], state: SessionState) -> ToolResult:
        try:
            params = self.params_model.model_validate(arguments)
        except ValidationError as exc:
            return ToolResult(
                output=f"Invalid arguments for {self.name}: {exc}",
                is_error=True,
                error=str(exc),
            )
        try:
            return self._run(params, state)
        except Exception as exc:  # noqa: BLE001
            return ToolResult(
                output=f"Tool {self.name} failed: {exc}",
                is_error=True,
                error=str(exc),
            )

    @abstractmethod
    def _run(self, params: BaseModel, state: SessionState) -> ToolResult:
        raise NotImplementedError
