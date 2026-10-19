# 迁移 ChatTongyi 出 langchain_community（sunset 告警）

## Goal

消除每次 `pytest` 启动期的 `DeprecationWarning: langchain-community is being sunset`，把唯一的 `ChatTongyi` 使用点迁到官方维护的独立集成包或等价封装，保持现有模型行为与配置契约不变。

## Background

- 唯一使用点：`backend/agent/app/adapters/llm/agent_factory.py:5` `from langchain_community.chat_models.tongyi import ChatTongyi`。
- `pyproject.toml` 显式 pin 了 `langchain-community==0.4.2`；每次跑 `uv run pytest` 都会打印 sunset 告警（最近一次全量 660 passed 仍带这条 warning）。
- LangChain 官方迁移方向：社区 chat models 迁到独立 partner 包（通义千问对应 `langchain-community` 之外的独立集成），或项目内做一层薄封装以切断对已 sunset 包的依赖。

## Requirements

- **R1 选定落点**：确认官方是否已有独立的通义千问 partner 包；有则换包，无则在 `adapters/llm` 内做一层薄封装，使 `agent_factory.py` 不再 import `langchain_community`。
- **R2 行为不变**：模型调用参数、流式行为、温度/默认值解析链保持现状（对照 `agent-guidelines.md` 的配置契约）。
- **R3 依赖收敛**：迁移完成后评估 `langchain-community` 是否还有其它引用；没有则从 `pyproject.toml` 移除。
- **R4 告警消失**：`uv run pytest` 的 warnings summary 不再出现 `langchain-community` sunset 告警。

## Out of Scope

- 换模型供应商、改默认模型参数、改 Prompt。
- Agent 其它链路的重构。

## Acceptance Criteria

- [ ] AC1：`agent_factory.py` 不再 import `langchain_community`。
- [ ] AC2：`uv run pytest` 全绿，且 warnings 中无 `langchain-community is being sunset`。
- [ ] AC3：若 `langchain-community` 已无引用，从 `pyproject.toml` 移除并成功 `uv sync`。
- [ ] AC4：现有 Agent 行为测试（config / factory 相关用例）不改断言即通过。
