# 错误处理规范

## Java Business

- 统一响应为 `Result<T>{code,message,data}`，HTTP 状态码与 `code` 相同；分页数据包在 `PageResult<T>` 内。
- Service 业务失败抛 `BizException(ErrorType, 中文消息[, data])`，禁止裸整数错误码。
- `GlobalExceptionHandler` 处理业务、校验、MVC、数据库约束和未知异常；未知异常只向客户端返回通用 500。
- Spring Security filter 中的 401/403 不经过 Controller advice，由 `SecurityConfig.writeJson` 直接输出同形 JSON。
- Controller 不捕获再包装业务异常；让统一处理器保留状态码与日志策略。

参考：`common/result/Result.java`、`common/exception/GlobalExceptionHandler.java`、`common/constant/ErrorType.java`。

## Python Agent

- HTTP 边界使用 FastAPI `HTTPException` 表达认证、权限和资源归属错误。
- `HttpBusinessGateway` 将 Business 超时、HTTP 错误和网络错误归一为 `{"error": true, "code"?, "message"}`。
- 工具必须检查 `error`，不能把错误字典当正常业务数据继续推理。
- SSE 执行异常映射为安全中文提示，内部异常类型只进入结构化日志。
- `asyncio.CancelledError` 表示客户端断开，不应记录成普通 500。

## 客户端可见信息

- 可以返回字段校验提示、登录过期、无权限、资源不存在和可执行的业务冲突。
- 不返回 SQL、堆栈、文件路径、对象存储详情、上游响应体、JWT 或密钥。
- 外部服务失败转换为领域化消息，例如“Agent 导入服务连接失败”。
- 409 用于唯一约束或状态冲突；404 只在明确语义下可被工具解释为“不存在”。
- 写操作结果不确定时不要假报成功，也不要清理可重试的待确认状态。

## 常见错误

- Controller 返回 HTTP 200，但 body 中塞非 200 错误码。
- Python 工具用裸 `except Exception: return {}` 吞掉失败。
- 把上游完整错误体拼入面向用户的消息。
- 为局部场景新建另一套响应结构。
