# 技术设计：Business 配置集中到 App 组合根

## 1. 架构边界

当前 Maven 依赖方向是：

```text
pojo ← common ← admin/client/agent ← app
              ↖──────────────── app
```

目标保持该方向不变，并让 `app` 成为唯一配置绑定与运行时装配层：

```text
application.yml
  → top.zhaizz.app.config.*Properties
  → top.zhaizz.app.config 的 @Bean 方法
  → common/agent 中只接收普通构造参数的实现类
```

任何 `pojo/common/client/admin/agent → app` 的 Java 包依赖都属于错误，由 ArchUnit 阻止；Maven reactor 继续阻止模块循环。

## 2. 目标文件结构

```text
backend/business/app/src/main/java/top/zhaizz/app/config/
├── AgentConfig.java
├── AgentProperties.java
├── CorsConfig.java
├── CorsProperties.java
├── MyBatisPlusConfig.java
└── SecurityConfig.java
```

不保留旧 `top.zhaizz.common.config` 类型。`RestTemplateConfig` 更名为 `AgentConfig`，因为它同时负责 Agent HTTP 客户端和 `AgentService` 装配。

## 3. Bean 装配契约

### AgentConfig

- 继续使用 `@EnableConfigurationProperties(AgentProperties.class)`，前缀保持 `at.agent`。
- `restTemplate(...)` 继续使用 `connectTimeout`、`readTimeout` 和 Trace interceptor。
- `traceForwardingInterceptor()` 的 Bean 和 `X-Request-ID` 行为保持不变。
- 新增 `AgentService agentService(RestTemplate, ObjectMapper, AgentProperties)` Bean，显式调用 `AgentServiceImpl` 构造器。
- `AgentServiceImpl` 保存 `baseUrl` 与 `connectTimeout` 普通字段；普通请求使用共享 `RestTemplate`，SSE 专用实例保持 `readTimeout=0`。
- `HttpImportAgentGateway` 位于 `app`，直接引用新的 `AgentProperties` 合法。

### CorsConfig

- 继续使用 `@EnableConfigurationProperties(CorsProperties.class)`，前缀保持 `at.cors`。
- `corsConfigurationSource(...)` 的 `/api/**`、Methods、Headers 和 Credentials 配置保持不变。
- 新增 `CookieOriginFilter cookieOriginFilter(CorsProperties)` Bean，将允许 Origin 集合作为构造参数传入。
- `CookieOriginFilter` 对 null/空白名单继续 fail closed；仅 refresh/logout POST 请求执行 Origin 检查。

### SecurityConfig / MyBatisPlusConfig

- `SecurityConfig` 继续注入唯一的 `CookieOriginFilter`、`JwtAuthenticationFilter`、`CorsConfigurationSource` 和 `ObjectMapper`。
- 两个过滤器相对顺序、路由匹配和 401/403 JSON 响应不变。
- MyBatis 分页仍使用 MySQL、最大 100 条与 overflow=true。

## 4. 下层消费者改造

### AgentServiceImpl

- 删除 `@Service`、`@RequiredArgsConstructor` 和 `AgentProperties` import。
- 显式构造器参数：`RestTemplate`、`ObjectMapper`、`String baseUrl`、`long connectTimeout`。
- 不把 `String` 或 `long` 注册成独立 Spring Bean；只由 `AgentConfig` 的 Bean 方法显式传值。

### CookieOriginFilter

- 删除 `@Component`、`@RequiredArgsConstructor` 和 `CorsProperties` import。
- 显式接收允许 Origin 集合；缺失或空集合与当前缺失 Properties 值一样拒绝目标请求。

## 5. 测试设计

全部测试放在 `app` 模块，复用现有 starter-test、security-test、Mockito 和 ArchUnit：

| 测试类 | 方法与断言 |
|---|---|
| `AppConfigurationBindingTest` | `ApplicationContextRunner` 验证属性绑定、关键 Bean 唯一性和 CORS 内容 |
| `SecurityConfigAuthorizationTest` | `@WebMvcTest` + 最小 Controller 验证公开/USER/ADMIN/默认拒绝及 401/403 JSON |
| `CookieOriginFilterTest` | `MockHttpServletRequest/Response/FilterChain` 验证 Origin 矩阵 |
| `AgentConfigTest` | 通过实际 `RestTemplate` 验证超时配置与 trace；MockRestServiceServer 验证 `X-Request-ID`；JDK HttpServer 黑盒验证 SSE |
| `ArchitectureBoundaryTest` | ArchUnit 排除测试类后验证下层包不依赖 `top.zhaizz.app..` |

禁止完整 `@SpringBootTest(AppApplication.class)`，避免误连 MySQL、Redis、MinIO。SSE 测试使用随机端口、有限总超时并在 finally 停止服务器；MDC 必须在 finally 清理。

## 6. 兼容、迁移与回滚

- 配置 key、默认值和环境变量映射不变，不需要配置迁移或部署双写。
- Java 包名属于仓库内部实现，一次性修复全部 import，不提供旧包 shim。
- `app/pom.xml` 补充 Web/Security 直接依赖，确保配置类不依赖传递依赖编译。
- 必须运行 `mvn -B clean test`，清除 `common/target/classes` 中旧配置 class，避免重复 Bean 或假成功。
- 回滚以提交为单位：先回退配置迁移，再回退行为测试；不得在同一工作树同时保留新旧配置类。

## 7. 主要风险与控制

- 安全过滤顺序或路由漂移：由授权矩阵与 Bean 唯一性测试控制。
- 配置绑定遗漏：由 `ApplicationContextRunner` 使用显式属性控制。
- Origin 保护变松：由允许/缺失/拒绝矩阵控制。
- SSE 超时测试抖动：使用明显大于普通 readTimeout 的延迟差、JUnit 总超时和资源清理。
- 模块反向依赖：由编译、ArchUnit 和 app 直接依赖共同控制。
