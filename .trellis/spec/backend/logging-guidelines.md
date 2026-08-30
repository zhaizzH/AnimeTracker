# 日志与可观测性规范

## 请求链路

- Business 的 `RequestIdFilter` 校验或生成 `X-Request-ID`，写入 MDC 与响应头。
- Spring 代理 Agent 时继续透传该请求头；Python `HttpBusinessGateway` 回查 Business 时也透传。
- Agent 的 `trace_context_middleware` 使用 ContextVar 保存 traceId，并在 `finally` 清理。
- 合法请求 ID 只允许 `[A-Za-z0-9._-]` 且不超过 128 字符，非法值生成 UUID。
- 排查跨服务问题先按同一 traceId 关联日志，不靠用户输入全文搜索。

## Business 日志

- `logback-spring.xml` 输出单行 JSON；生产代码使用 SLF4J，不用 `System.out`。
- 业务异常、校验失败和权限失败用 warn；未知异常与基础设施不可用用 error 并保留服务端堆栈。
- 管理写操作用 `@OperationLog`，字段抽取和脱敏由 `OperationLogAspect` 统一处理。
- 操作常量集中在 `OperationLogConstants`，不要在 Controller 重复字符串。
- 参数日志必须脱敏 password、code、token 等字段。

## Agent 日志

- 默认单行 JSON；仅本地可用 `ANIMETRACKER_LOG=human` 切换终端格式。
- 结构化事件统一走 `log_event`，字段必须在 `_ALLOWED_FIELDS` 白名单中。
- session/user 只记录不可逆短哈希，不记录原值。
- RAG 事件名和字段使用独立白名单，避免动态数据污染日志协议。
- 记录耗时、模型、工具名、路由和归一化错误类型，不记录内容正文。

## 隐私红线

禁止记录用户输入、完整回答、JWT、API Key、Cookie、密码、验证码、工具参数和完整 Business 响应体。新增日志字段前先检查 `app/shared/observability.py` 的白名单与此红线。
