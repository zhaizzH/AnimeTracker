# Email Verification (Resend) Implementation Plan

## 使用中文commit信息

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add email verification with Resend.com to the user registration flow.

**Architecture:** 
- Backend: `VerificationService` (new) handles code generation, Redis storage, and email sending via Resend Java SDK. `AuthServiceImpl` orchestrates the registration flow split into two steps: register (creates user + sends code) and verify-email (validates code + issues JWT).
- Frontend: Register.vue becomes a two-step form — submit registration, then verify code on the same page.
- Redis stores verification codes with 5-minute TTL using key format `auth:email:<email>`.

**Tech Stack:** Spring Boot 3.2, MyBatis-Plus, Redis (Lettuce), Resend Java SDK, Vue 3 + Pinia

## Global Constraints

- Java 21, Spring Boot 3.2.0, MyBatis-Plus 3.5.5
- Package base: `top.zhaizz`
- Existing RedisClient in common module reused for all Redis ops
- Use existing JwtTokenProvider for token generation
- Follow existing `BizException` + `ErrorType` error pattern
- Email becomes required in RegisterDTO (add `@NotBlank`)
- Verification code: 6 alphanumeric chars, 5min TTL, Redis key `auth:email:<email>`
- Resend API key configured via `resend.api-key` property
- Frontend follows existing Pinia store + axios patterns

---

### Task 1: Database Migration + Schema Sync

**Files:**
- Modify: `docs/db-schema.sql`
- Run manually on the DB

- [ ] **Step 1: Apply DDL to the database**

Run on the target MySQL instance:
```sql
ALTER TABLE `user`
  ADD COLUMN `email_verified` tinyint(1) NOT NULL DEFAULT 0 COMMENT '邮箱是否已验证';
```

- [ ] **Step 2: Sync `docs/db-schema.sql`**

Edit the `user` table definition to add the new column after `role`:

```sql
  `role` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'USER' COMMENT '角色: USER=普通用户, ADMIN=管理员',
  `email_verified` tinyint(1) NOT NULL DEFAULT 0 COMMENT '邮箱是否已验证',
  `created_at` datetime NOT NULL COMMENT '创建时间',
```

- [ ] **Step 3: Commit**

```bash
git add docs/db-schema.sql
git commit -m "feat: add email_verified column to user table"
```

---

### Task 2: User Entity + RegisterDTO

**Files:**
- Modify: `backend/business/pojo/src/main/java/top/zhaizz/pojo/entity/User.java`
- Modify: `backend/business/pojo/src/main/java/top/zhaizz/pojo/dto/RegisterDTO.java`

- [ ] **Step 1: Add `emailVerified` field to User entity**

```java
// Add after `role` field
private Boolean emailVerified;  // 邮箱是否已验证
```

- [ ] **Step 2: Make email required in RegisterDTO**

```java
@NotBlank(message = "邮箱不能为空")
@Email(message = "邮箱格式不正确")
@Size(max = 128, message = "邮箱长度不能超过128")
private String email;
```

- [ ] **Step 3: Commit**

```bash
git add backend/business/pojo/src/main/java/top/zhaizz/pojo/entity/User.java backend/business/pojo/src/main/java/top/zhaizz/pojo/dto/RegisterDTO.java
git commit -m "feat: add emailVerified to User, make email required in RegisterDTO"
```

---

### Task 3: ErrorType — Add Verification Error Codes

**Files:**
- Modify: `backend/business/common/src/main/java/top/zhaizz/common/ErrorType.java`

- [ ] **Step 1: Add `EMAIL_NOT_VERIFIED` and `VERIFICATION_FAILED`**

```java
VERIFICATION_FAILED(400, "验证失败"),
EMAIL_NOT_VERIFIED(403, "邮箱未验证"),
```

Insert in the enum between `TOO_MANY_REQUESTS` and `INTERNAL_ERROR`.

- [ ] **Step 2: Commit**

```bash
git add backend/business/common/src/main/java/top/zhaizz/common/ErrorType.java
git commit -m "feat: add VERIFICATION_FAILED and EMAIL_NOT_VERIFIED error codes"
```

