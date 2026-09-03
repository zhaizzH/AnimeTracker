# 跨层契约检查指南

## 先画真实数据流

```text
React client/admin
  → /api/**（shared API / SSE fetch）
  → Spring Controller → Service → Mapper/Store
  → MySQL / Redis / MinIO
  ↘ Spring Agent proxy → FastAPI → LangGraph → BusinessGateway ↗
```

不要只验证改动所在文件；AnimeTracker 的高风险问题集中在代理、类型和状态边界。

## 事实来源与冲突裁决

发生字段、状态或错误语义冲突时，按以下优先级处理：

1. 可执行源码、配置和测试（Controller/Router、DTO/VO、Pydantic、shared API/types、回归测试）。
2. OpenAPI 与数据库 Schema（用于跨层目标契约和结构基线，但必须核对实现）。
3. README、手工示例和历史说明。

发现冲突必须在同一变更中修正文档，并在审查记录中注明验证命令和核对日期；不能以 README 覆盖已存在的测试或源码事实。

## JSON API 变更

1. 修改 Java DTO/VO/Controller 或 Python Pydantic schema。
2. 更新 `docs/spec/openapi.yaml` 的路径、字段、状态码和示例。
3. 更新 `frontend/packages/shared/src/types` 与对应 API 命名空间。
4. 检查 Query key、表单、空值和错误渲染。
5. 运行前端 typecheck、相关测试和后端测试。

统一 Java 响应为 `{code,message,data}`，shared Axios 拦截器会直接返回 `data`；页面不能再解包一次。

当前 OpenAPI 是手工维护，CI 未自动证明它与三端一致；涉及路径、字段、状态码、Cookie、鉴权或追踪头时，必须把 OpenAPI、Java/Python 实现和 shared 类型逐项对照，并记录未同步项为已知债务。

## 认证链路

- 登录/刷新由 Spring 负责；Access Token 返回前端内存，refresh session 写 HttpOnly Cookie。
- shared request interceptor 添加 Bearer Token；401 通过 coordinator 单次刷新并重放。
- Spring Security 校验 client/admin 权限，再将 token 透传给 Agent。
- Agent 本地验签并从 claim 提取 userId/role，BusinessGateway 回查时继续透传 token。
- 修改 claim、Cookie path、CORS Origin 或 API 前缀时必须端到端验证。

## SSE 变更

- Python `AgentEvent` 是领域事件，`api/sse.py` 转换为 wire schema。
- Spring 代理必须保留流式响应，不能缓冲成普通 JSON。
- shared `streamSse` 负责分行，`useAgentChat` 负责事件状态机。
- 新事件需要兼容旧消费者或同步发布前端。
- 验证增量文本、工具 start/end、结束标记、Abort 和网络中断。
- wire 响应必须声明 `text/event-stream`，以空行分帧；每帧 `data:` JSON 至少包含 `type`、`content`、`is_end`，并按 `answer|thinking|function_call|status|end` 联合类型演进。
- `function_call.state` 的 `start|end|error` 必须在前端映射为 running → done/error；结束事件或 `is_end=true` 后不得继续写入消息。
- 当前 `docs/spec/openapi.yaml` 未完整表达 SSE content type、事件联合、刷新 Cookie、Bearer security 和 `X-Request-ID`；这是契约债务，本轮只在 spec 中记录，改动 API 时必须同步修复。

## Agent 写操作

```text
预览 → Redis PendingAction → 用户确认 → 注入系统参数 → Business 幂等写入
```

任何一层都不能绕过确认。重点验证 action 的 user/session 归属、TTL、preview 变化、部分失败和基础设施不确定性。

- Redis 写入失败不得被当作成功确认；若替换旧动作失败，必须使旧版本失效或清除，避免下一次确认执行旧动作。
- 最低失败路径：预存旧动作 → 替换失败 → 再次确认；断言 Business 没有收到旧动作。

## 数据与日志

- Schema 是表结构事实来源；字段变更同步 Java、Python importer/indexer、OpenAPI 与 TypeScript。
- `db-schema.sql` 含破坏性 `DROP TABLE IF EXISTS`，仅限明确确认的空库初始化；存量库必须采用备份、前向 ALTER/回填、兼容部署和回滚计划。
- `X-Request-ID` 从浏览器入口贯穿 Spring、Agent 和回查 Business。
- 日志禁止用户输入、完整回答、token、Cookie、Key、验证码和工具参数。
- 失败消息对用户可执行，内部细节只留服务端。
- 跨层验证至少覆盖一个成功路径与一个权限/失败路径。
- 每次跨层变更结束前核对：本指南列出的源码路径、受影响 spec、验证命令和已知债务是否同步。
