# MiniAgent Checklist

## 启动和配置

- [ ] `python -m miniagent --help` 可以显示帮助。
- [ ] 未配置访问令牌时，正常对话给出明确错误。
- [ ] 配置访问令牌后可以启动对话。
- [ ] `--session demo` 能指定 session。

## Agent 主循环

- [ ] 用户输入会写入 conversation。
- [ ] 每轮调用 LLM 前会构造 system prompt。
- [ ] tools schema 会传给 LLM。
- [ ] LLM final 会作为最终回答返回。
- [ ] LLM tool_call 会触发工具执行。
- [ ] 工具结果会写回 messages。
- [ ] 工具执行后会继续下一步 LLM 调用。
- [ ] 达到最大步数会停止。

## 工具

- [ ] `calculator` 可以完成基础计算。
- [ ] `search` 可以搜索 mock 文档。
- [ ] `todo` 可以创建任务。
- [ ] `todo` 可以查询任务。
- [ ] `todo` 可以更新任务。

## Session 和 Memory

- [ ] session 会保存到 `.miniagent/sessions/{session_id}.json`。
- [ ] 重新使用同一个 session id 可以恢复 messages。
- [ ] 重新使用同一个 session id 可以恢复 todos。
- [ ] 每次 LLM 调用前，todo 摘要会放进 system prompt。
- [ ] 第一轮创建任务，第二轮追问任务状态可以基于已有状态回答。

## Trace 和 Replay

- [ ] 工具调用会写入 `.miniagent/traces/{session_id}.jsonl`。
- [ ] trace 包含工具名、参数、结果、成功状态、错误信息。
- [ ] `python -m miniagent replay --session demo` 可以本地回放。
- [ ] replay 不调用 LLM。

## 安全和边界

- [ ] 工具执行前经过权限检查。
- [ ] 未允许的工具不会被执行。
- [ ] todo 非法 action 会被拒绝。
- [ ] 工具结果过长时会落盘，并只把摘要写回上下文。
- [ ] `.miniagent/` 不进入 Git 提交。
- [ ] 文档和代码中不包含凭证。

## 提交材料

- [ ] README 包含运行方式。
- [ ] README 包含系统设计。
- [ ] README 包含 memory 召回时机和放置方式。
- [ ] README 包含演示流程。
- [ ] `AI_PROMPTS.md` 记录 AI 辅助开发过程。
- [ ] `WRITTEN_TEST_REQUIREMENT.md` 保存题目要求。

