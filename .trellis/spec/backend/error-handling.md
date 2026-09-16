# 错误处理、日志与可观测性

同层相关规范按主题合并；目标设计与当前实现的状态标记保留，各章节约束继续有效。

- [错误处理规范](#错误处理规范)
- [日志与可观测性规范](#日志与可观测性规范)

## 错误处理规范

### Java Business

- 统一响应为 `Result<T>{code,message,data}`，HTTP 状态码与 `code` 相同；分页数据包在 `PageResult<T>` 内。
- Service 业务失败抛 `BizException(ErrorType, 中文消息[, data])`，禁止裸整数错误码。
- `GlobalExceptionHandler` 处理业务、校验、MVC、数据库约束和未知异常；未知异常只向客户端返回通用 500。
- Spring Security filter 中的 401/403 不经过 Controller advice，由 `SecurityConfig.writeJson` 直接输出同形 JSON。
- Controller 不捕获再包装业务异常；让统一处理器保留状态码与日志策略。

参考：`common/result/Result.java`、`app/web/GlobalExceptionHandler.java`、`common/constant/ErrorType.java`。

### common / app 异常边界（已实施）

#### 1. Scope / Trigger

已确认：common 只保留结果、分页、错误类型等基础定义；GlobalExceptionHandler 等 HTTP 异常适配已迁入 app.web。本节规则已实施，当前源码路径以 app.web 为准。

#### 2. Signatures

- `BizException(ErrorType, 中文消息[, data])`、`Result<T>`、`PageResult<T>`、`ErrorType` 留在 common。
- 当前 `app.web.GlobalExceptionHandler.handleBizException(BizException)` 返回 `ResponseEntity<Result<Object>>`，保留既有处理方法与响应契约。
- Controller/Service 不引用处理器实现，由 app 注册统一 `@RestControllerAdvice`；Security filter 的错误继续由安全配置处理。

#### 3. Contracts

- HTTP 状态和 `{code,message,data}` 保持一致，不因内部包迁移改变前端协议。
- 业务模块抛 common 的业务异常，不捕获后重新包装，不依赖 app。
- app 接管现有处理器和相关装配/测试；旧 common 处理器不留作第二个生效副本。MVC 类型、Servlet/ResponseEntity 等 HTTP 适配依赖不应因该处理器继续留在 common。

#### 4. Validation & Error Matrix

| 情况 | 保留语义 |
|---|---|
| BizException | 对应 HTTP 状态、消息及 data |
| 参数校验失败 | 400，保留字段提示或约束提示及既有 data 结构 |
| 方法级无权限 / 数据库约束冲突 | 分别 403 / 409 |
| 不支持方法 / 媒体类型 / 上传超限 | 分别 405 / 415 / 413 |
| 未找到资源 / 未知异常 | 分别 404 / 通用 500，未知异常不暴露内部信息 |

#### 5. Good / Base / Bad Cases

- Good：业务抛 BizException，由 app 的统一处理器输出 HTTP 响应。
- Base：只改变所有权、包引用和依赖，保留现有异常分类。
- Bad：为了复用异常处理而让 client 依赖 app，或把整个 Web starter 留在 common 继续传递。

#### 6. Tests Required

- 通过 app 上下文验证 advice 唯一生效，业务、校验、MVC、约束冲突和未知异常的 HTTP/body 一致。
- 分别验证 Controller advice 与 Security filter 的 401/403 路径，不能把两条处理链误合并。
- 检查 common 不再依赖迁出处理器所需的运行时框架，业务模块不反向依赖 app；迁移相关旧测试。

#### 7. Wrong vs Correct

- Wrong：common 内同时维护 BizException 和依赖 Web/Security/数据库框架的全局处理器。
- Correct：common 提供错误定义，app 负责 HTTP 协议适配；安全认证机制仍由 auth 承担。

### Python Agent

- HTTP 边界使用 FastAPI `HTTPException` 表达认证、权限和资源归属错误。
- `HttpBusinessGateway` 将 Business 超时、HTTP 错误和网络错误归一为 `{"error": true, "code"?, "message"}`。
- 工具必须检查 `error`，不能把错误字典当正常业务数据继续推理。
- SSE 执行异常映射为安全中文提示，内部异常类型只进入结构化日志。
- `asyncio.CancelledError` 表示客户端断开，不应记录成普通 500。

### 已实现边界与待治理项（2026-09-12）

- `backend/agent/app/agent/client/rag_tools.py::_items` 对不可用结果返回 `{available:false, reason, items:[]}`，正常无结果仍为 `[]`；调用方必须保留该区别，不能把故障伪装为空结果。
- `backend/agent/app/adapters/business_http.py::request` 对网络异常拼接 `str(e)`，对 HTTP 错误沿用上游 message；并未保证全部错误正文脱敏。成功非对象 JSON 和非 JSON 响应也缺少完整归一化，不得声称 Gateway 已覆盖任意上游响应。
- `backend/agent/app/chat/streaming.py` 捕获回答落库、PendingAction 持久化回调异常后记录结构化异常并发送 `status` 错误事件，再结束流；客户端应将其视为可重试的部分失败，不能显示为保存成功。

### 客户端可见信息

- 可以返回字段校验提示、登录过期、无权限、资源不存在和可执行的业务冲突。
- 不返回 SQL、堆栈、文件路径、对象存储详情、上游响应体、JWT 或密钥。
- 外部服务失败转换为领域化消息，例如“Agent 导入服务连接失败”。
- 409 用于唯一约束或状态冲突；404 只在明确语义下可被工具解释为“不存在”。
- 写操作结果不确定时不要假报成功，也不要清理可重试的待确认状态。

### 常见错误

- Controller 返回 HTTP 200，但 body 中塞非 200 错误码。
- Python 工具用裸 `except Exception: return {}` 吞掉失败。
- 把上游完整错误体拼入面向用户的消息。
- 为局部场景新建另一套响应结构。

## 日志与可观测性规范

### 请求链路

- Business 的 `RequestIdFilter` 校验或生成 `X-Request-ID`，写入 MDC 与响应头。
- Spring 代理 Agent 时继续透传该请求头；Python `HttpBusinessGateway` 回查 Business 时也透传。
- Agent 的 `trace_context_middleware` 使用 ContextVar 保存 traceId，并在 `finally` 清理。
- 合法请求 ID 只允许 `[A-Za-z0-9._-]` 且不超过 128 字符，非法值生成 UUID。
- 排查跨服务问题先按同一 traceId 关联日志，不靠用户输入全文搜索。

### Business 日志

- `logback-spring.xml` 输出单行 JSON；生产代码使用 SLF4J，不用 `System.out`。
- 业务异常、校验失败和权限失败用 warn；未知异常与基础设施不可用用 error 并保留服务端堆栈。
- 管理写操作用 `@OperationLog`，字段抽取和脱敏由 `OperationLogAspect` 统一处理。
- 操作常量集中在 `OperationLogConstants`，不要在 Controller 重复字符串。
- 参数日志必须脱敏 password、code、token 等字段。

### Business 操作日志模块（已实施设计）

#### 1. Scope / Trigger

Business 新增 `log` Maven 模块，统一负责操作日志采集、存储、清理和查询能力；`admin` 保留管理端接口、权限校验及面向管理端的 VO 转换。本节记录的目标边界已实施；日志模块测试与 Business reactor 测试均通过。应用运行日志、请求追踪与 Python 日志不因名称相近自动迁入此模块。

#### 2. Signatures / 迁移入口

- 当前入口：`OperationLogAspect.around(ProceedingJoinPoint, OperationLog)`、`OperationLogCleanupTask.cleanup()`、`AdminLogServiceImpl.listLogs(LogQueryDTO)`。
- 实现映射：`log.annotation`、`log.aspect`、`log.task` 承载操作日志注解、切面和清理任务；`log.mapper` 承载日志持久化与统计查询；admin 仅保留管理端 Service 和 VO 转换。
- 目标调用关系：`admin` 的业务服务调用 `log` 对外查询服务；分页、统计筛选与数据库访问由 `log` 封装。管理端不直接引用 `log` 内部 Mapper 或构造数据库查询条件。
- Entity/DTO/VO 统一由 pojo 管理，包括 OperationLog、LogQueryDTO、LogQueryResultDTO、LogVO；当前查询入口为 `LogQueryService.query(LogQueryDTO)`。

#### 3. Contracts / 职责与依赖

- `client/admin` 使用 `log` 提供的采集入口；`admin` 使用其查询能力，管理权限仍由 `admin` 负责。
- 已确认 `log → auth → infrastructure → common`。日志切面保留在 log，通过 auth 的公开身份读取能力获取当前用户；auth 不反向依赖 log。log 不依赖 client/admin/agent/app 的实现，app 负责组合装配。
- 日志分页与统计必须使用一致筛选语义：action、module、username、userId、status，以及 start 当日零点（含）至 end 次日零点（不含）。
- 保留当前成功状态 0、失败状态 1；清理任务保持每日 03:30 执行，删除创建时间早于当前时间减 90 天的记录，不擅自改变时区或保留期。
- 管理端 VO 转换继续放在 `admin.converter`；日志内部纯转换如有需要放在 `log.converter`，遵循目录规范的 Converter 规则。

#### 4. Validation & Error Matrix

| 条件 | 必须保持的行为 |
|---|---|
| 操作日志写入失败 | 告警，不改变原业务返回值或异常 |
| 原业务抛出异常 | 记录失败状态并继续抛出原异常 |
| start/end 缺失 | 不构造相应日期条件，不提前解引用空日期 |
| 无管理权限 | 在管理端鉴权边界拒绝，不通过新查询入口绕过权限 |

日志查询失败不等同于旁路采集失败，不能为了复用采集容错而伪造空列表成功响应。脱敏必须遵循本文隐私红线；当前切面不采集请求参数、输入用户名、User-Agent 或原始异常消息，后续扩展采集字段时仍须逐项审查。

#### 5. Good / Base / Bad Cases

- Good：admin 完成权限与请求处理，通过 log 查询服务获取分页和统计结果，再调用自己的 Converter 输出。
- Base：client/admin 通过统一注解采集；log 内部完成存储与清理，保持现有行为。
- Bad：只搬走 OperationLogMapper，admin 仍直接依赖它并维护另一套筛选条件；或让 log 依赖 AdminLogServiceImpl。

#### 6. Tests Required

- 边界验证：client/admin 不依赖 log 内部 Mapper；log 不依赖 client/admin/agent/app 实现；允许 log → auth，禁止 auth → log；匿名采集不因身份缺失中断原业务。
- 日志采集：成功/失败状态正确，写入失败不覆盖业务返回值或原异常；敏感字段不泄露。
- 查询：分页与统计在相同筛选条件下吻合，覆盖空日期和结束日期边界；管理端鉴权和响应字段保持一致。
- 清理：90 天阈值采用严格早于比较，任务只装配一次。

#### 7. Wrong vs Correct

- Wrong：`admin → OperationLogMapper / AdminLogMapper`，业务层直接拼装数据库筛选。
- Correct：`admin → log 查询服务 → log 内部 Mapper`，管理端权限与 VO 转换仍留在 admin。

证据：`backend/business/log/src/main/java/top/zhaizz/log/aspect/OperationLogAspect.java`、`backend/business/log/src/main/java/top/zhaizz/log/task/OperationLogCleanupTask.java`、`backend/business/log/src/main/java/top/zhaizz/log/service/LogQueryService.java`、`backend/business/admin/src/main/java/top/zhaizz/admin/service/impl/AdminLogServiceImpl.java`。

### Agent 日志

- 默认单行 JSON；仅本地可用 `ANIMETRACKER_LOG=human` 切换终端格式。
- 结构化事件统一走 `log_event`，字段必须在 `_ALLOWED_FIELDS` 白名单中。
- session/user 当前使用固定 salt 的 SHA-256 截断到 16 个十六进制字符，不记录原值。这是伪名化而非不可逆匿名化保证；低熵 ID 仍可枚举，禁止因此把日志视为无敏感风险。
- RAG 事件名和字段使用独立白名单，避免动态数据污染日志协议。
- 记录耗时、模型、工具名、路由和归一化错误类型，不记录内容正文。

证据：`backend/agent/app/shared/observability.py::hash_value/log_event`。`rag.evidence.enriched` 调用中的 `expectedCount/actualCount` 未列入 `_RAG_ALLOWED_FIELDS`，因此当前会被过滤；不能在运维文档中要求从现有日志读取这些字段。

Java `GlobalExceptionHandler` 的部分 warn 仍直接记录 `e.getMessage()`；白名单只约束 Python `log_event`，不自动脱敏其他 logger 或异常堆栈。后续修复应保留可定位错误类别并避免记录原始 SQL/请求敏感值。

### 隐私红线

禁止记录用户输入、完整回答、JWT、API Key、Cookie、密码、验证码、工具参数和完整 Business 响应体。新增日志字段前先检查 `app/shared/observability.py` 的白名单与此红线。
