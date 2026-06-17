# MiniAgent Written Test

MiniAgent 是一个用于笔试题的最小可用 Agent 项目。它的目标是展示一个 Agent runtime 的核心闭环，而不是依赖现成 Agent 框架把主流程封装掉。

核心流程：

```text
用户输入
-> LLM 判断直接回答还是调用工具
-> runtime 执行工具
-> 工具结果写回上下文
-> LLM 继续推理
-> 输出最终答案
```

本项目使用真实 LLM 接口，但 Agent 主循环、工具注册、session 保存、trace 日志、跨轮状态维护都由项目代码自己实现。

## 功能

| 功能 | 状态 |
|---|---|
| CLI 多轮对话 | 支持 |
| session 落盘保存 | 支持 |
| 真实 LLM 调用 | 支持 |
| 自研 Agent 主循环 | 支持 |
| 结构化工具调用 | 支持 |
| calculator 工具 | 支持 |
| search mock 工具 | 支持 |
| todo 工具 | 支持 |
| 最大步数限制 | 支持 |
| 基本异常处理 | 支持 |
| 工具调用 trace | 支持 |
| 跨轮继续执行 | 支持 |
| replay 本地回放 | 支持 |
| 工具权限检查 | 支持 |
| 工具结果长度预算 | 支持 |

当前不包含 Web UI、MCP、多 Agent、向量库 RAG、Redis、Kafka、数据库存储。

## 自研 Runtime 增强点

本项目没有把主流程交给固定 Agent 框架，是为了把 Agent runtime 的关键控制点显式写出来。这样可以直接看到：模型只负责产生意图，真正的执行、状态、日志和安全控制都在本地 runtime。

相比直接套一个封装好的 AgentExecutor，这个项目重点展示了下面几个可控点：

| 增强点 | 解决的问题 | 体现位置 |
|---|---|---|
| 显式 Agent 主循环 | 能清楚看到“LLM 决策 -> 工具执行 -> 结果回写 -> 继续推理”的完整闭环，而不是被框架隐藏 | `agent.py` 的 `Agent.run_turn()` |
| 结构化工具映射 | 模型返回 tool name 和 JSON arguments 后，本地 runtime 再映射到真实工具对象执行，避免从普通文本里正则解析 | `client.py`、`tools/`、`ToolRegistry` |
| 工具权限检查 | 模型不能想调什么就直接执行，所有工具调用先经过本地策略拦截 | `permissions.py`、`Agent._execute_tool()` |
| 工具结果长度预算 | 工具结果太长时不直接塞回上下文，超长结果落盘，只把摘要和预览写回消息 | `result_budget.py` |
| JSONL trace | 每次工具调用都有可检查记录，能证明工具是否真的执行、参数是什么、结果是什么、是否失败 | `trace.py`、`.miniagent/traces/` |
| replay 本地回放 | 不再次调用 LLM，也能复盘 session、todo 状态和工具调用链路，方便录屏和验收 | `replay.py` |
| session state memory | 聊天历史和结构化任务状态分开保存；todo 状态会在每次 LLM 调用前召回到 system prompt | `memory/session.py`、`prompts.py` |
| 多 provider / wire API 适配 | 模型调用层和 Agent runtime 解耦，可以切换 provider 或协议而不改主循环 | `config.py`、`client.py` |

这些增强点不是为了否定 LangChain 这类框架。框架适合快速集成，但 Agent runtime 本身：谁保存状态、谁决定工具、谁执行工具、谁记录 trace、谁处理异常、谁控制上下文成本这些由runtime控制更加自由和有强适应性。本项目把这些点拆成独立模块，便于阅读、调试。

## 快速开始

克隆仓库并进入仓库根目录：

```powershell
git clone <repo-url>
cd <repo-dir>
```

安装依赖：

```powershell
pip install -e .
```

配置模型访问令牌：

```powershell
$env:MINIAGENT_API_KEY="<provider-token>"
```

启动：

```powershell
python -m miniagent --provider deepseek --session demo
```

退出：

```text
quit
```

或：

```text
exit
```

## 推荐演示

启动后依次输入：

```text
Calculate 1 + 2 * 3
Search ReAct in this project
Create a task to prepare the written test demo
What is the status of the task from before?
quit
```

