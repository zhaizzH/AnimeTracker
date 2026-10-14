# Agent 模型配置默认值回显

## Goal

管理端「模型配置」表单在 Redis 未设置时全空，管理员看不到 `.env` / `Settings` 里实际生效的模型参数。需回显**生效值**并标注每个字段的**来源**（继承默认 vs 显式覆盖），且保存时不得把继承的默认值固化进 Redis。

## Background（已核实）

`agent_factory.py:122-134` 的解析链：

```
model        = runtime.get("model") or resolved.model
modelRoute   = runtime.get("modelRoute") or resolved.route_model     # 仅 CLIENT_ROUTE slot
temperature  = runtime.get("temperature", cfg.get("temperature", settings.llm_temperature))
maxTokens    = runtime.get("maxTokens") or settings.llm_max_tokens
thinkingBudget = runtime.get("thinkingBudget", settings.llm_thinking_budget)
reasoningEffort = runtime.get("reasoningEffort", resolved.reasoning_effort)
```

- `runtime` = Redis `agent:config:model`（`model_config_repository.py:15`），未设置时 `get_model_config()` 返回 `{}` → `GET /config` 返回 `{}` → 表单全空。
- 默认值来自 `Settings`（`config.py:27-29`）：`llm_temperature=0.3`、`llm_max_tokens=4096`、`llm_thinking_budget=2048`；模型来自 `resolve_llm_provider()`（`.env` 的 `{PROVIDER}_MODEL` / `_MODEL_ROUTE`）。

**关键约束**：`RedisModelConfigRepository.set()` 是 `SET` 整体替换。若把继承的默认值直接填表并保存，默认值会被写进 Redis，此后改 `.env` **不再生效**（`or` / `runtime.get` 会让 Redis 值永久压过 Settings）。这与 `10-14-agent-config-contract-fix` 已修的"整体替换抹字段"是同一类问题。

## Requirements

- **R1 来源可见**：`GET /admin/agent/config` 需返回每字段的生效值与其来源，区分「继承默认」与「Redis 显式覆盖」。
- **R2 不固化默认**：保存时只写用户显式填写的字段；继承默认的字段不得因一次保存被写入 Redis。
- **R3 契约形状**：新增字段的形状需与现有 camelCase 契约一致，且不破坏既有消费者（`configUpdate` 仍是 `ModelConfig`）。
- **R4 前端呈现**：继承默认显示为 placeholder（如「继承默认 0.3（.env）」）并置空 value；已覆盖显示实际值。
- **R5 清除覆盖**：需能删除某字段的覆盖、回退到继承默认（否则一旦覆盖无法撤销）。
- **R6 表单补齐**：`reasoningEffort` 已有输入框；确认 6 个字段全部可见（`10-14-agent-config-contract-fix` 已补 `modelRoute`/`reasoningEffort`）。

## Acceptance Criteria

- [ ] **AC1** Redis 为空时，GET 返回全部 6 个字段的生效值与 `source=default`。
- [ ] **AC2** 某字段被 Redis 覆盖时，该字段 `source=override`，其余仍为 `default`。
- [ ] **AC3** `.env` 改值后（Redis 空），GET 反映新值——证明回显确实来自 Settings 而非缓存常量。
- [ ] **AC4** 页面只填 1 个字段保存后，Redis 中仅存在该字段；其余仍继承 `.env`。
- [ ] **AC5** 前端区分显示继承（placeholder）与覆盖（value）。
- [ ] **AC6** 提供清除单个字段覆盖、回退继承默认的操作。
- [ ] **AC7** 既有 `configUpdate` 语义与调用方不破坏（前端仍能提交部分字段）。
- [ ] **AC8** 后端测试与 admin 前端测试补充；`uv run pytest`、`npm run typecheck`、`npm test` 全绿（记录实际数字）。
- [ ] **AC9** 不改 `agent_factory.py` 的解析语义（仅新增只读的"生效值"查询路径）。

## Out of Scope

- 不改 `ModelConfigRepository` 的整体替换语义。
- 不做多 provider 同时编辑（`model`/`modelRoute` 归属由 `LLM_PROVIDER` 决定的单一 provider）。

## Notes

- 前序任务：`10-14-agent-config-contract-fix`（已修字段保全与列表契约）。本任务在其基线上继续。
- 相关代码：`backend/agent/app/api/admin_config.py`、`schemas/admin_config.py`、`admin/config_service.py`、`config.py`；`frontend/admin/src/pages/AgentConfig.tsx`。
