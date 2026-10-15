# 设计决策：OpenAPI/SSE 契约同步

## 四项待决策的裁定（2026-10-14）

| # | 问题 | 裁定 | 理由 |
|---|---|---|---|
| 1 | SSE 在 OpenAPI 3.0 建模到多深 | **(a) 单帧 schema + description 说明分帧** | 3.0.1 无 `itemSchema`；升 3.1 需确认全部工具链（前端 `openapi-typescript` 等）成本高且本任务定为纯文档。过度建模 `\n\n` 分帧会失真，故用 `SSEFrame` 描述单帧、分帧写进 `description`/`info.description`。 |
| 2 | `end` 事件如何表达 | **按 wire 事实：`is_end=true`，`type` 枚举四值不含 `end`** | `app/api/sse.py:10-11` 权威；spec `agent-guidelines.md` 已明文「类型枚举只有四值，结束由 `is_end=true` 表达」。允许 `type=end` 需改实现，超纯文档范围。 |
| 3 | 是否引入校验脚本（AC-B） | **不引入，走 AC-A 人工对照表** | 无既有漂移校验设施；本任务风险低、范围窄。落点 `research/contract-alignment-table.md`（含逐项 `openapi.yaml:<line>` ↔ 实现 `<file>:<line>` + 校验命令 + 日期）。脚本收益长期确定，但引入新工具与 CI 步骤应另开任务。 |
| 4 | 契约基准层 | **Spring 对外层路径（现状）** | 浏览器只访问 `/api/**`，由 Spring 代理转发到 Python；openapi 记对外层与前端 shared 一致。Python 内部路径差异登记为债务（`info.description` 第 2 条）。 |
| 5 | 已知债务落点 | **`openapi.yaml` 内联 `info.description` + spec guide 更新** | 与契约同文件便于同步；`cross-layer-thinking-guide.md:63` 的「未完整表达」句已改写为已实现 + 残留债务指向。 |

## AC9 校验器实测

命令：`npx --yes @redocly/cli@latest lint docs/spec/openapi.yaml`

| 版本 | errors | warnings |
|---|---|---|
| 改前 | 101 | 171 |
| 改后 | 31 | 171 |

剩余 31 errors 全部为文件既有债务，非本任务引入：
- `spec-components-invalid-map-name` ×30 — `components.schemas` 用中文键名（如 `标签信息 VO`），不匹配 `^[a-zA-Z0-9\.\-_]+$`。改键名需同步 8 处 `$ref`，属独立工程。
- `no-empty-servers` ×1 — 无 `servers` 段。

**结论**：可被标准 OpenAPI 3.0 校验器解析（无语法/结构错误导致的致命失败）。AC9 满足，残留记为已知债务。

## 有意选择 / 已登记差异

1. **Spring 层 stream 请求体用 `Map` 透传、不校验形状**：契约记 Python 权威 `ChatRequest`（`session_id` + `content` 1..4096）。Spring 不校验属实现选择，非漂移。
2. **`X-Request-ID` 只声明在 agent + auth 范围端点**：`RequestIdFilter` 为全局 `@Order(HIGHEST_PRECEDENCE)` 过滤器，实际对所有 `/api/**` 生效；非 agent 的 52 个端点未逐一声明，登记为债务。
3. **path 级 `security: []` 曾试后废弃**：OpenAPI Path Item 无 `security` 字段（redocly `struct` 规则报 21 条错误）。改为把 `security: []` 写到每个公开 operation 上。
