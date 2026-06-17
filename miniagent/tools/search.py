from __future__ import annotations

from pydantic import BaseModel, Field

from ..models import SessionState, ToolResult
from .base import Tool


class SearchParams(BaseModel):
    query: str = Field(..., description="Search query for the local mock index.")


MOCK_DOCS = [
    {
        "title": "Mini Agent",
        "keywords": ["mini agent", "agent", "runtime"],
        "body": "Mini Agent is a small runtime with an LLM loop, tools, session state, and trace logs.",
    },
    {
        "title": "ReAct",
        "keywords": ["react", "reason", "act", "tool"],
        "body": "ReAct means the model decides an action, the runtime executes a tool, then the result is fed back for the next step.",
    },
    {
        "title": "Layered Agent runtime",
        "keywords": ["layering", "agent", "client", "conversation", "tools", "memory"],
        "body": "The project is split into agent, client, conversation, tools, memory, and trace modules.",
    },
    {
        "title": "Session memory",
        "keywords": ["session", "memory", "todo", "state"],
        "body": "Session memory is loaded before each LLM call and summarized in the system prompt.",
    },
    {
        "title": "Tool calling",
        "keywords": ["tool", "function", "schema", "json"],
        "body": "Tool calls use structured function-calling fields rather than regex over plain text.",
    },
]


class SearchTool(Tool):
    name = "search"
    description = "Search a small local mock knowledge base."
    params_model = SearchParams

    def _run(self, params: BaseModel, state: SessionState) -> ToolResult:
        query = params.query.strip().lower()  # type: ignore[attr-defined]
        if not query:
            return ToolResult("query cannot be empty", is_error=True)

        scored: list[tuple[int, dict[str, object]]] = []
        words = [w for w in query.replace("-", " ").split() if w]
        for doc in MOCK_DOCS:
            haystack = " ".join(
                [str(doc["title"]), str(doc["body"]), " ".join(doc["keywords"])]  # type: ignore[arg-type]
            ).lower()
            score = 0
            for word in words:
                if word in haystack:
                    score += 1
            if query in haystack:
                score += 3
            if score:
                scored.append((score, doc))

        scored.sort(key=lambda item: item[0], reverse=True)
        results = [doc for _, doc in scored[:3]]
        if not results:
            results = [MOCK_DOCS[0]]

        lines = []
        for index, doc in enumerate(results, start=1):
            lines.append(f"{index}. {doc['title']}: {doc['body']}")
        return ToolResult(output="\n".join(lines))
