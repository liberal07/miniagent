from __future__ import annotations

from .models import SessionState


def _todo_summary(state: SessionState) -> str:
    if not state.todos:
        return "No todo tasks in this session."
    lines = []
    for item in state.todos:
        notes = f" notes={item.notes}" if item.notes else ""
        lines.append(f"- id={item.id} status={item.status} title={item.title}{notes}")
    return "\n".join(lines)


def build_system_prompt(session_state: SessionState) -> str:
    return f"""You are MiniAgent, a minimal tool-using assistant.

Rules:
- Answer directly when no tool is needed.
- Use tools when calculation, mock search, or todo state management is needed.
- Tool calls must use the provided structured tool schema.
- After a tool result is returned, continue reasoning from that result and provide a final answer.
- Keep answers concise and clear.

Current session state:
session_id={session_state.session_id}
todos:
{_todo_summary(session_state)}

Memory placement:
- The current session state above is recalled before each LLM call.
- It is placed in this system prompt so cross-turn todo state can be used.
"""
