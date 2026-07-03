# AnimeTracker 技术方案文档

> **版本:** 2.0
> **日期:** 2026-07-03
> **状态:** 定稿

---

## 目录

1. [总体架构](#1-总体架构)
2. [技术选型](#2-技术选型)
3. [项目目录结构](#3-项目目录结构)
4. [后端模块设计](#4-后端模块设计)
5. [前端模块设计](#5-前端模块设计)
6. [AI Agent 设计](#6-ai-agent-设计)
7. [数据库设计](#7-数据库设计)
8. [Redis 缓存设计](#8-redis-缓存设计)
9. [安全设计](#9-安全设计)
10. [任务拆分与依赖关系](#10-任务拆分与依赖关系)
11. [API 接口一览](#11-api-接口一览)

---

## 1. 总体架构

### 1.1 架构风格

**分层单体架构（Layered Monolith）** — 单一 Spring Boot 进程运行后端服务，前端为独立 Vue 3 SPA，AI Agent 为独立 FastAPI 进程。三部分通过 REST API 通信。

```
┌──────────────────────────────────────────────────────┐
│                    Frontend                           │
│          Vue 3 + Vite + Tailwind CSS                  │
│          (独立 SPA，端口 5173)                          │
│          Axios 调用 REST API 通过 Vite Proxy           │
└──────────────┬───────────────────────────────────────┘
               │ HTTP/JSON (proxy → localhost:8080)
┌──────────────▼───────────────────────────────────────┐
│               Spring Boot Application                  │
│               (端口 8080)                              │
│                                                        │
│   ┌──────────────────────────────────────────────┐    │
│   │           Config Layer (config/)              │    │
│   │   Security · CORS · JWT · Knife4j · MP · Cache│   │
│   └──────────────────────────────────────────────┘    │
│                          │                             │
│   ┌──────────┐  ┌──────────────┐  ┌──────────┐      │
│   │ Common   │  │ User Module  │  │ Subject  │      │
│   │ ApiRes.  │  │ 注册/登录    │  │ 条目/剧集│      │
│   │ PageRes. │  │ 个人信息管理  │  │ 搜索/季度│      │
│   │ BizExcep.│  │ 用户管理     │  │ CRUD/标签│      │
│   │ ErrorType│  │ (ADMIN)      │  │ 导入控制 │      │
│   └──────────┘  └──────────────┘  └──────────┘      │
│                          │                             │
│                   ┌──────┴──────┐                     │
│                   │   MySQL     │                     │
│                   │    8.0      │                     │
│                   └──────┬──────┘                     │
│                          │                             │
│                   ┌──────┴──────┐                     │
│                   │   Redis     │                     │
│                   │   7-alpine  │                     │
│                   └─────────────┘                     │
└──────────────────────────────────────────────────────┘
               │ HTTP/JSON (backend_api_base)
┌──────────────▼───────────────────────────────────────┐
│             AI Agent (FastAPI)                         │
│             (端口 8090)                                │
│   Chat · SSE Streaming · LangChain · DashScope        │
│   会话存储: Redis (主) / SQLite (回退)                  │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│           Data Importer (Python CLI)                   │
│   Bangumi API 客户端 · SQLAlchemy · UPSERT 写入        │
│   四种模式: --full / --recent / --season / --since     │
└──────────────────────────────────────────────────────┘
```

### 1.2 架构决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 单体 vs 微服务 | 单体（Layered Monolith） | 个人项目，无水平扩展需求，避免微服务复杂度 |
| 前后端分离 | 是 | Vue SPA + REST API，开发解耦，部署灵活 |
| AI Agent 独立进程 | FastAPI 单独部署 | Python 生态适合 AI，与 Java 后端职责分离 |
| 容器化 | 否（暂不 Docker） | 开发阶段直接 JAR/uvicorn 运行，后续按需评估 |

---

## 2. 技术选型

### 2.1 技术选型表

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **后端语言** | Java (OpenJDK) | 21 LTS | 主业务逻辑 |
| **后端框架** | Spring Boot | 3.2.0 | 应用框架 |
| **ORM** | MyBatis-Plus | 3.5.5 | 数据库访问 |
| **安全** | Spring Security + JWT (jjwt) | 0.12.3 | 认证授权 |
| **API 文档** | Knife4j | 4.5.0 | OpenAPI 文档 UI（替代 SpringDoc） |
| **数据库** | MySQL | 8.0 | 关系数据库 |
| **缓存** | Redis | 7-alpine | 会话缓存 / 数据缓存 |
| **构建** | Maven | 3.9+ | Java 构建 |
| **前端框架** | Vue 3 + TypeScript | 3.4+ | SPA UI |
| **构建工具** | Vite | 5.3+ | 前端构建 |
| **CSS** | Tailwind CSS | 3.4+ | 样式框架 |
| **状态管理** | Pinia | 2.1+ | 前端状态 |
| **路由** | Vue Router | 4.4+ | 前端路由 |
| **HTTP 客户端** | Axios | 1.7+ | API 调用 |
| **图标库** | Lucide Vue Next | 0.400+ | UI 图标 |
| **AI Agent** | FastAPI | 0.110+ | Agent HTTP 服务 |
| **AI LLM** | LangChain + DashScope | 1.0+ / qwen3.7-max | LLM 集成 |
| **数据导入** | Python 3.10+ / SQLAlchemy | 2.x | 数据 ETL |

### 2.2 排除的技术

| 技术 | 排除原因 |
|------|----------|
| Spring Cloud / Nacos | 个人项目无需服务发现 |
| JPA / Hibernate | 保持 MyBatis-Plus 现有选型 |
| React / 其他前端框架 | 保持 Vue 3 |
| RabbitMQ / Kafka | 无异步消息需求 |
| Docker / Kubernetes | 开发阶段 JAR 直接运行 |
| Refresh Token | JWT 24h 过期后重新登录 |

---

## 3. 项目目录结构

```
AnimeTracker/
├── frontend/                          # ★ Vue 3 前端 SPA
│   ├── src/
│   │   ├── api/                       #   Axios 请求封装
│   │   │   ├── auth.ts                #     认证 API
│   │   │   ├── subjects.ts            #     条目 API
│   │   │   ├── tags.ts                #     标签 API
│   │   │   ├── users.ts               #     用户 API
│   │   │   └── admin.ts               #     管理 API
│   │   ├── components/                #   共享 UI 组件
│   │   │   ├── SubjectCard.vue        #     条目卡片
│   │   │   ├── SubjectCardSkeleton.vue
│   │   │   ├── DetailSkeleton.vue
│   │   │   ├── ListSkeleton.vue
│   │   │   ├── TableSkeleton.vue
│   │   │   ├── EpisodeList.vue        #     剧集列表
│   │   │   ├── SeasonPicker.vue       #     季度选择器
│   │   │   ├── TagBadge.vue           #     标签徽章
│   │   │   ├── Pagination.vue         #     分页组件
│   │   │   ├── EmptyState.vue         #     空状态
│   │   │   ├── ErrorState.vue         #     错误状态
│   │   │   └── AiAssistant.vue        #     AI 助手浮动窗口
│   │   ├── layouts/                   #   布局组件
│   │   │   ├── MainLayout.vue         #     主布局（含导航）
│   │   │   ├── AdminLayout.vue        #     管理后台布局
│   │   │   └── Footer.vue
│   │   ├── pages/                     #   页面组件
│   │   │   ├── Home.vue               #     首页
│   │   │   ├── Login.vue              #     登录
│   │   │   ├── Register.vue           #     注册
│   │   │   ├── SubjectDetail.vue      #     条目详情
│   │   │   ├── Search.vue             #     搜索
│   │   │   ├── Season.vue             #     季度浏览
│   │   │   ├── Tags.vue               #     标签列表
│   │   │   ├── TagSubjects.vue        #     标签条目
│   │   │   ├── Profile.vue            #     个人信息
│   │   │   └── admin/                 #   管理后台
│   │   │       ├── Dashboard.vue
│   │   │       ├── SubjectManage.vue
│   │   │       ├── Users.vue
│   │   │       └── ImportStatus.vue
│   │   ├── router/                    #   Vue Router 路由
│   │   │   └── index.ts
│   │   ├── stores/                    #   Pinia 状态管理
│   │   │   ├── auth.ts               #     认证状态
│   │   │   ├── chat.ts               #     AI 聊天状态
│   │   │   └── subjects.ts           #     条目浏览状态
│   │   └── types/                     #   TypeScript 类型定义
│   │       └── index.ts               #     通用接口类型
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
│
├── backend/                           # ★ 后端代码
│   ├── api/                           #   Java Spring Boot 单体应用
│   │   ├── pom.xml
│   │   ├── src/main/java/top/zhaizz/animetracker/
│   │   │   ├── AppApplication.java           # 启动入口
│   │   │   ├── common/                       # 公共模块
│   │   │   │   ├── ApiResponse.java
│   │   │   │   ├── PageResult.java
│   │   │   │   ├── BizException.java
│   │   │   │   ├── ErrorType.java
│   │   │   │   └── GlobalExceptionHandler.java
│   │   │   ├── config/                       # 全局配置
│   │   │   │   ├── SecurityConfig.java
│   │   │   │   ├── CorsConfig.java
│   │   │   │   ├── MyBatisPlusConfig.java
│   │   │   │   ├── Knife4jConfig.java
│   │   │   │   └── CacheConfig.java
│   │   │   ├── security/                     # JWT 安全
│   │   │   │   ├── JwtTokenProvider.java
│   │   │   │   ├── JwtAuthenticationFilter.java
│   │   │   │   └── UserPrincipal.java
│   │   │   ├── user/                         # 用户模块
│   │   │   │   ├── controller/
│   │   │   │   │   ├── AuthController.java
│   │   │   │   │   ├── UserController.java
│   │   │   │   │   └── AdminUserController.java
│   │   │   │   ├── service/
│   │   │   │   │   ├── AuthService.java
│   │   │   │   │   ├── UserService.java
│   │   │   │   │   └── impl/
│   │   │   │   ├── entity/User.java
│   │   │   │   ├── dto/
│   │   │   │   ├── vo/
│   │   │   │   ├── converter/
│   │   │   │   └── mapper/UserMapper.java
│   │   │   └── subject/                      # 条目模块
│   │   │       ├── controller/
│   │   │       │   ├── SubjectController.java
│   │   │       │   ├── TagController.java
│   │   │       │   ├── AdminController.java
│   │   │       │   └── ImportController.java
│   │   │       ├── service/
│   │   │       │   └── impl/
│   │   │       ├── entity/
│   │   │       │   ├── Subject.java
│   │   │       │   ├── Episode.java
│   │   │       │   └── SubjectTag.java
│   │   │       ├── dto/
│   │   │       ├── vo/
│   │   │       ├── converter/
│   │   │       ├── mapper/
│   │   │       └── util/SeasonUtil.java
│   │   └── src/main/resources/
│   │       ├── application.yml
│   │       ├── application-local.yml.example
│   │       └── mapper/                       # MyBatis XML
│   │           ├── UserMapper.xml
│   │           ├── SubjectMapper.xml
│   │           ├── EpisodeMapper.xml
│   │           └── SubjectTagMapper.xml
│   │
│   ├── ai/                           #   AI Agent (FastAPI)
│   │   ├── main.py                   #     应用入口
│   │   ├── config.py                 #     配置管理
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   ├── api/                      #     路由层
│   │   │   ├── chat.py
│   │   │   ├── sessions.py
│   │   │   └── config_api.py
│   │   ├── langchain_integration/    #     LangChain 集成
│   │   │   ├── agent.py
│   │   │   ├── llm.py
│   │   │   ├── memory.py
│   │   │   ├── prompts.py
│   │   │   └── tools.py
│   │   ├── services/
│   │   │   └── backend_client.py     #     Java API HTTP 客户端
│   │   ├── storage/
│   │   │   └── session_store.py      #     会话存储双实现
│   │   └── tests/
│   │       ├── test_agent.py
│   │       ├── test_api.py
│   │       ├── test_backend_client.py
│   │       ├── test_session_store.py
│   │       └── test_tools.py
│   │
│   ├── data/                         #   数据层
│   │   ├── importer/                 #     数据导入器
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── bangumi_client.py
│   │   │   ├── models.py
│   │   │   ├── db_writer.py
│   │   │   ├── import_runner.py
│   │   │   └── requirements.txt
│   │   └── schema/
│   │       └── init.sql              #     DDL 归档
│   │
│   └── README.md
│
├── docs/                             # ★ 项目文档
│   ├── PRD/
│   │   ├── phase1-skeleton.md
│   │   ├── phase2-java-api.md
│   │   ├── phase3-ai-agent.md
│   │   ├── phase4-data-importer.md
│   │   ├── phase5-cleanup.md
│   │   ├── phase6-redis.md
│   │   └── phase7-finalization.md
│   ├── superpowers/out/
│   │   ├── tech-spec.md              #   本文件
│   │   ├── api-spec.yaml             #   OpenAPI 规范
│   │   └── db-schema.sql             #   数据库建表脚本
│   ├── Scope.md                      #   项目范围说明书
│   └── db-schema.sql                 #   数据库建表脚本（源）
│
├── scripts/                          # 部署脚本
│   ├── build.sh
│   ├── start-prod.sh
│   └── seed-db.sh
│
└── README.md                         # 项目总 README
```

---

## 4. 后端模块设计

### 4.1 Common 模块

基础公用组件，无任何外部依赖。

| 类 | 职责 | 关键 API |
|----|------|----------|
| `ApiResponse<T>` | 统一响应体 | `success(data)`, `error(code, msg)`, `fail(code, msg)` |
| `PageResult<T>` | 统一分页格式 | `of(list, total, page, size)`, `empty(page, size)` |
| `BizException` | 业务异常 | 携带 `code(int)` + `message(String)` |
| `ErrorType` | 错误码枚举 | 7 种: BAD_REQUEST(400), UNAUTHORIZED(401), FORBIDDEN(403), NOT_FOUND(404), CONFLICT(409), TOO_MANY_REQUESTS(429), INTERNAL_ERROR(500) |
| `GlobalExceptionHandler` | 全局异常处理 | `@RestControllerAdvice`，捕获 BizException / MethodArgumentNotValidException / 通用 Exception |

**统一响应格式：**
```json
// 成功
{ "code": 200, "message": "success", "data": { ... } }

// 分页成功
{ "code": 200, "message": "success",
  "data": { "content": [], "total": 1024, "page": 1, "size": 20 } }

// 错误
{ "code": 400, "message": "请求参数错误", "data": null }
```

### 4.2 Config 模块

| 配置类 | 职责 | 关键配置 |
|--------|------|----------|
| `SecurityConfig` | Spring Security | 无状态 Session，BCrypt 密码编码，路由权限矩阵 |
| `JwtTokenProvider` | JWT 令牌 | SHA256 签名，24h 过期，从 `JWT_SECRET` 环境变量读取密钥 |
| `JwtAuthenticationFilter` | JWT 过滤器 | 从 `Authorization: Bearer <token>` 提取 → 解析 → 注入 SecurityContext |
| `CorsConfig` | CORS | 允许所有 Origin (`allowedOriginPatterns: "*"`)，支持凭证 |
| `MyBatisPlusConfig` | MyBatis-Plus | 分页拦截器（MySQL 方言） |
| `Knife4jConfig` | API 文档 | OpenAPI 3.0 分组配置，标题 "AnimeTracker API" |
| `CacheConfig` | Redis 缓存 | `RedisTemplate<String, Object>` + Jackson 序列化，`@EnableCaching` |

### 4.3 User 模块

| 组件 | 职责 | API 路径 |
|------|------|----------|
| `AuthController` | 注册/登录 | `POST /api/user/auth/register`, `POST /api/user/auth/login` |
| `UserController` | 个人信息 | `GET /api/user/me` (用户信息和最近收藏), `PUT /api/user/me` (修改昵称/头像/邮箱) |
| `AdminUserController` | 用户管理 | `GET /api/admin/users` (分页), `PUT /api/admin/users/{id}/role` (修改角色) |

**认证流程：**
```
Register: 校验参数 → 唯一性检查(username) → BCrypt 加密 → 写入 DB → 生成 JWT → 返回 {token, user}
Login:    查找用户 → BCrypt 验证 → 生成 JWT → 返回 {token, user}
Auth:     Authorization: Bearer <token> → 验证签名 → 注入 SecurityContext → 路由鉴权
```

**登录/注册响应体 (LoginResult)：**
```json
{
  "token": "eyJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@animetracker.local",
    "nickname": "管理员",
    "avatar": null,
    "role": "ADMIN"
  }
}
```

### 4.4 Subject 模块

| 组件 | 职责 | API 路径 |
|------|------|----------|
| `SubjectController` | 条目浏览 | `GET /api/user/subjects` 列表, `GET /api/user/subjects/search?q=` 搜索, `GET /api/user/subjects/season?year=&quarter=` 季度, `GET /api/user/subjects/{id}` 详情, `GET /api/user/subjects/{id}/episodes` 剧集 |
| `TagController` | 标签浏览 | `GET /api/user/tags` 所有标签, `GET /api/user/tags/{tag}/subjects` 按标签筛选 |
| `AdminController` | 条目管理 | `POST /api/admin/subjects` 新增, `PUT /api/admin/subjects/{id}` 编辑, `DELETE /api/admin/subjects/{id}` 删除 |
| `ImportController` | 导入控制 | `POST /api/admin/import/run` 触发导入, `GET /api/admin/import/status` 导入状态 |

**关键实体映射：**

| Java 实体 | 表 | 重要字段映射 |
|-----------|-----|-------------|
| `Subject` | `subject` | bangumiId(Integer)/image/airDate(LocalDate)/score(BigDecimal 3,1) |
| `Episode` | `episode` | bangumiEpId(Integer)/sort(BigDecimal 5,1)/airdate(LocalDate, 小写d) |
| `SubjectTag` | `subject_tag` | 字段一一对应 |

**搜索逻辑（旧代码兼容）：**
- MyBatis XML 中 `searchByKeyword` 方法参数名为 `keyword`
- SQL: `WHERE name LIKE CONCAT('%', #{keyword}, '%') OR name_cn LIKE CONCAT('%', #{keyword}, '%')`
- 分页在 Service 层手动处理（不依赖 Mapper 层分页插件）

**季度查询逻辑：**
- 根据 year + quarter（winter/spring/summer/autumn）计算起止日期
- `SeasonUtil.monthRange(year, quarter)` → `{startMonth, endMonth}`
- SQL: `WHERE air_date BETWEEN #{start} AND #{end}`

---

## 5. 前端模块设计

### 5.1 路由结构

| 路径 | 页面 | 认证 | 布局 |
|------|------|------|------|
| `/` | Home | 否 | MainLayout |
| `/login` | Login | 否 | MainLayout |
| `/register` | Register | 否 | MainLayout |
| `/search` | Search | 否 | MainLayout |
| `/season/:year?/:quarter?` | Season | 否 | MainLayout |
| `/subject/:id` | SubjectDetail | 否 | MainLayout |
| `/tags` | Tags | 否 | MainLayout |
| `/tags/:tag` | TagSubjects | 否 | MainLayout |
| `/profile` | Profile | 是 | MainLayout |
| `/admin` | Dashboard | 是(ADMIN) | AdminLayout |
| `/admin/subjects` | SubjectManage | 是(ADMIN) | AdminLayout |
| `/admin/users` | Users | 是(ADMIN) | AdminLayout |
| `/admin/import` | ImportStatus | 是(ADMIN) | AdminLayout |

### 5.2 Pinia Store 设计

```typescript
// auth store
interface AuthState {
  token: string | null;
  user: UserVO | null;
  isAuthenticated: boolean;
}
// actions: login(), register(), logout(), fetchProfile(), updateProfile()
// getters: isAdmin()

// subjects store (浏览状态)
interface SubjectsState {
  subjects: SubjectListVO[];
  currentPage: number;
  total: number;
  pageSize: number;
  sort: string;
  order: string;
  loading: boolean;
}
// actions: fetchSubjects(), fetchSeasonSubjects(), searchSubjects()

// chat store (AI 助手)
interface ChatState {
  sessions: ChatSession[];
  currentSessionId: string | null;
  messages: ChatMessage[];
  isStreaming: boolean;
}
// actions: sendMessage(), createSession(), listSessions(), deleteSession()
```

### 5.3 组件层级

```
App.vue
├── MainLayout.vue
│   ├── RouterView (NavBar + page content + Footer)
│   │   ├── Home.vue → SubjectCard.vue[], Pagination.vue
│   │   ├── Search.vue → SubjectCard.vue[], Pagination.vue
│   │   ├── Season.vue → SeasonPicker.vue, SubjectCard.vue[], Pagination.vue
│   │   ├── SubjectDetail.vue → EpisodeList.vue, TagBadge.vue[]
│   │   ├── Tags.vue → TagBadge.vue[]
│   │   ├── TagSubjects.vue → SubjectCard.vue[], Pagination.vue
│   │   ├── Login.vue / Register.vue
│   │   └── Profile.vue
│   └── AiAssistant.vue (浮动窗口，全局)
│
├── AdminLayout.vue
│   ├── AdminSidebar + RouterView
│   │   ├── Dashboard.vue
│   │   ├── SubjectManage.vue → TableSkeleton.vue
│   │   ├── Users.vue → TableSkeleton.vue
│   │   └── ImportStatus.vue
│   └── Footer.vue
```

### 5.4 状态组件覆盖

所有数据加载场景必须覆盖以下三种状态：

| 状态 | 组件 | 说明 |
|------|------|------|
| **加载中** | `SubjectCardSkeleton.vue` / `ListSkeleton.vue` / `DetailSkeleton.vue` / `TableSkeleton.vue` | Skeleton 骨架屏，非 loading 转圈 |
| **空数据** | `EmptyState.vue` | 无结果时的友好提示 + 操作引导 |
| **错误** | `ErrorState.vue` | 网络错误提示 + 重试按钮 |

---

## 6. AI Agent 设计

### 6.1 技术选型

| 组件 | 技术 | 版本 |
|------|------|------|
| Web 框架 | FastAPI | 0.110+ |
| LLM SDK | LangChain | 1.0+ |
| LLM 服务 | DashScope (阿里百炼) | qwen3.7-max 模型 |
| 协议 | OpenAI 兼容接口 | — |
| 会话存储（主） | Redis | 7-alpine，TTL 7 天 |
| 会话存储（回退） | SQLite | Python 内置 |

### 6.2 架构

```
用户 ──SSE──→ FastAPI ──LangChain──→ DashScope API
                  │
                  ├── Redis (会话存储)
                  │
                  └── HTTP → Spring Boot API → MySQL
```

### 6.3 对话流程

1. 用户发送消息 → `POST /api/chat` → 创建/复用 session
2. 从 `SessionStore.get_messages()` 加载历史
3. LangChain Agent 调用 Tool 获取动漫数据
4. LLM 生成自然语言回答
5. SSE 流式返回给前端
6. `SessionStore.add_message()` 持久化对话

### 6.4 工具函数清单

| 工具 | 参数 | 后端 API 调用 | 说明 |
|------|------|--------------|------|
| `search_subjects` | `keyword: str` | `GET /api/user/subjects/search?q={keyword}` | 搜索动漫 |
| `get_subject_detail` | `subject_id: int` | `GET /api/user/subjects/{id}` | 获取详情 |
| `get_season_subjects` | `year: int, season: str` | `GET /api/user/subjects/season?year={year}&quarter={season}` | 季度动漫 |
| `get_episodes` | `subject_id: int` | `GET /api/user/subjects/{id}/episodes` | 获取剧集 |

### 6.5 存储层接口

```python
class SessionStore(ABC):
    async def create_session() -> str: ...
    async def get_session(session_id) -> Optional[Dict]: ...
    async def add_message(session_id, role, content, tools_used): ...
    async def get_messages(session_id) -> List[Dict]: ...
    async def list_sessions() -> List[Dict]: ...
    async def delete_session(session_id): ...
```

**双实现策略：**
- 启动时优先尝试 `RedisSessionStore`
- Redis 不可用时，静默回退 `SqliteSessionStore`
- 通过配置切换：`SESSION_STORE=redis|sqlite`

---

## 7. 数据库设计

### 7.1 实体关系

```
user (1) ──── (N) collection     (预留，P2 实现)
subject (1) ── (N) episode       (ON DELETE CASCADE)
subject (1) ── (N) subject_tag   (ON DELETE CASCADE)
```

### 7.2 表结构总览

| 表名 | 行数预估 | 引擎 | 字符集 | 核心索引 |
|------|---------|------|--------|----------|
| `user` | < 100 | InnoDB | utf8mb4 | UK(username), idx(role) |
| `subject` | 10,000~50,000 | InnoDB | utf8mb4 | UK(bangumi_id), idx(air_date/score/rank/name_cn/type/air_weekday) |
| `episode` | 500,000~5,000,000 | InnoDB | utf8mb4 | FK(subject_id), idx(airdate/status) |
| `subject_tag` | 50,000~200,000 | InnoDB | utf8mb4 | UK(subject_id, name), idx(name) |
| `import_record` | < 1,000 | InnoDB | utf8mb4 | idx(status/started_at) |
| `collection` | 预留 | InnoDB | utf8mb4 | UK(user_id, subject_id) |

### 7.3 建表 SQL

完整的建表语句（含索引、外键、种子数据）详见 `docs/db-schema.sql` 和 `docs/superpowers/out/db-schema.sql`。

**关键设计决策：**
- 所有表使用 InnoDB 引擎 + utf8mb4 字符集
- `subject.bangumi_id` 设为 UNIQUE，来自 Bangumi API 的整数 ID
- `episode` 和 `subject_tag` 外键设置 `ON DELETE CASCADE`
- `episode.airdate` 字段名使用小写 `d`（兼容旧代码命名）
- `subject.image` 字段名为 `image` 而非 `imageUrl`（兼容旧代码命名）
- 阶段 2 将启用 `collection` 表（目前仅预留注释）

---

## 8. Redis 缓存设计

### 8.1 缓存策略

| 缓存键模式 | 存储数据 | TTL | 失效时机 |
|-----------|---------|-----|---------|
| `subject:detail:{id}` | SubjectDetailVO (JSON) | 30 分钟 | 条目被更新/删除时 `@CacheEvict` |
| `subject:search:{keyword}:{page}:{size}` | 搜索结果 (JSON) | 10 分钟 | 数据导入后批量失效 |
| `ai:session:{session_id}` | 会话数据 (Hash) | 7 天 | 显式删除会话时 |

### 8.2 缓存分层

```
Redis 实例
├── db=0    → AI Agent 会话缓存 (ai:session:*)
├── db=1    → Java API 数据缓存 (subject:detail:*, subject:search:*)
└── db=2    → 预留
```

### 8.3 穿透防护

- 查询未命中时，缓存空值（有效期 1 分钟）
- 防止恶意查询不存在的主键导致 MySQL 压力

### 8.4 降级策略

- Redis 连接失败 → 捕获 `RedisConnectionFailureException`
- API 缓存降级为直接查询 MySQL
- AI 会话降级为 SQLite 本地存储
- 应用启动不因 Redis 不可用而阻断

---

## 9. 安全设计

### 9.1 JWT 认证

```
Header:  { "alg": "HS256", "typ": "JWT" }
Payload: { "sub": userId, "username": "...", "role": "...", "iat": ..., "exp": ... }
签名:    HMAC-SHA256(base64UrlEncode(header) + "." + base64UrlEncode(payload), secret)
```

- 密钥通过 `JWT_SECRET` 环境变量提供（至少 256 位）
- 过期时间: 24 小时（86400000 ms）
- Token 通过 `Authorization: Bearer <token>` 请求头传递

### 9.2 路由权限矩阵

| 路径模式 | 方法 | 权限 |
|---------|------|------|
| `POST /api/user/auth/**` | POST | `permitAll()` |
| `GET /api/user/subjects/**` | GET | `permitAll()` |
| `GET /api/user/tags/**` | GET | `permitAll()` |
| `/api/user/me` | GET/PUT | `authenticated()` |
| `/api/admin/**` | ALL | `hasRole("ADMIN")` |
| `/swagger-ui/**`, `/v3/api-docs/**`, `/doc.html` | GET | `permitAll()` |

### 9.3 密码安全

- 使用 BCrypt 密码编码器（Spring Security 默认）
- 数据库不存储明文密码
- 注册时进行密码强度校验（长度 ≥ 6 位）

### 9.4 其他安全措施

- 无状态 Session（不创建 HttpSession）
- CORS 白名单（开发环境允许所有，生产环境按需限制）
- 用户名唯一性校验（防止重复注册）

---

## 10. 任务拆分与依赖关系

### 10.1 总览

项目共分 7 个 Phase，按依赖顺序执行：

```
Phase 1 (骨架搭建) ──→ Phase 2 (Java API 重写) ──→ Phase 5 (清理与验证)
                                                      │
                          ├── Phase 3 (AI Agent) ─────┤
                          │                           │
                          ├── Phase 4 (数据导入器) ────┤
                          │                           │
                          └── Phase 6 (Redis 深度集成) ┘
                                                      │
                                                      └── Phase 7 (收尾)
```

### 10.2 Phase 1：骨架搭建（0.5 天）

**目标：** 创建空的目录骨架 + 单模块 pom.xml + 配置文件

**前置：** 无

| 任务 | 内容 | 产出 |
|------|------|------|
| T1.1 | 创建 `backend/api/` 目录及子包结构 | 空 Java 包目录 |
| T1.2 | 创建 `backend/api/pom.xml`（单模块，引入所有依赖） | 可编译的 pom.xml |
| T1.3 | 创建 `backend/ai/` 目录及子包结构 | 空 Python 包目录 |
| T1.4 | 创建 `backend/data/` 及 `data/importer/`、`data/schema/` | 空数据目录 |
| T1.5 | 创建 `scripts/` 目录 | 脚本目录 |
| T1.6 | 创建基础配置（`application.yml`、`.env.example`） | 配置文件模板 |

### 10.3 Phase 2：Java API 重写（3 天）

**目标：** 在新位置从零搭建 Spring Boot 应用，各 API 签名与旧代码完全一致

**前置：** Phase 1
**涉及范围：** 后端 (backend/api/)

| 任务 | 内容 | 估算 |
|------|------|------|
| T2.1 Common 模块 | ApiResponse / PageResult / BizException / ErrorType / GlobalExceptionHandler + 单元测试 | 0.5 天 |
| T2.2 Config 模块 | SecurityConfig / CorsConfig / MyBatisPlusConfig / Knife4jConfig / CacheConfig | 0.5 天 |
| T2.3 Security 层 | JwtTokenProvider / JwtAuthenticationFilter / UserPrincipal | 0.3 天 |
| T2.4 User 模块 | User 实体 + Mapper(含 XML) + DTO/VO + Converter + Service + Controller(3 个) + 单元测试 | 0.7 天 |
| T2.5 Subject 模块 | Subject/Episode/SubjectTag 实体 + Mapper(含 XML) + DTO/VO + Converter + Service + Controller(4 个) + 单元测试 | 1.0 天 |

### 10.4 Phase 3：AI Agent 重写（1.5 天）

**目标：** 将根目录 `agent/` 迁移至 `backend/ai/`，在新位置重写 FastAPI + LangChain 应用

**前置：** Phase 2（Java API 提供数据查询接口）
**涉及范围：** AI (backend/ai/)

| 任务 | 内容 | 估算 |
|------|------|------|
| T3.1 FastAPI 骨架 | main.py / config.py / requirements.txt / .env.example | 0.2 天 |
| T3.2 会话存储 | SessionStore 抽象 + RedisSessionStore + SqliteSessionStore + 单元测试 | 0.3 天 |
| T3.3 LangChain 集成 | llm.py / agent.py / tools.py / memory.py / prompts.py + 单元测试 | 0.4 天 |
| T3.4 REST API 路由 | chat.py / sessions.py / config_api.py + 后端 HTTP 客户端 | 0.3 天 |
| T3.5 前端对接 | AiAssistant.vue 组件 + chat store + SSE 对接 | 0.3 天 |

### 10.5 Phase 4：数据导入器（1 天）

**目标：** 将 `backend/data-importer/` 迁移至 `backend/data/importer/`

**前置：** Phase 1
**涉及范围：** 数据层 (backend/data/importer/)

| 任务 | 内容 | 估算 |
|------|------|------|
| T4.1 | 迁移全部 Python 文件至 `backend/data/importer/`，调整路径和导入 | 0.5 天 |
| T4.2 | 复制 `init.sql` 至 `backend/data/schema/` 作为 DDL 归档 | 0.1 天 |
| T4.3 | 功能验证：四种导入模式运行正常 | 0.4 天 |

### 10.6 Phase 5：清理与验证（0.5 天）

**目标：** 删除旧目录，更新文档

**前置：** Phase 2, 3, 4 完成
**涉及范围：** 全项目

| 任务 | 内容 | 估算 |
|------|------|------|
| T5.1 | 删除 `backend/modules/`、`agent/`、`backend/data-importer/` | 0.1 天 |
| T5.2 | 更新 `.gitignore`（适配新路径） | 0.1 天 |
| T5.3 | 更新 README.md + 新建 backend/README.md | 0.2 天 |
| T5.4 | 全量验证（编译/测试/导入检查） | 0.1 天 |

### 10.7 Phase 6：Redis 深度集成（1 天）

**目标：** AI Agent 会话 Redis 实现 + API 数据缓存

**前置：** Phase 2, 3
**涉及范围：** 后端 (backend/api/) + AI (backend/ai/)

| 任务 | 内容 | 估算 |
|------|------|------|
| T6.1 | AI 会话存储重构为抽象接口 + Redis 实现 | 0.3 天 |
| T6.2 | Java API Subject 缓存（@Cacheable + @CacheEvict） | 0.4 天 |
| T6.3 | 缓存穿透防护 + 缓存清除 API | 0.2 天 |
| T6.4 | 降级测试（Redis 不可用时系统表现） | 0.1 天 |

### 10.8 Phase 7：收尾（0.5 天）

**目标：** 启动脚本 + 最终验证 + Squash merge

**前置：** Phase 5, 6
**涉及范围：** 全项目

| 任务 | 内容 | 估算 |
|------|------|------|
| T7.1 | 创建 `scripts/build.sh` / `scripts/start-prod.sh` / `scripts/seed-db.sh` | 0.2 天 |
| T7.2 | 最终全面功能验证 | 0.2 天 |
| T7.3 | Squash merge 到 main 分支 | 0.1 天 |

---

## 11. API 接口一览

### 11.1 认证接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/user/auth/register` | 用户注册 | 无 |
| POST | `/api/user/auth/login` | 用户登录 | 无 |

### 11.2 用户接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/user/me` | 获取个人资料 | 是 |
| PUT | `/api/user/me` | 更新个人资料 | 是 |

### 11.3 条目浏览接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/user/subjects` | 分页条目列表 | 无 |
| GET | `/api/user/subjects/search?q=` | 搜索条目 | 无 |
| GET | `/api/user/subjects/season?year=&quarter=` | 季度条目 | 无 |
| GET | `/api/user/subjects/{id}` | 条目详情 | 无 |
| GET | `/api/user/subjects/{id}/episodes` | 条目剧集 | 无 |

### 11.4 标签接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/user/tags` | 标签列表 | 无 |
| GET | `/api/user/tags/{tag}/subjects` | 标签条目 | 无 |

### 11.5 管理接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/admin/subjects` | 新增条目 | ADMIN |
| PUT | `/api/admin/subjects/{id}` | 编辑条目 | ADMIN |
| DELETE | `/api/admin/subjects/{id}` | 删除条目 | ADMIN |
| GET | `/api/admin/users` | 用户列表 | ADMIN |
| PUT | `/api/admin/users/{id}/role` | 修改用户角色 | ADMIN |
| POST | `/api/admin/import/run` | 触发导入 | ADMIN |
| GET | `/api/admin/import/status` | 导入状态 | ADMIN |
| DELETE | `/api/admin/cache/{key}` | 清除缓存 | ADMIN |

### 11.6 AI Agent 接口

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/health` | 健康检查 | 无 |
| POST | `/api/chat` | 发送聊天消息（SSE 流式） | 无 |
| GET | `/api/chat/{session_id}/messages` | 获取会话历史 | 无 |
| POST | `/api/sessions` | 创建会话 | 无 |
| GET | `/api/sessions` | 会话列表 | 无 |
| DELETE | `/api/sessions/{session_id}` | 删除会话 | 无 |
| GET | `/api/config` | Agent 配置信息 | 无 |

> 完整接口定义详见 `api-spec.yaml`。

---

## 附录 A：环境变量清单

| 变量 | 默认值 | 用途 | 所属 |
|------|--------|------|------|
| `MYSQL_HOST` | `localhost` | MySQL 主机 | Java API |
| `MYSQL_PORT` | `3306` | MySQL 端口 | Java API |
| `MYSQL_DATABASE` | `anime_tracker` | 数据库名 | Java API |
| `MYSQL_USER` | `root` | 数据库用户 | Java API |
| `MYSQL_PASSWORD` | `root` | 数据库密码 | Java API |
| `JWT_SECRET` | `your-256-bit-secret...` | JWT 签名密钥 | Java API |
| `REDIS_HOST` | `localhost` | Redis 主机 | Java API / AI Agent |
| `REDIS_PORT` | `6379` | Redis 端口 | Java API / AI Agent |
| `DASHSCOPE_API_KEY` | (空) | DashScope API 密钥 | AI Agent |
| `LLM_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | LLM 接口地址 | AI Agent |
| `LLM_MODEL` | `qwen3.7-max` | LLM 模型名称 | AI Agent |
| `LLM_TEMPERATURE` | `0.7` | LLM 温度参数 | AI Agent |
| `BACKEND_API_BASE` | `http://localhost:8080` | Java API 地址 | AI Agent |

## 附录 B：端口分配

| 服务 | 端口 | 说明 |
|------|------|------|
| Spring Boot API | 8080 | 后端 REST API |
| Vue 3 Frontend | 5173 | 前端开发服务器 |
| FastAPI Agent | 8090 | AI Agent 服务 |
| MySQL | 3306 | 数据库 |
| Redis | 6379 | 缓存 |
