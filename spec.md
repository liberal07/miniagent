# MiniAgent Spec

## 背景

本项目用于完成一道“从零实现一个最小可用 Agent”的笔试题。题目允许使用 AI 工具辅助开发，但要求核心 Agent runtime 自己实现，不能直接依赖现成 Agent 框架完成主流程。

## 目标

实现一个可通过 CLI 使用的最小 Agent，能够完成：

```text
用户输入
-> LLM 判断直接回答还是调用工具
-> runtime 执行工具
-> 工具结果写回上下文
-> LLM 继续推理
-> 输出最终答案
```

## 功能需求

- 支持多轮对话。
- 支持 session 保存和恢复。
- 使用真实 LLM 调用。
- 自己实现 Agent 主循环。
- 支持结构化工具调用。
- 至少提供三个工具：`calculator`、`search`、`todo`。
- 支持最大步数限制。
- 支持基本异常处理。
- 支持工具调用 trace。
- 支持跨轮继续执行场景。
- README 说明运行方式、系统设计、memory 召回时机和放置方式。
- 提供 AI Prompt 与问题解决记录。

## 非功能需求

- 代码结构清晰，便于评审阅读。
- 不把凭证写入代码或文档。
- 本地运行数据不进入 Git 提交。
- 工具调用链路可观察、可回放。
- 对异常和越权工具调用有兜底处理。

## 不做的事

当前版本不实现：

- Web UI。
- MCP。
- 多 Agent。
- 向量库 RAG。
- Redis / Kafka / 数据库存储。
- 复杂长期记忆总结。
- 自动上下文压缩。

## 验收标准

- 可以通过 `python -m miniagent` 启动。
- 同一个 session 内可以连续多轮对话。
- LLM 能返回 final answer 或 tool call。
- runtime 能执行工具并把结果写回上下文。
- `calculator`、`search`、`todo` 可用。
- 达到最大步数时能停止。
- 工具异常不会导致程序崩溃。
- 工具调用会写入 JSONL trace。
- 第一轮创建 todo，第二轮追问时可以基于已有 todo 状态回答。
- 运行数据保存在 `.miniagent/`，且不提交到仓库。

