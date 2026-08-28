# AnimeTracker Business

> **一句话定位**：Spring Boot 3.2.0 多模块后端（Java 21），提供番剧条目、剧集与进度、标签、用户认证与收藏等核心 API，并通过内置 `agent` 代理层将 AI 对话请求转发至独立的 Python Agent。

> 上级文档：[后端总览](../README.md) · [项目总览](../../README.md)

## 适用场景

- 为 AnimeTracker 用户端与管理端提供全部 REST API。
- 承载认证与会话（Access Token + HttpOnly 刷新 Cookie）、操作审计、限流与对象存储接入。
- 作为 Python Agent 的唯一对外代理：前端不直连 Agent，所有 `/api/{client,admin}/agent/**` 请求经本服务转发。

- **项目坐标**：`top.zhaizz:business:2.0.0`
- **默认端口**：`8080`
- **健康检查**：`/actuator/health`（liveness 仅看进程；readiness 要求 MySQL 与 Redis）
- **接口文档**：本模块未集成 Knife4j / springdoc，接口定义见 [`../../docs/spec/openapi.yaml`](../../docs/spec/openapi.yaml)

## 前置依赖

| 组件 | 版本 | 校验方式 |
|------|------|---------|
| JDK | 21 及以上 | `maven-enforcer-plugin` 强制 `[21,)` |
| Maven | 3.9 及以上 | `maven-enforcer-plugin` 强制 `[3.9,)` |
| MySQL | 8 | 库名 `anime_tracker`，建表脚本见 [`../../docs/database/db-schema.sql`](../../docs/database/db-schema.sql) |
| Redis | 5+ 协议兼容 | 会话、限流、缓存 |
| MinIO | 任意近期版本 | 头像与封面存储（缺失时上传类接口不可用） |

## 模块结构

Maven 父子多模块保持六个模块。依赖方向如下：

```text
app → {admin, client, agent, common}
admin → {common, pojo}
client → {common, pojo}
agent → common → pojo
```

```
business/
├── pom.xml          # 父 POM（依赖 / 插件版本统一管理）
├── common/          # 共享平台能力与多业务模块共用的外部端口
├── pojo/            # 共享 entity / dto / vo 数据模型
├── admin/           # 管理端 Controller → Service → Mapper/Store 与管理端 Gateway 端口
├── client/          # 用户端 Controller → Service → Mapper/Store 与用户端 Gateway 端口
├── agent/           # Python Agent 代理：Controller → AgentService → AgentServiceImpl
└── app/             # Spring Boot 组合根、安全策略与 runtime infrastructure 适配器
```

### 各模块职责

| 模块 | artifactId | 职责 |
|------|-----------|------|
| common | `animetracker-common` | 统一响应、异常、JWT/Redis、操作审计、限流和共享外部端口（含 `OperationLogMapper`） |
| pojo | `animetracker-pojo` | 共享 entity、dto、vo 数据模型 |
| admin | `animetracker-admin` | 管理端 Controller → Service → Mapper/Store；持有 `ImportAgentGateway` 端口 |
| client | `animetracker-client` | 用户端 Controller → Service → Mapper/Store；持有 `EmailGateway` 端口 |
| agent | `animetracker-agent` | `ClientAgentController` / `AdminAgentController` → AgentService，代理 Python Agent |
| app | `animetracker-app` | 启动、安全策略和 `infrastructure` 下的 MinIO、Resend、导入 HTTP 实现 |

外部端口由消费者模块定义，运行时实现由 `app.infrastructure` 装配：共享 `common.storage.ImageStorageGateway` 的 MinIO 实现在 `app.infrastructure.storage.minio`；`client.gateway.EmailGateway` 的 Resend 实现在 `app.infrastructure.email`；`admin.gateway.ImportAgentGateway` 的 HTTP 实现在 `app.infrastructure.agent`。

### Controller 清单

