# 邮箱修改验证 + 邮箱唯一性设计方案

> 为 Profile 页邮箱修改添加验证流程，同时补充注册时的邮箱唯一性检查和 DB 唯一约束。

---

## 1. 数据库

```sql
ALTER TABLE `user` ADD UNIQUE INDEX `uk_email`(`email`);
```

---

## 2. Redis Key 规范

| 场景 | Redis Key |
|------|-----------|
| 注册验证 | `auth:email:<email>`（不变） |
| 邮箱修改验证 | `auth:email-change:<userId>:<email>` |

注册 key 不改动，`sendVerificationCode(email)` 只有 email 参数拿不到 userId。邮箱修改新增独立前缀 `auth:email-change:`。

---

## 3. 后端改动

### 3.1 VerificationService

新增方法：

```java
/** 发送邮箱修改验证码（检查新邮箱唯一性） */
void sendEmailChangeCode(Long userId, String newEmail);

/** 校验邮箱修改验证码 → 更新 email + email_verified + 通知旧邮箱 */
void verifyEmailChangeCode(Long userId, String newEmail, String code);
```

`verifyEmailChangeCode` 实现要点：
- 用 `@Transactional` 保证验证码校验 + email 更新原子性
- 旧邮箱为 null 时跳过通知
- 旧邮箱通知用 try-catch 包裹，失败不回滚 email 更新（通知是附加行为）

### 3.2 AuthService / AuthServiceImpl

`register()` 新增邮箱唯一性检查：

```java
if (userMapper.existsByEmail(request.getEmail())) {
    throw new BizException(ErrorType.CONFLICT, "邮箱已被注册");
}
```

### 3.3 UserMapper

新增 `existsByEmail(email)` default 方法。

### 3.4 UserController

新增两个端点，移除 `UpdateUserDTO.email`：

| 端点 | 请求体 | 说明 |
|------|--------|------|
| `POST /api/user/me/send-email-code` | `{ newEmail }` | 验证新邮箱唯一性 → 发验证码 |
| `POST /api/user/me/verify-email-code` | `{ newEmail, code }` | 校验 code → 更新邮箱 + email_verified → 通知旧邮箱 |

`PUT /api/user/me` 的 `UpdateUserDTO` 移除 email 字段，邮箱改由验证端点处理。

### 3.5 UpdateUserDTO

移除 `email` 字段。

### 3.6 ErrorType

无需新增错误码，`CONFLICT(409)` 复用给邮箱重复场景。

---

## 4. 前端改动

### 4.1 types/index.ts

```ts
export interface SendEmailCodeRequest {
  newEmail: string
}
export interface VerifyEmailCodeRequest {
  newEmail: string
  code: string
}
```

### 4.2 api/auth.ts

```ts
sendEmailCode(data: SendEmailCodeRequest)
verifyEmailCode(data: VerifyEmailCodeRequest)
```

### 4.3 stores/auth.ts

新增 `sendEmailCode(newEmail)` 和 `verifyEmailCode(newEmail, code)` actions。

### 4.4 Profile.vue

邮箱区域改动：
- email 输入框不变，右侧新增"发送验证码"按钮
- email 输入框下方新增验证码输入框（初始隐藏）
- 点击"发送验证码"后 60s 倒计时

保存逻辑：
```
email 值变化 → emailDirty = true
  - 新旧邮箱相同 → emailDirty = false（跳过验证）
点"发送验证码" → 调 sendEmailCode(newEmail) → 按钮 60s 倒计时
点"保存":
  - emailDirty && !codeVerified → 提示"请先验证新邮箱"
  - emailDirty && codeVerified → 调 verifyEmailCode(newEmail, code) → 更新 store.user
      - 后端一次性完成：校验 code → 更新 email + email_verified → 通知旧邮箱
      - 如果第二步 updateProfile({nickname, avatar}) 失败，邮箱已成功变更，前端提示"邮箱已更新，昵称/头像保存失败请重试"
  - 调 updateProfile({ nickname, avatar }) 更新非邮箱字段
```

> `verifyEmailCode` 在服务端直接更新 email，所以即使后续 `updateProfile` 因网络波动失败，用户邮箱已成功修改。昵称/头像可单独重试保存。

验证码输入框和按钮只在 emailDirty 时显示。

---

## 5. 涉及文件总览

### 后端

| # | 文件 | 操作 |
|---|------|------|
| 1 | `docs/db-schema.sql` | email 加 unique index |
| 2 | `backend/.../entity/User.java` | 可能无需改动 |
| 3 | `backend/.../mapper/UserMapper.java` | 加 `existsByEmail()` |
| 4 | `backend/.../service/VerificationService.java` | 加 `sendEmailChangeCode()` / `verifyEmailChangeCode()` |
| 5 | `backend/.../service/impl/VerificationServiceImpl.java` | 实现新方法，注册 key 不动 |
| 6 | `backend/.../service/AuthService.java` | 无需改动（register 签名不变） |
| 7 | `backend/.../service/impl/AuthServiceImpl.java` | register 加邮箱唯一性检查 |
| 8 | `backend/.../controller/UserController.java` | 新增两个端点 |
| 9 | `backend/.../dto/UpdateUserDTO.java` | 移除 email 字段 |

### 前端

| # | 文件 | 操作 |
|---|------|------|
| 10 | `frontend/client/src/types/index.ts` | 加新 Request 类型 |
| 11 | `frontend/client/src/api/auth.ts` | 加两个 API 方法 |
| 12 | `frontend/client/src/stores/auth.ts` | 加两个 action |
| 13 | `frontend/client/src/pages/Profile.vue` | 加验证码发送/输入 UI + 保存逻辑 |

---

## 6. 不作改动

- AuthController — 不动
- Register.vue / Login.vue / VerifyEmail.vue — 不动，注册验证流程不受影响
- 注册验证的 API 端点路径 — 不动
- `UserConverter` — 不动
- `SecurityConfig` — 不动（`/api/user/**` 已需要认证，新端点共用该前缀）
