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

- [ ] AC1：`agent_factory.py` 不再 import `langchain_community`。
- [ ] AC2：`uv run pytest` 全绿，且 warnings 中无 `langchain-community is being sunset`。
- [ ] AC3：若 `langchain-community` 已无引用，从 `pyproject.toml` 移除并成功 `uv sync`（同时确认 `langchain-classic` 一并消失、`dashscope` 保留）。
- [ ] AC4：现有 Agent 行为测试（config / factory 相关用例）不改断言即通过。
- [ ] AC5：新增 `tests/adapters/test_llm_factory.py` 覆盖：client 类型与 base_url、qwen3 的 `extra_body`、`max_completion_tokens` 字段名、`bind_tools` 后 `extra_body` 保留、`stream_usage`、`langchain_community` 未加载、deepseek 分支回归。
- [ ] AC6：`agent-guidelines.md` 与 `quality-guidelines.md` 登记兼容端点、字段改名与 token 日志变化；测试基线数字按实测更新。
