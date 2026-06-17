from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .models import ToolResult


_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9_.-]+")


@dataclass(frozen=True)
class ToolResultBudget:
    data_dir: Path
    max_chars: int

    def apply(
        self,
        result: ToolResult,
        *,
        session_id: str,
        tool_call_id: str,
        tool_name: str,
    ) -> ToolResult:
        if self.max_chars <= 0 or len(result.output) <= self.max_chars:
            return result

        safe_id = _SAFE_NAME_RE.sub("_", tool_call_id or "tool-result")
        safe_tool = _SAFE_NAME_RE.sub("_", tool_name or "tool")
        out_dir = self.data_dir / "tool-results" / session_id
        out_dir.mkdir(parents=True, exist_ok=True)
        full_path = out_dir / f"{safe_id}-{safe_tool}.txt"
        full_path.write_text(result.output, encoding="utf-8")

        preview_len = max(120, min(self.max_chars, 800))
        preview = result.output[:preview_len].rstrip()
        compact = (
            "Tool result exceeded the inline budget.\n"
            f"Full result saved to: {full_path}\n"
            f"Original characters: {len(result.output)}\n"
            f"Preview:\n{preview}"
        )
        return ToolResult(output=compact, is_error=result.is_error, error=result.error)
