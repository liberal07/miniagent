from __future__ import annotations

import json
from pathlib import Path

from .models import TraceRecord


class TraceLogger:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.traces_dir = self.data_dir / "traces"

    def get_trace_path(self, session_id: str) -> Path:
        return self.traces_dir / f"{session_id}.jsonl"

    def record(self, record: TraceRecord) -> None:
        self.traces_dir.mkdir(parents=True, exist_ok=True)
        path = self.get_trace_path(record.session_id)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
