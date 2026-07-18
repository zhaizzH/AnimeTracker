# 未验证邮箱用户登录阻断设计方案

> 用户注册后若未验证邮箱，再次登录时提示验证，而非正常使用系统。

---

## 1. 概述

### 1.1 目标

当前 `POST /api/user/auth/login` 只校验用户名+密码，不检查 `email_verified` 状态。未验证邮箱的用户仍可正常登录使用系统。本次改动使其被阻断并引导完成邮箱验证。

### 1.2 流程

```
登录 POST /api/user/auth/login
  → 校验用户名+密码（通过）
  → 检查 email_verified
  → false → 返回 403 + 邮箱地址
           ↓
前端捕获 403 → 跳转 /verify-email?email=xxx
           ↓
用户输入验证码 → POST /api/user/auth/verify-email
           ↓
验证通过 → 自动登录 → 跳转首页

注册 POST /api/user/auth/register
  → 创建用户 → 发送验证码 → 返回成功
           ↓
前端跳转 /verify-email?email=xxx（统一验证页）
           ↓
用户输入验证码 → POST /api/user/auth/verify-email
           ↓
验证通过 → 自动登录 → 跳转首页
```

---

## 2. 改动范围

### 2.1 后端

| 文件 | 改动 |
|------|------|
| `BizException.java` | 加 `Object data` 字段 + 带 data 的构造器 |
| `GlobalExceptionHandler.java` | `handleBizException` 返回 `Result.error(code, message, e.getData())` |
| `AuthServiceImpl.java` | `login()` 在密码校验后增加 `emailVerified` 检查 |

#### AuthServiceImpl.login() 改动

```java
if (Boolean.FALSE.equals(user.getEmailVerified())) {
    throw new BizException(ErrorType.EMAIL_NOT_VERIFIED,
        "邮箱未验证，请先验证邮箱",
        Map.of("email", user.getEmail()));
}
```

#### 错误响应示例

```json
// 登录未验证用户时
HTTP 403
{
  "code": 403,
  "message": "邮箱未验证，请先验证邮箱",
  "data": {
    "email": "user@example.com"
  }
}
```

### 2.2 前端

| 文件 | 操作 | 改动 |
|------|------|------|
| `Login.vue` | 修改 | 捕获 403 EMAIL_NOT_VERIFIED，跳转 `/verify-email?email=xxx` |
| `Register.vue` | 修改 | 注册成功后跳转 `/verify-email?email=xxx`，移除内联验证码 UI |
| `VerifyEmail.vue` | **新建** | 统一的邮箱验证页面 |
| `router/index.ts` | 修改 | 新增 `/verify-email` 路由 |

#### Login.vue 改动

```ts
// handleLogin catch 中
const data = e?.response?.data
if (data?.code === 403 && data?.data?.email) {
  router.push({ name: 'VerifyEmail', query: { email: data.data.email } })
  return
}
```

#### Register.vue 改动

移除 `registered`、`code`、`handleVerify`、`handleResend`、`cooldown` 等状态和逻辑。
`handleRegister` 成功后改为：

```ts
await authStore.register(...)
router.push({ name: 'VerifyEmail', query: { email: email.value.trim() } })
```

#### VerifyEmail.vue 设计

- 邮箱地址（只读显示）
- 6 位验证码输入框
- 「完成验证」按钮 → `authStore.verifyEmail({ email, code })` → 成功跳转首页
- 「重新发送」按钮 + 60s 倒计时
- 「返回登录」链接
- 路由: `/verify-email`, 放在 AuthLayout 下，`meta: { guest: true }`

---

## 3. 错误处理

| 场景 | 行为 |
|------|------|
| 登录时邮箱已验证 | 正常登录，无影响 |
| 登录时邮箱未验证 | 返回 403 + 邮箱，前端跳转验证页 |
| 注册成功后跳转验证页 | 和现有注册流程一致 |
| 验证码过期/错误 | 验证页显示错误提示，可重新发送 |
| 重新发送验证码 | 复用已有 `POST /api/user/auth/resend-code` |

---

## 4. 涉及文件总清单

| # | 文件 | 操作 |
|---|------|------|
| 1 | `backend/business/common/src/main/java/.../exception/BizException.java` | 修改 |
| 2 | `backend/business/common/src/main/java/.../exception/GlobalExceptionHandler.java` | 修改 |
| 3 | `backend/business/user/src/main/java/.../service/impl/AuthServiceImpl.java` | 修改 |
| 4 | `frontend/client/src/pages/Login.vue` | 修改 |
| 5 | `frontend/client/src/pages/Register.vue` | 修改 |
| 6 | `frontend/client/src/pages/VerifyEmail.vue` | **新建** |
| 7 | `frontend/client/src/router/index.ts` | 修改 |

---

## 5. 不做的事

- 不改动数据库结构（`email_verified` 字段已存在）
- 不改动 `VerificationService` / `VerificationServiceImpl`
- 不改动 `ErrorType` 枚举（`EMAIL_NOT_VERIFIED` 已存在）
- 不改动 `authStore` / `authApi` / 类型定义（`verifyEmail` 等方法已存在）
- 不改动刷新 token、注销等其他认证流程