查看本地运行数据：

```powershell
Get-Content .miniagent\sessions\demo.json
Get-Content .miniagent\traces\demo.jsonl
python -m miniagent replay --session demo
```

`.miniagent/` 是本地运行目录，已经被 `.gitignore` 忽略，不应提交到仓库。

## 命令

查看帮助：

```powershell
python -m miniagent --help
```

常用命令：

```powershell
python -m miniagent --provider deepseek --session demo
python -m miniagent --provider openai --session demo
python -m miniagent --session demo --max-steps 6
python -m miniagent --session demo --max-tool-result-chars 1000
python -m miniagent replay --session demo
```

## 配置

| 配置项 | 说明 | 默认值 |
|---|---|---|
| `MINIAGENT_API_KEY` | 模型访问令牌 | 正常对话必须配置 |
| `MINIAGENT_PROVIDER` | provider 预设 | `deepseek` |
| `MINIAGENT_MODEL` | 模型名覆盖 | provider 预设 |
| `MINIAGENT_BASE_URL` | OpenAI-compatible 地址覆盖 | provider 预设 |
| `MINIAGENT_WIRE_API` | `chat_completions` 或 `responses` | provider 预设 |
| `MINIAGENT_MAX_STEPS` | 单轮最大 Agent 步数 | `6` |
| `MINIAGENT_MAX_TOOL_RESULT_CHARS` | 工具结果写回上下文的字符预算 | `4000` |

内置 provider：

| Provider | 默认模型 | 默认地址 | 协议 |
|---|---|---|---|
| `deepseek` | `deepseek-v4-pro` | `https://api.deepseek.com` | `chat_completions` |
| `openai` | `gpt-4.1-mini` | `https://api.openai.com/v1` | `chat_completions` |


## 项目结构

```text
miniagent-written-test/
|-- README.md
|-- AI_PROMPTS.md
|-- WRITTEN_TEST_REQUIREMENT.md
|-- pyproject.toml
`-- miniagent/
    |-- __main__.py
    |-- cli.py
    |-- config.py
    |-- agent.py
    |-- client.py
    |-- conversation.py
    |-- prompts.py
    |-- models.py
    |-- permissions.py
    |-- result_budget.py
    |-- replay.py
    |-- trace.py
    |-- memory/
    |   `-- session.py
    `-- tools/
        |-- base.py
        |-- calculator.py
        |-- search.py
        `-- todo.py
```

## 运行流程

```text
CLI
 |
 v
Agent.run_turn()
 |
 |-- 构造 system prompt，加入当前 session 状态摘要
 |-- 发送 system prompt、messages、tools schema 到 LLMClient
 |-- 接收 final 或 tool_call
 |-- tool_call 先经过 PermissionChecker
 |-- ToolRegistry 根据工具名找到本地工具
 |-- Pydantic 校验工具参数
 |-- Tool.execute() 执行工具
 |-- TraceLogger 写入 JSONL
 |-- 工具结果写回 messages
 `-- 继续循环，直到 final 或达到最大步数
```

## 架构图

```text
[User]
  |
  v
[CLI]
  |
  v
[Agent.run_turn]
  |
  +--> [Prompt Builder]
  |        |
  |        +--> system prompt
  |        +--> conversation messages
  |        `--> tool schemas
  |
  v
[LLMClient]
  |
  +--> final answer --------------------+
  |                                      |
  `--> tool_call                         |
          |                              |
          v                              |
   [PermissionChecker]                   |
          |                              |
          v                              |
   [ToolRegistry]                        |
          |                              |
          v                              |
   [Tool.execute]                        |
          |                              |
          v                              |
   [TraceLogger]                         |
          |                              |
          v                              |
   [tool result message]                 |
          |                              |
          +---------- loop --------------+
                                         |
                                         v
                                  [SessionStore]
