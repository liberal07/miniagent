from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..models import SessionState


_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionStore:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.sessions_dir = self.data_dir / "sessions"

    def _validate_session_id(self, session_id: str) -> str:
        if not session_id:
            raise ValueError("session id cannot be empty")
        if not _SESSION_ID_RE.match(session_id):
            raise ValueError(
                "session id can only contain letters, numbers, '.', '_' and '-'"
            )
        return session_id

    def get_session_path(self, session_id: str) -> Path:
        session_id = self._validate_session_id(session_id)
        return self.sessions_dir / f"{session_id}.json"

    def create(self, session_id: str | None = None) -> SessionState:
        sid = session_id or uuid.uuid4().hex[:12]
        self._validate_session_id(sid)
        now = utc_now()
        return SessionState(session_id=sid, created_at=now, updated_at=now)

    def load(self, session_id: str) -> SessionState:
        path = self.get_session_path(session_id)
        if not path.exists():
            return self.create(session_id)
        data = json.loads(path.read_text(encoding="utf-8"))
        return SessionState.from_dict(data)

    def save(self, state: SessionState) -> None:
        path = self.get_session_path(state.session_id)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        state.updated_at = utc_now()
        if not state.created_at:
            state.created_at = state.updated_at
        path.write_text(
            json.dumps(state.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
