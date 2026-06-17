# MiniAgent Plan

## 架构总览

```text
CLI
-> Agent.run_turn()
-> ConversationManager
-> build_system_prompt()
-> LLMClient
-> ToolRegistry
-> Tool.execute()
-> TraceLogger
-> SessionStore
```

## 模块职责

| 模块 | 职责 |
|---|---|
| `cli.py` | 命令行入口，读取用户输入，支持 replay |
| `config.py` | 加载 provider、model、base_url、最大步数等配置 |
| `agent.py` | Agent 主循环，控制模型调用、工具执行、停止条件 |
| `client.py` | 调用真实 LLM，并解析 final / tool_call |
| `conversation.py` | 管理 user / assistant / tool messages |
| `prompts.py` | 构造 system prompt，并注入当前 session 状态摘要 |
| `tools/` | 工具基类、工具注册表、calculator、search、todo |
| `memory/session.py` | session JSON 保存和恢复 |
| `trace.py` | 工具调用 JSONL 日志 |
| `permissions.py` | 工具执行前的本地权限检查 |
| `result_budget.py` | 工具结果长度预算，避免超长结果直接塞回上下文 |
| `replay.py` | 不调用 LLM 的本地回放 |

## 主流程

```text
1. CLI 读取用户输入。
2. Agent 把用户消息加入 conversation。
3. Agent 构造 system prompt，注入 todo 状态摘要。
4. Agent 将 system prompt、messages、tools schema 发给 LLMClient。
5. LLM 返回 final 或 tool_call。
6. 如果是 final，保存 session 并返回用户。
7. 如果是 tool_call，先做权限检查。
8. ToolRegistry 按工具名找到本地工具。
9. 工具执行后返回 ToolResult。
10. TraceLogger 写入 JSONL。
11. 工具结果写回 messages。
12. 循环继续，直到 final 或达到最大步数。
```

## Memory 放置方式

本项目使用 session state memory：

```text
messages: 保存完整多轮聊天和工具消息
todos: 保存结构化任务状态
```

每次调用 LLM 前，`prompts.py` 会把 todo 状态摘要放进 system prompt。这样模型能看到当前任务状态，同时完整对话历史仍然保存在 messages 中。

## 验证方式

- `python -m miniagent --help`
- `python -m miniagent --provider deepseek --session demo`
- `python -m miniagent replay --session demo`
- 查看 `.miniagent/sessions/{session_id}.json`
- 查看 `.miniagent/traces/{session_id}.jsonl`

