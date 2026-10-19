# 迁移 ChatTongyi 出 langchain_community（sunset 告警）

## Goal

消除每次 `pytest` 启动期的 `DeprecationWarning: langchain-community is being sunset`，把唯一的 `ChatTongyi` 使用点迁到官方维护的独立集成包或等价封装，保持现有模型行为与配置契约不变。

## Background

- 唯一使用点：`backend/agent/app/adapters/llm/agent_factory.py:5` `from langchain_community.chat_models.tongyi import ChatTongyi`。
- `pyproject.toml` 显式 pin 了 `langchain-community==0.4.2`；每次跑 `uv run pytest` 都会打印 sunset 告警（最近一次全量 660 passed 仍带这条 warning）。
- LangChain 官方迁移方向：社区 chat models 迁到独立 partner 包（通义千问对应 `langchain-community` 之外的独立集成），或项目内做一层薄封装以切断对已 sunset 包的依赖。

## Requirements

- **R1 选定落点（已定，见 `design.md`）**：`langchain-community` 已于 2026-05-26 sunset 归档，**无**官方维护的通义千问 partner 包（`langchain-tongyi` PyPI 404；`langchain-dashscope` 停更于 2024-07 且为第三方；`langchain-qwq` 为个人包且拖入 12 个依赖）。落点 = 百炼官方 OpenAI 兼容端点 `https://dashscope.aliyuncs.com/compatible-mode/v1`，用**已有直接依赖** `langchain-openai` 的 `ChatOpenAI` 承接，不引入任何新包。
- **R2 行为不变**：模型调用参数、流式行为、温度/默认值解析链保持现状（对照 `agent-guidelines.md` 的配置契约）。允许且必须登记的三处**有意差异**：`max_tokens` → `max_completion_tokens`（百炼 2026-04-20 起的新字段）、thinking 开关从 `model_kwargs` 挪到 `extra_body`、`stream_usage=True` 使 token 日志由恒 `None` 变为真实值。
- **R3 依赖收敛**：`langchain_community` 全仓唯一引用点就是本文件；`langchain-classic` 仅被它传递依赖。两者一并移除；`dashscope` SDK **保留**（`embeddings.py` 仍在用）。
- **R4 告警消失**：`uv run pytest` 的 warnings summary 不再出现 `langchain-community` sunset 告警。
- **R5 新增配置键**：`DASHSCOPE_BASE_URL` 需按 ADR-0014 同步 `app/config.py` + `.env.example` + README（区域化 workspace 端点必须可覆盖，不得硬编码在 Python 里）。

## Out of Scope

- 换模型供应商、改默认模型参数、改 Prompt。
- Agent 其它链路的重构。

## Acceptance Criteria

- [x] AC1：`agent_factory.py` 不再 import `langchain_community`。（`fa1673b7`）
- [x] AC2：`uv run pytest` 全绿，且 warnings 中无 `langchain-community is being sunset`。（`4c94f8d0` 后实测 0 warning）
- [x] AC3：若 `langchain-community` 已无引用，从 `pyproject.toml` 移除并成功 `uv sync`（同时确认 `langchain-classic` 一并消失、`dashscope` 保留）。（`4c94f8d0`）
- [x] AC4：现有 Agent 行为测试（config / factory 相关用例）不改断言即通过。
- [x] AC5：新增 `tests/adapters/test_llm_factory.py`。**覆盖项已按追加需求改写**：原定的百炼项（client 类型与 base_url、qwen3 `extra_body`、`max_completion_tokens`）作废，改为 DeepSeek 契约（`max_tokens` 旧字段名、`extra_body.thinking`、`reasoning_effort` 透传、`reasoning_content` 自捕获、`bind_tools` 后 `extra_body` 保留）外加 `dashscope` 拒绝用例。现 9 例。
- [x] AC6：`agent-guidelines.md` 与 `quality-guidelines.md` 已更新；**内容按追加需求改写为「只有 DeepSeek」**，原「百炼兼容端点 / 字段改名」登记已作废（见「作废登记」表）。基线 668 passed / 0 warning。

## 追加需求（2026-10-19 用户指令）：删除百炼对话模型，只留 DeepSeek

> 本节是 R1 的上位推翻，不是补充。R1/R2/R5 与 AC5/AC6 中关于百炼兼容端点的内容**已作废**（见末尾「作废登记」）。

### 追加背景

R1 的方案（`ChatTongyi` → `ChatOpenAI` + 百炼兼容端点）在 `fa1673b7` 落地并达成原 Goal：sunset 告警消失、660 → 670 passed / 0 warning。但用户在方案落地后明确要求「把 agent 的 aliyun llm 删除，只用 deepseek」。

即：**原始 Goal（消除告警）已完成；追加需求把「保留百炼作为第二家对话模型」这件事本身判定为不需要**。因此落点从「换个包继续用百炼」变为「整条百炼对话链路连同第二家 provider 一起移除」。

