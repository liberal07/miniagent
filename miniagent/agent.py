from __future__ import annotations

from datetime import datetime, timezone

from .client import LLMClient, LLMClientError
from .config import AgentConfig
from .conversation import ConversationManager
from .memory.session import SessionStore
from .models import AgentAction, SessionState, ToolResult, TraceRecord
from .permissions import PermissionChecker
from .prompts import build_system_prompt
from .result_budget import ToolResultBudget
from .tools import ToolRegistry
from .trace import TraceLogger


class Agent:
    def __init__(
        self,
        config: AgentConfig,
        client: LLMClient,
        conversation: ConversationManager,
        registry: ToolRegistry,
        session_store: SessionStore,
        trace_logger: TraceLogger,
        session_state: SessionState,
    ) -> None:
        self.config = config
        self.client = client
        self.conversation = conversation
        self.registry = registry
        self.session_store = session_store
        self.trace_logger = trace_logger
        self.session_state = session_state
        self.permission_checker = PermissionChecker()
        self.result_budget = ToolResultBudget(
            data_dir=config.data_dir,
            max_chars=config.max_tool_result_chars,
        )

    def run_turn(self, user_input: str) -> str:
        self.conversation.add_user(user_input)
        self._sync_and_save()

        for step in range(1, self.config.max_steps + 1):
            try:
                action = self.client.next_action(
                    system_prompt=build_system_prompt(self.session_state),
                    messages=self.conversation.to_llm_messages(),
                    tools=self.registry.get_all_schemas(),
                )
            except LLMClientError as exc:
                answer = f"LLM call failed: {exc}"
                self.conversation.add_assistant(answer)
                self._sync_and_save()
                return answer

            if action.type == "final":
                answer = action.content.strip() or "(empty response)"
                self.conversation.add_assistant(answer)
                self._sync_and_save()
                return answer

            if action.type == "tool_call":
                self.conversation.add_assistant_tool_call(action)
                result = self._execute_tool(action, step)
                self.conversation.add_tool_result(
                    action.tool_call_id or f"tool-{step}",
                    action.tool_name or "unknown",
                    result.output,
                )
                self._sync_and_save()
                continue

            answer = f"Unsupported action type: {action.type}"
            self.conversation.add_assistant(answer)
            self._sync_and_save()
            return answer

        answer = (
            f"Stopped after reaching max_steps={self.config.max_steps}. "
            "The task may need a simpler prompt or manual follow-up."
        )
        self.conversation.add_assistant(answer)
        self._sync_and_save()
        return answer

    def _execute_tool(self, action: AgentAction, step: int) -> ToolResult:
        tool_name = action.tool_name or ""
        tool_call_id = action.tool_call_id or f"tool-{step}"
        tool = self.registry.get(tool_name)
        if tool is None:
            result = ToolResult(
                output=f"Tool not found: {tool_name}",
                is_error=True,
                error="tool not found",
            )
        else:
            decision = self.permission_checker.check(tool_name, action.arguments)
            if not decision.allowed:
                result = ToolResult(
                    output=f"Permission denied for {tool_name}: {decision.reason}",
                    is_error=True,
                    error=decision.reason,
                )
            else:
                result = tool.execute(action.arguments, self.session_state)

        result = self.result_budget.apply(
            result,
            session_id=self.session_state.session_id,
            tool_call_id=tool_call_id,
            tool_name=tool_name or "unknown",
        )

        self.trace_logger.record(
            TraceRecord(
                session_id=self.session_state.session_id,
                step=step,
                tool_call_id=tool_call_id,
                tool_name=tool_name or "unknown",
                arguments=action.arguments,
                result=result.output,
                success=not result.is_error,
                error=result.error,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
        )
        return result

    def _sync_and_save(self) -> None:
        self.session_state.messages = self.conversation.to_session_messages()
        self.session_store.save(self.session_state)
