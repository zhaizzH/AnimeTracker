# AnimeTracker Business

Spring Boot 3.2 多模块后端（Java 21），提供番剧条目管理、剧集与进度、标签、用户认证与收藏等核心 API，并通过内置 `agent` 代理层将 AI 对话请求转发至独立的 Python Agent（见 [`../agent/README.md`](../agent/README.md)）。

- **项目坐标**：`top.zhaizz:business:2.0.0`
- **默认端口**：`8080`（Knife4j 文档：`/doc.html`）

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
| common | `animetracker-common` | 统一响应、异常、JWT/Redis、操作审计、限流和共享外部端口 |
| pojo | `animetracker-pojo` | 共享 entity、dto、vo 数据模型 |
| admin | `animetracker-admin` | 管理端 Controller → Service → Mapper/Store；持有 `ImportAgentGateway` 端口 |
| client | `animetracker-client` | 用户端 Controller → Service → Mapper/Store；持有 `EmailGateway` 端口 |
| agent | `animetracker-agent` | Controller → `AgentService` → `AgentServiceImpl`，代理 Python Agent |
| app | `animetracker-app` | 启动、安全策略和 `infrastructure` 下的 MinIO、Resend、导入 HTTP 实现 |

外部端口由消费者模块定义，运行时实现由 `app.infrastructure` 装配：共享 `common.storage.ImageStorageGateway` 的 MinIO 实现在 `app.infrastructure.storage.minio`；`client.gateway.EmailGateway` 的 Resend 实现在 `app.infrastructure.email`；`admin.gateway.ImportAgentGateway` 的 HTTP 实现在 `app.infrastructure.agent`。

### pojo 分包

- `entity` 扁平存放（8 个实体，见上表）。
- `dto` / `vo` 按 8 个领域子包分包：`auth` / `user` / `subject` / `collection` / `log` / `dashboard` / `imprt` / `tag`（`import` 是 Java 关键字故用 `imprt`；dashboard、tag 仅出现在 vo）。当前 `dto` 用到 6 个子包、`vo` 用到全部 8 个。
- 命名后缀：入参/请求体 `XxxDTO`、列表/查询筛选 `XxxQueryDTO`、出参 `XxxVO`；DTO 约束注解一律带中文 `message`。

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

## 关键依赖

- MyBatis-Plus `3.5.5`、JJWT `0.12.3`、Lombok `1.18.30`
- MinIO `8.5.7`（对象存储）、Resend `3.1.0`（邮件验证）
- Java 21 + Maven 3.9+（maven-enforcer-plugin 强制）

## 本地运行

```bash
# 构建全部模块
mvn clean install -DskipTests

# 启动（app 模块聚合了 admin、client 与 agent）
mvn -pl app spring-boot:run -Dspring-boot.run.arguments=--spring.profiles.active=local
# 或指定 profile 直接运行 jar：
# java -jar app/target/animetracker-app-*.jar --spring.profiles.active=local
```

配置文件位于 `app/src/main/resources`：

- `application.yml` —— 主配置（不默认激活 `local`；本地运行需显式使用 `--spring.profiles.active=local`，含 HikariCP / Lettuce 连接池、Jackson 日期格式、MyBatis-Plus、multipart 限制等）
- `application-local.yml` —— 本地开发覆盖（数据源、Redis、JWT、MinIO、Agent 地址等）

数据库结构不使用 Flyway，统一由项目级 `docs/database/db-schema.sql` 维护；新环境手动执行该脚本建表。

需配置：

- `at.datasource` —— MySQL 连接（库名 `anime_tracker`）
- `at.data.redis` —— Redis 连接
- `jwt.secret` / `jwt.expiration` / `jwt.refresh-expiration` —— JWT 签名密钥与有效期
- `minio.*` —— 对象存储（endpoint / key / bucket）
- `resend.api-key` —— 邮件验证服务密钥
- `at.agent.host` / `at.agent.port` —— Python Agent 服务地址（默认 `localhost:8090`）

## 数据库与 MyBatis XML

建表脚本见 [`../../docs/database/db-schema.sql`](../../docs/database/db-schema.sql)。MyBatis-Plus 配置 `mapper-locations: classpath*:mapper/*.xml`，自动扫描各模块 `src/main/resources/mapper/`：

| 模块 | XML 文件 |
|------|---------|
| admin | `AdminLogMapper.xml`、`DashboardMapper.xml` |
| client | `CollectionMapper.xml`、`SubjectMapper.xml`、`SubjectTagMapper.xml` |

> common 的 `OperationLogMapper` 使用 MyBatis-Plus 注解方式，无 XML 文件。

## 测试

测试清单以各模块的 `src/test/java` 为准。运行全部业务测试：

```bash
mvn test
```

## 相关文档

- 后端总览：[`../README.md`](../README.md)
- AI Agent：[`../agent/README.md`](../agent/README.md)
- 项目总览：[`../../README.md`](../../README.md)
- 后端 API 文档：[`../../docs/spec/openapi.yaml`](../../docs/spec/openapi.yaml)
