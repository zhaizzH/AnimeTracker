# 后端架构与模块边界

同层相关规范按主题合并；目标设计与当前实现的状态标记保留，各章节约束继续有效。

- [后端目录与依赖边界](#后端目录与依赖边界)
- [Business Auth 模块目标设计](#business-auth-模块目标设计)
- [Business Infrastructure 模块目标设计](#business-infrastructure-模块目标设计)
- [Business Java Agent 模块目标设计](#business-java-agent-模块目标设计)

## 后端目录与依赖边界

### Business 目标模块总览（已实施）

本节是本轮确认后的目标边界；后文标注“迁移前”的目录、配置与依赖仅用于核对现有源码。新增模块已落地；实现与测试状态以本任务记录和 Business reactor 验证为准。

| 模块 | 目标职责 | 允许的项目内直接依赖上限 |
|---|---|---|
| common | Result、PageResult、BizException、ErrorType 等基础定义 | 无其他业务模块 |
| pojo | 统一 DTO、VO、Entity，按业务分包 | 必要时使用 common 基础类型，不依赖实现模块 |
| infrastructure（新增） | Redis、限流、图片、邮件的公开技术接口与现有实现 | common、pojo（实际需要时） |
| auth（新增） | Token、会话、请求认证、当前身份读取 | infrastructure、common、pojo |
| log（新增） | 操作日志采集、存储、清理、查询 | auth、common、pojo；实际使用通用能力时可依赖 infrastructure |
| agent | Python Agent HTTP/SSE 与导入通信接口、实现 | log（现有管理员代理日志采集）、common、pojo；实际需要时使用 auth/infrastructure 公开能力 |
| client | 用户业务、用户接口与本端 Converter | auth、log、infrastructure、common、pojo |
| admin | 管理员业务、管理接口与本端 Converter | agent、auth、log、infrastructure、common、pojo |
| app | 启动、组合装配、安全配置、HTTP 异常适配 | 按装配需要依赖上述模块 |

依赖上限不是要求引入全部依赖。每项直接使用显式声明；禁止 client/admin 相互依赖，禁止下层依赖 app，禁止 auth → log、infrastructure → auth/log/agent/client/admin。业务方只能使用能力模块的公开入口，不直接引用内部 Mapper 或供应商实现。

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

#### 实施与验收边界

本次交付已按本节规范完成代码迁移、依赖调整、配置装配与旧路径清理；具体实现签名以当前源码和测试为准，后续修改继续遵守本文依赖和已有 HTTP/数据契约。

本轮已按基础类型与接口 → infrastructure → auth → log → agent → client/admin 调用及 Converter → app 装配与旧实现清理的顺序完成迁移。后续变更仍按依赖方向实施，不允许恢复已删除的旧实现。

验收同时覆盖旧实现清理、Maven 无环与显式依赖、Bean 唯一装配、Mapper XML/类型引用、接口字段/权限/错误/SSE 行为，以及各目标规范列出的行为断言。本轮已运行完整 Business `mvn -B clean test`；后续修改配置或架构边界时仍必须重复该验证。

### 当前总体结构（迁移前）

```text
backend/
├── business/                 # Spring Boot 业务与鉴权，:8080
│   ├── pojo/                 # Entity / DTO / VO
│   ├── common/               # 跨模块平台能力
│   ├── client/               # 用户端 Controller / Service / Mapper / Store / Gateway
│   ├── admin/                # 管理端 Controller / Service / Mapper / Gateway
│   ├── agent/                # Python Agent 的 HTTP 代理
│   └── app/                  # 启动组合根与基础设施适配器
└── agent/                    # FastAPI + LangGraph，:8090
    ├── app/api/              # HTTP/SSE 边界
    ├── app/agent|chat|rag/   # 用例、状态、端口与领域逻辑
    ├── app/adapters/         # HTTP、Redis、MySQL、LLM、提示词、子进程实现
    └── jobs/                 # importer / indexer / backfill / scheduler
```

证据：`backend/business/pom.xml`、`backend/agent/main.py`、`backend/agent/app/agent/dependencies.py`。

### Spring Business 当前放置规则（迁移前）

- `pojo` 只放数据结构：请求用 DTO，响应用 VO，数据库映射用 Entity。
- `client/admin` 遵循 Controller → Service → Mapper/Store；Controller 只做绑定、鉴权上下文和响应包装。
- 外部系统先在消费模块定义 Gateway，实现在 `app.infrastructure`。参考 `ImportAgentGateway` → `HttpImportAgentGateway`。
- 只有多个业务模块共享的能力才放 `common`；模块私有端口不要上提。
- `app` 是组合根，聚合业务模块并承载 MinIO、Resend、Agent HTTP 等适配器，以及本次从旧 `common.config` 迁移的六类 Spring 配置绑定和运行时 Bean 装配；它不是所有领域配置类的唯一所在地。

### Business 模块重设计状态

上方目录和下方依赖表保留迁移前证据；以下已确认的目标规则与当前实现一致，并作为持续约束。重设计目标为低耦合、高内聚，保留 client/admin 各自的用户与管理员业务职责。

- `log`：操作日志采集、存储、清理和查询统一归属；admin 保留管理端接口、权限与 VO 转换。详见 [操作日志模块目标设计](./error-handling.md#business-操作日志模块已实施设计)。
- Converter：各模块独立维护，位置与迁移边界见下一节。
- `auth`：Token、请求认证和会话技术能力归属 auth；client/admin 保留账户业务决策，app 负责安全装配。详见 [Auth 模块目标设计](./directory-structure.md#business-auth-模块目标设计)。
- `infrastructure`：并入现有 Redis、限流、图片存储、邮件发送等技术实现及对应通用技术接口；业务方使用公开能力接口，app 负责启动和装配。迁移清单与约束见 [Infrastructure 模块目标设计](./directory-structure.md#business-infrastructure-模块目标设计)。
- `common` 收紧为通用结果、分页、错误类型等基础定义；HTTP 异常适配归 app。日志与身份协作方向已确认为 log → auth → infrastructure → common。

#### Java agent 通信边界（已确认）

Java agent 统一负责 Python Agent 通信，原 admin 的 ImportAgentGateway 与 app 的 HttpImportAgentGateway 一并迁入；admin 保留导入业务校验与记录查询。依赖单向为 admin → agent，agent 不反向引用 admin，数据模型继续归 pojo，app 负责装配。详见 [Java Agent 模块目标设计](./directory-structure.md#business-java-agent-模块目标设计)。

#### common 与 app 边界（已确认）

- common 保留 `Result`、`PageResult`、`BizException`、`ErrorType` 等无业务运行逻辑的基础定义；“多个模块使用”不再是放入 common 的充分理由。
- common 不承载 Controller、Service、Mapper、Converter、切面、过滤器、定时任务、技术适配器或运行时配置。认证、日志、Redis/限流/存储/邮件按已确认目标迁往 auth、log、infrastructure。
- `GlobalExceptionHandler` 等 HTTP 异常适配迁入 app 的 Web 适配包，由 app 统一启用；业务模块只依赖基础错误定义，不引用 app 的处理器。详见 [HTTP 异常适配迁移](./error-handling.md#common--app-异常边界目标设计)。
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

已核实的迁移候选包括 `CollectionServiceImpl.toSimpleVO`、`ClientSubjectServiceImpl.toBatchItemVO` 的字段映射部分、`EvidenceServiceImpl.buildCandidate` 和 `DashboardServiceImpl.trends` 的 VO 组装部分。对应的查询、收藏分类、状态解释和统计口径仍由业务层负责。

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
- `AgentConfigTest`：断言超时、`X-Request-ID` 透传与 SSE 无读超时；`ArchitectureBoundaryTest`：断言下层不依赖 `top.zhaizz.app..`。

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

### 当前模块依赖与配置例外（迁移前）

| 模块 | 允许依赖/职责 | 当前边界说明 |
|---|---|---|
| `pojo` | 数据结构与 DTO/VO/Entity | 不依赖业务实现或 `app` |
| `common` | 跨模块常量、结果、日志、安全和共享端口 | 不反向依赖 `client/admin/agent/app` |
| `client` | 用户端 Controller、Service、Mapper、Store、Gateway | 可依赖 `pojo/common`；不得依赖 `app` |
| `admin` | 管理端 Controller、Service、Mapper、Gateway | 可依赖 `pojo/common`；不得依赖 `app` 或 `client` 实现 |
| `agent` | Spring 到 Python Agent 的代理边界 | 只依赖契约和共享基础能力，不把 Python 实现引入 Java 业务模块 |
| `app` | 组合根、基础设施适配器、配置装配 | 可组合下层模块，不向下层泄露 Spring 配置类型 |

当前 `ArchitectureBoundaryTest` 主要保护“下层不得依赖 `top.zhaizz.app..`”，不会自动覆盖所有 sibling 依赖（例如 `admin → client`）。新增跨模块 import 时必须同时做人工依赖审查，并为新边界补 ArchUnit 断言。

配置例外必须按真实源码处理：`client/config/AuthCookieProperties`、`CollectionProgressConfig`、`app/infrastructure/**` 等仍属于消费方或基础设施自身配置；迁移规则只适用于本次列出的 `app.config` 类，不得扩大解释为“所有 `@ConfigurationProperties` 都在 app”。

### 启动、Profile 与健康检查契约

- 当前仓库实际跟踪的 Business 配置文件只有 `app/src/main/resources/application.yml`；文件头部提到的 local/prod 配置不能视为已存在实现。
- 数据库、Redis、Agent 和 CORS 读取的 key 以 `application.yml` 的占位符为准；文档示例不得改写成未在配置或启动脚本中出现的环境变量名。
- `at.cors.origins` 当前没有安全默认值；缺失/空白值时应保持 fail closed，并通过配置绑定测试确认启动或请求阶段的失败语义。
- CORS 绑定类的属性路径是 `at.cors.allowed-origins`，但当前 YAML 占位符写成 `${at.cors.origins}`；这是必须由配置绑定测试裁决的现状偏差，新增环境变量前先统一命名。
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
- 不得因父 POM 已引入 ArchUnit 就声称边界已有自动保护；必须保留 `ArchitectureBoundaryTest` 并运行 `mvn -B clean test`。

## Business Auth 模块目标设计

状态：已实施并通过 auth/infrastructure 针对性测试及 Business reactor 测试。`auth` Maven 模块已承接原 common 与 client 中的认证技术能力，当前接口和包路径以源码为准。

### 1. Scope / Trigger

| 模块 | 已确认职责 |
|---|---|
| auth | Token 签发与验证、请求认证、会话刷新与撤销、技术过期策略 |
| client | 注册、登录业务校验、邮箱验证、重置密码等用户业务 |
| admin | 用户管理、角色修改、禁用用户等管理员业务 |
| app | 安全配置和模块装配 |

业务层决定何时签发或撤销，auth 执行认证技术操作。不得将整个 AuthServiceImpl 因类名含 Auth 就迁入 auth。

### 2. Signatures / 迁移入口

当前实现的认证能力签名如下；实现位于 `auth.security`，会话数据类型位于 `pojo.dto.auth`：

```java
// auth.security.JwtTokenProvider
String generateToken(Long userId, String role);
boolean validateToken(String token);
// auth.security.AuthSessionStore
void saveRefresh(String rawToken, Long userId, long startedAtEpochMs, long ttlMs);
Optional<ConsumedRefreshSession> consumeRefresh(String rawToken);
void revokeAccess(String rawToken);
void revokeRefresh(String rawToken);
void revokeAll(Long userId);
```

迁移对象包括 JwtTokenProvider、JwtAuthenticationFilter、AuthSessionStore、认证身份类型，以及 client 的会话生成方法中的随机令牌生成、access 白名单维护、refresh 保存与技术过期计算。账户查询、启用状态校验和 UserVO 组装留在 client。

认证公开能力、返回类型和包结构已按实施设计落地；不要求将所有存储方法直接暴露给业务方。业务 DTO/VO/Entity 统一归 pojo；UserVO/LoginVO 的类型声明留在 pojo，组装职责留在 client，不能把类型声明与组装逻辑一起迁入 auth。

### 3. Contracts / 边界与保留行为

- client/admin 调用 auth 的能力，传入已由业务验证的 userId、role 等必要身份信息；auth 不依赖 client/admin/app 实现，不查询业务 UserMapper，不返回面向用户端的 UserVO/LoginVO。
- client 决定注册唯一性、初始角色、邮箱验证、登录资格与密码重置；admin 决定角色修改、禁用及保护规则。重置密码、修改角色、禁用用户后的会话撤销，由业务流程触发 auth 执行。
- 刷新保持先原子消费 refresh，再由业务查询账户并检查存在/启用状态，最后完成寿命校验与重新签发的行为；原始会话起点不能因刷新重置。业务校验由 client/admin 完成，auth 通过 `AuthTokenService.issue` 执行会话寿命计算与签发。
- refresh TTL 保持为配置有效期与剩余绝对会话时长中的较小值；迁移不得修改现有配置 key、单位或默认值。
- Redis 中使用 Token 的 SHA-256 摘要作键，保留 access 白名单和 access/refresh 用户索引；refresh 消费保留 GETDEL 的单次消费语义。
- 请求认证保持 JWT 验证与 access 白名单双重检查；app 负责安全链装配与路由规则，不能在 auth 中混入管理员用户管理规则。
- HTTP 路由、响应字段、at_refresh HttpOnly Cookie 与 401/403 协议保持现状。客户端响应和 Cookie 处理不因内部模块迁移自动改变归属或行为。
- 已确认依赖方向为 `log → auth → infrastructure → common`：log 通过 auth 读取当前身份，auth 使用 infrastructure 的 Redis 能力，不反向依赖 log。
- 现有 `SecurityUtil` 随身份读取能力迁入 auth；`CookieOriginFilter` 随请求安全机制归 auth，由 app 提供配置并唯一注册。Spring Security 身份实现仍归 auth；纯业务 DTO/VO/Entity 遵守 pojo 统一规则。
- auth 内不使用 log 的操作日志注解或存储服务。需要记录登录/会话业务操作时，由 client/admin 等上层调用方采集；auth 的普通运行日志使用 SLF4J，不引入 log 模块。

### 4. Validation & Error Matrix

| 条件 | 必须保持的行为 |
|---|---|
| refresh 缺失、空白、失效或已消费 | UNAUTHORIZED，不签发新会话 |
| 刷新时账户不存在或被禁用 | 业务层拒绝，返回 UNAUTHORIZED |
| 绝对会话有效期耗尽 | UNAUTHORIZED，不重置会话起点续期 |
| 同一个 refresh 并发使用 | 最多一个请求成功消费 |
| JWT 无效或不在 access 白名单 | 不建立已认证身份，继续由安全链按路由决定响应 |
| 用户业务要求撤销全部会话 | 删除该用户 access/refresh 凭据及对应索引 |

### 5. Good / Base / Bad Cases

- Good：admin 校验管理员权限与被操作用户保护规则，修改用户后调用 auth 撤销会话。
- Base：client 完成登录业务校验，将身份交给 auth 签发，自己通过 Converter 组装用户端响应。
- Bad：auth 依赖 AdminUserServiceImpl，或直接查询 UserMapper 决定注册、禁用、邮箱修改规则。

### 6. Tests Required

- 架构：auth 不反向依赖 client/admin/app/log 的实现，业务方不继续自行维护 Token 存储与生成细节；身份读取保持匿名场景返回空身份的既有语义。
- 会话：refresh 单次消费、绝对寿命、TTL 上界及原始起点保持一致；单会话与全部会话撤销均验证凭据和索引。
- 业务：登录资格、邮箱验证、禁用/角色修改/重置密码触发撤销的行为保持一致。
- HTTP 与装配：JWT 与白名单双重校验、既有 401/403 和 Cookie 行为、安全组件唯一装配。

### 7. Wrong vs Correct

- Wrong：把注册、邮件验证、UserMapper 与 UserVO 连同 Token 代码整包搬入 auth。
- Correct：业务保留账户决策，auth 封装认证机制，app 组合安全配置。

### 代码证据

- `backend/business/auth/src/main/java/top/zhaizz/auth/security/AuthSessionStore.java`
- `backend/business/auth/src/main/java/top/zhaizz/auth/security/JwtTokenProvider.java`
- `backend/business/auth/src/main/java/top/zhaizz/auth/security/JwtAuthenticationFilter.java`
- `backend/business/client/src/main/java/top/zhaizz/client/service/impl/AuthServiceImpl.java`
- `backend/business/client/src/main/java/top/zhaizz/client/service/impl/VerificationServiceImpl.java`
- `backend/business/admin/src/main/java/top/zhaizz/admin/service/impl/AdminUserServiceImpl.java`

## Business Infrastructure 模块目标设计

状态：已实施；Redis、限流、图片存储和邮件实现已迁入 infrastructure，并通过针对性测试。Agent 专属导入通信已确定归 Java agent；身份与日志协作采用 log → auth → infrastructure → common。

### 1. Scope / Trigger

新增 `infrastructure` Maven 模块，承接 Redis、限流、图片存储、邮件发送等技术实现，内部按能力分包。必须迁移并复用现有代码，不能新建空模块或平行实现而保留原有生产实现。`app` 负责启动与组合装配。

这不是所有持久化代码的集中仓库：auth 的 Token/会话规则、log 的操作日志查询/存储/清理、client/admin 的业务查询和规则仍属于各自所有者。Redis 通用访问可供这些模块使用，不代表其业务键、TTL 决策或 Mapper 也必须迁入 infrastructure。

### 2. Signatures / 现有迁移入口

现有技术接口（迁移保持行为，通用接口与实现均归 infrastructure 的对应能力包）：

```java
boolean allowOrCount(String bucket, int limit, int windowSeconds);
void reset(String bucket);
String upload(MultipartFile file, ImageCategory category);
void send(String recipient, String subject, String text);
```

| 当前来源（Java 包或模块） | 并入目标 |
|---|---|
| common.util.RedisUtil | infrastructure 的 Redis 能力包 |
| common.ratelimit 的 RateLimit、RateLimitAspect、RateLimiter | infrastructure 的限流能力包 |
| app.infrastructure.storage.minio 的 MinioImageStorageGateway | infrastructure 的图片存储能力包 |
| app.infrastructure.email 的 ResendEmailGateway | infrastructure 的邮件能力包 |
| client.gateway.EmailGateway | infrastructure.email 的公开接口 |
| common.storage.ImageStorageGateway/ImageCategory | infrastructure.storage 的公开接口及参数类型 |

与实现相伴的 MinioConfig、MinioProperties、ResendConfig 必须纳入迁移审查：供应商客户端构建与初始化属于技术实现，组合启用由 app 负责；禁止迁移时重复注册 Bean、重复初始化存储桶或遗漏配置绑定。供应商配置与 Properties 随能力位于 infrastructure 内，由 app 组合启用；应用级安全、CORS 与跨模块装配继续归 app。

`EmailGateway` 与 `ImageStorageGateway` 等通用技术接口统一归入 infrastructure 对应能力包，不再留在 client/admin/common；配套参数类型 ImageCategory 随接口迁入 storage。`agent.gateway.HttpImportAgentGateway` 与原 admin 的 ImportAgentGateway 已统一归入 Java agent，admin 单向调用 agent，见 [Java Agent 模块目标设计](./directory-structure.md#business-java-agent-模块目标设计)。

### 3. Contracts / 迁移约束

- 以搬迁、调整依赖与调用方为主，保留已有实现逻辑；不另写一套 Redis、限流、MinIO、Resend 生产实现。
- 对每项能力同时核对实现、接口、调用方、配置、依赖声明和测试；旧路径不能保留仍被装配的副本。
- app 保留应用配置入口和组合装配；基础设施不得反向依赖 app 的类型。
- 业务模块依赖 infrastructure 的公开能力接口；供应商实现与 SDK 使用限制在 infrastructure 内部，app 负责装配。通用技术能力不反向依赖 client/admin/agent/auth/log/app 的实现。
- 同模块内按能力组织公开接口与实现，例如 `infrastructure.email.EmailGateway` 与 `infrastructure.email.resend.ResendEmailGateway`，`infrastructure.storage.ImageStorageGateway` 与 `infrastructure.storage.minio.MinioImageStorageGateway`。业务方不得直接构造或引用供应商实现。
- 接口迁移同时更新实现的 implements、全部消费者与测试 import、Maven 依赖和装配扫描；不在旧业务包中保留平行接口来掩盖循环依赖。
- 不要求给每个 Redis 薄封装机械新增接口；已有通用接口统一归属，新增抽象必须有实际使用需求。专属 Agent 导入接口不能仅因后缀为 Gateway 就视为通用技术接口。
- 邮件收件人、模板内容、业务触发时机仍由 client 等业务所有者决定；限流配额和业务成功后的 reset 时机由使用方决定。
- 保留现有配置 key、单位、默认值和外部协议。供应商 SDK 类型不得暴露给业务；图片接口目前接受 MultipartFile，不因本次搬迁擅自改签名。

### 4. Validation & Error Matrix

| 场景 | 迁移要求 |
|---|---|
| 限流计数返回 null | 保持现有 allowOrCount 返回 true 的逻辑 |
| 超出限额 | 保持拒绝行为和既有 HTTP 429 映射 |
| Redis 抛异常 | 按 RedisUtil 实现和调用方核对，不凭注释声称所有故障均放行 |
| 图片校验/上传或邮件发送失败 | 保留当前错误映射，不吞错或返回伪造成功结果 |
| 迁移后重复 Bean 或循环依赖 | 视为迁移未完成，不能靠同时保留两套实现交付 |

### 5. Good / Base / Bad Cases

- Good：现有 ResendEmailGateway 搬入新模块，配置与调用方同步调整，业务仍决定发送内容。
- Base：复用 RedisUtil 和 RateLimiter，保持计数、窗口、reset 及错误语义。
- Bad：新建 InfrastructureRedisUtil，同时让 common.RedisUtil 继续承担实际生产调用；或把会话、收藏规则一并塞入 infrastructure。

### 6. Tests Required

- Maven 依赖图无循环；通用技术能力不反向依赖业务实现或 app；业务调用方不再引用迁出的旧接口/实现路径，也不直接依赖供应商实现或 SDK 类型。
- 配置与上下文验证：所需 Bean 唯一注册，MinIO 初始化和邮件客户端配置行为保持一致。
- Redis/限流覆盖窗口、超限、reset 与故障行为；图片/邮件覆盖成功及原有失败路径，迁移已有测试而非只新增空模块测试。
- 清理审查：旧实现、旧扫描/导入、冗余依赖与旧测试路径同步处理；运行相关模块及完整 Business 构建测试。

### 7. Wrong vs Correct

- Wrong：只新增 infrastructure 模块，把现有 common/app 技术实现标记为以后再搬，却宣称迁移完成。
- Correct：逐项完成现有实现、调用、配置、依赖和测试的迁移，旧生产实现不再残留，验证通过后再标记实施完成。

证据目录：`backend/business/infrastructure/src/main/java/top/zhaizz/infrastructure/{redis,ratelimit,storage,email}`、`backend/business/agent/src/main/java/top/zhaizz/agent/gateway`、`backend/business/app/src/main/java/top/zhaizz/app/config/AgentConfig.java`。

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
- 复用现有 HTTP 实现，迁移接口、调用方、配置和测试，不保留旧 app 实现副本。

### 4. Validation & Error Matrix

| 条件 | 保留语义 |
|---|---|
| 不支持的 mode，或 season 缺 key / since 缺 since | admin 返回 BAD_REQUEST，不调用上游 |
| 上游 409 | CONFLICT，已有导入任务运行中 |
| 其他上游 4xx / 5xx | 分别为 BAD_REQUEST / INTERNAL_ERROR |
| 网络连接失败 | INTERNAL_ERROR，Agent 导入服务连接失败 |

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

### 7. Wrong vs Correct

- Wrong：admin → agent → admin，或 app → agent → app。
- Correct：admin → agent → pojo/common，app 单向装配下层模块；按实际使用显式声明依赖。

证据：`backend/business/admin/src/main/java/top/zhaizz/admin/service/impl/ImportServiceImpl.java`、`backend/business/agent/src/main/java/top/zhaizz/agent/gateway/ImportAgentGateway.java`、`backend/business/agent/src/main/java/top/zhaizz/agent/gateway/HttpImportAgentGateway.java`。
