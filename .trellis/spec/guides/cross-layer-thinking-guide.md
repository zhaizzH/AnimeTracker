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

## JSON API 变更

1. 修改 Java DTO/VO/Controller 或 Python Pydantic schema。
2. 更新 `docs/spec/openapi.yaml` 的路径、字段、状态码和示例。
3. 更新 `frontend/packages/shared/src/types` 与对应 API 命名空间。
4. 检查 Query key、表单、空值和错误渲染。
5. 运行前端 typecheck、相关测试和后端测试。

统一 Java 响应为 `{code,message,data}`，shared Axios 拦截器会直接返回 `data`；页面不能再解包一次。

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

## Agent 写操作

```text
预览 → Redis PendingAction → 用户确认 → 注入系统参数 → Business 幂等写入
```

任何一层都不能绕过确认。重点验证 action 的 user/session 归属、TTL、preview 变化、部分失败和基础设施不确定性。

## 数据与日志

- Schema 是表结构事实来源；字段变更同步 Java、Python importer/indexer、OpenAPI 与 TypeScript。
- `X-Request-ID` 从浏览器入口贯穿 Spring、Agent 和回查 Business。
- 日志禁止用户输入、完整回答、token、Cookie、Key、验证码和工具参数。
- 失败消息对用户可执行，内部细节只留服务端。
- 跨层验证至少覆盖一个成功路径与一个权限/失败路径。
