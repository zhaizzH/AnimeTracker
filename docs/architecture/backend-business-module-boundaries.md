# backend/business 模块边界规范

状态：已确认，待实施  
日期：2026-08-26  
适用范围：`backend/business`

## 1. 目标

在不改变 REST API、JSON 字段、数据库结构和部署方式的前提下，明确六个 Maven 模块的职责，阻止 `common` 继续吸收运行时实现。

本次保持：

- `admin`、`client`、`agent` 按使用者划分，不改为领域模块。
- `common`、`pojo`、`app` 继续作为独立 Maven 模块。
- `admin`、`client` 保持 Controller → Service → Mapper/Store 三层。
- 现有 Service 接口与 `impl` 实现全部保留。
- `ImageStorageGateway`、`ImageCategory` 继续位于 `common.storage`。

## 2. 依赖方向

```text
pojo
common
admin  ──→ common + pojo
client ──→ common + pojo
agent  ──→ common
app    ──→ admin + client + agent + common
```

硬性约束：

1. `admin`、`client`、`agent` 互不依赖。
2. `common` 不依赖 `app` 或任一业务模块。
3. `pojo` 不依赖其他项目内模块。
4. `app` 是唯一组合根，负责装配 Spring Bean 和运行时适配器。
5. Controller 不直接依赖 Mapper、Service 实现类或 `app.infrastructure`。

## 3. 模块职责

### 3.1 common：稳定契约

允许内容：

| 包 | 内容 |
|---|---|
| `common.result` | `Result`、`PageResult` |
| `common.exception` | `BizException` |
| `common.constant` | `ErrorType`、`OperationLogConstants`、`TraceConstants` |
| `common.audit` | `OperationLog` 注解 |
| `common.storage` | `ImageStorageGateway`、`ImageCategory` |

`ImageStorageGateway` 是 admin/client 共同消费、由 app 实现的端口，因此保留在内层共享契约模块。若移入 `app`，会形成 `admin/client → app → admin/client` 的 Maven 循环依赖。

禁止内容：

- `@Component`、`@Service`、`@Configuration`、`@RestControllerAdvice`、`@Scheduled`。
- AOP Aspect、MyBatis Mapper、Redis 操作、JWT 实现、HTTP Client 配置。
- Entity/DTO/VO 转换器或其他具体业务实现。
- 对 `org.springframework.data..`、`org.springframework.security..`、`org.springframework.context..`、`org.springframework.scheduling..`、`org.aspectj..`、`com.baomidou.mybatisplus..`、`jakarta.servlet..` 的依赖。

允许契约接口使用必要的边界类型，例如 `ImageStorageGateway.upload` 的 `MultipartFile`。

### 3.2 pojo：共享数据结构

允许内容：

- Entity、DTO、VO、枚举。
- Jackson、Jakarta Validation、MyBatis-Plus 数据映射注解。
- 仅与数据表达相关的构造器、访问器和简单派生属性。

禁止内容：

- Controller、Service、Mapper、Gateway 实现、Converter。
- Spring 运行时 Bean、定时任务、AOP。
- 访问数据库、Redis、HTTP 或当前登录用户的行为。

### 3.3 admin：管理端业务

- 管理端 Controller、Service 接口/实现、Mapper、Converter。
- 管理员用户、番剧维护、仪表盘、导入和操作日志查询。
- `ImportAgentGateway` 等由管理端消费的外部端口。
- 独立的 `SubjectConverter`，不再依赖 `common.converter`。

### 3.4 client：用户端业务与认证实现

- 用户端 Controller、Service 接口/实现、Mapper/Store、Converter。
- 用户认证、验证码、收藏、追番进度、条目和标签查询。
- `JwtTokenProvider`、`UserPrincipal`、`SecurityUtil`。
- `RedisUtil`、`RedisKeys` 以及限流注解、Aspect、Limiter。
- 独立的 `SubjectConverter`，不再依赖 `common.converter`。

### 3.5 agent：Java Agent 代理

