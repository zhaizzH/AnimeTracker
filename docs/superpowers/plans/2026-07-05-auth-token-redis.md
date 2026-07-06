# 认证 Token Redis 存储实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 JWT Token 存入 Redis 白名单，实现登录态管理和注销时即时失效。

**Architecture:** 采用白名单模式 — 登录时将 JWT 的 SHA256 摘要作为 Key 存入 Redis（TTL=24h），过滤器每次请求检查 Redis 中是否存在该 Key，注销时删除。不使用降级策略，Redis 不可用时认证全部拒绝（401）。

**Tech Stack:** Java 21, Spring Boot 3.2, Spring Security, Redis (lettuce), commons-codec (DigestUtils)

## Global Constraints

- Redis 不可用时不做降级，认证接口全部返回 401
- Token 的 SHA256 摘要作为 Redis Key，key 格式：`auth:token:{sha256}`
- TTL 与 JWT 过期时间一致（`jwt.expiration` 配置项，默认 86400000ms）
- 不修改 JWT Token 格式、LoginVO 响应格式、API 接口路径
- 统一使用 `JwtTokenProvider` 生成 Token，消除 `AuthServiceImpl` 中的重复逻辑
- 过滤器一旦检测到 Redis 中不存在该 token，跳过设置认证上下文（不设置 SecurityContext）
- SHA256 使用 `org.apache.commons.codec.digest.DigestUtils.sha256Hex()`

---

## 文件结构

| # | 文件 | 操作 | 职责 |
|---|------|------|------|
| 1 | `backend/api/src/main/java/top/zhaizz/animetracker/common/util/RedisClient.java` | 修改 | 增加带 TTL 的 `set()` 重载 |
| 2 | `backend/api/src/main/java/top/zhaizz/animetracker/user/service/AuthService.java` | 修改 | `logout()` → `logout(String token)` |
| 3 | `backend/api/src/main/java/top/zhaizz/animetracker/user/service/impl/AuthServiceImpl.java` | 修改 | 注入 JwtTokenProvider、实现 logout、Redis TTL |
| 4 | `backend/api/src/main/java/top/zhaizz/animetracker/security/JwtAuthenticationFilter.java` | 修改 | 增加 Redis 白名单检查 |
| 5 | `backend/api/src/main/java/top/zhaizz/animetracker/user/controller/AuthController.java` | 修改 | logout 中提取 Bearer Token 传给 Service |

**不涉及的文件：** JwtTokenProvider、UserPrincipal、SecurityConfig、全部前端文件

---

### Task 1: RedisClient — 增加带 TTL 的 set 方法

**文件：**
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/common/util/RedisClient.java`

**接口：**
- Produces: `void set(String key, String value, long ttl, TimeUnit unit)` — 带过期时间的存储方法

- [ ] **Step 1: 编写测试类**

```java
// backend/api/src/test/java/top/zhaizz/animetracker/common/util/RedisClientTest.java
package top.zhaizz.animetracker.common.util;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
class RedisClientTest {

    @Autowired
    private RedisClient redisClient;

    @Test
    void setWithTtl_shouldStoreAndExpire() throws InterruptedException {
        String key = "test:ttl:" + System.currentTimeMillis();
        String value = "test-value";

        // 写入带 1 秒 TTL
        redisClient.set(key, value, 1, TimeUnit.SECONDS);
        assertEquals(value, redisClient.get(key));

        // 等待过期
        TimeUnit.MILLISECONDS.sleep(1100);
        assertNull(redisClient.get(key));
    }
}
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
cd backend/api && mvn test -Dtest=RedisClientTest#setWithTtl_shouldStoreAndExpire -Dspring.profiles.active=test
```

Expected: FAIL — `RedisClient` 没有 `set(String, String, long, TimeUnit)` 方法

- [ ] **Step 3: 实现 TTL 重载方法**

```java
// RedisClient.java — 新增方法
/**
 * 保存数据（带过期时间）
 * @param key   键
 * @param value 值
 * @param ttl   过期时间长度
 * @param unit  过期时间单位
 */
