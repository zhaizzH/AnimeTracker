# Admin Agent 配置页契约修复

## Goal

让 `/agent-config` 页与后端真实契约一致，消除两处会**静默丢数据**的缺陷：提示词列表因字段名错读而整页不可用（且保存会以空内容覆盖提示词）；模型配置保存时整体替换，抹掉页面上不存在的运行时字段 `modelRoute` / `reasoningEffort`。

## Background（已在运行中的服务实测复现）

后端契约（`backend/agent/app/api/admin_config.py`、`schemas/admin_config.py`、`admin/config_service.py`）：

- `GET /admin/agent/prompts` 返回**裸数组** `[{promptKey, promptContent}, ...]`，字段名为 `promptKey`（非 `key`），也**不是** `{keys: [...]}`。
- 合法 key 共 5 个：`client_gateway_prompt`、`client_search_agent_prompt`、`client_discover_agent_prompt`、`client_recommend_agent_prompt`、`admin_agent_prompt`。
- `GET/POST /admin/agent/config` 的 `ModelConfig` 有 6 个字段：`model`、`modelRoute`、`temperature`、`maxTokens`、`thinkingBudget`、`reasoningEffort`。
- `config_service.py:36` → `RedisModelConfigRepository.set()` 执行 `SET` **整体替换**（非合并）。

缺陷证据（curl 实测，账号 test1）：

1. `AgentConfig.tsx:41` 的 `raw.map((x) => String(x.key))` 对真实响应产出 `["undefined"×5]`；实际字段为 `["promptKey","promptContent"]`。array 分支落空，`raw.keys` 分支永不命中。
2. 写入 `{model, modelRoute, reasoningEffort}` 后，再按页面表单提交 `{model}`，GET 只剩 `{model}` —— 另两个字段被静默抹除。
3. `modelRoute` 与 `reasoningEffort` 是**运行时真读**字段：`agent_factory.py:126` 用 `modelRoute` 选路由模型、`:134` 用 `reasoningEffort`；全仓无其他写入方。

## Requirements

- **R1 提示词列表解析**：`AgentConfig.tsx` 按真实契约解析列表，取 `promptKey`。移除针对不存在形状的猜测分支（裸数组 / `{keys}` 双分支适配）。
- **R2 提示词保存防丢失**：详情加载失败（如 404）时不得允许以空内容保存覆盖提示词；保存按钮需在内容未成功加载时禁用，或保存前校验。
- **R3 模型配置字段保全**：保存时保留服务端已有但表单未呈现的字段（`modelRoute`、`reasoningEffort`），使保存成为"合并"而非"整体替换"。
- **R4 补齐表单字段**：将 `modelRoute`、`reasoningEffort` 纳入表单可编辑（两者均为 free-form string）。
- **R5 列表错误态**：区分"加载失败"与"暂无提示词"（当前只判 `isLoading`，`isError` 显示为"暂无提示词"）。
- **R6 切换竞态**：快速切换提示词时保证 `content` 与 `selected` 一致（请求序号或取消）。
- **R7 重置错误处理**：`resetPrompt` 补 `onError`，不再静默失败。
- **R8 测试契约对齐**：修正 `AgentConfig.test.tsx` 中固化的错误 mock 形状（`{keys: [...]}`），改为真实形状，并覆盖 R1–R4。

## Acceptance Criteria

- [x] **AC1** 以真实响应 `[{promptKey, promptContent}]` 渲染时，左栏显示真实 key 名，无 `undefined` 条目。
- [x] **AC2** 详情加载失败时无法以空内容提交覆盖提示词（按钮禁用或有明确阻断）。
- [x] **AC3** 服务端预置 `modelRoute`/`reasoningEffort` 后提交表单，两字段仍在（实测 GET 保留）。
- [x] **AC4** 表单可编辑并提交 `modelRoute`/`reasoningEffort`。
- [x] **AC5** 列表请求失败时显示错误态，而非"暂无提示词"。
- [x] **AC6** 快速连续切换两个提示词，最终 content 与标题一致。
- [x] **AC7** 重置失败给出 toast 错误提示。
- [x] **AC8** `AgentConfig.test.tsx` 使用真实响应形状；上述行为有断言覆盖。
- [x] **AC9** admin 包 `npm run typecheck` 与 `npm test` 全绿（记录实际数字）。
- [x] **AC10** 不改后端契约（本次仅修前端；后端 `ModelConfig` 字段与 SET 语义保持原样）。

## Non-Goals / Out of Scope

- 不新增后端字段校验（`thinkingBudget` 无范围校验一事仅记录，不在本任务修）。
- 不处理 `docs/spec/openapi.yaml:2535-2734` 的文档漂移（另记，本任务不改）。

## Notes

- 修复应落在前端；后端行为（整体替换语义）保持不变，由前端负责保全未知字段。
- 涉及文件预期：`frontend/admin/src/pages/AgentConfig.tsx`、`frontend/admin/src/pages/AgentConfig.test.tsx`。
