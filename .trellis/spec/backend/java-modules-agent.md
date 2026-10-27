# Business Java Agent 模块目标设计

> 从 [目录结构与模块边界](./directory-structure.md) 拆出（2026-10-22）。原文件把三个 Java 模块的完整七段式混在一起（36KB），按模块拆开便于按需注入。
> 模块边界总览、Business 现状对照、Python Agent 结构与 `app/rag` 拆分仍在主文件。

## Business Java Agent 模块目标设计

状态：已实施；Java Agent HTTP/SSE 与导入网关已归 agent，app 负责装配。此处 agent 指 backend/business/agent，不改变 Python backend/agent 内部架构。

### 1. Scope / Trigger

Java agent 统一负责与 Python Agent 的 HTTP/SSE 通信。现有 ClientAgentController、AdminAgentController、AgentService 继续承担代理职责；导入通信接口及实现一并迁入 agent。admin 保留管理权限、导入业务校验、导入状态和记录查询。

### 2. Signatures / 迁移入口

保留 `void runImport(String authorization, ImportRunDTO request)`，请求类型仍在 pojo。

| 当前来源 | 目标 |
|---|---|
| agent.gateway.ImportAgentGateway | agent 的公开导入通信接口 |
| agent.gateway.HttpImportAgentGateway | agent 内部 HTTP 实现 |
| pojo.dto.imprt.ImportRunDTO | 继续归 pojo |
| admin.service.impl.ImportServiceImpl | 保留 admin 业务流程，更新接口引用 |

### 3. Contracts

- 依赖单向为 admin → agent，agent 不依赖 admin/client 的接口或实现，DTO/VO/Entity 使用 pojo。
- app 装配模块并提供 URL、超时与 HTTP 客户端。迁入的 HttpImportAgentGateway 不得继续引用 app.config.AgentProperties，应通过构造器接受所需普通参数。
- POST 保持 mode、key、since、workers 查询参数、可选参数省略规则、URI 编码及 Authorization 透传。
- 模式校验和 season/key、since/since 要求留在 admin；导入记录 Mapper 与统计查询不迁入 agent 或 infrastructure。
- 已有普通代理与 SSE 的序列化、请求追踪、超时和转发行为保持一致。导入错误映射与通用代理不同，不能为复用强制统一。
- chat run 的 client/admin 三路由由 `AgentApiPaths.CLIENT_RUNS/ADMIN_RUNS` 与既有 sessions 常量组成；GET 重连通过 `AgentService.streamGet(path, query, authorization, lineConsumer)` 转发，`after` 只作为查询参数，不写 GET 请求体。SSE 写出统一由 `AgentSseResponseWriter` 延迟到上游首行后提交。
- 通用代理上游 409 转换为 `BizException(ErrorType.CONFLICT, 中文消息, detail)`，由 `GlobalExceptionHandler` 输出 HTTP 409 统一信封；`data` 是上游 `detail` 对象，原始上游正文不得拼入 message。其他 4xx/5xx 映射不变。
- 复用现有 HTTP 实现，迁移接口、调用方、配置和测试，不保留旧 app 实现副本。

### 4. Validation & Error Matrix

| 条件 | 保留语义 |
|---|---|
| 不支持的 mode，或 season 缺 key / since 缺 since | admin 返回 BAD_REQUEST，不调用上游 |
| 上游 409 | CONFLICT，已有导入任务运行中 |
| 其他上游 4xx / 5xx | 分别为 BAD_REQUEST / INTERNAL_ERROR |
| 网络连接失败 | INTERNAL_ERROR，Agent 导入服务连接失败 |
| 通用代理上游 409 | HTTP 409 + `{code,message,data}`；`data` 保留 `active_run_id` 等 detail 字段，解析失败时 data 为空 |
| 通用代理 GET run 重连 | GET + `after` 查询；无请求体/JSON Content-Type；上游首行前不提交响应 |

导入网关当前已将非 409 上游 HTTP 错误转换为通用消息，不拼接上游错误正文；仍需补齐错误分类与正文不泄露的回归测试。

### 5. Good / Base / Bad Cases

- Good：admin 校验后调用 agent 的接口，agent 使用 pojo 请求与 Python 通信，app 提供配置。
- Base：保留既有代理 Controller/Service，迁入散落在 admin/app 的导入通信代码。
- Bad：admin 依赖 agent，但 agent 仍实现 admin 内的接口，或仍注入 app 的 Properties 类型。

### 6. Tests Required

- 边界：admin 可依赖 agent，agent 不依赖 admin/client/app；旧接口和实现引用同步清理。
- 请求：模式校验、可选参数、URI 编码、Authorization 透传。
- 错误：409、其他 4xx/5xx、网络失败保持分类，敏感错误正文不泄露。
- 回归：装配唯一，普通代理和 SSE 超时/透传测试继续通过。
- run 代理：client/admin 三路由的 path/method/query、GET 无 body、409 detail 进入 data、上游错误前不取 writer；`tests/contracts/test_run_route_contract.py` 钉住 OpenAPI 六条路由。

### 7. Wrong vs Correct

- Wrong：admin → agent → admin，或 app → agent → app。
- Correct：admin → agent → pojo/common，app 单向装配下层模块；按实际使用显式声明依赖。

证据：`backend/business/admin/src/main/java/top/zhaizz/admin/service/impl/ImportServiceImpl.java`、`backend/business/agent/src/main/java/top/zhaizz/agent/gateway/ImportAgentGateway.java`、`backend/business/agent/src/main/java/top/zhaizz/agent/gateway/HttpImportAgentGateway.java`。