public void set(String key, String value, long ttl, TimeUnit unit) {
    stringRedisTemplate.opsForValue().set(key, value, ttl, unit);
}
```

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
cd backend/api && mvn test -Dtest=RedisClientTest#setWithTtl_shouldStoreAndExpire -Dspring.profiles.active=test
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/api/src/main/java/top/zhaizz/animetracker/common/util/RedisClient.java
git add backend/api/src/test/java/top/zhaizz/animetracker/common/util/RedisClientTest.java
git commit -m "feat: RedisClient 增加带 TTL 的 set 方法"
```

---

### Task 2: AuthService — 重构 generateToken + 实现 logout

**文件：**
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/user/service/AuthService.java`
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/user/service/impl/AuthServiceImpl.java`

**接口：**
- Consumes: `RedisClient.set(key, value, ttl, TimeUnit)` (from Task 1)
- Produces: `AuthService.logout(String token)` — 接收原始 Token 字符串，从 Redis 删除
- Produces: `AuthServiceImpl` 注入 `JwtTokenProvider`，删除自身的 `generateToken()`

- [ ] **Step 1: 修改 AuthService 接口**

```java
// AuthService.java — logout 方法增加 token 参数
public interface AuthService {

    UserVO register(RegisterDTO request);

    LoginVO login(LoginDTO request);

    /**
     * 用户注销
     * @param token 原始 JWT Token 字符串（从请求头提取）
     */
    void logout(String token);

    String generateToken(Long userId, String role);  // 保留（被其他调用者引用，后续清理）
}
```

- [ ] **Step 2: 修改 AuthServiceImpl**

```java
// AuthServiceImpl.java — 完整文件变更
package top.zhaizz.animetracker.user.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.apache.commons.codec.digest.DigestUtils;
import org.springframework.stereotype.Service;
import top.zhaizz.animetracker.common.exception.BizException;
import top.zhaizz.animetracker.common.ErrorType;
import top.zhaizz.animetracker.common.util.RedisClient;
import top.zhaizz.animetracker.security.JwtTokenProvider;
import top.zhaizz.animetracker.user.converter.UserConverter;
import top.zhaizz.animetracker.common.dto.LoginDTO;
import top.zhaizz.animetracker.common.dto.RegisterDTO;
import top.zhaizz.animetracker.common.entity.User;
import top.zhaizz.animetracker.user.mapper.UserMapper;
import top.zhaizz.animetracker.user.service.AuthService;
import top.zhaizz.animetracker.common.vo.LoginVO;
import top.zhaizz.animetracker.common.vo.UserVO;

import java.time.LocalDateTime;
import java.util.concurrent.TimeUnit;

/**
 * 认证服务实现
 */
@Service
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final UserMapper userMapper;
    private final PasswordEncoder passwordEncoder;
    private final RedisClient redisClient;
    private final JwtTokenProvider jwtTokenProvider;

    @Value("${jwt.expiration}")
    private long jwtExpiration; // 过期时间，单位毫秒

    private static final String REDIS_TOKEN_PREFIX = "auth:token:";

    @Override
    public UserVO register(RegisterDTO request) {
        // 1. 检查用户名唯一性
        if (userMapper.existsByUsername(request.getUsername())) {
            throw new BizException(ErrorType.CONFLICT, "用户名已存在");
        }

        // 2. 创建用户实体
        User user = new User();
        user.setUsername(request.getUsername());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setEmail(request.getEmail());
        user.setNickname(request.getUsername());
        user.setRole("USER");
        user.setCreatedAt(LocalDateTime.now());
        user.setUpdatedAt(LocalDateTime.now());

        // 3. 保存
        userMapper.insert(user);

        return UserConverter.toUserVO(user);
    }

    @Override
    public LoginVO login(LoginDTO request) {
        // 1. 查找用户
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>()
                        .eq(User::getUsername, request.getUsername())
        );

        if (user == null || !passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new BizException(ErrorType.UNAUTHORIZED, "用户名或密码错误");
        }

        // 2. 生成 JWT（统一使用 JwtTokenProvider）
        String token = jwtTokenProvider.generateToken(user.getId(), user.getRole());

        // 3. 计算 SHA256 摘要，存入 Redis（带 TTL）
        String tokenHash = DigestUtils.sha256Hex(token);
        redisClient.set(REDIS_TOKEN_PREFIX + tokenHash, user.getId().toString(), jwtExpiration, TimeUnit.MILLISECONDS);

        // 4. 返回 Token + 用户信息
        return new LoginVO(token, UserConverter.toUserVO(user));
    }

    @Override
    public void logout(String token) {
        // 计算 SHA256 摘要，从 Redis 删除
        String tokenHash = DigestUtils.sha256Hex(token);
        redisClient.del(REDIS_TOKEN_PREFIX + tokenHash);
    }

    @Override
    public String generateToken(Long userId, String role) {
        // 委派给 JwtTokenProvider（兼容旧调用者）
        return jwtTokenProvider.generateToken(userId, role);
    }
}
```

