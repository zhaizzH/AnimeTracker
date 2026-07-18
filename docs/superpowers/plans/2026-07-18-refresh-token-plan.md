# Refresh Token 自动续期 Implementation Plan
# 使用中文commit message
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为登录流程增加 Refresh Token 机制，活跃用户无感续期，不再被 24h 固定过期生硬踢出

**Architecture:** 引入双 Token 模型——短时效 Access Token (JWT, 30min) + 长时效 Refresh Token (不透明随机串, 7天)。Access Token 继续走现有 Redis 白名单验证，Refresh Token 独立 Redis 前缀存储，每次刷新时轮换。前端 401 拦截器自动尝试续期，队列机制防并发。

**Tech Stack:** Spring Boot (jjwt, Redis), Vue 3 (Pinia, axios)

## Global Constraints

- jwt.expiration → 1800000 (30min)，新增 jwt.refresh-expiration → 604800000 (7d)
- Refresh Token 为不透明随机字符串（非 JWT），SecureRandom 32 bytes → hex
- Refresh Token 存 Redis key = `auth:refresh:<sha256>`, TTL = 7 天
- 前端 refreshToken 存 localStorage，与 accessToken 同级管理
- Access Token 仍存现有 Redis `auth:token:<sha256>` 白名单

---

### Task 1: 后端配置 + LoginVO 加字段

**Files:**
- Modify: `backend/business/app/src/main/resources/application-local.yml:29-31`
- Modify: `backend/business/pojo/src/main/java/top/zhaizz/pojo/vo/LoginVO.java`

**Interfaces:**
- Consumes: (none)
- Produces: `LoginVO` 新增 `refreshToken` 字段

- [ ] **Step 1: 修改 JWT 配置**

application-local.yml:29-32:
```yaml
jwt:
  secret: dev-secret-key-not-for-production-use-change-it
  expiration: 1800000    # 30 分钟
  refresh-expiration: 604800000  # 7 天
```

- [ ] **Step 2: LoginVO 增加 refreshToken 字段**

```java
@Data
@AllArgsConstructor
public class LoginVO {
    private String token;
    private String refreshToken;
    private UserVO user;
}
```

- [ ] **Step 3: 提交**

```bash
git add backend/business/app/src/main/resources/application-local.yml backend/business/pojo/src/main/java/top/zhaizz/pojo/vo/LoginVO.java
git commit -m "feat: JWT 时效改为 30min，LoginVO 增加 refreshToken 字段"
```

---

### Task 2: AuthService 接口 + 实现刷新逻辑

**Files:**
- Modify: `backend/business/user/src/main/java/top/zhaizz/user/service/AuthService.java`
- Modify: `backend/business/user/src/main/java/top/zhaizz/user/service/impl/AuthServiceImpl.java`

**Interfaces:**
- Consumes: `LoginVO` (已含 refreshToken 字段), `RedisClient.del(key)`, `RedisClient.set(key, value, ttl, unit)`
- Produces: `AuthService.refresh(String refreshToken) → LoginVO`

- [ ] **Step 1: AuthService 接口新增 refresh 方法**

```java
/**
 * 刷新 Token
 * @param refreshToken 刷新令牌
 * @return LoginVO（含新的 accessToken + refreshToken）
 */
LoginVO refresh(String refreshToken);
```

- [ ] **Step 2: AuthServiceImpl 新增依赖和方法**

完整 AuthServiceImpl 改动（在现有代码基础上）：