---

### Task 4: Resend Dependency + Configuration

**Files:**
- Modify: `backend/business/user/pom.xml`
- Modify: `backend/business/app/src/main/resources/application.yml`
- Modify: `backend/business/app/src/main/resources/application-local.yml`

- [ ] **Step 1: Add Resend Java SDK dependency to `user/pom.xml`**

```xml
<!-- Resend Email -->
<dependency>
    <groupId>com.resend</groupId>
    <artifactId>resend-java</artifactId>
    <version>3.1.0</version>
</dependency>
```

Insert after the spring-boot-starter-security dependency block.

- [ ] **Step 2: Add Resend config property to `application.yml`**

```yaml
# Resend 邮件服务
resend:
  api-key: ${resend.api-key}
```

Insert after the `minio` section.

- [ ] **Step 3: Add Resend API key placeholder to `application-local.yml`**

```yaml
resend:
  api-key: re_xxxxxxxxxxxx
```

Insert after the `minio` section. Use a placeholder value that the developer replaces with their actual key.

- [ ] **Step 4: Add Resend version property to parent `pom.xml`**

In the `<properties>` section of `backend/business/pom.xml`:
```xml
<resend-java.version>3.1.0</resend-java.version>
```

And add the dependency to `<dependencyManagement>`:
```xml
<dependency>
    <groupId>com.resend</groupId>
    <artifactId>resend-java</artifactId>
    <version>${resend-java.version}</version>
</dependency>
```

- [ ] **Step 5: Commit**

```bash
git add backend/business/pom.xml backend/business/user/pom.xml backend/business/app/src/main/resources/application.yml backend/business/app/src/main/resources/application-local.yml
git commit -m "feat: add Resend Java SDK dependency and config"
```

---

### Task 5: VerificationService — Interface

**Files:**
- Create: `backend/business/user/src/main/java/top/zhaizz/user/service/VerificationService.java`

- [ ] **Step 1: Create the interface**

Use the user module's existing package structure (`top.zhaizz.user.service`):

```java
package top.zhaizz.user.service;

/**
 * 邮箱验证服务：验证码生成、发送、校验
 */
public interface VerificationService {

    /**
     * 生成验证码并发送到指定邮箱
     *
     * @param email 目标邮箱
     * @throws top.zhaizz.common.exception.BizException 当发送失败时抛出
     */
    void sendVerificationCode(String email);

    /**
     * 校验邮箱验证码
     * <p>校验成功后标记 user.email_verified = true</p>
     *
     * @param email 邮箱
     * @param code  用户输入的验证码
     * @throws top.zhaizz.common.exception.BizException 验证码过期或错误时抛出
     */
    void verifyEmail(String email, String code);
}
```

- [ ] **Step 2: Commit**

```bash
git add backend/business/user/src/main/java/top/zhaizz/user/service/VerificationService.java
git commit -m "feat: add VerificationService interface"
```

---

### Task 6: VerificationServiceImpl — Implementation

**Files:**
- Create: `backend/business/user/src/main/java/top/zhaizz/user/service/impl/VerificationServiceImpl.java`

- [ ] **Step 1: Create the implementation**