注意需要在文件顶部 import `org.apache.commons.codec.digest.DigestUtils`，同时删除不再需要的 `io.jsonwebtoken.*` 和 `javax.crypto.*` 导入。

- [ ] **Step 3: 编译确认**

Run:
```bash
cd backend/api && mvn compile -q
```

Expected: BUILD SUCCESS — 无编译错误

- [ ] **Step 4: 提交**

```bash
git add backend/api/src/main/java/top/zhaizz/animetracker/user/service/AuthService.java
git add backend/api/src/main/java/top/zhaizz/animetracker/user/service/impl/AuthServiceImpl.java
git commit -m "feat: AuthService 重构 — 统一 JwtTokenProvider + 实现 logout + Redis TTL"
```

---

### Task 3: JwtAuthenticationFilter — 增加 Redis 白名单检查

**文件：**
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/security/JwtAuthenticationFilter.java`

**接口：**
- Consumes: `RedisClient.exists(key)` (existing), `DigestUtils.sha256Hex(token)` (commons-codec)
- Produces: 过滤器在 JWT 签名验证通过后，额外检查 Redis 白名单

- [ ] **Step 1: 修改过滤器实现**

```java
// JwtAuthenticationFilter.java — 完整文件
package top.zhaizz.animetracker.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.apache.commons.codec.digest.DigestUtils;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;
import top.zhaizz.animetracker.common.util.RedisClient;

import java.io.IOException;

/**
 * JWT 认证过滤器：提取 Authorization 头，校验 Token + Redis 白名单，设置 SecurityContext
 */
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtTokenProvider jwtTokenProvider;
    private final RedisClient redisClient;

    private static final String AUTHORIZATION_HEADER = "Authorization";
    private static final String BEARER_PREFIX = "Bearer ";
    private static final String REDIS_TOKEN_PREFIX = "auth:token:";

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {

        String token = resolveToken(request);

        if (StringUtils.hasText(token) && jwtTokenProvider.validateToken(token)) {
            // 计算 SHA256 摘要，检查 Redis 白名单
            String tokenHash = DigestUtils.sha256Hex(token);
            Boolean exists = redisClient.exists(REDIS_TOKEN_PREFIX + tokenHash);

            if (Boolean.TRUE.equals(exists)) {
                Long userId = jwtTokenProvider.getUserIdFromToken(token);
                String role = jwtTokenProvider.getRoleFromToken(token);

                UserPrincipal principal = new UserPrincipal(userId, role);
                principal.setAuthenticated(true);
                SecurityContextHolder.getContext().setAuthentication(principal);
            }
            // Redis 中不存在 → token 已失效，不设置认证上下文
        }

        filterChain.doFilter(request, response);
    }

    /**
     * 从请求头中提取 Bearer Token
     */
    private String resolveToken(HttpServletRequest request) {
        String bearerToken = request.getHeader(AUTHORIZATION_HEADER);
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith(BEARER_PREFIX)) {
            return bearerToken.substring(BEARER_PREFIX.length());
        }
        return null;
    }
}
```

- [ ] **Step 2: 编译确认**

Run:
```bash
cd backend/api && mvn compile -q
```

Expected: BUILD SUCCESS

- [ ] **Step 3: 提交**

```bash
git add backend/api/src/main/java/top/zhaizz/animetracker/security/JwtAuthenticationFilter.java
git commit -m "feat: JwtAuthenticationFilter 增加 Redis 白名单检查"
```

---

### Task 4: AuthController — logout 提取 Token

**文件：**
- Modify: `backend/api/src/main/java/top/zhaizz/animetracker/user/controller/AuthController.java`

**接口：**
- Consumes: `AuthService.logout(String token)` (from Task 2)
- Produces: `GET /api/user/auth/logout` 从请求头提取 Token 并调用 Service

- [ ] **Step 1: 修改 AuthController.logout()**

```java
// AuthController.java — 修改 logout 方法
/**
 * 用户注销
 */
