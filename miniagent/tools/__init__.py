from __future__ import annotations

from .base import Tool
from .calculator import CalculatorTool
from .search import SearchTool
from .todo import TodoTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def get_all_schemas(self) -> list[dict[str, object]]:
        schemas: list[dict[str, object]] = []
        for tool in self._tools.values():
            spec = tool.get_schema()
            schemas.append(
                {
                    "name": spec.name,
                    "description": spec.description,
                    "parameters": spec.parameters,
                }
            )
        return schemas


def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(SearchTool())
    registry.register(TodoTool())
    return registry


__all__ = ["ToolRegistry", "create_default_registry"]