```java
package top.zhaizz.user.service.impl;

import com.resend.Resend;
import com.resend.core.exception.ResendException;
import com.resend.services.emails.model.CreateEmailOptions;
import com.resend.services.emails.model.CreateEmailResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.util.RedisClient;
import top.zhaizz.pojo.entity.User;
import top.zhaizz.user.mapper.UserMapper;
import top.zhaizz.user.service.VerificationService;

import java.security.SecureRandom;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class VerificationServiceImpl implements VerificationService {

    private final RedisClient redisClient;
    private final UserMapper userMapper;

    @Value("${resend.api-key}")
    private String resendApiKey;

    private static final String REDIS_KEY_PREFIX = "auth:email:";
    private static final long CODE_TTL_MINUTES = 5;
    private static final int CODE_LENGTH = 6;
    private static final String ALPHANUMERIC = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789";
    private static final SecureRandom RANDOM = new SecureRandom();

    @Override
    public void sendVerificationCode(String email) {
        // 1. 生成6位字母数字验证码
        StringBuilder code = new StringBuilder(CODE_LENGTH);
        for (int i = 0; i < CODE_LENGTH; i++) {
            code.append(ALPHANUMERIC.charAt(RANDOM.nextInt(ALPHANUMERIC.length())));
        }

        // 2. 存入 Redis（5分钟 TTL）
        redisClient.set(REDIS_KEY_PREFIX + email, code.toString(), CODE_TTL_MINUTES, TimeUnit.MINUTES);

        // 3. 通过 Resend 发送邮件
        Resend resend = new Resend(resendApiKey);
        CreateEmailOptions params = CreateEmailOptions.builder()
                .from("noreply@animetracker.top")
                .to(email)
                .subject("[AnimeTracker] 邮箱验证码")
                .text("你的验证码是：" + code + "\n\n此验证码5分钟内有效，请勿泄露给他人。")
                .build();

        try {
            CreateEmailResponse response = resend.emails().send(params);
        } catch (ResendException e) {
            // 发送失败时清理 Redis 中的验证码
            redisClient.del(REDIS_KEY_PREFIX + email);
            throw new BizException(ErrorType.INTERNAL_ERROR, "验证码发送失败，请稍后重试");
        }
    }

    @Override
    public void verifyEmail(String email, String code) {
        // 1. 从 Redis 获取存储的验证码
        String storedCode = redisClient.get(REDIS_KEY_PREFIX + email);

        if (storedCode == null) {
            throw new BizException(ErrorType.VERIFICATION_FAILED, "验证码已过期，请重新发送");
        }

        if (!storedCode.equals(code)) {
            throw new BizException(ErrorType.VERIFICATION_FAILED, "验证码不正确");
        }

        // 2. 校验通过，删除 Redis key
        redisClient.del(REDIS_KEY_PREFIX + email);

        // 3. 更新用户 email_verified 状态
        User user = userMapper.selectOne(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<User>()
                        .eq(User::getEmail, email)
        );
        if (user == null) {
            throw new BizException(ErrorType.NOT_FOUND, "用户不存在");
        }
        user.setEmailVerified(true);
        user.setUpdatedAt(java.time.LocalDateTime.now());
        userMapper.updateById(user);
    }
}
```

**Note:** The `from` email (`noreply@animetracker.top`) assumes you have a verified sending domain in Resend. If your Resend account sends from a different domain, adjust this value.

- [ ] **Step 2: Commit**

```bash
git add backend/business/user/src/main/java/top/zhaizz/user/service/impl/VerificationServiceImpl.java
git commit -m "feat: implement VerificationService - code gen, Redis store, Resend send"
```

---

### Task 7: Update AuthService Interface

**Files:**
- Modify: `backend/business/user/src/main/java/top/zhaizz/user/service/AuthService.java`

- [ ] **Step 1: Add `verifyEmail` method and update `register` doc**

```java
package top.zhaizz.user.service;

import top.zhaizz.pojo.dto.LoginDTO;
import top.zhaizz.pojo.dto.RegisterDTO;
import top.zhaizz.pojo.vo.LoginVO;
import top.zhaizz.pojo.vo.UserVO;

/**
 * 认证服务接口
 */
public interface AuthService {

    /**
     * 用户注册
     * <p>创建用户（email_verified=false）并发送验证码邮件</p>
     *
     * @param request 注册信息
     */
    void register(RegisterDTO request);

    /**
     * 验证邮箱
     * <p>校验验证码通过后标记邮箱已验证并返回 JWT</p>
     *
     * @param email 邮箱地址
     * @param code  验证码
     * @return LoginVO（含 JWT Token 和用户信息）
     */
    LoginVO verifyEmail(String email, String code);

    /**
     * 用户登录
     * @return LoginVO（含 JWT Token 和用户信息）
     */
    LoginVO login(LoginDTO request);

    /**
     * 用户注销
     */
    void logout(String token);

    /**
     * 生成 JWT Token
     */
    String generateToken(Long userId, String role);
}
```

