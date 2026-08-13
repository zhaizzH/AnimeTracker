# AnimeTracker Business

Spring Boot 3.2 多模块后端（Java 21），提供番剧条目管理、剧集与进度、标签、用户认证与收藏等核心 API，并通过内置 `agent` 代理层将 AI 对话请求转发至独立的 Python Agent（见 [`../agent/README.md`](../agent/README.md)）。

- **项目坐标**：`top.zhaizz:business:2.0.0`
- **默认端口**：`8080`（Knife4j 文档：`/doc.html`）

## 模块结构

Maven 父子多模块，依赖方向 `app → {admin, client, agent} → {common, pojo}`：

```
business/
├── pom.xml          # 父 POM（依赖 / 插件版本统一管理）
├── common/          # 公共基础：Result/PageResult、异常、JWT、Redis、安全/CORS/MinIO 配置
├── pojo/            # entity / dto / vo（dto、vo 按领域子包分包）
├── admin/           # 管理端：条目 CRUD、用户管理、数据导入、仪表盘统计、操作日志
├── client/          # 用户端：认证、浏览/搜索、收藏、标签、剧集进度
├── agent/           # Agent 代理层：转发 /api/{client,admin}/agent/* 至 Python Agent
└── app/             # 启动模块：聚合 admin + client + agent，Spring Boot 入口
```

### 各模块职责

| 模块 | artifactId | 职责 |
|------|-----------|------|
| common | `animetracker-common` | 统一响应 `Result`/`PageResult`、全局异常处理、`JwtTokenProvider`/`JwtAuthenticationFilter`、RedisUtil、Security/Cors/MinIO 配置、`@OperationLog` 操作审计、`@RateLimit` 限流、`FileController`（MinIO 上传） |
| pojo | `animetracker-pojo` | `entity`（Subject、Episode、SubjectTag、SubjectRelation、User、UserCollection、ImportRecord、OperationLog）、`dto`（入参）、`vo`（出参） |
| admin | `animetracker-admin` | `AdminSubjectController`/`AdminUserController`/`AdminDashboardController`/`ImportController`/`AdminLogController` + Service/Converter/Mapper |
| client | `animetracker-client` | `AuthController`/`SubjectController`/`CollectionController`/`TagController`/`UserController` + Service/Converter/Mapper |
| agent | `animetracker-agent` | `ClientAgentController`（`/api/client/agent/*`）+ `AdminAgentController`（`/api/admin/agent/*`）+ `AgentService`：转发至 Python Agent（默认 `localhost:8090`），SSE 流式透传 |
| app | `animetracker-app` | 聚合 admin + client + agent，主类 `top.zhaizz.app.AppApplication`（`@MapperScan("top.zhaizz.**.mapper")`、`@EnableScheduling`） |

> **操作审计日志**：common 提供 `@OperationLog` 注解 + `OperationLogAspect` AOP 切面，自动记录后台操作（登录、注册、条目增删改、角色变更、导入等）到 `operation_log` 表；admin 经 `AdminLogController`/`AdminLogService` 提供查询接口。定时清理由 `OperationLogCleanupTask` 负责。

### pojo 分包

- `entity` 扁平存放（8 个实体，见上表）。
- `dto` / `vo` 按 8 个领域子包分包：`auth` / `user` / `subject` / `collection` / `log` / `dashboard` / `imprt` / `tag`（`import` 是 Java 关键字故用 `imprt`；dashboard、tag 仅出现在 vo）。当前 `dto` 用到 6 个子包、`vo` 用到全部 8 个。
- 命名后缀：入参/请求体 `XxxDTO`、列表/查询筛选 `XxxQueryDTO`、出参 `XxxVO`；DTO 约束注解一律带中文 `message`。

## 分层约定

每个业务模块统一分层，entity↔vo/dto 转换一律走 converter 包，禁止在 service/controller 手写转换：

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
- 安全层 401/403 走 `SecurityConfig.writeJson`；业务异常 / 参数校验走 `GlobalExceptionHandler`。
- 响应体统一 `{code, message, data}`；禁止向客户端透传内部细节（resourcePath、SQL、堆栈）。

## 关键依赖

- MyBatis-Plus `3.5.5`、JJWT `0.12.3`、Lombok `1.18.30`
- MinIO `8.5.7`（对象存储）、Resend `3.1.0`（邮件验证）
- Java 21 + Maven 3.9+（maven-enforcer-plugin 强制）

## 本地运行

```bash
# 构建全部模块
mvn clean install -DskipTests

# 启动（app 模块聚合了 admin、client 与 agent）
mvn -pl app spring-boot:run -Dspring-boot.run.profiles.active=local
# 或指定 profile 直接运行 jar：
# java -jar app/target/animetracker-app-*.jar
```

配置文件位于 `app/src/main/resources`：

- `application.yml` —— 主配置（默认激活 `local`，含 HikariCP / Lettuce 连接池、Jackson 日期格式、MyBatis-Plus、multipart 限制等）
- `application-local.yml` —— 本地开发覆盖（数据源、Redis、JWT、MinIO、Agent 地址等）
- `application-template.yml` —— 模板文件（敏感值用 `<placeholder>` 占位，供新开发者复制）

需配置：

- `zzz.datasource` —— MySQL 连接（库名 `anime_tracker`）
- `zzz.data.redis` —— Redis 连接
- `jwt.secret` / `jwt.expiration` / `jwt.refresh-expiration` —— JWT 签名密钥与有效期
- `minio.*` —— 对象存储（endpoint / key / bucket）
- `resend.api-key` —— 邮件验证服务密钥
- `at.agent.host` / `at.agent.port` —— Python Agent 服务地址（默认 `localhost:8090`）

## 数据库与 MyBatis XML

建表脚本见 [`../../docs/database/db-schema.sql`](../../docs/database/db-schema.sql)。MyBatis-Plus 配置 `mapper-locations: classpath*:mapper/*.xml`，自动扫描各模块 `src/main/resources/mapper/`：

| 模块 | XML 文件 |
|------|---------|
| admin | `DashboardMapper.xml` |
| client | `SubjectMapper.xml`、`EpisodeMapper.xml`、`SubjectTagMapper.xml`、`CollectionMapper.xml`、`SubjectRelationMapper.xml` |

> common 的 `OperationLogMapper` 使用 MyBatis-Plus 注解方式，无 XML 文件。

## 测试

测试类位于 `app/src/test/`，使用 Spring Boot Test + H2 内存数据库，共 11 个：

| 分组 | 测试类 |
|------|--------|
| 认证 / 收藏 | `AuthServiceImplTest`、`CollectionServiceImplTest`、`VerificationServiceImplTest` |
| 导入 / 仪表盘 | `ImportServiceImplTest`、`DashboardMapperTest` |
| 审计 / 限流 | `OperationLogAspectTest`、`OperationLogCleanupTaskTest`、`RateLimiterTest`、`RateLimitAspectTest` |
| 异常 / 校验 | `GlobalExceptionHandlerTest`、`SubjectScheduleValidationTest` |

## 相关文档

- 后端总览：[`../README.md`](../README.md)
- AI Agent：[`../agent/README.md`](../agent/README.md)
- 项目总览：[`../../README.md`](../../README.md)
- 前端总览：[`../../frontend/README.md`](../../frontend/README.md)
- 后端 API 文档：[`../../docs/spec/openapi.yaml`](../../docs/spec/openapi.yaml)
