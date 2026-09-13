# 跨层契约与代码复用检查

同层相关规范按主题合并；目标设计与当前实现的状态标记保留，各章节约束继续有效。

- [跨层契约检查指南](#跨层契约检查指南)
- [代码复用检查指南](#代码复用检查指南)

## 跨层契约检查指南

### 先画真实数据流

```text
React client/admin
  → /api/**（shared API / SSE fetch）
  → Spring Controller → Service → Mapper/Store
  → MySQL / Redis / MinIO
  ↘ Spring Agent proxy → FastAPI → LangGraph → BusinessGateway ↗
```

不要只验证改动所在文件；AnimeTracker 的高风险问题集中在代理、类型和状态边界。

### 事实来源与冲突裁决

发生字段、状态或错误语义冲突时，按以下优先级处理：

1. 可执行源码、配置和测试（Controller/Router、DTO/VO、Pydantic、shared API/types、回归测试）。
2. OpenAPI 与数据库 Schema（用于跨层目标契约和结构基线，但必须核对实现）。
3. README、手工示例和历史说明。

发现冲突必须在同一变更中修正文档，并在审查记录中注明验证命令和核对日期；不能以 README 覆盖已存在的测试或源码事实。

测试文件也需核对导入和可执行性：2026-09-10 曾发现能力路由测试引用缺失符号；2026-09-12 的既有质量记录说明该测试已重写。此处保留历史教训，不将旧失败描述为当前状态；本次文档合并未重新运行测试。

### JSON API 变更

1. 修改 Java DTO/VO/Controller 或 Python Pydantic schema。
2. 更新 `docs/spec/openapi.yaml` 的路径、字段、状态码和示例。
3. 更新 `frontend/packages/shared/src/types` 与对应 API 命名空间。
4. 检查 Query key、表单、空值和错误渲染。
5. 运行前端 typecheck、相关测试和后端测试。

统一 Java 响应为 `{code,message,data}`，shared Axios 拦截器会直接返回 `data`；页面不能再解包一次。

当前 OpenAPI 是手工维护，CI 未自动证明它与三端一致；涉及路径、字段、状态码、Cookie、鉴权或追踪头时，必须把 OpenAPI、Java/Python 实现和 shared 类型逐项对照，并记录未同步项为已知债务。

### 认证链路

- 登录/刷新由 Spring 负责；Access Token 返回前端内存，refresh session 写 HttpOnly Cookie。
- shared request interceptor 添加 Bearer Token；401 通过 coordinator 单次刷新并重放。
- Spring Security 校验 client/admin 权限，再将 token 透传给 Agent。
- Agent 本地验签并从 claim 提取 userId/role，BusinessGateway 回查时继续透传 token。
- 修改 claim、Cookie path、CORS Origin 或 API 前缀时必须端到端验证。

### SSE 变更

- Python `AgentEvent` 是领域事件，`api/sse.py` 转换为 wire schema。
- Spring 代理必须保留流式响应，不能缓冲成普通 JSON。
- shared `streamSse` 负责分行，`useAgentChat` 负责事件状态机。
- 新事件需要兼容旧消费者或同步发布前端。
- 验证增量文本、工具 start/end、结束标记、Abort 和网络中断。
- wire 响应必须声明 `text/event-stream`，以空行分帧；每帧 `data:` JSON 至少包含 `type`、`content`、`is_end`，并按 `answer|thinking|function_call|status|end` 联合类型演进。
- `function_call.state` 的 `start|end|error` 必须在前端映射为 running → done/error；结束事件或 `is_end=true` 后不得继续写入消息。
- 当前 `docs/spec/openapi.yaml` 未完整表达 SSE content type、事件联合、刷新 Cookie、Bearer security 和 `X-Request-ID`；这是契约债务，本轮只在 spec 中记录，改动 API 时必须同步修复。

### Agent 写操作

```text
预览 → Redis PendingAction → 用户确认 → 注入系统参数 → Business 幂等写入
```

任何一层都不能绕过确认。重点验证 action 的 user/session 归属、TTL、preview 变化、部分失败和基础设施不确定性。

- Redis 写入失败不得被当作成功确认；若替换旧动作失败，必须使旧版本失效或清除，避免下一次确认执行旧动作。
- 最低失败路径：预存旧动作 → 替换失败 → 再次确认；断言 Business 没有收到旧动作。

### 数据与日志

- Schema 是表结构事实来源；字段变更同步 Java、Python importer/indexer、OpenAPI 与 TypeScript。
- `db-schema.sql` 含破坏性 `DROP TABLE IF EXISTS`，仅限明确确认的空库初始化；存量库必须采用备份、前向 ALTER/回填、兼容部署和回滚计划。
- `X-Request-ID` 从浏览器入口贯穿 Spring、Agent 和回查 Business。
- 日志禁止用户输入、完整回答、token、Cookie、Key、验证码和工具参数。
- 失败消息对用户可执行，内部细节只留服务端。
- 跨层验证至少覆盖一个成功路径与一个权限/失败路径。
- 每次跨层变更结束前核对：本指南列出的源码路径、受影响 spec、验证命令和已知债务是否同步。

### RAG 版本与发布链

- 画出 `indexer → MySQL search_document → Redis Vector Set → MySQL search_index_release → Business lexical → Agent RRF → Evidence` 的真实数据流，并标出 `indexVersion/profileVersion` 在每一跳的来源。
- 区分三个状态：索引 shadow 已构建、MySQL release 已 `ACTIVE`、Agent `RAG_ENABLED` 已开启；不能用其中一个状态代替另外两个。
- 发布前核对 quality/capacity/eval/latency/human 五份同版本报告和 gate 阈值；发布后记录至少 24 小时灰度窗口与回滚结果。
- 回滚必须同时检查功能开关和 MySQL release 指针，保留旧投影；Redis alias 不是发布或回滚事实。
- 详细字段、错误矩阵、测试路径和 Wrong/Correct 示例见 [RAG 检索与版本发布契约](../backend/rag-retrieval-contract.md)。

### Agent 回答异常的跨层核对

- 按 `JWT role → graph.py 节点 → tools 注册 → Prompt 来源/缓存 → 模型 delta → SSE → shared Hook → client/admin UI` 检查，不从单条自然语言回答推断后端能力。
- 管理员节点当前没有 rag_*，客户端有；RAG 总开关与 ACTIVE release 又分别影响执行路径。权限边界不能靠提示词绕过。
- 中文提示词、英文 reasoning 过滤、中文处理状态是不同机制；当前源码只有提示词约束与原始 reasoning 转发。不得把固定状态文本描述成模型原始思考。
- 季度映射须核对 Java SeasonUtil 与 Python planner/filter；当前两端映射不一致。首播日期也不能证明已经完结。
- 详细源码与验证缺口见 [Agent 运行与提示词契约](../backend/agent-guidelines.md#agent-角色提示词与流式输出契约)。

## 代码复用检查指南

### 写代码前搜索

```bash
rg "业务关键词|接口路径|字段名" frontend backend docs
rg "interface|class|def|export" 目标目录
```

先定位所有者，再决定复用、扩展或新建；不要按文件名猜测不存在。

### 已有单一来源

| 领域 | 所有者 |
|---|---|
| 前端跨应用 API 与类型 | `frontend/packages/shared/src` |
| Java 常量 | 通用协议基础定义可在 common；认证、日志、Agent、业务 Redis 键归对应所有者，见后端架构目标规范 |
| Agent 上游路径 | `AgentApiPaths.java`，并与 Python Router 同步 |
| 数据库结构 | `docs/database/db-schema.sql` |
| Agent 事件与 SSE | `app/chat/events.py`、`app/api/sse.py` |
| 外部系统抽象 | Java Gateway / Python Protocol + adapters |

### 应该复用或扩展

- client/admin 都需要的 API、类型、主题、鉴权或 SSE 能力进入 shared。
- Java 按已确认的目标边界组织外部能力：通用技术接口与现有实现归 infrastructure，Python Agent 通信接口与实现归 Java agent，app 负责装配；旧“消费模块 Gateway + app.infrastructure”仅为迁移前现状。详见 [后端架构](../backend/directory-structure.md)。
- Java DTO/VO/Entity 统一归 pojo；Converter 归各消费模块，不因共享数据类型而集中转换逻辑。ServiceImpl/Controller 内的纯映射按目标规范迁出。
- Python 新后端沿用领域端口，在 `app/adapters` 增加实现。
- 新日志事件沿用现有白名单和 trace context，不创建第二套 logger 协议。

### 不要过早抽象

- 仅一个页面使用且逻辑简单的展示状态保留本地。
- client/admin 视觉相似但业务与交互不同，不因“看起来像”强行共享整页。
- 单次可读常量不必提取；跨模块契约常量必须集中。
- 两个外部服务错误语义不同，不要只为减少行数合并异常处理。
- 抽象不能隐藏预览确认、权限或事务边界。

### 重复警报

出现以下任一情况先停下搜索：

1. 同一路径或字段结构在两个应用重复声明。
2. 多处把同一未知 payload 强转成不同类型。
3. Controller/Router 重复拼装相同响应或错误。
4. 多个 Agent 工具各自实现 token/header/trace 透传。
5. 同一状态值在 Java、Python、TypeScript 中出现不一致拼写。

复用后仍要运行所有受影响工作区的检查，公共代码通过自身测试不代表两个消费者都兼容。
