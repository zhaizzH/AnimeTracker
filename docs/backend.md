# AnimeTracker 后端文档

> 个人动漫追番平台 — 后端 API 服务

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术栈](#2-技术栈)
3. [模块结构](#3-模块结构)
4. [快速启动](#4-快速启动)
5. [API 接口文档](#5-api-接口文档)
6. [数据库设计](#6-数据库设计)
7. [安全认证](#7-安全认证)
8. [错误码](#8-错误码)
9. [部署与构建](#9-部署与构建)

---

## 1. 项目概述

AnimeTracker 是一个个人动漫追番管理平台，后端基于 Spring Boot 3.2 构建，采用 Maven 多模块架构。提供番剧条目管理、剧集管理、标签管理、用户认证与管理、数据导入等功能。

- **项目坐标**: `top.zhaizz:business:2.0.0`
- **启动类**: `top.zhaizz.app.AppApplication`
- **主配置文件**: `application.yml` + `application-local.yml`（环境覆盖）

---

## 2. 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 语言 | Java | 21 |
| 框架 | Spring Boot | 3.2.0 |
| ORM | MyBatis-Plus | 3.5.5 |
| 数据库 | MySQL | 8.0+ |
| 缓存 | Redis (Lettuce) | — |
| 安全 | Spring Security + JWT (jjwt) | 0.12.3 |
| 构建 | Maven | 3.9+ |
| 工具 | Lombok | 1.18.30 |

---

## 3. 模块结构

```
backend/business/
├── pom.xml                     # 父 POM — 统一版本管理
├── common/                     # 公共模块
│   └── src/main/java/top/zhaizz/common/
│       ├── config/             # 全局配置（Security, CORS, MyBatis-Plus）
│       ├── security/           # JWT 认证（TokenProvider, Filter, UserPrincipal）
│       ├── exception/          # 全局异常处理
│       ├── result/             # 统一响应体（Result, PageResult）
│       ├── util/               # RedisClient
│       └── ErrorType.java      # 错误码枚举
├── pojo/                       # 数据模型模块
│   └── src/main/java/top/zhaizz/pojo/
│       ├── entity/             # 数据库实体（User, Subject, Episode, SubjectTag, ImportRecord）
│       ├── dto/                # 请求 DTO（Login, Register, SubjectCreate, SubjectUpdate 等）
│       └── vo/                 # 响应 VO（UserVO, SubjectListVO, SubjectDetailVO 等）
├── user/                       # 用户模块
│   └── src/main/java/top/zhaizz/user/
│       ├── controller/         # AuthController, UserController, AdminUserController
│       ├── service/            # AuthService, UserService
│       ├── service/impl/       # AuthServiceImpl, UserServiceImpl
│       ├── converter/          # UserConverter
│       └── mapper/             # UserMapper
├── subject/                    # 番剧模块
│   └── src/main/java/top/zhaizz/subject/
│       ├── controller/         # SubjectController, TagController, AdminController, ImportController
│       ├── service/            # SubjectService, EpisodeService, TagService, ImportService
│       ├── service/impl/       # 各服务实现
│       ├── converter/          # SubjectConverter
│       ├── mapper/             # SubjectMapper, EpisodeMapper, SubjectTagMapper, ImportRecordMapper
│       └── util/               # SeasonUtil（季度日期计算）
└── app/                        # 启动模块
    └── src/main/java/top/zhaizz/app/
        └── AppApplication.java # 应用入口
```

### 模块依赖关系

```
app ─┬── user ───┬── common
     │           └── pojo
     └── subject ─┬── common
                  └── pojo
```

### 关键包说明

| 包 | 功能 |
|----|------|
| `common.config` | `SecurityConfig` — Spring Security 安全规则；`CorsConfig` — 跨域放行；`MyBatisPlusConfig` — 分页插件 |
| `common.security` | `JwtTokenProvider` — Token 签发/解析；`JwtAuthenticationFilter` — 请求拦截认证；`UserPrincipal` — 认证用户上下文 |
| `common.exception` | `BizException` — 业务异常；`GlobalExceptionHandler` — 全局统一异常处理 |
| `common.result` | `Result<T>` — 统一 JSON 响应；`PageResult<T>` — 统一分页格式 |
| `subject.util` | `SeasonUtil` — 动漫季度（冬/春/夏/秋）日期范围计算 |

---

## 4. 快速启动

### 4.1 环境要求

- JDK 21+
- Maven 3.9+
- MySQL 8.0+
- Redis 6+

### 4.2 数据库初始化

```sql
-- 创建数据库
CREATE DATABASE anime_tracker DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 导入表结构（详见 docs/db-schema.sql）
mysql -u root -p anime_tracker < docs/db-schema.sql
```

### 4.3 配置文件

复制 `application-local.yml` 模板后填入实际配置：

```yaml
# backend/business/app/src/main/resources/application-local.yml
zzz:
  datasource:
    host: 127.0.0.1
    port: 3306
    database: anime_tracker
    username: root
    password: your-password
  data:
    redis:
      host: 127.0.0.1
      port: 6379
      database: 1

jwt:
  secret: your-256-bit-secret
  expiration: 86400000   # 24h
```

### 4.4 启动

```bash
cd backend/business
mvn clean install -DskipTests
mvn -pl app spring-boot:run
# 或指定 profile:
mvn -pl app spring-boot:run -Dspring-boot.run.profiles.active=local
```

服务默认监听 `http://localhost:8080`。

---

## 5. API 接口文档

### 5.1 认证接口 — `/api/user/auth`

#### POST `/api/user/auth/register` — 用户注册

**请求体** (`RegisterDTO`):

```json
{
  "username": "string (1~32, 必填)",
  "password": "string (6~128, 必填)",
  "email":    "string (邮箱格式, 可选)"
}
```

**响应** `200`:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "token": "jwt...",
    "user": {
      "id": 1,
      "username": "xxx",
      "email": "xxx@example.com",
      "nickname": "xxx",
      "role": "USER",
      "createdAt": "2026-01-01 12:00:00"
    }
  }
}
```

> 注册成功后自动登录，直接返回 JWT Token 和用户信息。

---

#### POST `/api/user/auth/login` — 用户登录

**请求体** (`LoginDTO`):

```json
{
  "username": "string (必填)",
  "password": "string (必填)"
}
```

**响应** `200`:

```json
{
  "code": 200, "message": "success",
  "data": { "token": "jwt...", "user": { ... } }
}
```

**错误** `401`:

```json
{ "code": 401, "message": "用户名或密码错误" }
```

---

#### GET `/api/user/auth/logout` — 用户注销

**请求头**: `Authorization: Bearer <token>`

**响应** `200`:

```json
{ "code": 200, "message": "success" }
```

> 服务端删除 Redis 中的 Token 白名单记录，后续该 Token 失效。

---

### 5.2 用户接口 — `/api/user`

> 以下接口需认证（请求头携带 `Authorization: Bearer <token>`）。

#### GET `/api/user/me` — 获取个人信息

**响应** `200`:

```json
{
  "code": 200, "message": "success",
  "data": { "id": 1, "username": "xxx", "email": "...", "nickname": "...", ... }
}
```

---

#### PUT `/api/user/me` — 修改个人信息

**请求体** (`UpdateUserDTO`，所有字段可选):

```json
{
  "nickname": "新昵称",
  "avatar": "https://...",
  "email": "new@example.com"
}
```

**响应** `200`: 返回更新后的 `UserVO`。

---

### 5.3 番剧接口 — `/api/user/subjects`

> `GET` 方法公开访问，无需认证。

#### GET `/api/user/subjects` — 番剧列表（分页 + 排序）

**查询参数**: `page`(默认1) `size`(默认20, 最大100) `sort`(默认score) `order`(默认desc)

| sort 可选值 | 说明 |
|-------------|------|
| `score` | 按评分排序 |
| `name` | 按名称排序 |
| `air_date` | 按播出日期排序 |
| `rank` | 按排名排序 |

**响应** `200`:

```json
{
  "code": 200, "message": "success",
  "data": {
    "content": [ { "id": 1, "name": "...", "nameCn": "...", "score": 8.5, ... } ],
    "total": 100,
    "page": 1,
    "size": 20
  }
}
```

---

#### GET `/api/user/subjects/search` — 搜索番剧

**查询参数**: `q`(关键词) `page`(默认1) `size`(默认20, 最大100)

> 关键词的匹配优先级：中文名匹配 > 日文/英文名匹配，同优先级内按评分降序。

---

#### GET `/api/user/subjects/season` — 按季度筛选

**查询参数**: `year`(1970~2100) `quarter`(spring/summer/autumn/winter) `page` `size`

- 日本动画季度划分：
  - 冬季: 1月1日 ~ 3月31日
  - 春季: 4月1日 ~ 6月30日
  - 夏季: 7月1日 ~ 9月30日
  - 秋季: 10月1日 ~ 12月31日

---

#### GET `/api/user/subjects/{id}` — 番剧详情（含标签）

**响应** `200`:

```json
{
  "code": 200, "message": "success",
  "data": {
    "id": 1, "name": "...", "nameCn": "...", "score": 8.5,
    "summary": "...", "bangumiId": 123, "rank": 100,
    "eps": 12, "airDate": "2026-01-05", "nsfw": false,
    "tags": [ { "id": 1, "name": "热血", "count": 5 } ],
    "createdAt": "2026-01-01T00:00:00"
  }
}
```

---

#### GET `/api/user/subjects/{id}/episodes` — 获取番剧剧集

**响应** `200`:

```json
{
  "code": 200, "message": "success",
  "data": [
    { "id": 1, "subjectId": 1, "type": 0, "sort": 1.0, "name": "第1话", "status": "Air", ... }
  ]
}
```

| 剧集类型 (`type`) | 说明 |
|-------------------|------|
| 0 | 本篇 |
| 1 | SP（特别篇）|
| 2 | OP（片头曲）|
| 3 | ED（片尾曲）|
| 4 | 预告 |

| 播出状态 (`status`) | 说明 |
|---------------------|------|
| `Air` | 已播出 |
| `Today` | 今日播出 |
| `NA` | 未播出 |

---

### 5.4 标签接口 — `/api/user/tags`

> `GET` 方法公开访问。

#### GET `/api/user/tags` — 获取标签列表

**响应**: `List<TagVO>`，按使用次数降序。

---

#### GET `/api/user/tags/{tag}/subjects` — 获取标签下的番剧

**查询参数**: `page`(默认1) `size`(默认20, 最大100)

---

### 5.5 管理接口 — `/api/admin/*`

> 以下接口需 `ADMIN` 角色。

#### 用户管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/users` | 分页查看所有用户 |
| PUT | `/api/admin/users/{id}/role` | 修改用户角色（`USER` / `ADMIN`，id=1 不可修改）|

**PUT 请求体** (`UpdateRoleDTO`):

```json
{ "role": "ADMIN" }
```

> 管理员角色（id=1）不能被修改。

---

#### 番剧管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/admin/subjects` | 创建新番剧 |
| PUT | `/api/admin/subjects/{id}` | 更新番剧信息（所有字段可选）|
| DELETE | `/api/admin/subjects/{id}` | 删除番剧 |

**POST 请求体** (`SubjectCreateDTO`):

```json
{
  "name": "名称 (必填)",
  "nameCn": "中文名",
  "summary": "简介",
  "type": 2,
  "eps": 12,
  "bangumiId": 123,
  "airDate": "2026-01-01",
  "image": "https://..."
}
```

> 如果 `bangumiId` 已存在，返回 409 冲突错误。

---

#### 数据导入

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/admin/import/run` | 触发数据导入（桩实现，实际由 Python 脚本完成）|
| GET | `/api/admin/import/status` | 获取导入状态 |

**导入状态响应** (`ImportStatusVO`):

```json
{
  "lastImportedAt": "2026-07-01T12:00:00",
  "totalSubjects": 1200,
  "recentRecords": [
    {
      "id": 1,
      "season": "2026-spring",
      "startedAt": "2026-07-01T12:00:00",
      "completedAt": "2026-07-01T12:05:00",
      "status": "COMPLETED",
      "subjectCount": 50
    }
  ]
}
```

---

### 5.6 响应格式说明

所有接口统一返回 `Result<T>` 结构：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

分页接口额外返回 `PageResult<T>` 结构包裹在 `data` 中：

```json
{
  "content": [ ... ],
  "total": 100,
  "page": 1,
  "size": 20
}
```

---

## 6. 数据库设计

### 6.1 ER 概览

```
user (1) ── (N) 无直接关联
subject (1) ── (N) episode
subject (1) ── (N) subject_tag
import_record (独立表，记录导入任务)
```

### 6.2 表结构

#### `user` — 用户表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | bigint | PK AUTO_INCREMENT | 用户 ID |
| username | varchar(32) | UNIQUE NOT NULL | 用户名 |
| password | varchar(255) | NOT NULL | BCrypt 加密 |
| email | varchar(128) | | 邮箱 |
| nickname | varchar(64) | | 昵称 |
| avatar | varchar(512) | | 头像 URL |
| role | varchar(16) | DEFAULT 'USER' | `USER` / `ADMIN` |
| created_at | datetime | NOT NULL | |
| updated_at | datetime | NOT NULL | |

#### `subject` — 条目表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | bigint | PK | |
| bangumi_id | int | UNIQUE NOT NULL | Bangumi API ID |
| name | varchar(255) | NOT NULL | 日文/英文名 |
| name_cn | varchar(255) | | 中文名 |
| summary | text | | 简介 |
| type | tinyint | DEFAULT 2 | 2=动画 |
| eps | int | | 总集数 |
| volumes | int | | 总卷数 |
| air_date | date | | 播出日期 |
| air_weekday | tinyint | | 播出星期 (0=周日) |
| image | varchar(512) | | 封面 URL |
| score | decimal(3,1) | | 评分 0.0~10.0 |
| rank | int | | 排名 |
| collection_total | int | | 收藏数 |
| nsfw | tinyint(1) | DEFAULT 0 | 0=否, 1=是 |
| import_status | tinyint | DEFAULT 0 | 0=待导入, 1=已导入 |
| last_imported_at | datetime | | 最近导入时间 |
| created_at | datetime | NOT NULL | |
| updated_at | datetime | NOT NULL | |

#### `episode` — 剧集表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | bigint | PK | |
| subject_id | bigint | FK -> subject.id CASCADE | |
| bangumi_ep_id | int | | Bangumi 剧集 ID |
| type | tinyint | DEFAULT 0 | 0=本篇 1=SP 2=OP 3=ED 4=预告 |
| sort | decimal(5,1) | | 集数序号 (支持 1, 1.5, 2) |
| name | varchar(255) | | 日文/英文标题 |
| name_cn | varchar(255) | | 中文标题 |
| duration | varchar(16) | | 时长 (如 "24m") |
| airdate | date | | 播出日期 |
| description | text | | 剧情简介 |
| status | varchar(4) | DEFAULT 'NA' | Air/Today/NA |
| created_at | datetime | NOT NULL | |

#### `subject_tag` — 标签关联表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | bigint | PK | |
| subject_id | bigint | FK -> subject.id CASCADE | |
| name | varchar(32) | NOT NULL | 标签名 |
| count | int | DEFAULT 0 | 使用次数 |

UNIQUE KEY: `(subject_id, name)`

#### `import_record` — 导入记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | bigint | PK | |
| mode | varchar(16) | NOT NULL | full/recent/season/since |
| season_key | varchar(32) | | 如 "2026-spring" |
| started_at | datetime | NOT NULL | |
| completed_at | datetime | | |
| status | varchar(16) | DEFAULT 'RUNNING' | RUNNING/COMPLETED/FAILED |
| subject_count | int | DEFAULT 0 | |
| error_message | text | | |

---

## 7. 安全认证

### 7.1 认证流程

```
客户端                   服务端
  │                       │
  │── POST /login ──────→ │  验证用户名密码
  │                       │  生成 JWT（含 userId, role）
  │                       │  Token SHA256 存入 Redis（白名单）
  │←── { token } ────────│
  │                       │
  │── GET /api/user/me ──→│  JwtAuthenticationFilter 拦截
  │   Authorization:      │  提取 Token → 验证签名
  │   Bearer <jwt>        │  检查 Redis 白名单
  │                       │  设置 SecurityContext
  │←── { data } ─────────│
```

### 7.2 JWT Token

- **算法**: HS256
- **Payload**: `{ userId, role }`
- **有效期**: 24h（可通过 `jwt.expiration` 配置）
- **签发**: `JwtTokenProvider.generateToken()`
- **存储**: 每次登录将 Token 的 SHA256 摘要存入 Redis，用于主动失效
- **注销**: 从 Redis 删除摘要记录，Token 即失效
- **白名单检查**: `JwtAuthenticationFilter` 在每个请求中校验 Redis 存在性

### 7.3 权限体系

| 角色 | 接口范围 |
|------|----------|
| 未登录 | 公开 GET（番剧列表、搜索、详情、标签）|
| 未登录 | 注册、登录 |
| `USER` | `/api/user/**`（个人信息、认证）|
| `ADMIN` | `/api/admin/**`（用户管理、番剧管理、数据导入）|

### 7.4 安全配置

```yaml
# SecurityConfig 安全规则
- POST /api/user/auth/register    → permitAll
- POST /api/user/auth/login       → permitAll
- GET  /api/user/subjects/**      → permitAll
- GET  /api/user/tags/**          → permitAll
- /api/admin/**                   → hasRole("ADMIN")
- /api/user/**                    → authenticated
- 其余                             → permitAll

# 附加策略
- CORS: 全局放行（支持跨域凭据）
- CSRF: 禁用（JWT 无状态）
- Session: STATELESS
```

---

## 8. 错误码

| HTTP 状态码 | 业务 code | ErrorType | 说明 |
|-------------|-----------|-----------|------|
| 400 | 400 | `BAD_REQUEST` | 请求参数错误 / 参数校验失败 |
| 401 | 401 | `UNAUTHORIZED` | 未认证 / 用户名或密码错误 |
| 403 | 403 | `FORBIDDEN` | 无权限（如修改管理员角色）|
| 404 | 404 | `NOT_FOUND` | 资源不存在 |
| 409 | 409 | `CONFLICT` | 资源冲突（用户名重复、Bangumi ID 重复）|
| 429 | 429 | `TOO_MANY_REQUESTS` | 请求太频繁 |
| 500 | 500 | `INTERNAL_ERROR` | 服务器内部错误 |

### 响应示例

```json
// 参数校验失败
{ "code": 400, "message": "请求参数错误", "data": { "username": "用户名长度需在1~32之间" } }

// 业务异常
{ "code": 409, "message": "用户名已存在" }

// 无权限
{ "code": 403, "message": "无权限" }
```

### 全局异常处理

`GlobalExceptionHandler` 统一拦截以下异常：

| 异常 | 说明 |
|------|------|
| `BizException` | 业务异常（手动抛出）|
| `MethodArgumentNotValidException` | `@Valid` 参数校验失败 |
| `ConstraintViolationException` | `@Validated` 参数校验失败 |
| `NoHandlerFoundException` | 接口不存在 (404) |
| `Exception` | 未知异常 (500) |

---

## 9. 部署与构建

### 构建

```bash
cd backend/business
mvn clean package -DskipTests
# 产物: app/target/animetracker-app-2.0.0.jar
```

### 部署

```bash
java -jar animetracker-app-2.0.0.jar \
  --spring.profiles.active=local \
  --jwt.secret=<your-secret> \
  --zzz.datasource.password=<db-password>
```

### 环境配置

配置按 profile 分离：

| Profile | 文件 | 用途 |
|---------|------|------|
| `default` | `application.yml` | 通用配置（数据源占位符、MyBatis-Plus、JWT、日志）|
| `local` | `application-local.yml` | 本地开发（具体数据库连接、控制台 SQL 日志）|

所有敏感值均通过占位符 `${...}` 引用，支持环境变量覆盖。