| 模块 | Controller |
|------|-----------|
| admin | `AdminDashboardController`、`AdminFileController`、`AdminLogController`、`AdminSubjectController`、`AdminUserController`、`ImportController` |
| client | `AuthController`、`ClientFileController`、`CollectionController`、`CollectionProgressController`、`SubjectController`、`TagController`、`UserController` |
| agent | `AdminAgentController`、`ClientAgentController` |

### pojo 分包

- `entity` 扁平存放，共 8 个实体：`Episode`、`ImportRecord`、`OperationLog`、`Subject`、`SubjectRelation`、`SubjectTag`、`User`、`UserCollection`。
- `dto` 按 6 个领域子包分包：`auth` / `collection` / `imprt` / `log` / `subject` / `user`。
- `vo` 按 8 个领域子包分包：`auth` / `collection` / `dashboard` / `imprt` / `log` / `subject` / `tag` / `user`。
- `import` 是 Java 关键字，故导入相关包统一命名为 `imprt`。
- 命名后缀：入参/请求体 `XxxDTO`、列表/查询筛选 `XxxQueryDTO`、出参 `XxxVO`；DTO 约束注解一律带中文 `message`。

> pojo 模块要求所有字段都加 Javadoc 注释，entity 按 `docs/database/db-schema.sql` 描述撰写，详见 [`../../docs/conventions/backend-conventions.md`](../../docs/conventions/backend-conventions.md)。

## 分层约定

`admin` 与 `client` 统一采用 Controller → Service → Mapper/Store 分层。entity↔vo/dto 转换中复杂或可复用的部分集中到 converter 包，简单映射可在 service 内完成；controller 不承载转换逻辑：

```
controller/   # 参数绑定 + SecurityUtil 取身份 + 调 service（无业务逻辑、无 SQL）
service/      # 业务逻辑（impl/ 为实现）
mapper/       # MyBatis-Plus Mapper 接口
converter/    # 实体 ⇄ DTO/VO 转换
```

### controller 参数 / 返回

- 单参 / `@PathVariable` / `@RequestHeader` / multipart / 仅 page/size → 不折叠 DTO，校验留在方法签名（类级 `@Validated`）。
- 两个及以上 query/body 字段 → 收进一个 DTO，形参名固定 `request`；query 一律 model-attribute 绑定，`@RequestBody` 仅 POST/PUT JSON body。
- 返回一律 `Result<T>`，分页 `PageResult<T>`；分页默认 page=1、size=20、上限 `@Max(100)`（导入记录例外：默认 10、上限 1000）。

### 错误拦截

- 错误码 = HTTP 状态码，统一 `ErrorType` 枚举 + `BizException`；Service 层 `throw new BizException(ErrorType.X, "中文消息")`。
- 安全层 401/403 走 app 模块的 `SecurityConfig.writeJson`；业务异常 / 参数校验走 `GlobalExceptionHandler`。
- 响应体统一 `{code, message, data}`；禁止向客户端透传内部细节（resourcePath、SQL、堆栈）。
- `DataIntegrityViolationException` → 409，方法级鉴权失败 → 403，未知异常 → 500。

完整规范见 [`../../docs/conventions/backend-conventions.md`](../../docs/conventions/backend-conventions.md)。

## 关键依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| MyBatis-Plus | `3.5.5` | ORM |
| JJWT | `0.12.3` | JWT 签名与验签 |
| Lombok | `1.18.30` | 代码简化（`provided`） |
| MinIO | `8.5.7` | 对象存储 |
| Resend Java | `3.1.0` | 邮件验证 |
| ArchUnit | `1.5.0` | 模块边界守卫（已在 app 模块引入，尚无测试类落地） |
| Logstash Logback Encoder | `7.4` | 单行 JSON 结构化日志 |
| Spring Boot | `3.2.0` | 父 POM |

## 快速开始

```bash
# 构建全部模块
mvn clean install -DskipTests

# 启动（app 模块聚合了 admin、client 与 agent）
mvn -pl app spring-boot:run -Dspring-boot.run.arguments=--spring.profiles.active=local

# 或打包后运行 jar
java -jar app/target/animetracker-app-*.jar --spring.profiles.active=local
```

