from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .models import AgentConfig, WireAPI


class ConfigError(Exception):
    pass


PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "openai": {
        "model": "gpt-4.1-mini",
        "base_url": "https://api.openai.com/v1",
        "wire_api": "chat_completions",
    },
    "deepseek": {
        "model": "deepseek-v4-pro",
        "base_url": "https://api.deepseek.com",
        "wire_api": "chat_completions",
    },
}


def _int_value(value: Any, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Invalid max steps: {value!r}") from exc
    if parsed <= 0:
        raise ConfigError("max steps must be greater than 0")
    return parsed


def _wire_api_value(value: Any) -> WireAPI:
    wire_api = (value or "chat_completions").strip().lower().replace("-", "_")
    if wire_api in {"chat", "chat_completion", "chat_completions"}:
        return "chat_completions"
    if wire_api in {"response", "responses"}:
        return "responses"
    raise ConfigError(
        "MINIAGENT_WIRE_API must be 'chat_completions' or 'responses'"
    )


def _user_env(name: str) -> str:
    try:
        import subprocess

        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"[Environment]::GetEnvironmentVariable('{name}', 'User')",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return ""
    return completed.stdout.strip()


def load_config(args: Any) -> AgentConfig:
    provider = (
        getattr(args, "provider", None) or os.getenv("MINIAGENT_PROVIDER") or "deepseek"
    ).strip().lower()
    if provider not in PROVIDER_PRESETS:
        known = ", ".join(sorted(PROVIDER_PRESETS))
        raise ConfigError(f"Unknown provider {provider!r}. Known providers: {known}")
    preset = PROVIDER_PRESETS[provider]

    api_key = os.getenv("MINIAGENT_API_KEY", "").strip() or _user_env(
        "MINIAGENT_API_KEY"
    )
    if not api_key:
        raise ConfigError("MINIAGENT_API_KEY is required for real LLM API calls.")

    model = (
        getattr(args, "model", None)
        or os.getenv("MINIAGENT_MODEL")
        or preset["model"]
    )
    base_url = (
        getattr(args, "base_url", None)
        or os.getenv("MINIAGENT_BASE_URL")
        or preset["base_url"]
    )
    wire_api = _wire_api_value(
        getattr(args, "wire_api", None)
        or os.getenv("MINIAGENT_WIRE_API")
        or preset["wire_api"]
    )
    max_steps = _int_value(
        getattr(args, "max_steps", None) or os.getenv("MINIAGENT_MAX_STEPS"),
        default=6,
    )
    max_tool_result_chars = _int_value(
        getattr(args, "max_tool_result_chars", None)
        or os.getenv("MINIAGENT_MAX_TOOL_RESULT_CHARS"),
        default=4000,
    )
    session_id = getattr(args, "session", None) or "default"
    data_dir = Path.cwd() / ".miniagent"

    return AgentConfig(
        model=model,
        api_key=api_key,
        base_url=base_url,
        wire_api=wire_api,
        max_steps=max_steps,
        max_tool_result_chars=max_tool_result_chars,
        data_dir=data_dir,
        session_id=session_id,
    )