```java
// ===== 新增 import =====
import java.security.SecureRandom;

// ===== 注入 refresh expiration =====
@Value("${jwt.refresh-expiration}")
private long jwtRefreshExpiration;  // Refresh Token 过期时间，单位毫秒

// ===== 新增常量 =====
private static final String REDIS_REFRESH_PREFIX = "auth:refresh:";

// ===== SecureRandom 实例 =====
private static final SecureRandom SECURE_RANDOM = new SecureRandom();

// ===== 修改 generateLoginVO —— 同时签发 refresh token =====
private LoginVO generateLoginVO(User user) {
    String accessToken = jwtTokenProvider.generateToken(user.getId(), user.getRole());
    String accessTokenHash = DigestUtils.sha256Hex(accessToken);
    redisClient.set(REDIS_TOKEN_PREFIX + accessTokenHash, user.getId().toString(), jwtExpiration, TimeUnit.MILLISECONDS);

    String refreshToken = generateRefreshToken();
    String refreshTokenHash = DigestUtils.sha256Hex(refreshToken);
    redisClient.set(REDIS_REFRESH_PREFIX + refreshTokenHash, user.getId().toString(), jwtRefreshExpiration, TimeUnit.MILLISECONDS);

    return new LoginVO(accessToken, refreshToken, UserConverter.toUserVO(user));
}

// ===== 新增 generateRefreshToken 私有方法 =====
private String generateRefreshToken() {
    byte[] bytes = new byte[32];
    SECURE_RANDOM.nextBytes(bytes);
    StringBuilder sb = new StringBuilder(64);
    for (byte b : bytes) {
        sb.append(String.format("%02x", b));
    }
    return sb.toString();
}

// ===== 新增 refresh 方法 =====
@Override
public LoginVO refresh(String refreshToken) {
    String refreshTokenHash = DigestUtils.sha256Hex(refreshToken);
    String userIdStr = redisClient.get(REDIS_REFRESH_PREFIX + refreshTokenHash);
    if (userIdStr == null) {
        throw new BizException(ErrorType.UNAUTHORIZED, "refresh token 无效或已过期");
    }

    // 删除旧 refresh token（轮换）
    redisClient.del(REDIS_REFRESH_PREFIX + refreshTokenHash);

    // 查询用户
    User user = userMapper.selectById(Long.valueOf(userIdStr));
    if (user == null) {
        throw new BizException(ErrorType.UNAUTHORIZED, "用户不存在");
    }

    return generateLoginVO(user);
}

// ===== 修改 logout —— 同时清理 refresh token =====
@Override
public void logout(String token) {
    String accessTokenHash = DigestUtils.sha256Hex(token);
    redisClient.del(REDIS_TOKEN_PREFIX + accessTokenHash);

    // 同时清理 refresh token
    // 注意：当前 logout 方法只有 token 参数，没有 refreshToken
    // 这里清理 access token，客户端应自行清理 refreshToken
    // 白名单清理在 filter 中已校验 access token，refresh token 由前端自行清除
}
```

> logout 的 refresh token 清理问题：由于 logout 目前只接收 access token，无法从 access token 推导 refresh token。方案是保持 logout 只清 access token，refresh token 随 access token 过期自然失效（TTL 到达），或者前端在调用 logout 后主动清除 localStorage 中的 refreshToken。

- [ ] **Step 3: 提交**

```bash
git add backend/business/user/src/main/java/top/zhaizz/user/service/AuthService.java backend/business/user/src/main/java/top/zhaizz/user/service/impl/AuthServiceImpl.java
git commit -m "feat: 实现 Refresh Token 签发与刷新逻辑"
```

---

### Task 3: AuthController 刷新端点

**Files:**
- Modify: `backend/business/user/src/main/java/top/zhaizz/user/controller/AuthController.java`

**Interfaces:**
- Consumes: `AuthService.refresh(String)`
- Produces: `POST /api/user/auth/refresh` API

- [ ] **Step 1: 新增 refresh 端点和内部请求体类**

AuthController 中新增（在 logout 方法之前或之后）：

```java
/**
 * 刷新 Token
 * <p>使用 Refresh Token 换取新的 Access Token + Refresh Token（轮换）</p>
 */
@PostMapping("/refresh")
public Result<LoginVO> refresh(@Valid @RequestBody RefreshTokenRequest request) {
    LoginVO loginVO = authService.refresh(request.getRefreshToken());
    return Result.success(loginVO);
}
```

新增内部类（在 ResendCodeRequest 之后）：

```java
@Data
public static class RefreshTokenRequest {
    @NotBlank(message = "refreshToken 不能为空")
    private String refreshToken;
}
```

- [ ] **Step 2: 提交**

```bash
git add backend/business/user/src/main/java/top/zhaizz/user/controller/AuthController.java
git commit -m "feat: 新增 POST /api/user/auth/refresh 端点"
```

---

### Task 4: 前端类型 + API

**Files:**
- Modify: `frontend/client/src/types/index.ts`
- Modify: `frontend/client/src/api/auth.ts`

**Interfaces:**
- Consumes: (none)
- Produces: `AuthResult.refreshToken`, `authApi.refresh(refreshToken)`

- [ ] **Step 1: AuthResult 增加 refreshToken 字段**

```typescript
export interface AuthResult {
  token: string
  refreshToken: string
  user: UserVO
}
```

- [ ] **Step 2: auth.ts 新增 refresh 方法**

