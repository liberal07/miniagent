# AI Prompt And Problem-Solving Record

本文记录开发过程中使用 AI 辅助的方式。内容已经脱敏，不包含个人环境信息、私有项目名或凭证。

## 原始目标

从零实现一个最小可用 Agent，满足笔试题要求：

- 支持多轮对话和 session 维护。
- 不直接依赖现成 Agent 框架完成主流程。
- 核心 runtime 自己实现。
- 使用真实 LLM 调用。
- 至少提供三个工具：calculator、search、todo。
- 支持最大步数限制。
- 支持基本异常处理。
- 支持工具调用 trace 或执行日志。
- 支持跨轮继续执行场景。
- README 说明运行方式、系统设计、memory 召回时机与放置方式。

## 主要开发 Prompt

```text
按照 spec-driven development 的流程，从零实现一个最小可用 Agent 笔试项目。

项目做成通用 mini Agent。
不复用现成 Agent runtime。
优先满足笔试题原始要求。
交互方式使用 CLI。

先写 spec.md、plan.md、task.md、checklist.md。
这些设计文档确认后，再开始实现代码。

核心要求：
- 支持多轮对话和 session 维护。
- 使用真实 LLM 调用。
- 自己实现 Agent 主循环。
- 支持工具调用：calculator、search、todo。
- 支持最大步数限制。
- 支持基本异常处理。
- 支持工具调用 trace。
- 支持跨轮继续执行。
- README 说明运行方式、系统设计、memory 的召回时机与放置方式。
```

## 开发流程

```text
spec.md -> plan.md -> task.md -> checklist.md -> implementation -> validation
```

先明确需求、设计和验收项，再写实现代码。

## 关键设计决策

### Runtime

决策：主循环放在 `agent.py`。

原因：笔试题要求核心 runtime 自己实现，不能交给 LangChain、OpenHands、AutoGen 等框架接管。

### LLM 调用

决策：使用 OpenAI-compatible SDK 和结构化 tool calling。

原因：现代工具调用接口会返回工具名和 JSON 参数字段，不需要从普通文本里用正则解析工具调用。

### 工具映射

决策：模型返回的工具名通过 `ToolRegistry` 映射成本地工具对象。

流程：

```text
LLM tool_call.name -> ToolRegistry.get(name) -> Tool.execute(arguments, state)
```

这个流程能清楚展示：模型只提出“要调用哪个工具和参数”，真正执行由本地 runtime 控制。

### Session Memory

决策：把 messages 和 todo 状态保存为本地 JSON。

原因：足够满足笔试题要求，也方便录屏和检查。

### Memory Recall

决策：每次调用 LLM 前，把当前 todo 摘要写入 system prompt。

原因：跨轮追问时，模型可以看到 runtime 保存的结构化任务状态。

### Trace

决策：每次工具调用写一行 JSONL。

原因：JSONL 适合追加写入，便于检查工具是否真的被执行。

### Calculator Safety

决策：calculator 使用 AST 白名单解析。

原因：避免执行任意 Python 代码。

## 问题与处理

### 问题：不能做成本地 if/else 假 Agent

如果完全靠本地规则判断是否调用工具，会不符合“使用真实 LLM 调用”的要求。

处理：正常对话必须走 `LLMClient.next_action()`，由模型返回 final 或 tool_call。

### 问题：从纯文本解析工具调用不稳定

模型普通文本里可能出现格式错误、缺字段、转义错误。

处理：使用结构化工具调用字段，runtime 读取工具名和 JSON 参数。

### 问题：跨轮状态需要可验证

只靠聊天历史不容易证明任务状态真的被保存。

处理：todo 写入 `SessionState.todos`，并持久化到 session JSON。

### 问题：需要证明工具真的执行过

只看最终回答无法证明工具调用链路。

处理：每次工具调用都写入 JSONL trace，包含工具名、参数、结果、成功状态和错误信息。

### 问题：工具结果过长会撑大上下文

长结果直接写回 messages 会增加上下文成本。

处理：设置工具结果字符预算，超长结果落盘，只把摘要写回上下文。
