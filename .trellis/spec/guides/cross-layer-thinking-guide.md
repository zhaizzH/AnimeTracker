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

测试文件也需核对导入和可执行性：2026-09-10 曾发现能力路由测试引用缺失符号；2026-09-12 的既有质量记录说明该测试已重写。此处保留历史教训，不将旧失败描述为当前状态；2026-09-16 本轮复核重新运行了 Business Java 测试和 Javadoc 检查，结果见 [后端质量门禁](../backend/quality-guidelines.md#当前测试基线)。

**环境事实不写进 spec。** spec 只缓存「查不到的东西」（约定、取舍理由、踩过的坑）；一次查找就能得到的照抄进来只会变成陈旧副本。典型读错案例：`quality-guidelines.md` 曾手写「CI 跑哪几步」，而 `ci.yml` 早已多了 `npm test` 与 `npm run build`；也曾在同一节里并存 862/125 与 814/111 两套测试通过数。同类不要抄的：`ci.yml` 的步骤与版本、`package.json` 的 scripts、目录布局、依赖清单。写「以 `<文件>` 为准」给指针，不复制内容。

**写环境事实前先跑一次能读到该事实的命令。** 源码里「支持 X」不等于本机「X 生效」。2026-10-27 的实例：`resolvePiCli()` 确实优先读 `TRELLIS_PI_CLI_JS`，据此把环境变量写成首选解法并发文；实测 `echo "[$TRELLIS_PI_CLI_JS]"` → `[]`，该值从未到达进程（`setx` 只写注册表，不会补给已存在的父进程链）。代价是两次让人重启 + 整篇文档重写。一条命令就能提前推翻结论。

### JSON API 变更

1. 修改 Java DTO/VO/Controller 或 Python Pydantic schema。
2. 更新 `docs/spec/openapi.yaml` 的路径、字段、状态码和示例。
3. 更新 `frontend/packages/shared/src/types` 与对应 API 命名空间。
4. 检查 Query key、表单、空值和错误渲染。
5. 运行前端 typecheck、相关测试和后端测试。

统一 Java 响应为 `{code,message,data}`，shared Axios 拦截器会直接返回 `data`；页面不能再解包一次。

当前 OpenAPI 是手工维护，CI **已能**自动校验 agent↔契约这一侧边界（`backend/agent/tests/contracts/`：每条出站 HTTP 调用的 method+path 必须解析到契约 operation、静态可判定的请求字段必须已声明、SSE 帧与 `SSEFrame` 双向对齐、pending-action 持久化协议由测试锁定，并在 CI 中单独成步）。但**契约↔business Java 源码仍无自动校验**：Java DTO 字段改名而契约没跟着改时，agent 仍匹配（已过时的）契约，套件保持全绿。因此涉及路径、字段、状态码、Cookie、鉴权或追踪头时，仍必须把 OpenAPI 与 Java 实现逐项对照，并记录未同步项为已知债务。

> **改 API 前先想一件事："能解析成功"不等于"拼写正确"。** 路径模板会吃掉拼写错误——`/collections/count` 会静默落到 `/collections/{subjectId}`，让一个不存在的端点看起来合法。所以新增或改动调用点时，先问：
> 1. 是否**字面命中**操作？只能通配命中且调用点本身不含运行时 ID，就是拼写错误的信号，不是合法用法。
> 2. 改的是**请求**还是**响应**字段？字段校验只覆盖 agent 实际发送的请求字段；改一个无人调用的响应字段（如某个 VO 内部字段），契约测试仍会全绿，必须人工核对。
>
> 具体规则、白名单机制与两次漂移演练的原文记录见 [Agent↔Business 契约测试](../backend/contract-tests.md#8-边界声明不要高估这套测试)。

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
- wire 响应必须声明 `text/event-stream`，以空行分帧；每帧 `data:` JSON 至少包含 `type`、`content`、`is_end`。事件 `type` 取值为 `answer|thinking|function_call|status|ui_action` 五值，**不存在 `type=end`**——结束由 `is_end=true` 表达（与 [Agent 运行与提示词契约](../backend/agent-guidelines.md#agent-角色提示词与流式输出契约) 一致）。
- `function_call.state` 的 `start|end` 必须在前端映射为 running → done，失败以 `end` + `result=error` 表达；`state=error` 只出现在 `status` 事件上。结束标记或 `is_end=true` 后不得继续写入消息。
- `docs/spec/openapi.yaml` 已表达 SSE content type（`text/event-stream` + 单帧 `SSEFrame` schema）、事件联合、刷新 Cookie（`at_refresh` + `Set-Cookie`）、Bearer securityScheme（`bearerAuth`）与 `X-Request-ID`；未同步项登记在 `openapi.yaml` 的 `info.description`「已知债务」节与任务 `research/contract-alignment-table.md`。CI 的 `backend-python` job 有一条 `contract drift (agent <-> openapi)` 步骤跑 `pytest tests/contracts`，能拦住 agent 侧路径/字段漂移与契约文件结构损坏；但它不校验契约与 Java 源码是否一致，改动 API 时仍须同步并重新对照。

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
- 季度映射两端已对齐：Java `SeasonUtil` 为权威，Python 唯一词表在 `app/rag/seasons.py`；改动任一端后必须运行 `tests/rag/test_season_alignment.py` 核对。首播日期也不能证明已经完结。
- 详细源码与验证缺口见 [Agent 运行与提示词契约](../backend/agent-guidelines.md#agent-角色提示词与流式输出契约)。

## 项目术语表

跨层共享术语。只定义词汇，不含实现细节与决策理由。新术语在含义被钉死时立即写入，不批量补。

**领域术语已迁至 [`.trellis/spec/GLOSSARY.md`](../GLOSSARY.md)**（Subject、Collection、Evidence、gate、PendingAction 等）。本表只保留**工程约定类**词汇——它们是本项目的做事方式，不是领域概念，故不进 glossary。

| 术语 | 定义 |
|---|---|
| **基线数字** | 历史上指 spec 里带日期的实测测试通过数。**自 2026-10-27 起不再记录于 spec**：数字每次手抄都与实际不一致（152→125 笔误、814 与 862 两段并存），权威结果改由 CI 给出。要引用数字时现场跑 [后端质量门禁](../backend/quality-guidelines.md#当前测试基线) 的命令，**不得沿用历史通过数**。 |
| **move-only 重构** | 只移动代码、不改行为的重构：不改逻辑、参数、fail-closed 语义；私有方法转模块级函数后原类以 `staticmethod` 委托别名保留旧调用点；验收标准为测试数与拆前一致。模板见 [app/rag 模块结构](../backend/directory-structure.md#apprag-模块结构2026-10-05提交-08799fdb)。 |
| **flaky / 测试隔离问题** | 单跑通过、全量偶发失败、重跑全绿的测试；指向测试间状态泄漏或顺序依赖而非源码缺陷。登记于 `backend/quality-guidelines.md`「已知 flaky 测试」。禁止把「重跑即绿」当常态接受。 |
| **xfail(strict=True)** | Python 侧已知缺陷的登记方式；严格模式在缺陷修复后强制用例失败，倒逼清理标记。2026-10-15 实测已无标记；新增时在对应契约章节登记。 |

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
