# 后端目录与依赖边界

## 总体结构

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
    └── jobs/                 # importer / indexer / scheduler
```

证据：`backend/business/pom.xml`、`backend/agent/main.py`、`backend/agent/app/agent/dependencies.py`。

## Spring Business 放置规则

- `pojo` 只放数据结构：请求用 DTO，响应用 VO，数据库映射用 Entity。
- `client/admin` 遵循 Controller → Service → Mapper/Store；Controller 只做绑定、鉴权上下文和响应包装。
- 外部系统先在消费模块定义 Gateway，实现在 `app.infrastructure`。参考 `ImportAgentGateway` → `HttpImportAgentGateway`。
- 只有多个业务模块共享的能力才放 `common`；模块私有端口不要上提。
- `app` 是组合根，聚合业务模块并承载 MinIO、Resend、Agent HTTP 等适配器，以及所有 Spring 配置绑定和运行时 Bean 装配。

## 配置装配契约：Business → App

### 1. Scope / Trigger

- 触发条件：新增或迁移 Business 运行时配置、Properties 绑定类或跨模块基础设施 Bean。
- 目标：让 `app` 成为唯一配置组合根，避免 `common`/`agent` 反向依赖应用层。

### 2. Signatures

- 配置类位于 `top.zhaizz.app.config`：`AgentConfig`、`AgentProperties`、`CorsConfig`、`CorsProperties`、`MyBatisPlusConfig`、`SecurityConfig`。
- 下层实现使用普通构造器：`AgentServiceImpl(RestTemplate, ObjectMapper, String baseUrl, long connectTimeout)`、`CookieOriginFilter(List<String> allowedOrigins)`。

### 3. Contracts

- 保留 `at.agent.base-url/connect-timeout/read-timeout` 与 `at.cors.allowed-origins` key、默认值和环境变量映射。
- `AgentConfig` 创建共享 `RestTemplate`、`AgentService` 和 trace interceptor；SSE 实例 `readTimeout=0`。
- `CorsConfig` 创建 `/api/**` CORS source 与 Cookie Origin filter；Origin 白名单精确匹配并允许 credentials。

### 4. Validation & Error Matrix

- 缺失或空 `allowed-origins` + refresh/logout POST → 403（fail closed）。
- 非 Cookie 路径或非 POST → 跳过 Origin 检查并继续过滤链。
- 未认证私有路由 → 401 JSON；已认证但角色不足/未匹配路由 → 403 JSON。
- Agent 普通请求使用配置读超时；SSE 请求不因普通读超时中断；上游网络失败继续映射为 `SERVICE_UNAVAILABLE`。

### 5. Good / Base / Bad Cases

- Good：`app.config` 绑定 Properties，并通过 `@Bean` 显式向下层传普通值。
- Base：下层模块只依赖 `common` 契约、接口或 JDK 类型，不读取 Spring Environment。
- Bad：在 `common`/`agent` 中新增 `@Component` 读取 `top.zhaizz.app` 或直接注入 `*Properties`。

### 6. Tests Required

- `AppConfigurationBindingTest`：断言 Properties、RestTemplate、AgentService、CookieOriginFilter、CORS source 唯一注册及具体 key 值。
- `SecurityConfigAuthorizationTest`：断言公开、匿名私有、USER、ADMIN、默认拒绝及 401/403 JSON。
- `CookieOriginFilterTest`：断言 refresh/logout 的允许、缺失、未知 Origin 和非目标路径。
- `AgentConfigTest`：断言超时、`X-Request-ID` 透传与 SSE 无读超时；`ArchitectureBoundaryTest`：断言下层不依赖 `top.zhaizz.app..`。

### 7. Wrong vs Correct

#### Wrong

```java
@Component
class AgentServiceImpl {
    AgentServiceImpl(AgentProperties properties) { }
}
```

#### Correct

```java
@Bean
AgentService agentService(RestTemplate restTemplate, ObjectMapper mapper, AgentProperties properties) {
    return new AgentServiceImpl(restTemplate, mapper, properties.getBaseUrl(), properties.getConnectTimeout());
}
```

## Python Agent 放置规则

- `app/api` 只负责协议、依赖注入与序列化，业务流程进入 `app/chat`、`app/agent`、`app/rag`。
- 领域层通过 `Protocol` 或 `AgentDependencies` 访问外部能力。
- Redis、HTTP、LLM、MySQL 和子进程实现只放 `app/adapters`，由 `main.py` lifespan 组装。
- importer/indexer/scheduler 属于 `jobs`，不要塞进 FastAPI 路由。
- 新 Agent 工具按最小权限放到 client/admin 对应节点，不创建全局万能工具集。

## 禁止做法

- `client/admin` 直接依赖 `app.infrastructure`。
- Python 领域节点直接创建 Redis、httpx 或 LLM 客户端。
- Controller/Router 内堆积事务、批处理或复杂状态转换。
- 不得因父 POM 已引入 ArchUnit 就声称边界已有自动保护；必须保留 `ArchitectureBoundaryTest` 并运行 `mvn -B clean test`。
