# 迁移 Business 配置到 App 装配层

## Goal

将 Business 的运行时配置绑定与 Bean 装配集中到 `app` 组合根，清空 `common.config`，同时保持现有安全、CORS、MyBatis、Agent HTTP/SSE 行为和 Maven 模块依赖方向不变。

## Background

- `common.config` 当前包含 `SecurityConfig`、`CorsConfig`、`MyBatisPlusConfig`、`RestTemplateConfig`、`AgentProperties`、`CorsProperties` 六个类。
- `AgentServiceImpl` 位于 `agent` 模块，却直接依赖 `AgentProperties`；`CookieOriginFilter` 位于 `common` 模块，却直接依赖 `CorsProperties`。
- `app` 已依赖 `common`、`admin`、`client`、`agent`，是唯一可以安全聚合全部配置和业务 Bean 的最外层模块。
- `AppApplication` 扫描整个 `top.zhaizz`，迁移后的 `top.zhaizz.app.config` 会被自动发现。
- 仓库当前没有受 Git 管理的 Java 测试源码；普通 `mvn test` 可能受旧 `target/classes` 影响，因此迁移验证必须使用 `clean`。

## Requirements

- 将六个配置类全部迁移到 `app/src/main/java/top/zhaizz/app/config`，不保留 `top.zhaizz.common.config` 兼容类。
- 将 `RestTemplateConfig` 重命名为 `AgentConfig`；其他五个类保留现有类名。
- `app` 成为唯一配置绑定和运行时 Bean 装配层；`common`、`agent`、`client`、`admin` 不得依赖 `top.zhaizz.app..`。
- `AgentServiceImpl` 移除自动组件注册，通过显式构造器接收 `RestTemplate`、`ObjectMapper`、Agent base URL 和连接超时；由 `AgentConfig` 创建 `AgentService` Bean。
- `CookieOriginFilter` 移除自动组件注册，通过显式构造器接收允许的 Origin 集合；由 `CorsConfig` 创建 Bean。
- `HttpImportAgentGateway` 继续由 `app` 管理，并改为引用迁移后的 `AgentProperties`。
- `app/pom.xml` 显式声明配置实现直接需要的 Web 与 Security 依赖，不依赖下层模块的传递依赖侥幸编译。
- 保持 `at.agent.*`、`at.cors.*` 前缀、默认超时、普通请求超时、SSE 无限读超时、Trace Header、CORS 白名单、Cookie Origin fail-closed、安全路由、401/403 JSON 和过滤器顺序不变。
- 先补迁移前行为测试，再执行迁移；不使用完整 `@SpringBootTest` 连接 MySQL、Redis、MinIO 等外部服务。
- 同步后端目录和质量规范，记录配置归属、显式装配方式及 `mvn -B clean test` 要求。

## Acceptance Criteria

- [x] `backend/business/common/src/main/java/top/zhaizz/common/config` 不再包含 Java 类，仓库没有 `top.zhaizz.common.config` 引用。
- [x] 六个配置类位于 `top.zhaizz.app.config`，其中 HTTP/Agent 装配类名为 `AgentConfig`。
- [x] `AgentServiceImpl` 与 `CookieOriginFilter` 不再依赖 Properties 类型，也不再通过 `@Service` / `@Component` 自动注册。
- [x] Spring 上下文中 `AgentProperties`、`CorsProperties`、`RestTemplate`、`AgentService`、`CookieOriginFilter`、`CorsConfigurationSource` 和 `SecurityFilterChain` 均按预期唯一注册。
- [x] 配置绑定测试验证 `at.agent.base-url/connect-timeout/read-timeout` 与 `at.cors.allowed-origins`。
- [x] 安全测试覆盖匿名公开路由、匿名私有路由、USER、ADMIN、默认拒绝及统一 401/403 JSON。
- [x] Cookie Origin 测试覆盖允许、缺失、拒绝、refresh/logout 和非目标路径。
- [x] Agent 测试覆盖普通请求超时、`X-Request-ID` 透传和 SSE 无读超时。
- [x] ArchUnit 验证 `pojo/common/client/admin/agent` 不依赖 `top.zhaizz.app..`。
- [x] `cd backend/business && mvn -B clean test` 退出码为 0，且不连接真实外部服务。
- [x] 后端 spec 与最终代码一致，Git diff 不包含本任务范围外的行为修改。

## Out of Scope

- 修改 API、数据库 Schema、Python Agent、前端或部署环境变量名称。
- 引入新的 Settings 接口/值对象，或建立完整 Java 集成测试基础设施。
- 把 `AgentServiceImpl`、`CookieOriginFilter` 移入 `app`，或重构其他业务服务。
- 保留旧包 deprecated 桥接类、双注册配置或兼容 Bean。

## Key Decisions

- 全部六个类迁入 `app.config`，必要解耦通过 app 显式 `@Bean` 装配完成。
- 下层消费者使用普通构造参数，不新增 Settings 抽象，也不反向依赖 `app`。
- HTTP 配置类命名为 `AgentConfig`。
- 使用一个 Trellis 任务，按“测试当前行为 → 迁移 → 全量验证”执行。
- 使用五类最小回归测试，不使用仅验证启动成功的空测试或完整外部服务上下文。
- 不提供旧 Java 包兼容层。
