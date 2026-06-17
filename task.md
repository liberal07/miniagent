# MiniAgent Task Breakdown

## T1 包结构

- 创建 `miniagent/` 包。
- 添加 `__init__.py` 和 `__main__.py`。
- 支持 `python -m miniagent` 启动。

## T2 CLI

- 实现命令行参数。
- 支持 `--session`。
- 支持 `--provider`、`--model`、`--base-url`。
- 支持 `replay` 子命令。

## T3 配置

- 从环境变量和命令行参数读取配置。
- 支持 provider preset。
- 缺少访问令牌时给出明确错误。

## T4 数据模型

- 定义 session、message、tool result、trace record 等核心结构。

## T5 Conversation

- 管理多轮 messages。
- 支持 user、assistant、assistant tool call、tool result。
- 能转换成 LLM API 需要的 messages 格式。

## T6 LLM Client

- 调用真实 LLM。
- 支持结构化工具调用。
- 把模型返回统一成 final 或 tool_call。

## T7 Tools

- 实现工具基类。
- 实现工具注册表。
- 实现 `calculator`。
- 实现 `search` mock。
- 实现 `todo`。

## T8 Agent 主循环

- 接收用户输入。
- 调用 LLM。
- 判断 final / tool_call。
- 执行工具。
- 写回工具结果。
- 循环直到 final 或最大步数。

## T9 Session Memory

- session 落盘保存。
- 启动时按 session id 恢复。
- todo 状态在每次 LLM 调用前召回到 system prompt。

## T10 Trace 和 Replay

- 工具调用写入 JSONL。
- replay 能读取 session 和 trace。
- replay 不调用 LLM。

## T11 Runtime 增强

- 添加工具权限检查。
- 添加工具结果长度预算。
- 添加 provider / wire API 适配。

## T12 文档

- README 说明运行方式、系统设计、memory 召回时机和放置方式。
- 保存原始笔试题要求。
- 保存 AI Prompt 与问题解决记录。