- [ ] **Step 2: Commit**

```bash
git add backend/business/user/src/main/java/top/zhaizz/user/service/AuthService.java
git commit -m "feat: add verifyEmail method to AuthService"
```

---

### Task 8: Update AuthServiceImpl

**Files:**
- Modify: `backend/business/user/src/main/java/top/zhaizz/user/service/impl/AuthServiceImpl.java`

- [ ] **Step 1: Rewrite `register()` to send verification code instead of auto-login**

```java
package top.zhaizz.user.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import lombok.RequiredArgsConstructor;
import org.apache.commons.codec.digest.DigestUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import top.zhaizz.common.exception.BizException;
import top.zhaizz.common.ErrorType;
import top.zhaizz.common.util.RedisClient;
import top.zhaizz.common.security.JwtTokenProvider;
import top.zhaizz.user.converter.UserConverter;
import top.zhaizz.pojo.dto.LoginDTO;
import top.zhaizz.pojo.dto.RegisterDTO;
import top.zhaizz.pojo.entity.User;
import top.zhaizz.user.mapper.UserMapper;
import top.zhaizz.user.service.AuthService;
import top.zhaizz.user.service.VerificationService;
import top.zhaizz.pojo.vo.LoginVO;
import top.zhaizz.pojo.vo.UserVO;

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
    private final VerificationService verificationService;

    @Value("${jwt.expiration}")
    private long jwtExpiration; // 过期时间，单位毫秒

    private static final String REDIS_TOKEN_PREFIX = "auth:token:";

    @Override
    public void register(RegisterDTO request) {
        // 1. 检查用户名唯一性
        if (userMapper.existsByUsername(request.getUsername())) {
            throw new BizException(ErrorType.CONFLICT, "用户名已存在");
        }

        // 2. 创建用户实体
        User user = new User();
        user.setUsername(request.getUsername());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setEmail(request.getEmail());
        user.setNickname(request.getUsername()); // 默认昵称为用户名
        user.setRole("USER");
        user.setEmailVerified(false);
        user.setCreatedAt(LocalDateTime.now());
        user.setUpdatedAt(LocalDateTime.now());

        // 3. 保存
        userMapper.insert(user);

        // 4. 发送验证码邮件
        verificationService.sendVerificationCode(request.getEmail());
    }

    @Override
    public LoginVO verifyEmail(String email, String code) {
        // 1. 校验验证码（内部会更新 email_verified = true）
        verificationService.verifyEmail(email, code);

        // 2. 查找用户
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>()
                        .eq(User::getEmail, email)
        );

        // 3. 生成 JWT
        String token = jwtTokenProvider.generateToken(user.getId(), user.getRole());

        // 4. Token 摘要存入 Redis 白名单
        String tokenHash = DigestUtils.sha256Hex(token);
        redisClient.set(REDIS_TOKEN_PREFIX + tokenHash, user.getId().toString(), jwtExpiration, TimeUnit.MILLISECONDS);

        // 5. 返回 Token + 用户信息
        return new LoginVO(token, UserConverter.toUserVO(user));
    }

    // login(), logout(), generateToken() — unchanged from current implementation
    @Override
    public LoginVO login(LoginDTO request) {
        User user = userMapper.selectOne(
                new LambdaQueryWrapper<User>()
                        .eq(User::getUsername, request.getUsername())
        );
        if (user == null || !passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new BizException(ErrorType.UNAUTHORIZED, "用户名或密码错误");
        }
        String token = jwtTokenProvider.generateToken(user.getId(), user.getRole());
        String tokenHash = DigestUtils.sha256Hex(token);
        redisClient.set(REDIS_TOKEN_PREFIX + tokenHash, user.getId().toString(), jwtExpiration, TimeUnit.MILLISECONDS);
        return new LoginVO(token, UserConverter.toUserVO(user));
    }

    @Override
    public void logout(String token) {
        String tokenHash = DigestUtils.sha256Hex(token);
        redisClient.del(REDIS_TOKEN_PREFIX + tokenHash);
    }

    @Override
    public String generateToken(Long userId, String role) {
        return jwtTokenProvider.generateToken(userId, role);
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add backend/business/user/src/main/java/top/zhaizz/user/service/impl/AuthServiceImpl.java
git commit -m "feat: split register flow - create user then verify email"
```