- Agent Controller、Service 接口/实现。
- `AgentProperties` 和 `AgentApiPaths`，作为该集成能力拥有的配置与协议。
- 继续依赖 `common` 的结果、异常和 Trace 契约。

### 3.6 app：组合根与运行时实现

- `AppApplication`、Spring Security 配置、CORS、MyBatis、RestTemplate 配置。
- `GlobalExceptionHandler`。
- `JwtAuthenticationFilter`。
- 操作日志 Aspect、写入 Mapper、清理任务。
- MinIO、Resend、Python Agent HTTP 适配器。

`app` 可以依赖业务模块并复用其公开 Bean；业务模块不得反向依赖 `app`。

## 4. 目标文件迁移

| 当前内容 | 目标位置 |
|---|---|
| `common.config.CorsConfig/CorsProperties/MyBatisPlusConfig/RestTemplateConfig` | `app.config` |
| `common.exception.GlobalExceptionHandler` | `app.web` |
| `common.security.JwtAuthenticationFilter` | `app.security` |
| `common.log.OperationLogAspect/OperationLogCleanupTask` | `app.audit` |
| `common.mapper.OperationLogMapper` | 拆为 `app.audit.mapper.OperationLogWriteMapper`；管理查询并入 `admin.mapper.AdminLogMapper` |
| `common.config.AgentProperties` | `agent.config` |
| `common.constant.AgentApiPaths` | `agent.contract` |
| `common.security.JwtTokenProvider/UserPrincipal` | `client.security` |
| `common.util.SecurityUtil` | `client.security` |
| `common.util.RedisUtil`、`common.constant.RedisKeys` | `client.redis` |
| `common.ratelimit.*` | `client.ratelimit` |
| `common.converter.SubjectVoConverter` | 方法分别合并到 admin/client 的 `SubjectConverter` |
| `common.log.OperationLog` | `common.audit.OperationLog` |

## 5. 审计边界

操作日志保持当前同步、尽力而为语义：

- `common.audit.OperationLog` 只描述审计标记。
- `app.audit.OperationLogAspect` 读取 HTTP/Security 上下文并写库，写入失败只告警，不影响业务结果。
- `app.audit.OperationLogCleanupTask` 保持每日清理 90 天前记录。
- `app.audit.mapper.OperationLogWriteMapper` 只服务写入和清理。
- `admin.mapper.AdminLogMapper` 同时提供分页基础能力与聚合统计，`AdminLogServiceImpl` 不再依赖 common Mapper。

## 6. 安全与 Redis 边界

- Token 签发、Redis 会话白名单和验证码属于 client 认证业务。
- Servlet Filter 与 URL 授权策略属于 app 的运行时 Web 装配。
- `app.security.JwtAuthenticationFilter` 可以依赖 `client.security.JwtTokenProvider` 与 `client.redis.RedisUtil`，因为 `app → client` 符合既定依赖方向。
- 限流目前仅服务 client 认证入口，整体移入 `client.ratelimit`。

本次只迁移归属，不改变 JWT、Redis Key、TTL、即时注销和限流行为。

## 7. 验收标准

1. REST 路径、请求/响应 JSON、HTTP 状态码、数据库表结构均不变。
2. `common` 不再包含运行时 Bean、Mapper、Aspect、Redis/JWT 实现或具体领域 Converter。
3. `common` 不再依赖 `pojo`，POM 仅保留契约所需最小依赖。
4. admin/client 使用各自的 `SubjectConverter`，结果字段与重构前一致。
5. 登录、鉴权、限流、操作日志、图片上传和 Agent 转发测试通过。
6. ArchUnit 自动阻止违反本规范的依赖重新进入仓库。

## 8. 明确不做

- 不改为 DDD、Clean Architecture 或微服务。
- 不新增 Maven 模块。
- 不删除 Service 接口。
- 不移动 `ImageStorageGateway`、`ImageCategory` 到 `app`。
- 不修改 REST API、数据库脚本和业务行为。

