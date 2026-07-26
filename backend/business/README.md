# AnimeTracker Business

Spring Boot 3.2 多模块后端，提供番剧条目管理、剧集与进度、标签、用户认证与收藏等核心 API。

- **项目坐标**：`top.zhaizz:business:2.0.0`
- **默认端口**：`8080`（Knife4j 文档：`/doc.html`）

## 模块结构

采用 Maven 父子模块架构，依赖方向 `app → {admin, client} → {common, pojo}`：

```
business/
├── pom.xml          # 父 POM（依赖管理、插件管理）
├── common/          # 公共基础：Result/PageResult、异常、JWT、Redis、安全配置、MinIO
├── pojo/            # 实体 / DTO / VO（entity、dto、vo 包）
├── admin/           # 管理端：条目 CRUD、用户管理、数据导入
├── client/          # 用户端：浏览/搜索、认证、收藏、标签、剧集进度
└── app/             # 启动模块：聚合 admin + client，Spring Boot 入口
```

### 各模块职责

| 模块 | artifactId | 说明 |
|------|-----------|------|
| common | `animetracker-common` | 统一响应 `Result`/`PageResult`、全局异常处理、`JwtTokenProvider`/`JwtAuthenticationFilter`、RedisUtil、Security/Cors/MinIO 配置 |
| pojo | `animetracker-pojo` | `entity`（Subject、Episode、User、UserCollection…）、`dto`（入参）、`vo`（出参） |
| admin | `animetracker-admin` | `AdminController`/`AdminUserController`/`ImportController` + Service/Converter/Mapper |
| client | `animetracker-client` | `Auth`/`Subject`/`Collection`/`Tag`/`User` Controller + Service/Mapper/Converter |
| app | `animetracker-app` | 聚合 admin + client，含主类 `top.zhaizz.app.AppApplication` |

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
mvn clean package -DskipTests

# 启动（app 模块聚合了 admin 与 client）
java -jar app/target/animetracker-app-*.jar
```

配置文件（如 `application.yml`）位于 `app/src/main/resources`，需配置：

- `spring.datasource` —— MySQL 连接
- `spring.data.redis` —— Redis 连接
- `minio` —— 对象存储（endpoint / key / bucket）
- `jwt.secret` —— JWT 签名密钥

## 数据库

建表脚本见项目根 `docs/db-schema.sql`；更细分的 DDL 位于 `../docs/sql`。