---

### Task 9: Update AuthController

**Files:**
- Modify: `backend/business/user/src/main/java/top/zhaizz/user/controller/AuthController.java`

- [ ] **Step 1: Add `POST /verify-email` endpoint and update `register` response**

```java
package top.zhaizz.user.controller;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.dto.LoginDTO;
import top.zhaizz.pojo.dto.RegisterDTO;
import top.zhaizz.user.service.AuthService;
import top.zhaizz.pojo.vo.LoginVO;

/**
 * 认证控制器
 */
@RestController
@RequestMapping("/api/user/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    /**
     * 用户注册
     * <p>创建用户并发送验证码邮件，注册成功后需调用 verify-email 完成验证</p>
     */
    @PostMapping("/register")
    public Result<Void> register(@Valid @RequestBody RegisterDTO request) {
        authService.register(request);
        return Result.success(null);
    }

    /**
     * 验证邮箱
     * <p>校验验证码，通过后标记邮箱已验证并返回 JWT Token 和用户信息</p>
     */
    @PostMapping("/verify-email")
    public Result<LoginVO> verifyEmail(@Valid @RequestBody VerifyEmailRequest request) {
        LoginVO loginVO = authService.verifyEmail(request.getEmail(), request.getCode());
        return Result.success(loginVO);
    }

    /**
     * 用户登录
     */
    @PostMapping("/login")
    public Result<LoginVO> login(@Valid @RequestBody LoginDTO request) {
        LoginVO loginVO = authService.login(request);
        return Result.success(loginVO);
    }

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

    /**
     * 验证邮箱请求体
     */
    @Data
    public static class VerifyEmailRequest {
        @NotBlank(message = "邮箱不能为空")
        @Email(message = "邮箱格式不正确")
        private String email;

        @NotBlank(message = "验证码不能为空")
        @Size(min = 6, max = 6, message = "验证码为6位")
        private String code;
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add backend/business/user/src/main/java/top/zhaizz/user/controller/AuthController.java
git commit -m "feat: add verify-email endpoint"
```

---

### Task 10: Update Frontend Types

**Files:**
- Modify: `frontend/client/src/types/index.ts`

- [ ] **Step 1: Add `VerifyEmailRequest` and update `RegisterRequest`**

```typescript
export interface RegisterRequest {
  username: string
  password: string
  email: string  // changed from optional to required
}

export interface VerifyEmailRequest {
  email: string
  code: string
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/client/src/types/index.ts
git commit -m "feat: add VerifyEmailRequest type, make email required in RegisterRequest"
```

---

### Task 11: Update Frontend Auth API

**Files:**
- Modify: `frontend/client/src/api/auth.ts`

- [ ] **Step 1: Add `verifyEmail` API call**

```typescript
import http from './http'
import type { ApiResponse, AuthResult, LoginRequest, RegisterRequest, UserVO, UpdateProfileRequest, VerifyEmailRequest } from '@/types'

export const authApi = {
  login(data: LoginRequest) {
    return http.post<ApiResponse<AuthResult>>('/api/user/auth/login', data)
  },
  register(data: RegisterRequest) {
    return http.post<ApiResponse<string>>('/api/user/auth/register', data)
  },
  verifyEmail(data: VerifyEmailRequest) {
    return http.post<ApiResponse<AuthResult>>('/api/user/auth/verify-email', data)
  },
  logout() {
    return http.get<ApiResponse<string>>('/api/user/auth/logout')
  },
  getMe() {
    return http.get<ApiResponse<UserVO>>('/api/user/me')
  },
  updateProfile(data: UpdateProfileRequest) {
    return http.put<ApiResponse<UserVO>>('/api/user/me', data)
  },
}
```

Note: `register` response type changed from `ApiResponse<AuthResult>` to `ApiResponse<string>` since it no longer returns a token.