### 追加 Requirements

- **R6 删除百炼对话模型**：`app/adapters/llm/agent_factory.py` 删除 dashscope 分支与 `ChatOpenAI` 引用；`app/config.py` 删除 `dashscope_model`、`dashscope_model_route`、`dashscope_base_url`；`ResolvedLlmProviderConfig.provider` 收窄为 `Literal["deepseek"]`。
- **R7 保留 DashScope 嵌入**：`DASHSCOPE_API_KEY` + `dashscope` SDK + `DashScopeEmbeddingClient`（`text-embedding-v4`）**不动**——它是 RAG 向量来源，删除会使整条 RAG 检索失效。该 Key 语义由「LLM Key」改为「仅嵌入 Key」，注释必须写明，避免后人误以为可删。
- **R8 删除 `thinkingBudget` 全链路**：`llm_thinking_budget`（Settings）、`thinkingBudget`（`admin_config.py` 的 Config 与 `_sources`）、`AdminConfigService._defaults()`、管理页 `CONFIG_FIELDS`（6 → 5）、`ModelConfigVO`、`docs/spec/openapi.yaml`、`.env`/`.env.example`、README。只删后端会留下「能填但永远无效」的管理页输入框，比留着更糟。
- **R9 无效 provider 明确报错**：`LLM_PROVIDER` 只接受 `deepseek`；设成 `dashscope` 或任何其它值必须抛 `ValueError`，**不得**静默回退到 DeepSeek——静默回退会让人以为切到了百炼、实际在跑 DeepSeek，比启动失败难查得多。
- **R10 删除死代码**：`_patch_chat_openai_reasoning()` 一并删除。实测 `ChatDeepSeek` 在 `_convert_chunk_to_generation_chunk` 里自行写入 `additional_kwargs["reasoning_content"]`，而该补丁打的是 `_convert_delta_to_message_chunk`——`ChatDeepSeek` 从不经过那条路径，补丁零对象。

### 追加 Acceptance Criteria

- [x] AC7：`create_llm(provider="dashscope")` 与 `resolve_llm_provider(llm_provider="dashscope")` 均抛 `ValueError`（回归 `tests/adapters/test_llm_factory.py`、`tests/test_llm_route_model.py`）。
- [x] AC8：全仓 `grep -r "thinkingBudget\|thinking_budget\|DASHSCOPE_MODEL\|DASHSCOPE_BASE_URL"` 除「已删除，不得恢复」的说明性文字外零命中。
- [x] AC9：`DASHSCOPE_API_KEY` 与 `dashscope` SDK 仍在，RAG 嵌入链路的测试不改断言即通过。
- [x] AC10：后端 668 passed / 0 warning（含 `-W error::DeprecationWarning`）；前端 143 例 + typecheck + build 全绿。
- [x] AC11：`.env` 本地文件同步清理（该文件在 `.gitignore` 内，不提交）。

### 作废登记（不得照旧文档「修复」）

R1/R2.3 曾把两条百炼专属契约写进 spec，现已随链路移除。**留着不删会误导后人把 DeepSeek 配置「修」成百炼形态**：

| 作废的旧契约 | 现状（DeepSeek 真相） |
|---|---|
| `max_tokens` → `max_completion_tokens`（百炼新字段） | DeepSeek 仍用 **旧字段名** `max_tokens` |
| `extra_body.enable_thinking` / `thinking_budget`（qwen3 专有） | `extra_body={"thinking": {"type": "enabled"}}` + `reasoning_effort` |
| `reasoning_content` 靠项目侧 monkey patch 捕获 | `ChatDeepSeek` 自捕获，补丁已删（R10） |
| `DASHSCOPE_BASE_URL` 可覆盖区域化端点（R5） | 键已删除；DeepSeek 的 `base_url` 仍从 `DEEPSEEK_BASE_URL` 读 |

`DASHSCOPE_MODEL_ROUTE` 所承载的「主模型 / 路由模型」双档设计随之消失：DeepSeek 侧 `model_route` 字段仍在（清理路径复用），但不再有百炼的 route model 语义。

## 落地记录

| 提交 | 内容 |
|---|---|
| `fa1673b7` | ChatTongyi → ChatOpenAI 百炼兼容端点（+10 契约用例） |
| `4c94f8d0` | 移除 `langchain-community` 依赖（连带 `langchain-classic`、`langchain-text-splitters`、`numpy`） |
| `ef2b892b` | 登记百炼兼容端点与 `max_completion_tokens` 契约（**部分内容随后作废**） |
| `00993ff3` | 移除百炼对话模型，只保留 DeepSeek；删除 `thinkingBudget` 全链路与 `_patch_chat_openai_reasoning` |

**最终状态**：668 passed / 0 warning（`-W error::DeprecationWarning` 亦全绿）；前端 143 例、typecheck、build 全绿。