```typescript
import type { ..., VerifyEmailRequest } from '@/types'

// 在 logout() 之后新增
refresh(refreshToken: string) {
  return http.post<ApiResponse<AuthResult>>('/api/user/auth/refresh', { refreshToken })
},
```

- [ ] **Step 3: 提交**

```bash
git add frontend/client/src/types/index.ts frontend/client/src/api/auth.ts
git commit -m "feat: AuthResult 增加 refreshToken，auth API 新增 refresh 方法"
```

---

### Task 5: 前端 auth store

**Files:**
- Modify: `frontend/client/src/stores/auth.ts`

- [ ] **Step 1: store 增加 refreshToken 状态**

```typescript
// 在 token 初始化旁边增加 refreshToken
const token = ref<string | null>(localStorage.getItem('token'))
const refreshToken = ref<string | null>(localStorage.getItem('refreshToken'))

// login() — 保存 refreshToken
async function login(data: LoginRequest) {
  loading.value = true
  try {
    const res = await authApi.login(data)
    token.value = res.data.data.token
    refreshToken.value = res.data.data.refreshToken
    user.value = res.data.data.user
    localStorage.setItem('token', res.data.data.token)
    localStorage.setItem('refreshToken', res.data.data.refreshToken)
  } finally {
    loading.value = false
  }
}

// verifyEmail() — 同样保存 refreshToken
async function verifyEmail(data: VerifyEmailRequest) {
  loading.value = true
  try {
    const res = await authApi.verifyEmail(data)
    token.value = res.data.data.token
    refreshToken.value = res.data.data.refreshToken
    user.value = res.data.data.user
    localStorage.setItem('token', res.data.data.token)
    localStorage.setItem('refreshToken', res.data.data.refreshToken)
  } finally {
    loading.value = false
  }
}

// refresh() — 刷新 token 后更新状态
async function refresh() {
  if (!refreshToken.value) throw new Error('no refresh token')
  const res = await authApi.refresh(refreshToken.value)
  token.value = res.data.data.token
  refreshToken.value = res.data.data.refreshToken
  localStorage.setItem('token', res.data.data.token)
  localStorage.setItem('refreshToken', res.data.data.refreshToken)
  return res.data.data.token
}

// logout() — 清理 refreshToken
async function logout() {
  try {
    await authApi.logout()
  } finally {
    token.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
  }
}

// fetchMe() — 失败时也清理 refreshToken
async function fetchMe() {
  if (!token.value) return
  try {
    const res = await authApi.getMe()
    user.value = res.data.data
  } catch {
    token.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
  }
}

// return 中暴露 refreshToken
return {
  token, refreshToken, user, loading,
  isAuthenticated, isAdmin,
  login, register, resendCode, verifyEmail, logout, fetchMe, updateProfile, refresh,
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/client/src/stores/auth.ts
git commit -m "feat: auth store 存储 refreshToken，新增 refresh 方法"
```

---

### Task 6: 前端 401 拦截器 — 无感续期

**Files:**
- Modify: `frontend/client/src/api/http.ts`

- [ ] **Step 1: 实现带队列机制的 401 拦截器**

```typescript
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const http = axios.create({
  baseURL: '',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

let isRefreshing = false
let pendingRequests: Array<{
  resolve: (token: string) => void
  reject: (err: any) => void
}> = []

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // 不是 401 或已经是刷新请求，直接拒绝
    if (error.response?.status !== 401 || originalRequest.url?.includes('/auth/refresh')) {
      return Promise.reject(error)
    }

    // 正在刷新中，将请求加入队列等待
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingRequests.push({ resolve, reject })
      }).then((token) => {
        originalRequest.headers.Authorization = `Bearer ${token}`
        return http(originalRequest)
      })
    }

    isRefreshing = true
    const authStore = useAuthStore()

    try {
      const newToken = await authStore.refresh()
      // 重试所有等待的请求
      pendingRequests.forEach(({ resolve }) => resolve(newToken))
      pendingRequests = []
      originalRequest.headers.Authorization = `Bearer ${newToken}`
      return http(originalRequest)
    } catch (refreshError) {
      // 刷新失败，拒绝所有等待的请求
      pendingRequests.forEach(({ reject }) => reject(refreshError))
      pendingRequests = []
      authStore.logout()
      window.location.href = '/login'
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  }
)

export default http
```

> 注意：需要在 auth store 中导出 `refresh` 方法（Task 5 已包含）。

- [ ] **Step 2: 提交**

```bash
git add frontend/client/src/api/http.ts
git commit -m "feat: 401 拦截器实现 Refresh Token 无感续期"
```