- [ ] **Step 2: Commit**

```bash
git add frontend/client/src/api/auth.ts
git commit -m "feat: add verifyEmail API call"
```

---

### Task 12: Update Frontend Auth Store

**Files:**
- Modify: `frontend/client/src/stores/auth.ts`

- [ ] **Step 1: Add `VerifyEmailRequest` import and `verifyEmail` action**

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { UserVO, LoginRequest, RegisterRequest, UpdateProfileRequest, VerifyEmailRequest } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<UserVO | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'ADMIN')

  async function login(data: LoginRequest) {
    loading.value = true
    try {
      const res = await authApi.login(data)
      token.value = res.data.data.token
      user.value = res.data.data.user
      localStorage.setItem('token', res.data.data.token)
    } finally {
      loading.value = false
    }
  }

  async function register(data: RegisterRequest) {
    loading.value = true
    try {
      await authApi.register(data)
      // register no longer returns token; user must verify email
    } finally {
      loading.value = false
    }
  }

  async function verifyEmail(data: VerifyEmailRequest) {
    loading.value = true
    try {
      const res = await authApi.verifyEmail(data)
      token.value = res.data.data.token
      user.value = res.data.data.user
      localStorage.setItem('token', res.data.data.token)
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      token.value = null
      user.value = null
      localStorage.removeItem('token')
    }
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const res = await authApi.getMe()
      user.value = res.data.data
    } catch {
      token.value = null
      user.value = null
      localStorage.removeItem('token')
    }
  }

  async function updateProfile(data: UpdateProfileRequest) {
    const res = await authApi.updateProfile(data)
    user.value = res.data.data
  }

  return {
    token, user, loading,
    isAuthenticated, isAdmin,
    login, register, verifyEmail, logout, fetchMe, updateProfile,
  }
})
```

- [ ] **Step 2: Commit**

```bash
git add frontend/client/src/stores/auth.ts
git commit -m "feat: add verifyEmail action to auth store"
```

---

### Task 13: Update Register.vue — Two-Step Registration Flow

**Files:**
- Modify: `frontend/client/src/pages/Register.vue`

- [ ] **Step 1: Rewrite the component with two-step flow**

The component needs two states:
1. **Form view**: username, email, password, confirm password (same as current, but email is now required)
2. **Verify view**: shows "验证码已发送到 xxx@email.com" + 6-digit verification code input + submit

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, Mail, Eye, EyeOff } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const step = ref<'form' | 'verify'>('form')
const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const code = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''

  if (!username.value.trim()) {
    error.value = '请填写用户名'
    return
  }
  if (!email.value.trim()) {
    error.value = '请填写邮箱'
    return
  }
  if (!password.value) {
    error.value = '请填写密码'
    return
  }
  if (password.value.length < 6) {
    error.value = '密码长度不能少于6位'
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致'
    return
  }

  loading.value = true
  try {
    await authStore.register({
      username: username.value.trim(),
      password: password.value,
      email: email.value.trim(),
    })
    step.value = 'verify'
  } catch (e: any) {
    error.value = e?.response?.data?.message || '注册失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function handleVerify() {
  error.value = ''

  if (!code.value.trim() || code.value.length !== 6) {
    error.value = '请输入6位验证码'
    return
  }

  loading.value = true
  try {
    await authStore.verifyEmail({
      email: email.value.trim(),
      code: code.value.trim(),
    })
    router.push('/')
  } catch (e: any) {
    error.value = e?.response?.data?.message || '验证失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-[80vh] flex items-center justify-center app-container">
    <div class="w-full max-w-md">
      <div class="app-card p-8">
        <!-- Form Step -->
        <template v-if="step === 'form'">
          <div class="text-center mb-8">
            <h1 class="page-title mb-2">创建账户</h1>
            <p class="page-subtitle">加入我们</p>
          </div>

          <!-- Error -->
          <Transition name="fade">
            <div
              v-if="error"
              class="mb-6 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-600 dark:text-red-400 text-center"
            >
              {{ error }}
            </div>
          </Transition>

          <!-- Form -->
          <form @submit.prevent="handleRegister" class="space-y-5">
            <!-- Username -->
            <div>
              <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">用户名</label>
              <div class="relative">
                <User class="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4" style="color: var(--color-text-secondary)" />
                <input
                  v-model="username"
                  type="text"
                  placeholder="输入用户名"
                  class="input-field pl-10"
                  autocomplete="username"
                />
              </div>
            </div>

            <!-- Email (now required) -->
            <div>
              <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">邮箱</label>
              <div class="relative">
                <Mail class="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4" style="color: var(--color-text-secondary)" />
                <input
                  v-model="email"
                  type="email"
                  placeholder="输入邮箱地址"
                  class="input-field pl-10"
                  autocomplete="email"
                />
              </div>
            </div>

            <!-- Password -->
            <div>
              <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">密码</label>
              <div class="relative">
                <Lock class="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4" style="color: var(--color-text-secondary)" />
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="至少6位密码"
                  class="input-field pl-10 pr-10"
                  autocomplete="new-password"
                />
                <button
                  type="button"
                  class="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded-md hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
                  style="color: var(--color-text-secondary)"
                  @click="showPassword = !showPassword"
                  tabindex="-1"
                >
                  <EyeOff v-if="showPassword" class="h-4 w-4" />
                  <Eye v-else class="h-4 w-4" />
                </button>
              </div>
            </div>

            <!-- Confirm Password -->
            <div>
              <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">确认密码</label>
              <div class="relative">
                <Lock class="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4" style="color: var(--color-text-secondary)" />
                <input
                  v-model="confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  placeholder="再次输入密码"
                  class="input-field pl-10 pr-10"
                  autocomplete="new-password"
                />
                <button
                  type="button"
                  class="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded-md hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
                  style="color: var(--color-text-secondary)"
                  @click="showConfirmPassword = !showConfirmPassword"
                  tabindex="-1"
                >
                  <EyeOff v-if="showConfirmPassword" class="h-4 w-4" />
                  <Eye v-else class="h-4 w-4" />
                </button>
              </div>
            </div>

            <!-- Submit -->
            <button type="submit" class="btn-primary w-full py-3" :disabled="loading">
              <svg v-if="loading" class="animate-spin h-4 w-4 inline mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              {{ loading ? '注册中...' : '注册' }}
            </button>
          </form>

          <div class="mt-6 text-center text-sm" style="color: var(--color-text-secondary)">
            已有账户？
            <router-link to="/login" class="text-primary-500 hover:text-primary-600 font-medium transition-colors">
              登录
            </router-link>
          </div>
        </template>

        <!-- Verify Step -->
        <template v-else>
          <div class="text-center mb-8">
            <h1 class="page-title mb-2">验证邮箱</h1>
            <p class="page-subtitle">验证码已发送到 <strong class="text-primary-500">{{ email }}</strong></p>
          </div>

          <Transition name="fade">
            <div
              v-if="error"
              class="mb-6 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-600 dark:text-red-400 text-center"
            >
              {{ error }}
            </div>
          </Transition>

          <form @submit.prevent="handleVerify" class="space-y-6">
            <!-- Code Input -->
            <div>
              <label class="block text-sm font-medium mb-2 text-center" style="color: var(--color-text)">输入验证码</label>
              <input
                v-model="code"
                type="text"
                maxlength="6"
                placeholder="输入6位验证码"
                class="input-field text-center text-2xl tracking-[0.5em] font-mono"
                autocomplete="one-time-code"
              />
            </div>

            <!-- Submit -->
            <button type="submit" class="btn-primary w-full py-3" :disabled="loading">
              <svg v-if="loading" class="animate-spin h-4 w-4 inline mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              {{ loading ? '验证中...' : '验证' }}
            </button>
          </form>

          <div class="mt-6 text-center text-sm" style="color: var(--color-text-secondary)">
            未收到验证码？
            <button class="text-primary-500 hover:text-primary-600 font-medium transition-colors bg-transparent border-none cursor-pointer">
              重新发送
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/client/src/pages/Register.vue
git commit -m "feat: two-step registration with email verification"
```