配置文件位于 `app/src/main/resources`：

- `application.yml` —— 主配置，**不默认激活 `local`**；本地运行需显式传 `--spring.profiles.active=local`。包含 HikariCP / Lettuce 连接池、Jackson 日期格式、MyBatis-Plus、multipart 限制、Actuator 与 JWT 默认值。
- `application-local.yml` —— 本地开发覆盖（数据源、Redis、JWT、MinIO、Resend、Agent 地址）。该文件已被 `.gitignore` 忽略，可安全填写真实密钥。
- `logback-spring.xml` —— 结构化 JSON 日志格式。

数据库结构不使用 Flyway（`spring.sql.init.mode: never`），统一由项目级 [`../../docs/database/db-schema.sql`](../../docs/database/db-schema.sql) 维护；新环境手动执行该脚本建表。

### 需配置的关键项

| 配置 | 说明 |
|------|------|
| `at.datasource.host` / `port` / `database` / `username` / `password` | MySQL 连接（默认库名 `anime_tracker`） |
| `at.data.redis.host` / `port` / `password` / `database` | Redis 连接（默认 database=1） |
| `at.jwt.secret` / `expiration` / `refresh-expiration` / `max-session-expiration` | JWT 签名密钥与有效期；**必须与 Agent 的 `JWT_SECRET` 一致** |
| `minio.host` / `port`、`at.minio.access-key` / `secret-key` / `bucket` | 对象存储 |
| `at.resend.api-key` / `send-email` | 邮件验证服务 |
| `at.agent.host` / `port` | Python Agent 服务地址（默认 `localhost:8090`） |
| `at.cors.allowed-origins` | CORS 白名单，逗号分隔（本地默认含 `5173`、`5174`） |
| `AT_AUTH_COOKIE_SECURE` | 刷新 Cookie 是否启用 Secure，默认 `true`；本地 HTTP 需显式设为 `false` |
| `at.admin.superadmin-id` | 管理员用户 ID，默认 `1` |

## 核心用法示例

### 用户注册与登录

```bash
# 注册（随后需邮箱验证）
curl -X POST http://localhost:8080/api/client/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"Secret123!"}'

# 登录：响应体只含短期 accessToken 与用户信息，刷新凭据写入 at_refresh Cookie
curl -i -X POST http://localhost:8080/api/client/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"Secret123!"}'

# 刷新（依赖浏览器自动回传 Cookie）
curl -X POST http://localhost:8080/api/client/auth/refresh \
  -H "Origin: http://localhost:5173" \
  -b "at_refresh=<refresh-token>"
```

### 浏览与收藏

```bash
# 按季度浏览
curl "http://localhost:8080/api/client/subjects/season?year=2026&quarter=3&page=1&size=20"

# 加入想看（业务侧保证不覆盖已有收藏）
curl -X POST http://localhost:8080/api/client/collections/123/wishlist \
  -H "Authorization: Bearer <access-token>"

# 追番进度预览 → 执行（Agent 侧两段式确认的业务支撑接口）
curl -X POST http://localhost:8080/api/client/collections/progress-preview \
  -H "Authorization: Bearer <access-token>"
curl -X POST "http://localhost:8080/api/client/collections/progress-preview/<previewId>/execute" \
  -H "Authorization: Bearer <access-token>"
```

### 转发 Agent 流式对话

```bash
curl -N -X POST http://localhost:8080/api/client/agent/stream \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": null, "message": "我最近想看轻松的日常番"}'
```

business 的 `agent` 模块会把请求代理到 `http://${at.agent.host}:${at.agent.port}`，连接超时 10s、读取超时 30s。

## 数据库与 MyBatis XML

建表脚本见 [`../../docs/database/db-schema.sql`](../../docs/database/db-schema.sql)。MyBatis-Plus 配置 `mapper-locations: classpath*:mapper/*.xml`，自动扫描各模块 `src/main/resources/mapper/`：

