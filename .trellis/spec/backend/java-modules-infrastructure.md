# Business Infrastructure 模块目标设计

> 从 [目录结构与模块边界](./directory-structure.md) 拆出（2026-10-22）。原文件把三个 Java 模块的完整七段式混在一起（36KB），按模块拆开便于按需注入。
> 模块边界总览、Business 现状对照、Python Agent 结构与 `app/rag` 拆分仍在主文件。

## Business Infrastructure 模块目标设计

状态：已实施；Redis、限流、图片存储和邮件实现已迁入 infrastructure，并通过针对性测试。Agent 专属导入通信已确定归 Java agent；身份与日志协作采用 log → auth → infrastructure → common。

### 1. Scope / Trigger

新增 `infrastructure` Maven 模块，承接 Redis、限流、图片存储、邮件发送等技术实现，内部按能力分包。必须迁移并复用现有代码，不能新建空模块或平行实现而保留原有生产实现。`app` 负责启动与组合装配。

这不是所有持久化代码的集中仓库：auth 的 Token/会话规则、log 的操作日志查询/存储/清理、client/admin 的业务查询和规则仍属于各自所有者。Redis 通用访问可供这些模块使用，不代表其业务键、TTL 决策或 Mapper 也必须迁入 infrastructure。

### 2. Signatures / 现有迁移入口

现有技术接口（迁移保持行为，通用接口与实现均归 infrastructure 的对应能力包）：

```java
boolean allowOrCount(String bucket, int limit, int windowSeconds);
void reset(String bucket);
String upload(MultipartFile file, ImageCategory category);
void send(String recipient, String subject, String text);
```

| 当前来源（Java 包或模块） | 并入目标 |
|---|---|
| common.util.RedisUtil | infrastructure 的 Redis 能力包 |
| common.ratelimit 的 RateLimit、RateLimitAspect、RateLimiter | infrastructure 的限流能力包 |
| app.infrastructure.storage.minio 的 MinioImageStorageGateway | infrastructure 的图片存储能力包 |
| app.infrastructure.email 的 ResendEmailGateway | infrastructure 的邮件能力包 |
| client.gateway.EmailGateway | infrastructure.email 的公开接口 |
| common.storage.ImageStorageGateway/ImageCategory | infrastructure.storage 的公开接口及参数类型 |

与实现相伴的 MinioConfig、MinioProperties、ResendConfig 必须纳入迁移审查：供应商客户端构建与初始化属于技术实现，组合启用由 app 负责；禁止迁移时重复注册 Bean、重复初始化存储桶或遗漏配置绑定。供应商配置与 Properties 随能力位于 infrastructure 内，由 app 组合启用；应用级安全、CORS 与跨模块装配继续归 app。

`EmailGateway` 与 `ImageStorageGateway` 等通用技术接口统一归入 infrastructure 对应能力包，不再留在 client/admin/common；配套参数类型 ImageCategory 随接口迁入 storage。`agent.gateway.HttpImportAgentGateway` 与原 admin 的 ImportAgentGateway 已统一归入 Java agent，admin 单向调用 agent，见 [Java Agent 模块目标设计](./java-modules-agent.md)。

### 3. Contracts / 迁移约束

- 以搬迁、调整依赖与调用方为主，保留已有实现逻辑；不另写一套 Redis、限流、MinIO、Resend 生产实现。
- 对每项能力同时核对实现、接口、调用方、配置、依赖声明和测试；旧路径不能保留仍被装配的副本。
- app 保留应用配置入口和组合装配；基础设施不得反向依赖 app 的类型。
- 业务模块依赖 infrastructure 的公开能力接口；供应商实现与 SDK 使用限制在 infrastructure 内部，app 负责装配。通用技术能力不反向依赖 client/admin/agent/auth/log/app 的实现。
- 同模块内按能力组织公开接口与实现，例如 `infrastructure.email.EmailGateway` 与 `infrastructure.email.resend.ResendEmailGateway`，`infrastructure.storage.ImageStorageGateway` 与 `infrastructure.storage.minio.MinioImageStorageGateway`。业务方不得直接构造或引用供应商实现。
- 接口迁移同时更新实现的 implements、全部消费者与测试 import、Maven 依赖和装配扫描；不在旧业务包中保留平行接口来掩盖循环依赖。
- 不要求给每个 Redis 薄封装机械新增接口；已有通用接口统一归属，新增抽象必须有实际使用需求。专属 Agent 导入接口不能仅因后缀为 Gateway 就视为通用技术接口。
- 邮件收件人、模板内容、业务触发时机仍由 client 等业务所有者决定；限流配额和业务成功后的 reset 时机由使用方决定。
- 保留现有配置 key、单位、默认值和外部协议。供应商 SDK 类型不得暴露给业务；图片接口目前接受 MultipartFile，不因本次搬迁擅自改签名。

### 4. Validation & Error Matrix

| 场景 | 迁移要求 |
|---|---|
| 限流计数返回 null | 保持现有 allowOrCount 返回 true 的逻辑 |
| 超出限额 | 保持拒绝行为和既有 HTTP 429 映射 |
| Redis 抛异常 | 按 RedisUtil 实现和调用方核对，不凭注释声称所有故障均放行 |
| 图片校验/上传或邮件发送失败 | 保留当前错误映射，不吞错或返回伪造成功结果 |
| 迁移后重复 Bean 或循环依赖 | 视为迁移未完成，不能靠同时保留两套实现交付 |

### 5. Good / Base / Bad Cases

- Good：现有 ResendEmailGateway 搬入新模块，配置与调用方同步调整，业务仍决定发送内容。
- Base：复用 RedisUtil 和 RateLimiter，保持计数、窗口、reset 及错误语义。
- Bad：新建 InfrastructureRedisUtil，同时让 common.RedisUtil 继续承担实际生产调用；或把会话、收藏规则一并塞入 infrastructure。

### 6. Tests Required

- Maven 依赖图无循环；通用技术能力不反向依赖业务实现或 app；业务调用方不再引用迁出的旧接口/实现路径，也不直接依赖供应商实现或 SDK 类型。
- 配置与上下文验证：所需 Bean 唯一注册，MinIO 初始化和邮件客户端配置行为保持一致。
- Redis/限流覆盖窗口、超限、reset 与故障行为；图片/邮件覆盖成功及原有失败路径，迁移已有测试而非只新增空模块测试。
- 清理审查：旧实现、旧扫描/导入、冗余依赖与旧测试路径同步处理；运行相关模块及完整 Business 构建测试。

### 7. Wrong vs Correct

- Wrong：只新增 infrastructure 模块，把现有 common/app 技术实现标记为以后再搬，却宣称迁移完成。
- Correct：逐项完成现有实现、调用、配置、依赖和测试的迁移，旧生产实现不再残留，验证通过后再标记实施完成。

证据目录：`backend/business/infrastructure/src/main/java/top/zhaizz/infrastructure/{redis,ratelimit,storage,email}`、`backend/business/agent/src/main/java/top/zhaizz/agent/gateway`、`backend/business/app/src/main/java/top/zhaizz/app/config/AgentConfig.java`。
