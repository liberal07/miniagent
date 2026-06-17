from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from .models import AgentAction, WireAPI


class LLMClientError(Exception):
    pass


class LLMClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        wire_api: WireAPI = "chat_completions",
    ) -> None:
        self.model = model
        self.wire_api = wire_api
        kwargs: dict[str, Any] = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)

    def next_action(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, object]],
    ) -> AgentAction:
        if self.wire_api == "responses":
            return self._next_action_responses(system_prompt, messages, tools)
        return self._next_action_chat_completions(system_prompt, messages, tools)

    def _next_action_chat_completions(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, object]],
    ) -> AgentAction:
        llm_messages = [{"role": "system", "content": system_prompt}, *messages]
        api_tools = [self._to_openai_tool_schema(t) for t in tools]
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=llm_messages,
                tools=api_tools,
                tool_choice="auto",
            )
        except Exception as exc:  # noqa: BLE001
            raise LLMClientError(f"LLM API call failed: {exc}") from exc

        message = response.choices[0].message
        tool_calls = message.tool_calls or []
        if tool_calls:
            call = tool_calls[0]
            raw_args = call.function.arguments or "{}"
            try:
                arguments = json.loads(raw_args)
            except json.JSONDecodeError as exc:
                raise LLMClientError(
                    f"LLM returned invalid tool arguments JSON: {raw_args}"
                ) from exc
            return AgentAction(
                type="tool_call",
                tool_call_id=call.id,
                tool_name=call.function.name,
                arguments=arguments,
            )

        return AgentAction(type="final", content=message.content or "")

    def _to_openai_tool_schema(self, spec: dict[str, object]) -> dict[str, object]:
        return {
            "type": "function",
            "function": {
                "name": spec["name"],
                "description": spec["description"],
                "parameters": spec["parameters"],
            },
        }

    def _next_action_responses(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, object]],
    ) -> AgentAction:
        api_tools = [self._to_responses_tool_schema(t) for t in tools]
        response_input = self._to_responses_input(system_prompt, messages)
        try:
            response = self.client.responses.create(
                model=self.model,
                input=response_input,
                tools=api_tools,
                tool_choice="auto",
            )
        except Exception as exc:  # noqa: BLE001
            raise LLMClientError(f"LLM API call failed: {exc}") from exc

        action = self._parse_responses_tool_call(response)
        if action is not None:
            return action
        return AgentAction(type="final", content=self._extract_responses_text(response))

    def _to_responses_tool_schema(self, spec: dict[str, object]) -> dict[str, object]:
        return {
            "type": "function",
            "name": spec["name"],
            "description": spec["description"],
            "parameters": spec["parameters"],
        }

    def _to_responses_input(
        self, system_prompt: str, messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        response_input: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            }
        ]
        for message in messages:
            role = str(message.get("role", "user"))
            content = str(message.get("content") or "")
            if role == "assistant" and message.get("tool_calls"):
                for call in message.get("tool_calls") or []:
                    function = call.get("function", {})
                    response_input.append(
                        {
                            "type": "function_call",
                            "call_id": call.get("id") or "",
                            "name": function.get("name") or "",
                            "arguments": function.get("arguments") or "{}",
                        }
                    )
                continue
            if role == "tool":
                response_input.append(
                    {
                        "type": "function_call_output",
                        "call_id": message.get("tool_call_id") or "",
                        "output": content,
                    }
                )
                continue
            if role not in {"user", "assistant", "system", "developer"}:
                role = "user"
            response_input.append(
                {
                    "role": role,
                    "content": [{"type": "input_text", "text": content}],
                }
            )
        return response_input

    def _parse_responses_tool_call(self, response: Any) -> AgentAction | None:
        for item in getattr(response, "output", []) or []:
            item_type = getattr(item, "type", None)
            if item_type != "function_call":
                continue
            raw_args = getattr(item, "arguments", None) or "{}"
            try:
                arguments = json.loads(raw_args)
            except json.JSONDecodeError as exc:
                raise LLMClientError(
                    f"LLM returned invalid tool arguments JSON: {raw_args}"
                ) from exc
            return AgentAction(
                type="tool_call",
                tool_call_id=getattr(item, "call_id", None)
                or getattr(item, "id", None),
                tool_name=getattr(item, "name", None),
                arguments=arguments,
            )
        return None

    def _extract_responses_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if output_text:
            return str(output_text)

        chunks: list[str] = []
        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text = getattr(content, "text", None)
                if text:
                    chunks.append(str(text))
        return "\n".join(chunks)
