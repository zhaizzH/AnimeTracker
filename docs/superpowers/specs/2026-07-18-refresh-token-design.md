---
name: Refresh Token 自动续期设计
description: 为登录流程增加 Refresh Token 机制，实现无感自动续期，解决固定过期生硬退出问题
metadata:
  type: spec
---

# Refresh Token 自动续期设计

## 背景

当前登录流程使用固定 24h 过期的 JWT Access Token，到期后无任何提醒，直接 401 跳转登录页，用户体验生硬。

## 目标

引入 Refresh Token 机制，在保证安全性的前提下实现无感续期，活跃用户不会被强制退出。

## 令牌模型

| Token 类型 | 格式 | 时效 | Redis 前缀 | 用途 |
|------------|------|------|------------|------|
| Access Token | JWT (含 userId, role) | 30 分钟 | `auth:token:` (现有) | 请求认证 |
| Refresh Token | 不透明随机字符串 (SHA256 摘要存储) | 7 天 | `auth:refresh:` (新增) | 续期 Access Token |

- Refresh Token 采用不透明随机字符串，不由 JWT 签发，避免携带额外载荷
- Refresh Token 每次使用时轮换（旧值失效，签发新值）
- Access Token 的 JWT `exp` 仍校验，与 Redis 白名单双重验证

## 流程设计

### 登录

```text
POST /api/user/auth/login
  → 验证用户名密码
  → 签发 Access Token (30min) → 存 Redis auth:token:<sha256>
  → 签发 Refresh Token (7天)  → 存 Redis auth:refresh:<sha256>
  → 返回 { accessToken, refreshToken, user }
```

### 邮箱验证

```text
POST /api/user/auth/verify-email
  → 校验验证码
  → 标记 email_verified = true
  → 同上签发 access + refresh token
  → 返回 { accessToken, refreshToken, user }
```

### 续期

```text
POST /api/user/auth/refresh
  Body: { refreshToken: string }
  → 校验 refreshToken 在 Redis 中存在
  → 删除旧 refreshToken (轮换)
  → 签发新 Access Token (30min) + 新 Refresh Token (7天)
  → 返回 { accessToken, refreshToken }
  → 失败: 401, refresh token 无效或已过期
```

### 登出

```text
GET → POST /api/user/auth/logout
  → 删除 Redis auth:token:<sha256> (现有)
  → 删除 Redis auth:refresh:<sha256> (新增)
```

### 前端无感续期

```text
axios 401 拦截器
  ├─ 判断是否正在刷新 (isRefreshing 锁，防并发)
  ├─ 调用 POST /api/user/auth/refresh
  │   ├─ 成功 → 更新 auth store (accessToken, refreshToken) + localStorage
  │   │       → 用新 accessToken 重试原请求
  │   └─ 失败 → 清空 token，跳转 /login
  └─ 其他 401 队列等待刷新完成后统一重试
```

## 影响范围

### 后端 (4 文件)

| 文件 | 改动 |
|------|------|
| `AuthController.java` | 新增 `POST /refresh` 端点 |
| `AuthService.java` | 新增 `LoginVO refresh(String refreshToken)` |
| `AuthServiceImpl.java` | `login()` / `verifyEmail()` 签发双 token；新增 `refresh()` / `generateRefreshToken()` |
| `application-local.yml` | `jwt.expiration` → 1800000(30min)；新增 `jwt.refresh-expiration: 604800000(7d)` |

### 前端 (4 文件)

| 文件 | 改动 |
|------|------|
| `types/index.ts` | `AuthResult` 增加 `refreshToken` 字段 |
| `api/auth.ts` | 新增 `refresh(refreshToken)` |
| `stores/auth.ts` | 存储 refreshToken；提供 refresh 方法 |
| `api/http.ts` | 401 拦截器实现无感续期 |

## 安全考量

- Refresh Token 每次刷新时轮换，旧 token 立即失效
- Refresh Token 以 SHA256 摘要形式存 Redis，原始值仅在一次响应中传输
- Access Token 30 分钟短时效，减少泄露影响面
- 登出时同时清除 access + refresh token

## 未纳入范围

- 不引入 HttpOnly Cookie（沿用现有 localStorage 方案）
- 不做「即将过期提醒弹窗」（无感续期已解决体验问题）
- 不限制多设备登录（按现有行为，一人可多端同时登录）
