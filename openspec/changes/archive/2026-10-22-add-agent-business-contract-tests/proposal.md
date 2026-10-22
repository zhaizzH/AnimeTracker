# Proposal: agent ↔ business 契约测试

## Why

agent 消费 business 的两类跨层契约（HTTP 路径/字段、SSE 帧、previewId 写协议）目前**零自动化校验**，全靠字段名硬编码字符串与人工对照。父任务 PRD 已诊断：跨层字段改名或语义漂移时 CI 拦不住，只能等用户发现；`.trellis/spec/guides/cross-layer-thinking-guide.md` 也明写「当前 OpenAPI 是手工维护，CI 未自动证明它与三端一致」。

### 执行本提案前发现的阻断事实

契约基准 `docs/spec/openapi.yaml` 在提交 `22d7cb63`（`chore(task): 归档 10-20-opt-previewable-action`）中被**整体回退**到一份更旧的导出状态，与同提交 message 声明的「仅归档任务」不符。相对上一版 `00993ff3`（2026-10-19），净损失：

| 丢失内容 | 证据 |
|---|---|
| `info.description`（SSE 契约说明 + 已知债务清单） | `00993ff3` 有 35 行，当前 0 行 |
| 顶层 `security` 与逐 operation 的 `security: []` | 当前文件 `grep -c security` → 0 |
| `components.securitySchemes.bearerAuth` | 当前 `securitySchemes` 缺失 |
| `ChatRequest` / `SSEFrame` / `EvidenceCandidate` / `LexicalSearchResult` / `LexicalSearchCandidate` | 5 个 schema 消失 |
| 全部 `$ref` 复用 | 当前 `$ref` 计数 = 0，38 个 schema 全部无人引用 |
| 8 个 operation 的字段级细节 | `evidence/batch`、`evidence/resolve`、两个 `*/agent/stream`、`agent/config`、`agent/config/update`、`agent/health`、`auth/login` 退化为占位 |
| 混入 4 条 Java **测试**夹具路径 | `/api/client/subjects/1`、`/api/client/private`、`/api/admin/private`、`/actuator/health` 来自 `SecurityConfigAuthorizationTest.java`，不是真实对外接口 |

**契约测试若建在这份已被改坏的文件上，只会把「坏契约」固化成断言。** 因此修复基准文件是本提案的第一步，而非可选清理。

## What Changes

- **修复契约基准**：把 `docs/spec/openapi.yaml` 恢复到 `00993ff3` 的完整契约状态，保留其后 `00993ff3..HEAD` 之间无 openapi 改动的事实，并剔除混入的 4 条测试夹具路径。
- **补齐 agent 实际调用但契约缺失的字段级定义**：`evidence/batch`、`evidence/resolve`、两个 `*/agent/stream`（`text/event-stream` + `SSEFrame`）。这些是契约测试要断言的对象，不能留占位。
- **新增契约测试三件套** `backend/agent/tests/contracts/`：
  - `test_http_contract.py`：agent 侧每个 `business.request(...)` 的 method + path 在 openapi.yaml 里有定义；请求体/查询字段在该 operation 的 schema 里有声明。
  - `test_sse_contract.py`：`AgentEventType` → wire `type` 取值域、`is_end` 帧序、`result=error` 与 `state=error` 的区分、`SSEFrame` 字段集与实现一致。
  - `test_preview_contract.py`：Redis `agent:pending-action:{session_id}` 键格式、600s TTL、`PendingAction` 四种判别类型的序列化/反序列化往返、确认时 payload 与 preview 版本绑定。
- **交叉校验**：契约测试同时断言 openapi.yaml 自身的结构完整性（`$ref` 无悬空、无未引用 schema），使「契约文件被再次改坏」本身也变成红灯。
- **CI 强制**：`backend-python` job 已跑 `uv run pytest`，测试落在 `tests/` 下即自动纳入；补一条显式契约 job 步骤与失败提示，让红灯指向「契约漂移」而不是泛化测试失败。

**非 BREAKING**：不改任何运行时行为、协议、Redis 键、TTL 或 business Java 代码。

## Capabilities

### New Capabilities

- `agent-business-contract`: agent 对 business HTTP 接口的消费必须与仓库内 OpenAPI 契约一致（路径、方法、请求字段、响应字段），且契约文件自身结构完整。
- `agent-stream-wire-contract`: SSE 帧的 wire 层契约（`type` 取值域、`is_end` 语义、`content` 字段集、错误表达方式）由测试锁定，不得静默漂移。
- `pending-action-protocol`: 预览→确认写协议的持久化契约（Redis 键格式、TTL、判别联合序列化往返、preview 版本绑定）由测试锁定。

### Modified Capabilities

无。项目当前 `openspec/specs/` 为空，本次为全新能力。

## Impact

| 区域 | 影响 |
|---|---|
| `docs/spec/openapi.yaml` | 恢复 + 补齐字段级定义（纯文档） |
| `backend/agent/tests/contracts/` | 新增目录与三类测试 + 一个 OpenAPI 解析辅助模块 |
| `backend/agent/pyproject.toml` | 可能需要显式声明 `PyYAML`（当前经 `uvicorn[standard]` 间接引入，测试直接 import 则应显式声明） |
| `.github/workflows/ci.yml` | `backend-python` job 补契约测试显式步骤 |
| `backend/agent/app/**` | **零改动**（约束：不合规即修契约测试或契约文件，不改运行时） |
| `backend/business/**` | **零改动** |
| `frontend/**` | 零改动 |

## 验收信号

- 改 `openapi.yaml` 里任一被断言字段名 → `pytest tests/contracts` 红（手动演练一次并记录）。
- 改 agent 侧任一 `request()` 路径拼写 → 契约测试红（手动演练一次并记录）。
- `uv run pytest` 基线 668 用例保持全绿，契约测试为净增。
- `docs/spec/openapi.yaml` 的 `$ref` 悬空数 = 0，未引用 schema 数 = 0，混入的测试夹具路径数 = 0。

## Out of Scope

- 引入 springdoc / 自动 OpenAPI 导出（父任务约束：不动 business 构建）。
- 静态解析 business Java 源码做跨仓联动（已在决策中否掉，成本与脆弱性不划算）。
- prompt 回归评测套件（父任务明确划归下一轮）。
- 修复 `tests/jobs/importer/test_contract_drift.py` 记录的数据层漂移（与本契约无关）。
- 补齐 openapi.yaml 其余 `$ref` 未覆盖路径的字段级细节（本提案只覆盖 agent 实际调用的 18 个 operation + 契约自完整性）。
