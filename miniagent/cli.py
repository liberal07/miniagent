from __future__ import annotations

import argparse
import sys

from .agent import Agent
from .client import LLMClient
from .config import ConfigError, load_config
from .conversation import ConversationManager
from .memory import SessionStore
from .replay import render_replay
from .tools import create_default_registry
from .trace import TraceLogger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="miniagent")
    subparsers = parser.add_subparsers(dest="command")
    replay = subparsers.add_parser("replay", help="Replay a local session and trace.")
    replay.add_argument("--session", default="default", help="Session id to replay.")
    parser.add_argument("--session", default="default", help="Session id to load.")
    parser.add_argument(
        "--provider",
        choices=["openai", "deepseek"],
        default=None,
        help="Provider preset to use.",
    )
    parser.add_argument("--model", default=None, help="LLM model name.")
    parser.add_argument("--base-url", default=None, help="OpenAI-compatible base URL.")
    parser.add_argument(
        "--wire-api",
        choices=["chat_completions", "responses"],
        default=None,
        help="LLM wire API to use.",
    )
    parser.add_argument("--max-steps", type=int, default=None, help="Max agent steps.")
    parser.add_argument(
        "--max-tool-result-chars",
        type=int,
        default=None,
        help="Inline character budget for a tool result.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "replay":
        data_dir = __import__("pathlib").Path.cwd() / ".miniagent"
        print(render_replay(data_dir, args.session))
        return

    try:
        config = load_config(args)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        sys.exit(1)

    session_store = SessionStore(config.data_dir)
    try:
        session_state = session_store.load(config.session_id)
    except ValueError as exc:
        print(f"Session error: {exc}", file=sys.stderr)
        sys.exit(1)

    conversation = ConversationManager.from_session_state(session_state)
    registry = create_default_registry()
    trace_logger = TraceLogger(config.data_dir)
    client = LLMClient(
        api_key=config.api_key,
        model=config.model,
        base_url=config.base_url,
        wire_api=config.wire_api,
    )
    agent = Agent(
        config=config,
        client=client,
        conversation=conversation,
        registry=registry,
        session_store=session_store,
        trace_logger=trace_logger,
        session_state=session_state,
    )

    print(f"MiniAgent session={config.session_id}. Type 'quit' or 'exit' to stop.")
    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit"}:
            break
        answer = agent.run_turn(user_input)
        print(answer)
