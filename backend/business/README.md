# AnimeTracker Business

Spring Boot 3.2 多模块后端，提供番剧条目管理、剧集与进度、标签、用户认证与收藏等核心 API，并通过内置的 `agent` 代理层将 AI 对话请求转发至独立的 Python Agent 服务。

- **项目坐标**：`top.zhaizz:business:2.0.0`
- **默认端口**：`8080`（Knife4j 文档：`/doc.html`）

## 模块结构

采用 Maven 父子模块架构，依赖方向 `app → {admin, client, agent} → {common, pojo}`：

```
business/
├── pom.xml          # 父 POM（依赖管理、插件管理）
├── common/          # 公共基础：Result/PageResult、异常、JWT、Redis、安全配置、MinIO
├── pojo/            # 实体 / DTO / VO（entity、dto、vo 包）
├── admin/           # 管理端：条目 CRUD、用户管理、数据导入、仪表盘统计、操作审计日志
├── client/          # 用户端：浏览/搜索、认证、收藏、标签、剧集进度
├── agent/           # Agent 代理层：转发 /api/agent/* 至 Python Agent 服务
└── app/             # 启动模块：聚合 admin + client + agent，Spring Boot 入口
```

### 各模块职责

| 模块 | artifactId | 说明 |
|------|-----------|------|
| common | `animetracker-common` | 统一响应 `Result`/`PageResult`、全局异常处理、`JwtTokenProvider`/`JwtAuthenticationFilter`、RedisUtil、Security/Cors/MinIO 配置 |
| pojo | `animetracker-pojo` | `entity`（Subject、Episode、User、UserCollection…）、`dto`（入参）、`vo`（出参） |
| admin | `animetracker-admin` | `AdminSubjectController`/`AdminDashboardController`/`AdminUserController`/`ImportController`/`AdminLogController` + Service/Converter/Mapper |
| client | `animetracker-client` | `Auth`/`Subject`/`Collection`/`Tag`/`User` Controller + Service/Mapper/Converter |
| agent | `animetracker-agent` | `AgentController`/`AgentService`：将 `/api/agent/*` 转发至 Python Agent（默认 `http://localhost:8090`），SSE 流式透传 |
| app | `animetracker-app` | 聚合 admin + client + agent，含主类 `top.zhaizz.app.AppApplication` |

> **操作审计日志**：admin 模块通过 `AdminLogController` / `AdminLogService` 落库 `operation_log` 表，记录登录、注册、条目增删改、角色变更、导入任务等后台操作（含操作人、动作、模块、IP、耗时、成败状态），供运营后台「日志」页审计追溯。

## 分层约定

每个业务模块统一分层：

```
controller/   # 接收 HTTP 请求，参数校验
service/      # 业务逻辑（impl/ 为实现）
mapper/       # MyBatis-Plus Mapper 接口
converter/    # 实体 ⇄ DTO/VO 转换
```

## 关键依赖（父 POM 统一管理版本）

- MyBatis-Plus `3.5.5`、JJWT `0.12.3`、Lombok `1.18.30`
- MinIO `8.5.7`（对象存储）、Resend `3.1.0`（邮件验证）
- Java 21 + Maven 3.9+（由 maven-enforcer-plugin 强制）

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

- `application.yml` —— 生产配置（默认激活 `local` profile）
- `application-local.yml` —— 本地覆盖（数据源、Redis、JWT、MinIO、Agent 地址等）

需配置：

- `zzz.datasource` —— MySQL 连接（库名 `anime_tracker`）
- `zzz.data.redis` —— Redis 连接
- `jwt.secret` / `jwt.expiration` —— JWT 签名密钥与有效期
- `minio.*` —— 对象存储（endpoint / key / bucket）
- `at.agent.host` / `at.agent.port` —— Python Agent 服务地址（默认 `localhost:8090`）

## 数据库

建表脚本见项目根 [`../../docs/db-schema.sql`](../../docs/db-schema.sql)。
