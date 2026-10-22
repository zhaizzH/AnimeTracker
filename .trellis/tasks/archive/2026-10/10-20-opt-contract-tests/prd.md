# 优化项 4: agent ↔ business 契约测试

## Goal

基于 business 的 OpenAPI 导出建立契约测试。在 backend/agent/tests/contracts/ 下新增三类：(1) HTTP 契约：断言 business_http.py 所有 request() 调用的路径和字段在 OpenAPI 里有定义；(2) SSE 帧契约：state 字段取值域、result=error vs state=error、is_end 帧序；(3) pending-action 写协议契约：Redis key 格式、TTL、确认时 payload 与 preview 版本绑定。CI 必跑。完成信号：contract 改字段名 agent 测试红；agent 改路径拼写测试红。

## Requirements

- `docs/spec/openapi.yaml` 必须可被测试直接消费：无悬空 `$ref`、无孤儿 schema、不含只存在于 Java 测试类里的夹具路径。
- HTTP 契约覆盖 agent 全部出站调用点（method + path → 唯一 operation），并对静态可判定的请求体字段做声明性校验。
- 路径匹配必须字面优先；只能通配匹配且调用点不含运行时 ID 时判为拼写错误，除非显式进白名单。
- SSE 契约覆盖 `type` 四值枚举、`content` 子字段集、单帧 `SSEFrame`、错误语义分离（工具失败 = `state=end` + `result=error`；持久化失败 = `status` + `state=error`）、唯一 `is_end` 收尾。
- pending-action 契约覆盖 Redis 键模板、600s TTL、判别联合往返、`expires_at`、preview 版本绑定。
- CI 在 `uv run pytest` 之前单独跑契约子集，失败日志需能区分「契约漂移」与普通用例失败。
- 运行时代码零改动：`backend/agent/app/**`、`backend/business/**`、`frontend/**`。

## Acceptance Criteria

### 契约基线

- [x] `docs/spec/openapi.yaml` 自洽：69 paths / 5 schemas / 0 悬空 `$ref` / 0 孤儿 schema / `securitySchemes: bearerAuth` 保留 / `info.description` 保留。
- [x] 删除 4 条 Java 测试夹具路径（`/api/client/subjects/1`、`/api/client/private`、`/api/admin/private`、`/actuator/health`），补声明 `GET /actuator/health/liveness`。
- [x] 删除 32 个无引用的 Spring 导出占位 schema；其中 30 个在 `paths` 里有逐字节相同的内联副本，行为等价。

### 三类契约测试

- [x] **HTTP**：AST 遍历得 **25 个调用点 = 24 个属性 `.request` + 1 个 `asyncio.to_thread` 健康探针**，逐个解析到唯一 operation；静态可判定请求字段与契约比对。
- [x] **SSE**：`type` 四值枚举（`answer`/`thinking`/`function_call`/`status`，**无 `end`**）、`content` 子字段集、单帧 `SSEFrame`、错误语义分离、唯一 `is_end` 收尾、帧内无 `event:` 行。
- [x] **pending-action**：键模板 `agent:pending-action:{session_id}`、600s TTL、判别联合往返、`expires_at`、preview 版本绑定。
  - 注：本任务的原始描述写的是 "previewId 写协议"，与实际字段不符——**代码中从未有过 `previewId`**。实际形态是 business DTO 字段用驼峰（`subjectId`/`summary`/`actionId`），agent 自定义信封字段保持蛇形（`preview_id`/`user_id`/`expires_at`），后者是 Redis 存量载荷的形态。按实现现状修正描述，不改 runtime。

### 漂移检测有效性

- [x] **契约侧漂移会红**：把 save 操作请求体字段 `epStatus` 改成 `ep_status` → 失败信息点名 operation、字段、调用点 `business_http.py:92`。
- [x] **agent 侧漂移会红**：把 `/collections/counts` 手误成 `/collections/count` → 失败信息点名 `collections.py:60`。
  - 注意：`/collections/count` **能**通配匹配到 `/collections/{subjectId}`，所以"能解析到 operation"单独不足以拦截，必须靠"只能通配且无运行时 ID"这条规则。

### CI 与回归

- [x] CI `backend-python` job 新增 `contract drift (agent <-> openapi)` 步骤，位于 `uv run pytest` 之前。
- [x] 契约测试 146 个（HTTP 87 / SSE 29 / pending-action 30）。
- [x] 全量 `uv run pytest -q` → **814 passed**（基线 668 + 契约 146）。
- [x] `backend/agent/app/**`、`backend/business/**`、`frontend/**` 零 diff。

### 文档

- [x] 范围诚实性写入 `.trellis/spec/backend/contract-tests.md` 第 8 节、`tests/contracts/__init__.py`、`drills.md`、`docs/README.md`：本套件只证明 agent ↔ `openapi.yaml` 一致，`openapi.yaml` 为手工维护，**契约 ↔ Java 源码无自动校验**。
- [x] 两次漂移演练原文记录在 `openspec/changes/archive/2026-10-22-add-agent-business-contract-tests/drills.md`。

## Notes

- 契约事实源是 `docs/spec/openapi.yaml`，**手工维护**，不是 springdoc 自动导出；因此「契约 ↔ Java 源码」这条边仍需人工对照。
- 套件只断言 agent **实际发送**的字段，不覆盖无人调用的响应字段（演练中曾改响应体字段而全绿即为此边界）。
- `openspec/specs/` 下三份 spec 与 `.trellis/spec/backend/contract-tests.md` 有意共存：前者是变更归档的历史记录，后者是日常开发读的执行规范。
