# 后端架构与模块边界

同层相关规范按主题合并；目标设计与当前实现的状态标记保留，各章节约束继续有效。

- [后端目录与依赖边界](#后端目录与依赖边界)
- [Business Auth 模块目标设计](./java-modules-auth.md)
- [Business Infrastructure 模块目标设计](./java-modules-infrastructure.md)
- [Business Java Agent 模块目标设计](./java-modules-agent.md)

## 后端目录与依赖边界

### Business 当前模块总览（已实施）

本节是当前九模块边界；实现与测试状态以当前源码、POM、`ArchitectureBoundaryTest` 和质量记录为准。

| 模块 | 当前职责 | 允许的项目内直接依赖上限 |
|---|---|---|
| common | Result、PageResult、BizException、ErrorType 等基础定义 | 无其他业务模块 |
| pojo | 统一 DTO、VO、Entity，按业务分包 | `common`（矩阵允许；当前 POM 未声明该依赖） |
| infrastructure（新增） | Redis、限流、图片、邮件的公开技术接口与现有实现 | common、pojo（实际需要时） |
| auth（新增） | Token、会话、请求认证、当前身份读取 | infrastructure、common、pojo |
| log（新增） | 操作日志采集、存储、清理、查询 | auth、infrastructure、common、pojo |
| agent | Python Agent HTTP/SSE 与导入通信接口、实现 | log、auth、infrastructure、common、pojo |
| client | 用户业务、用户接口与本端 Converter | auth、log、infrastructure、common、pojo |
| admin | 管理员业务、管理接口与本端 Converter | agent、auth、log、infrastructure、common、pojo |
| app | 启动、组合装配、安全配置、HTTP 异常适配 | 按装配需要依赖上述模块 |

依赖上限不是要求引入全部依赖。每项直接使用显式声明；当前 POM 可能比矩阵更窄，例如 `pojo` 当前没有内部模块依赖。禁止 client/admin 相互依赖，禁止下层依赖 app，禁止 auth → log、infrastructure → auth/log/agent/client/admin。业务方只能使用能力模块的公开入口，不直接引用内部 Mapper 或供应商实现。

矩阵的可执行证据是 `backend/business/app/src/test/java/top/zhaizz/app/architecture/ArchitectureBoundaryTest.java`：它覆盖九模块禁止边、排除测试夹具、断言 `common` 仅含四个基础类型，并对除 `app` 外的模块拒绝跨模块访问 Mapper、Service 实现和供应商适配器。新增边界时必须同时核对 POM、生产源码和该测试

关键协作链：`admin → agent → log → auth → infrastructure → common`。各层按需使用 pojo；链条不要求中间模块替其他模块转发调用。现有 agent 管理员代理使用操作日志注解，因此迁移清单必须同时更新其 log 依赖。

#### common 迁移映射（已完成）

| 内容 | 目标 |
|---|---|
| SubjectVoConverter | 拆回 client/admin 各自 converter，DTO/VO 仍在 pojo |
| SecurityUtil、UserPrincipal、JWT/会话、CookieOriginFilter | auth；app 配置和注册安全组件 |
| OperationLog 注解/切面/清理、Mapper、OperationLogConstants | log；日志 Entity/DTO/VO 在 pojo |
| RedisUtil、RateLimit 注解/切面/实现、图片接口 | infrastructure 对应能力包 |
| GlobalExceptionHandler | app 的 HTTP 适配包 |
| AgentApiPaths | agent 的通信协议常量 |
| RedisKeys | 按认证、限流、收藏等职责拆回所有者，保持键文本与 TTL 行为 |
| TraceConstants | agent 的请求追踪协议常量 |

DTO/VO/Entity 统一放 pojo；框架身份实现、技术接口与其配套枚举不按名称机械搬入 pojo。common 收紧时同步移除不再使用的 pojo/运行时依赖，不保留只为迁出代码提供框架的传递依赖。

#### 历史实施与验收记录（保留）

迁移任务曾按本节规范完成代码迁移、依赖调整、配置装配与旧路径清理；具体实现签名以当前源码和测试为准，后续修改继续遵守本文依赖和已有 HTTP/数据契约。

历史迁移按基础类型与接口 → infrastructure → auth → log → agent → client/admin 调用及 Converter → app 装配与旧实现清理的顺序完成。后续变更仍按依赖方向实施，不允许恢复已删除的旧实现。

验收同时覆盖旧实现清理、Maven 无环与显式依赖、Bean 唯一装配、Mapper XML/类型引用、接口字段/权限/错误/SSE 行为，以及各目标规范列出的行为断言。本轮已运行完整 Business `mvn -B clean test`；后续修改配置或架构边界时仍必须重复该验证。

### Python Agent 总体结构

```text
backend/agent/                # FastAPI + LangGraph，:8090
├── app/api/              # HTTP/SSE 边界
├── app/agent|chat|rag/   # 用例、状态、端口与领域逻辑
├── app/adapters/         # HTTP、Redis、MySQL、LLM、提示词、子进程实现
└── jobs/                 # importer / indexer / backfill / scheduler
```

证据：`backend/agent/main.py`、`backend/agent/app/agent/dependencies.py`。

### app/rag 模块结构（2026-10-05，提交 `08799fdb`）

`retrieval.py` 曾达 1030 行、23 个方法，按管线阶段拆四模块（move-only，行为零变化）：

| 模块 | 职责 |
|---|---|
| `lexical.py` | Redis 转义、查询表达式、词法项 |
| `entity_resolution.py` | 实体名称/ID 解析、安全校验 |
| `authority.py` | 权威回查、Evidence enrich/校验 |
| `rerank.py` | 候选构建、RRF、规则重排 |

`retrieval.py`（402 行）只留 `RetrievalCandidate`/`RetrievalResult` dataclass 与 `RagRetrievalService` 编排。关键取舍：

1. **move-only**：不改逻辑、参数、fail-closed 语义；验收锚点是 pytest 通过数拆前拆后一致。
2. **`staticmethod` 委托别名**：service 保留 `_enrich_evidence = staticmethod(enrich_evidence)` 等别名，既有调用点与测试不改。新增代码必须直接调模块级函数；别名是过渡产物，未来清理需独立任务。
3. **authority 三方法留 service**：`_authoritative_result`、`_business_fallback`、`_authoritative_allowlist_result` 依赖 `self` 的 gateway/ports 且承担编排，未移入 `authority.py`。
4. **文件名以代码为准**：PRD 曾写 `authority_enrich.py`，落地 `authority.py`（职责含回查不止 enrich）。

该模式是后续拆分 `jobs/importer`（862 行）、`jobs/indexer`（785 行）的模板。

### Business 模块重设计状态

以下已确认的目标规则与当前实现一致，并作为持续约束。重设计目标为低耦合、高内聚，保留 client/admin 各自的用户与管理员业务职责。

- `log`：操作日志采集、存储、清理和查询统一归属；admin 保留管理端接口、权限与 VO 转换。详见 [操作日志模块目标设计](./error-handling.md#business-操作日志模块已实施设计)。
- Converter：各模块独立维护，位置与迁移边界见下一节。
- `auth`：Token、请求认证和会话技术能力归属 auth；client/admin 保留账户业务决策，app 负责安全装配。详见 [Auth 模块目标设计](./java-modules-auth.md)。
- `infrastructure`：并入现有 Redis、限流、图片存储、邮件发送等技术实现及对应通用技术接口；业务方使用公开能力接口，app 负责启动和装配。迁移清单与约束见 [Infrastructure 模块目标设计](./java-modules-infrastructure.md)。
- `common` 收紧为通用结果、分页、错误类型等基础定义；HTTP 异常适配归 app。日志与身份协作方向已确认为 log → auth → infrastructure → common。

#### Java agent 通信边界（已确认）

Java agent 统一负责 Python Agent 通信，原 admin 的 ImportAgentGateway 与 app 的 HttpImportAgentGateway 一并迁入；admin 保留导入业务校验与记录查询。依赖单向为 admin → agent，agent 不反向引用 admin，数据模型继续归 pojo，app 负责装配。详见 [Java Agent 模块目标设计](./java-modules-agent.md)。

#### common 与 app 边界（已确认）

- common 保留 `Result`、`PageResult`、`BizException`、`ErrorType` 等无业务运行逻辑的基础定义；“多个模块使用”不再是放入 common 的充分理由。
- common 不承载 Controller、Service、Mapper、Converter、切面、过滤器、定时任务、技术适配器或运行时配置。认证、日志、Redis/限流/存储/邮件按已确认目标迁往 auth、log、infrastructure。
- `GlobalExceptionHandler` 等 HTTP 异常适配迁入 app 的 Web 适配包，由 app 统一启用；业务模块只依赖基础错误定义，不引用 app 的处理器。详见 [HTTP 异常适配边界](./error-handling.md#common--app-异常边界已实施)。
- 迁移同时收紧 common 的 POM：删除迁出功能遗留的 Web、AOP、Redis、Security、MyBatis、JWT 等运行时依赖；不能靠 common 继续给消费者隐式提供整套框架。各消费者显式声明实际所需依赖。
- Result/PageResult 是 common 中的通用响应容器；业务 DTO/VO/Entity 统一放 pojo。Converter 统一模块内目录规范，继续归各消费模块，不集中进 pojo 或另建全局 converter 模块。

#### pojo 统一管理规则（已确认）

Business 的 DTO、VO、Entity 统一放在 pojo 管理，无论只被一个模块使用还是跨模块共享。按 dto/vo/entity 及业务主题分包，沿用现有结构。

- 不把仅 client/admin 使用作为将 DTO/VO 移出 pojo 的理由，也不在业务模块保留同名副本。
- 两端语义相同时可以共享类型；字段可见性或业务语义不同时，在 pojo 内定义明确区分的类型或子包，不要求合并成一个包含所有字段的对象。
- Converter 仍分别归属 client/admin/log 等消费模块；共享数据类型不代表共享转换逻辑。UserVO/SubjectDetailVO 可继续由两端独立 Converter 生成。
- OperationLog、LogQueryDTO、LogVO 等日志数据类型仍归 pojo；新增跨模块业务请求/响应类型也统一归 pojo。
- pojo 只承载数据结构及必要的序列化、校验、映射声明，不放 Service、Converter、Mapper、供应商实现或运行时装配，不反向依赖业务模块。

本规则统一的是 DTO/VO/Entity；技术接口、供应商 SDK 类型与框架身份实现不因被跨模块使用就成为 pojo 数据模型。ImageCategory 等技术接口配套类型已随 infrastructure 能力迁移。

实施时检查 Java import、Mapper XML 类型名、嵌套/继承模型与接口字段契约；统一存放不能成为意外暴露管理端字段的理由。

### Converter 放置与职责（已实施规范）

本节是 Business 分层重设计的已实施约定。`client` 保留用户业务职责，`admin` 保留管理员业务职责；两端各自维护面向本端的对象转换。

#### 位置与调用

- 转换类统一放在所属模块的 `top.zhaizz.<module>.converter` 包；数量较多时按业务细分，如 `converter.subject`。
- 用户端和管理端分别维护自己的 Converter，不通过 `common` 共享面向两端的 VO 转换，也不相互引用对方的 Converter。
- Service 获取所需数据、完成业务判断后调用 Converter；关联数据由调用方显式传入，Converter 不自行加载。
- 按实际转换需要创建类，不要求每个 Entity 都对应一个 Converter。

#### 纯转换与业务行为的边界

| 行为 | 归属 |
|---|---|
| Entity → VO、DTO → Entity 的字段映射与无副作用的展示格式计算 | 模块内 Converter |
| 数据库查询、关联数据加载、外部服务调用 | Service 或其依赖的 Mapper/Store/Gateway |
| 权限校验、业务资格判断、状态迁移、事务和持久化 | Service 或所属业务组件 |
| 依赖当前用户权限的字段可见性判断 | Service 决定允许输出的数据，Converter 只映射显式传入的结果 |

“纯计算”不等于所有不访问数据库的逻辑都应迁出：资格判断、状态规则等即使只使用内存数据，也仍是业务职责。

#### 现有内嵌转换的迁移要求

- 检查 ServiceImpl、Controller 及其他业务代码中的 `toVO`、`convert`、`buildVO` 等方法，以及内联 setter、builder、属性复制或 Stream 映射；按实际职责识别，不能只按方法名判断。
- 完整的 DTO/Entity/VO 字段映射迁入所属模块 Converter；混合查询与转换的方法先拆开，仅迁出纯转换部分。
- 不把所有 setter 都视为转换：业务状态更新、业务默认值和写入校验继续由业务层负责。
- 保留接口字段、空值约定、集合顺序和敏感字段处理；已有行为验证应覆盖迁移前后的一致性，不为简单字段复制机械增加测试。

#### 错误与正确做法

- 错误：ServiceImpl 内维护完整 VO 映射；或把该方法搬到 Converter 后仍在其中调用 Mapper、读取当前用户权限。
- 正确：Service 查询实体和关联数据并完成业务判断，再调用模块内 Converter 映射输出。

迁移已完成，映射归属现为：`CollectionConverter.toSimpleVO`、`SubjectConverter.toBatchItemVO`、`EvidenceConverter.toCandidate`，以及仍留在 `DashboardServiceImpl.trends` 的 VO 组装部分。对应的查询、收藏分类、状态解释和统计口径仍由业务层负责。

本次实现已逐项核对现有内嵌转换及原 `common.converter.SubjectVoConverter` 的两端使用方，并按本节边界完成迁移；后续修改需继续遵守这些规则。

### 配置装配契约：Business → App

#### 1. Scope / Trigger

- 触发条件：新增或迁移 Business 运行时配置、Properties 绑定类或跨模块基础设施 Bean。
- 目标：让 `app` 成为唯一配置组合根，避免 `common`/`agent` 反向依赖应用层。

#### 2. Signatures

- 配置类位于 `top.zhaizz.app.config`：`AgentConfig`、`AgentProperties`、`CorsConfig`、`CorsProperties`、`MyBatisPlusConfig`、`SecurityConfig`。
- 下层实现使用普通构造器：`AgentServiceImpl(RestTemplate, ObjectMapper, String baseUrl, long connectTimeout)`、`CookieOriginFilter(List<String> allowedOrigins)`。

#### 3. Contracts

- 保留 `at.agent.base-url/connect-timeout/read-timeout` 与 `at.cors.allowed-origins` key、默认值和环境变量映射。
- `AgentConfig` 创建共享 `RestTemplate`、`AgentService` 和 trace interceptor；SSE 实例 `readTimeout=0`。
- `CorsConfig` 创建 `/api/**` CORS source 与 Cookie Origin filter；Origin 白名单精确匹配并允许 credentials。

#### 4. Validation & Error Matrix

- 缺失或空 `allowed-origins` + refresh/logout POST → 403（fail closed）。
- 非 Cookie 路径或非 POST → 跳过 Origin 检查并继续过滤链。
- 未认证私有路由 → 401 JSON；已认证但角色不足/未匹配路由 → 403 JSON。
- Agent 普通请求使用配置读超时；SSE 请求不因普通读超时中断；上游网络失败继续映射为 `SERVICE_UNAVAILABLE`。

#### 5. Good / Base / Bad Cases

- Good：`app.config` 绑定 Properties，并通过 `@Bean` 显式向下层传普通值。
- Base：下层模块只依赖 `common` 契约、接口或 JDK 类型，不读取 Spring Environment。
- Bad：在 `common`/`agent` 中新增 `@Component` 读取 `top.zhaizz.app` 或直接注入 `*Properties`。

#### 6. Tests Required

- `AppConfigurationBindingTest`：断言 Properties、RestTemplate、AgentService、CookieOriginFilter、CORS source 唯一注册及具体 key 值。
- `SecurityConfigAuthorizationTest`：断言公开、匿名私有、USER、ADMIN、默认拒绝及 401/403 JSON。
- `CookieOriginFilterTest`：断言 refresh/logout 的允许、缺失、未知 Origin 和非目标路径。
- `AgentConfigTest`：断言超时、`X-Request-ID` 透传与 SSE 无读超时；`ArchitectureBoundaryTest`：断言完整九模块依赖矩阵、`common` 四个基础定义、内部实现包隔离和测试夹具拒绝非法边。

#### 7. Wrong vs Correct

##### Wrong

```java
@Component
class AgentServiceImpl {
    AgentServiceImpl(AgentProperties properties) { }
}
```

##### Correct

```java
@Bean
AgentService agentService(RestTemplate restTemplate, ObjectMapper mapper, AgentProperties properties) {
    return new AgentServiceImpl(restTemplate, mapper, properties.getBaseUrl(), properties.getConnectTimeout());
}
```

### 配置例外（迁移后仍归消费方）

配置例外必须按真实源码处理：`client/config/AuthCookieProperties`、`CollectionProgressConfig`、`infrastructure` 模块自身的 `MinioConfig`/`MinioProperties` 等仍属于消费方或基础设施自身配置；`app` 模块当前只有 `config`、`filter`、`web` 三个包，MinIO/Resend 实现已迁入 `infrastructure` 模块。迁移规则只适用于本次列出的 `app.config` 类，不得扩大解释为“所有 `@ConfigurationProperties` 都在 app”。

### 启动、Profile 与健康检查契约

- 当前工作树的 `app/src/main/resources` 包含 `application.yml`、`application-local.yml`、`logback-spring.xml`；Git 跟踪 `application.yml` 和 `logback-spring.xml`，`application-local.yml` 是被忽略的本地 Profile 文件。是否启用某个 Profile 仍以启动参数和配置内容为准，不能把本地文件值当作共享契约。
- 数据库、Redis、Agent 和 CORS 读取的 key 以 `application.yml` 的占位符为准；文档示例不得改写成未在配置或启动脚本中出现的环境变量名。
- `at.cors.origins` 当前没有安全默认值；缺失/空白值时应保持 fail closed，并通过配置绑定测试确认启动或请求阶段的失败语义。
- CORS 绑定类的属性路径是 `at.cors.allowed-origins`，但当前 YAML 占位符写成 `${at.cors.origins}`；现有 `AppConfigurationBindingTest` 使用显式 `at.cors.allowed-origins[0]`，未覆盖该占位符命名偏差。新增环境变量或修改配置前必须先统一命名并补回归测试。
- `/actuator/health/**` 的公开范围、liveness/readiness 分组和匿名访问权限必须作为一个整体验证；当前 Security 仅显式放行 health 路径，其他 URL 仍由 `anyRequest().denyAll()` 拒绝。

| 变更 | 必须核对 |
|---|---|
| 新增 Profile 或环境变量 | 配置文件、绑定类、`.env.example`/部署入口和缺值行为 |
| 调整 CORS/Cookie | key 名、Origin 精确匹配、credentials、refresh/logout 的 403 语义 |
| 调整健康探针 | URL 是否被 Security 放行、依赖范围、匿名响应字段和 HTTP 状态 |
| 修改 Agent 超时 | 普通请求与 SSE 的读超时必须分别验证 |

### Python Agent 放置规则

- `app/api` 只负责协议、依赖注入与序列化，业务流程进入 `app/chat`、`app/agent`、`app/rag`。
- 领域层通过 `Protocol` 或 `AgentDependencies` 访问外部能力。
- Redis、HTTP、LLM、MySQL 和子进程实现只放 `app/adapters`，由 `main.py` lifespan 组装。
- importer/indexer/backfill/scheduler 属于 `jobs`，不要塞进 FastAPI 路由；`jobs/backfill/worker.py` 负责实体详情回填，不能遗漏该任务层。
- 新 Agent 工具按最小权限放到 client/admin 对应节点，不创建全局万能工具集。

### 禁止做法

- `client/admin` 直接依赖 `app.infrastructure`。
- Python 领域节点直接创建 Redis、httpx 或 LLM 客户端。
- Controller/Router 内堆积事务、批处理或复杂状态转换。
- 不得只因父 POM 已引入 ArchUnit 就假设边界完整；当前自动保护由 `ArchitectureBoundaryTest` 提供，边界或配置迁移后必须运行 `mvn -B clean test`。

## 三个目标模块的设计细则

以下三个模块的完整设计（Scope / Signatures / Contracts / Validation / Good-Bad / Tests / Wrong-Correct）已拆为独立文件，按需读取：

| 模块 | 文件 |
|---|---|
| Auth（Token / 会话 / 认证机制归属） | [java-modules-auth.md](./java-modules-auth.md) |
| Infrastructure（Redis / 限流 / 图片 / 邮件技术实现） | [java-modules-infrastructure.md](./java-modules-infrastructure.md) |
| Java Agent（Python Agent 通信、导入网关） | [java-modules-agent.md](./java-modules-agent.md) |
