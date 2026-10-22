# Business Auth 模块目标设计

> 从 [目录结构与模块边界](./directory-structure.md) 拆出（2026-10-22）。原文件把三个 Java 模块的完整七段式混在一起（36KB），按模块拆开便于按需注入。
> 模块边界总览、Business 现状对照、Python Agent 结构与 `app/rag` 拆分仍在主文件。

## Business Auth 模块目标设计

状态：已实施并通过 auth/infrastructure 针对性测试及 Business reactor 测试。`auth` Maven 模块已承接原 common 与 client 中的认证技术能力，当前接口和包路径以源码为准。

### 1. Scope / Trigger

| 模块 | 已确认职责 |
|---|---|
| auth | Token 签发与验证、请求认证、会话刷新与撤销、技术过期策略 |
| client | 注册、登录业务校验、邮箱验证、重置密码等用户业务 |
| admin | 用户管理、角色修改、禁用用户等管理员业务 |
| app | 安全配置和模块装配 |

业务层决定何时签发或撤销，auth 执行认证技术操作。不得将整个 AuthServiceImpl 因类名含 Auth 就迁入 auth。

### 2. Signatures / 迁移入口

当前实现的认证能力签名如下；实现位于 `auth.security`，会话数据类型位于 `pojo.dto.auth`：

```java
// auth.security.JwtTokenProvider
String generateToken(Long userId, String role);
boolean validateToken(String token);
// auth.security.AuthSessionStore
void saveRefresh(String rawToken, Long userId, long startedAtEpochMs, long ttlMs);
Optional<ConsumedRefreshSession> consumeRefresh(String rawToken);
void revokeAccess(String rawToken);
void revokeRefresh(String rawToken);
void revokeAll(Long userId);
```

迁移对象包括 JwtTokenProvider、JwtAuthenticationFilter、AuthSessionStore、认证身份类型，以及 client 的会话生成方法中的随机令牌生成、access 白名单维护、refresh 保存与技术过期计算。账户查询、启用状态校验和 UserVO 组装留在 client。

认证公开能力、返回类型和包结构已按实施设计落地；不要求将所有存储方法直接暴露给业务方。业务 DTO/VO/Entity 统一归 pojo；UserVO/LoginVO 的类型声明留在 pojo，组装职责留在 client，不能把类型声明与组装逻辑一起迁入 auth。

### 3. Contracts / 边界与保留行为

- client/admin 调用 auth 的能力，传入已由业务验证的 userId、role 等必要身份信息；auth 不依赖 client/admin/app 实现，不查询业务 UserMapper，不返回面向用户端的 UserVO/LoginVO。
- client 决定注册唯一性、初始角色、邮箱验证、登录资格与密码重置；admin 决定角色修改、禁用及保护规则。重置密码、修改角色、禁用用户后的会话撤销，由业务流程触发 auth 执行。
- 刷新保持先原子消费 refresh，再由业务查询账户并检查存在/启用状态，最后完成寿命校验与重新签发的行为；原始会话起点不能因刷新重置。业务校验由 client/admin 完成，auth 通过 `AuthTokenService.issue` 执行会话寿命计算与签发。
- refresh TTL 保持为配置有效期与剩余绝对会话时长中的较小值；迁移不得修改现有配置 key、单位或默认值。
- Redis 中使用 Token 的 SHA-256 摘要作键，保留 access 白名单和 access/refresh 用户索引；refresh 消费保留 GETDEL 的单次消费语义。
- 请求认证保持 JWT 验证与 access 白名单双重检查；app 负责安全链装配与路由规则，不能在 auth 中混入管理员用户管理规则。
- HTTP 路由、响应字段、at_refresh HttpOnly Cookie 与 401/403 协议保持现状。客户端响应和 Cookie 处理不因内部模块迁移自动改变归属或行为。
- 已确认依赖方向为 `log → auth → infrastructure → common`：log 通过 auth 读取当前身份，auth 使用 infrastructure 的 Redis 能力，不反向依赖 log。
- 现有 `SecurityUtil` 随身份读取能力迁入 auth；`CookieOriginFilter` 随请求安全机制归 auth，由 app 提供配置并唯一注册。Spring Security 身份实现仍归 auth；纯业务 DTO/VO/Entity 遵守 pojo 统一规则。
- auth 内不使用 log 的操作日志注解或存储服务。需要记录登录/会话业务操作时，由 client/admin 等上层调用方采集；auth 的普通运行日志使用 SLF4J，不引入 log 模块。

### 4. Validation & Error Matrix

| 条件 | 必须保持的行为 |
|---|---|
| refresh 缺失、空白、失效或已消费 | UNAUTHORIZED，不签发新会话 |
| 刷新时账户不存在或被禁用 | 业务层拒绝，返回 UNAUTHORIZED |
| 绝对会话有效期耗尽 | UNAUTHORIZED，不重置会话起点续期 |
| 同一个 refresh 并发使用 | 最多一个请求成功消费 |
| JWT 无效或不在 access 白名单 | 不建立已认证身份，继续由安全链按路由决定响应 |
| 用户业务要求撤销全部会话 | 删除该用户 access/refresh 凭据及对应索引 |

### 5. Good / Base / Bad Cases

- Good：admin 校验管理员权限与被操作用户保护规则，修改用户后调用 auth 撤销会话。
- Base：client 完成登录业务校验，将身份交给 auth 签发，自己通过 Converter 组装用户端响应。
- Bad：auth 依赖 AdminUserServiceImpl，或直接查询 UserMapper 决定注册、禁用、邮箱修改规则。

### 6. Tests Required

- 架构：auth 不反向依赖 client/admin/app/log 的实现，业务方不继续自行维护 Token 存储与生成细节；身份读取保持匿名场景返回空身份的既有语义。
- 会话：refresh 单次消费、绝对寿命、TTL 上界及原始起点保持一致；单会话与全部会话撤销均验证凭据和索引。
- 业务：登录资格、邮箱验证、禁用/角色修改/重置密码触发撤销的行为保持一致。
- HTTP 与装配：JWT 与白名单双重校验、既有 401/403 和 Cookie 行为、安全组件唯一装配。

### 7. Wrong vs Correct

- Wrong：把注册、邮件验证、UserMapper 与 UserVO 连同 Token 代码整包搬入 auth。
- Correct：业务保留账户决策，auth 封装认证机制，app 组合安全配置。

### 代码证据

- `backend/business/auth/src/main/java/top/zhaizz/auth/security/AuthSessionStore.java`
- `backend/business/auth/src/main/java/top/zhaizz/auth/security/JwtTokenProvider.java`
- `backend/business/auth/src/main/java/top/zhaizz/auth/security/JwtAuthenticationFilter.java`
- `backend/business/client/src/main/java/top/zhaizz/client/service/impl/AuthServiceImpl.java`
- `backend/business/client/src/main/java/top/zhaizz/client/service/impl/VerificationServiceImpl.java`
- `backend/business/admin/src/main/java/top/zhaizz/admin/service/impl/AdminUserServiceImpl.java`