@GetMapping("/logout")
public Result<Void> logout(HttpServletRequest request) {
    String authHeader = request.getHeader("Authorization");
    if (authHeader != null && authHeader.startsWith("Bearer ")) {
        String token = authHeader.substring(7);
        authService.logout(token);
    }
    return Result.success(null);
}
```

同时需要在文件顶部增加 import：`import jakarta.servlet.http.HttpServletRequest;`

- [ ] **Step 2: 编译确认**

Run:
```bash
cd backend/api && mvn compile -q
```

Expected: BUILD SUCCESS

- [ ] **Step 3: 提交**

```bash
git add backend/api/src/main/java/top/zhaizz/animetracker/user/controller/AuthController.java
git commit -m "feat: AuthController logout 从请求头提取 Token"
```

---

### Task 5: 集成验证

- [ ] **Step 1: 全量编译**

Run:
```bash
cd backend/api && mvn clean compile -q
```

Expected: BUILD SUCCESS

- [ ] **Step 2: 运行全部测试**

Run:
```bash
cd backend/api && mvn test -Dspring.profiles.active=test
```

Expected: BUILD SUCCESS（全部测试通过）

- [ ] **Step 3: 端到端验证（启动应用后手动测试）**

启动应用：
```bash
cd backend/api && mvn spring-boot:run
```

验证流程（使用 curl 或 Postman）：

```bash
# 1. 登录 — 应返回 token
curl -s -X POST http://localhost:8080/api/user/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# Expected: 200 + { "data": { "token": "eyJ...", "user": { ... } } }

# 2. 携带 token 访问需认证接口 — 应成功
TOKEN="<上一步返回的 token>"
curl -s http://localhost:8080/api/user/me \
  -H "Authorization: Bearer $TOKEN"
# Expected: 200 + 用户信息

# 3. 注销
curl -s http://localhost:8080/api/user/auth/logout \
  -H "Authorization: Bearer $TOKEN"
# Expected: 200

# 4. 使用已注销的 token 访问 — 应 401
curl -s http://localhost:8080/api/user/me \
  -H "Authorization: Bearer $TOKEN"
# Expected: 401（未认证）

# 5. 非法 token 访问 — 应 401
curl -s http://localhost:8080/api/user/me \
  -H "Authorization: Bearer invalid-token"
# Expected: 401
```

- [ ] **Step 4: 最终提交**

```bash
git add -A && git commit -m "feat: 认证 Token 存储到 Redis（白名单模式）"
```

---

## 自检查

**1. Spec 覆盖：**
- ✅ 登录/注册存储 Token 到 Redis → Task 2
- ✅ 过滤器检查 Redis 白名单 → Task 3
- ✅ 注销删除 Token → Task 2 + Task 4
- ✅ Redis TTL 与 JWT 过期一致 → Task 2（`redisClient.set(..., jwtExpiration, MILLISECONDS)`）
- ✅ Key 格式 `auth:token:{sha256}` → Task 2（`REDIS_TOKEN_PREFIX + tokenHash`）
- ✅ 不使用降级策略 → Task 3（Redis 查不到或异常，不设置认证上下文）
- ✅ 消除重复 generateToken → Task 2（注入 JwtTokenProvider）
- ✅ API 接口不变 → Task 4（保持 `GET /api/user/auth/logout`）
- ✅ 前端不需修改 → 无前端变更

**2. 占位符检查：** ✅ 无 TBD/TODO

**3. 类型一致性：**
- `AuthService.logout(String token)` → 一致出现在 Task 2 接口和 Task 4 调用处
- `RedisClient.set(String, String, long, TimeUnit)` → 一致出现在 Task 1 定义和 Task 2 使用处
- `DigestUtils.sha256Hex()` → 一致出现在 Task 2 和 Task 3
- `REDIS_TOKEN_PREFIX = "auth:token:"` → 一致出现在 Task 2 和 Task 3