```

## 工具

### calculator

用于基础数学计算。

示例：

```text
Calculate 12 * (3 + 4)
```

实现特点：

- 使用 AST 解析表达式。
- 使用白名单限制允许的语法节点。
- 不用 Python `eval()` 或 `exec()` 执行任意代码。

### search

用于搜索本地 mock 知识库。

示例：

```text
Search ReAct in this project
```

说明：

- 数据在 `miniagent/tools/search.py` 的 `MOCK_DOCS` 中。
- 不访问互联网。
- 主要用于演示工具调用链路。

### todo

用于保存当前 session 的任务状态，是跨轮继续执行的核心。

支持动作：

```text
create
list
get
update
```

示例：

```text
Create a task to prepare the written test demo
What is the status of the task from before?
```

第二轮能回答，是因为 todo 状态已经写入 session，并在下一次调用 LLM 前被召回。

## Session 和 Memory

本项目实现的是 session state memory，不是向量检索或长期记忆总结。

session 文件位置：

```text
.miniagent/sessions/{session_id}.json
```

保存内容：

```text
messages: 多轮 user / assistant / tool 消息
todos: 结构化任务状态
created_at
updated_at
```

每次调用 LLM 前，`prompts.py` 会把当前 todo 摘要写入 system prompt。

可以理解为：

```text
messages = 对话历史
todo summary = 当前任务状态摘要
```

所以用户后续追问“刚才那个任务怎么样了”时，模型能看到 runtime 保存并重新放入 prompt 的任务状态。

## Trace 和 Replay

工具调用日志位置：

```text
.miniagent/traces/{session_id}.jsonl
```

每一行是一条工具调用记录：

```text
step
tool_call_id
tool_name
arguments
result
success
error
created_at
```

回放命令：

```powershell
python -m miniagent replay --session demo
```

replay 不调用 LLM，只读取本地 session 和 trace，方便检查一次演示中发生了什么。

## 笔试题要求对照

| 笔试题要求 | 本项目实现 |
|---|---|
| 多轮对话和 session 维护 | `ConversationManager` + `SessionStore` |
| 不依赖现成 Agent 框架完成主流程 | 主循环在 `Agent.run_turn()` |
| 接收用户输入 | `cli.py` |
| 判断直接回答还是调用工具 | `LLMClient` 解析结构化工具调用 |
| 执行工具 | `Agent._execute_tool()` + `ToolRegistry` |
| 读取工具结果 | 工具结果转成 tool message |
| 继续下一步直到最终答案 | 工具结果写回后继续循环 |
| 至少三个工具 | `calculator`、`search`、`todo` |
| 最大步数限制 | `AgentConfig.max_steps` |
| 基本异常处理 | LLM、参数、权限、工具异常都会兜底 |
| trace 或执行日志 | `TraceLogger` 写 JSONL |
| 跨轮继续执行 | todo 状态持久化并在 prompt 中召回 |
| 真实 LLM 调用 | OpenAI-compatible SDK |
| README | 当前文件 |
| AI Prompt 与问题解决记录 | `AI_PROMPTS.md` |

## 自检

编译检查：

```powershell
python -m compileall miniagent
```

确认运行数据和敏感信息没有进入提交：

```powershell
git status --ignored
```

发布前可搜索常见敏感模式：

```powershell
Select-String -Path (Get-ChildItem -Recurse -File).FullName -Pattern "sk-[A-Za-z0-9]+|[A-Za-z]:\\\\|secret|token"
```

## 常见问题

### 提示缺少 `MINIAGENT_API_KEY`

正常对话需要先配置模型访问令牌：

```powershell
$env:MINIAGENT_API_KEY="<provider-token>"
```

本地回放不需要访问令牌：

```powershell
python -m miniagent replay --session demo
```

### `No module named miniagent`

请在仓库根目录运行：

```powershell
python -m miniagent --session demo
```

或者先安装：

```powershell
pip install -e .
```

### 模型没有调用工具

可以把指令写得更明确：

```text
Use the calculator tool to calculate 1 + 2 * 3.
```

或：

```text
Use the search tool to search ReAct in this project.
```

## 提交材料对应

| 提交要求 | 对应内容 |
|---|---|
| 代码链接 | GitHub 仓库地址 |
| 终端操作录屏 | 使用“推荐演示”部分 |
| README | `README.md` |
| 系统设计 | “运行流程”和“架构图”部分 |
| memory 召回时机与放置方式 | “Session 和 Memory”部分 |
| AI Prompt 与问题解决记录 | `AI_PROMPTS.md` |
