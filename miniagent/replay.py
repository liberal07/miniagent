from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .memory import SessionStore


def _short(text: str, limit: int = 500) -> str:
    text = text.replace("\r\n", "\n")
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + f"\n... ({len(text) - limit} more chars)"


def _format_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def render_replay(data_dir: Path, session_id: str) -> str:
    store = SessionStore(data_dir)
    session_path = store.get_session_path(session_id)
    trace_path = data_dir / "traces" / f"{session_id}.jsonl"
    display_session_path = Path(".miniagent") / "sessions" / f"{session_id}.json"
    display_trace_path = Path(".miniagent") / "traces" / f"{session_id}.jsonl"

    lines: list[str] = [
        f"MiniAgent replay: session={session_id}",
        f"Session file: {display_session_path}",
        f"Trace file: {display_trace_path}",
        "",
    ]

    if not session_path.exists():
        lines.append("Session file not found.")
        return "\n".join(lines)

    state = store.load(session_id)
    lines.append("Messages")
    lines.append("--------")
    if not state.messages:
        lines.append("(no messages)")
    for idx, message in enumerate(state.messages, start=1):
        lines.append(f"[{idx}] role={message.role}")
        if message.tool_calls:
            lines.append("tool_calls:")
            lines.append(_short(_format_json(message.tool_calls), 1200))
        if message.tool_call_id:
            lines.append(f"tool_call_id={message.tool_call_id} name={message.tool_name}")
        if message.content:
            lines.append(_short(message.content))
        lines.append("")

    lines.append("Todos")
    lines.append("-----")
    if not state.todos:
        lines.append("(no todos)")
    for item in state.todos:
        notes = f" notes={item.notes}" if item.notes else ""
        lines.append(f"- id={item.id} status={item.status} title={item.title}{notes}")
    lines.append("")

    lines.append("Tool Trace")
    lines.append("----------")
    if not trace_path.exists():
        lines.append("Trace file not found. This is OK if no tool was called.")
        return "\n".join(lines)

    trace_count = 0
    with trace_path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError as exc:
                lines.append(f"[line {line_no}] invalid JSON: {exc}")
                continue
            trace_count += 1
            lines.append(
                f"Step {item.get('step')} tool={item.get('tool_name')} "
                f"success={item.get('success')} id={item.get('tool_call_id')}"
            )
            lines.append("arguments:")
            lines.append(_short(_format_json(item.get("arguments", {})), 1000))
            if item.get("error"):
                lines.append(f"error: {item.get('error')}")
            lines.append("result:")
            lines.append(_short(str(item.get("result", ""))))
            lines.append("")

    if trace_count == 0:
        lines.append("(no trace records)")

    return "\n".join(lines)