| 模块 | XML 文件 |
|------|---------|
| admin | `AdminLogMapper.xml`、`DashboardMapper.xml` |
| client | `CollectionMapper.xml`、`SubjectMapper.xml`、`SubjectTagMapper.xml` |

> common 的 `OperationLogMapper` 使用 MyBatis-Plus 注解方式，无 XML 文件。

脚本包含 12 张表：`episode`、`import_record`、`operation_log`、`rag_index_job`、`subject`、`subject_alias`、`subject_credit`、`subject_meta_tag`、`subject_relation`、`subject_tag`、`user`、`user_collection`。其中 `rag_index_job` 由 Agent 的 `jobs/indexer` 读写，business 不直接操作。

## 测试

当前 `app/src/test` 与 `client/src/test` 目录存在但**没有任何测试类**。运行全部业务测试：

```bash
mvn test
```

父 POM 已引入 `spring-boot-starter-test`、`spring-security-test`、`h2` 与 `archunit-junit5`，可直接新增单元测试或架构约束测试。Agent 侧的有效测试位于 [`../agent/tests/`](../agent/tests/)。

## 常见问题

**Q：启动时报 `Could not resolve placeholder 'at.cors.origins'`？**
A：`application.yml` 中 `at.cors.allowed-origins` 取自 `${at.cors.origins}`，没有默认值。必须在 `application-local.yml` 或环境变量中显式配置。

**Q：为什么改了 `minio.*` 没生效？**
A：endpoint 由 `minio.host` / `minio.port` 拼接，而凭据与桶名在 `at.minio.*` 下，两组前缀不一致，容易只改一半。

**Q：Actuator health 显示 DOWN 但服务能用？**
A：readiness 组只包含 `db` 与 `redis`，任一不可用即 DOWN。liveness 只看进程状态。MinIO 与 Agent 不参与就绪判定。

**Q：登录接口响应里没有 refresh token？**
A：这是预期设计。刷新凭据只通过 `at_refresh` HttpOnly Cookie 下发，前端不应也无法从 JS 读取。

**Q：本地刷新接口返回 401/403？**
A：检查 `AT_AUTH_COOKIE_SECURE` 是否为 `false`（HTTP 环境下 Secure Cookie 不会被回传），以及 `at.cors.allowed-origins` 是否包含请求 `Origin`——刷新与退出接口会校验 Origin。

**Q：上传头像/封面失败？**
A：确认 MinIO 已启动且 `at.minio.bucket` 对应的桶已存在。multipart 限制为单文件 5MB、单请求 10MB。

## 与相邻模块的关联

- **Python Agent**（[`../agent/README.md`](../agent/README.md)）：business 通过 `at.agent.*` 指向它；两者共享 `JWT_SECRET`，Agent 本地验签。
- **共享数据库**：`rag_index_job` 与 `import_record` 由 Agent 侧 `jobs/` 写入，business 只读展示。
- **文档**：接口规范 [`../../docs/spec/openapi.yaml`](../../docs/spec/openapi.yaml)、编码规范 [`../../docs/conventions/backend-conventions.md`](../../docs/conventions/backend-conventions.md)。
- **后端总览**：[`../README.md`](../README.md) · **项目总览**：[`../../README.md`](../../README.md)

## 待补充

1. **测试用例**：`app/src/test` 与 `client/src/test` 为空，ArchUnit 模块边界守卫（父 POM 已声明依赖）尚未落地，规划待确认。
2. **管理端细粒度权限**：`at.admin.superadmin-id` 表明当前以超级管理员 ID 做粗粒度控制，角色与权限矩阵未在代码中形成可文档化的规则。
3. **邮件验证的本地替代**：`application-local.yml` 中的 Resend Key 为真实凭据示例，本地无网络或无 Key 时的降级路径（如打印验证码到日志）未在代码中体现。
