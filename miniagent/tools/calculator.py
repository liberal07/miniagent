from __future__ import annotations

import ast
import operator
from typing import Any

from pydantic import BaseModel, Field

from ..models import SessionState, ToolResult
from .base import Tool


class CalculatorParams(BaseModel):
    expression: str = Field(..., description="Basic math expression to evaluate.")


class CalculatorTool(Tool):
    name = "calculator"
    description = "Safely evaluate a basic math expression."
    params_model = CalculatorParams

    _binary_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    _unary_ops = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    def _run(self, params: BaseModel, state: SessionState) -> ToolResult:
        expression = params.expression.strip()  # type: ignore[attr-defined]
        if not expression:
            return ToolResult("expression cannot be empty", is_error=True)
        try:
            tree = ast.parse(expression, mode="eval")
            value = self._eval_node(tree.body)
        except Exception as exc:  # noqa: BLE001
            return ToolResult(
                output=f"Invalid math expression: {exc}",
                is_error=True,
                error=str(exc),
            )
        return ToolResult(output=str(value))

    def _eval_node(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self._binary_ops:
                raise ValueError(f"operator {op_type.__name__} is not allowed")
            return self._binary_ops[op_type](
                self._eval_node(node.left),
                self._eval_node(node.right),
            )
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in self._unary_ops:
                raise ValueError(f"operator {op_type.__name__} is not allowed")
            return self._unary_ops[op_type](self._eval_node(node.operand))
        raise ValueError(f"node {type(node).__name__} is not allowed")
