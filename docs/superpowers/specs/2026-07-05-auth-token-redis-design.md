# 认证 Token Redis 存储设计方案

> **版本:** 1.0
> **日期:** 2026-07-05
> **状态:** 定稿

## 1. 目标

将项目认证使用的 JWT Token 存储在 Redis 中，实现登录态管理和注销时 Token 即时失效。

## 2. 方案选型

**White-List 白名单模式**（推荐且已确认）

登录时将 Token 存入 Redis（带 TTL），过滤器每次请求检查 Redis 中是否存在该 Token。注销时从 Redis 删除。Redis 不可用时直接返回 401（无降级策略）。

## 3. Redis Key 设计

```
auth:token:{sha256(token)} → userId
```

| 项 | 值 | 说明 |
|---|---|---|
| Key 前缀 | `auth:token:` | 与业务缓存 `subject:*`、AI 会话 `ai:session:*` 隔离 |
| Key 内容 | JWT 的 SHA256 摘要 | 避免存储完整的 JWT 长字符串 |
| Value | 用户 ID（String） | 用于快速定位用户 |
| TTL | 与 JWT 过期时间一致（24h） | Redis 到期自动清理，无需手动清除 |

## 4. 核心流程

### 4.1 登录流程

```
用户 POST /api/user/auth/login
  → 校验用户名密码
  → JwtTokenProvider.generateToken(userId, role) 生成 JWT
  → DigestUtils.sha256Hex(token) 计算摘要
  → RedisClient.set("auth:token:" + sha256, userId, jwtExpiration, MILLISECONDS)
  → 返回 LoginVO { token, user }
```

### 4.2 注册流程

注册成功后复用登录逻辑（不变），自动触发 Token 的 Redis 存储。

### 4.3 认证过滤器流程

```
JwtAuthenticationFilter.doFilterInternal()
  → resolveToken() 提取 Bearer Token
  → jwtTokenProvider.validateToken(token) 验证 JWT 签名
  → 计算 SHA256(token)
  → RedisClient.exists("auth:token:" + sha256) 检查白名单
    ├─ true  → 设置 SecurityContext（认证通过）
    └─ false → 不设置认证上下文，后续请求返回 401
  → 异常处理：Redis 查询抛异常时，视为 Token 无效（不设置认证）
```

### 4.4 注销流程

```
用户 GET /api/user/auth/logout
  → AuthController 从请求头提取 Bearer Token
  → authService.logout(token) 传入原始 token
  → 计算 SHA256(token)
  → RedisClient.del("auth:token:" + sha256)
  → 返回成功
```

注：`AuthService.logout(String token)` 接收原始 JWT 字符串，由 Controller 负责从请求头提取。

## 5. 变更文件

### 修改文件

| 文件 | 变更内容 |
|------|----------|
| `common/util/RedisClient.java` | 增加带 TTL 的 `set(key, value, ttl, timeUnit)` 方法 |
| `security/JwtAuthenticationFilter.java` | 增加 Redis 白名单检查逻辑 |
| `user/service/impl/AuthServiceImpl.java` | 注入 `JwtTokenProvider` 替代重复的 `generateToken`；实现 `logout(token)`；Redis SET 增加 TTL |
| `user/service/AuthService.java` | `logout()` → `logout(String token)` 接收原始 Token 字符串 |
| `user/controller/AuthController.java` | `logout()` 中从请求头提取 Token 并传给 Service |

### 不变文件

- `JwtTokenProvider.java` — Token 生成/验证逻辑不变
- `UserPrincipal.java` — 用户身份封装不变
- `SecurityConfig.java` — 安全配置不变
- `AuthController.java` — API 接口签名不变
- 全部前端文件 — 不需要修改

## 6. 不变的部分

- JWT 格式不变：HS256 签名，payload 含 `userId`、`role`、`iat`、`exp`
- LoginVO 响应格式不变
- API 接口路径和签名不变
- 前端无需任何修改
- 配置项不变（`jwt.secret`、`jwt.expiration`、Redis 连接配置）

## 7. 安全注意事项

- 不使用降级策略：Redis 不可用时认证接口全部拒绝（401），避免安全缺口
- Token 的 SHA256 摘要作为 Redis Key，避免恶意遍历
- Redis Key 的 TTL 与 JWT 过期时间严格一致，防止长期残留
