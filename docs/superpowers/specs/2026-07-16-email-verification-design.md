# 邮箱验证（Resend）设计方案

> 为 AnimeTracker 用户注册流程增加邮箱验证，使用 Resend.com 发送验证码。

---

## 1. 概述

### 1.1 目标

用户注册时通过邮箱验证，确保邮箱地址真实可用，为后续密码找回、通知推送等功能奠定基础。

### 1.2 注册流程

```
用户填写表单（用户名 + 邮箱 + 密码）
        │
        ▼
POST /api/user/auth/register
   → 校验参数（邮箱改为必填）
   → 检查用户名唯一性
   → 创建用户（email_verified = false）
   → 生成6位字母数字验证码，存入 Redis（key: auth:email:<邮箱>, TTL: 5min）
   → 通过 Resend 发送验证码邮件
   → 返回 { message: "验证码已发送" }
        │
        ▼
用户在注册页输入收到的验证码
        │
        ▼
POST /api/user/auth/verify-email
   → 校验 email + code
   → 标记 user.email_verified = true
   → 生成 JWT
   → 返回 { token, user }
        │
        ▼
前端保存 Token，跳转首页
```

---

## 2. 改动范围

### 2.1 数据库

**User 表新增字段：**

```sql
ALTER TABLE `user`
  ADD COLUMN `email_verified` tinyint(1) NOT NULL DEFAULT 0 COMMENT '邮箱是否已验证';
```

同步更新 `docs/db-schema.sql`。

### 2.2 后端

| 文件 | 改动 |
|------|------|
| `user/pom.xml` | 加 Resend Java SDK 依赖 |
| `application.yml` | 加 `resend.api-key` 配置 |
| `RegisterDTO.java` | email 字段加 `@NotBlank`（改为必填） |
| `User.java` | 加 `emailVerified` 字段 |
| `ErrorType.java` | 加 `EMAIL_NOT_VERIFIED` 错误码 |
| `AuthService.java` | 加 `verifyEmail(email, code)` 方法 |
| `AuthServiceImpl.java` | `register()` 改为创建用户→发验证码（不登录）；实现 `verifyEmail()` |
| `AuthController.java` | 加 `POST /verify-email` 接口 |
| `VerificationService.java` | **新建** — 验证码接口 |
| `VerificationServiceImpl.java` | **新建** — 生成/存储/发送/校验实现 |

#### VerificationService 接口

```java
public interface VerificationService {
    /** 生成验证码并发送邮件 */
    void sendVerificationCode(String email);

    /** 校验验证码，成功则标记邮箱已验证 */
    void verifyEmail(String email, String code);
}
```

#### 验证码参数

- **格式**: 6位字母数字混合（如 `A3fK8x`）
- **有效期**: 5分钟
- **存储**: Redis, key=`auth:email:<email>`, value=验证码, TTL=5min
- **校验后**: 从 Redis 删除 key，更新 DB 中 `user.email_verified = true`

#### Resend 邮件模板

简单纯文本邮件，内容示例：

```
主题: [AnimeTracker] 邮箱验证码

你的验证码是：A3fK8x

此验证码5分钟内有效，请勿泄露给他人。
```

### 2.3 前端

| 文件 | 改动 |
|------|------|
| `Register.vue` | 注册流程改为两步：第一屏提交注册 → 第二屏输入验证码 |
| `auth.ts` | 新增 `verifyEmail(email, code)` action |
| `types.ts` (或对应类型文件) | 新增 `VerifyEmailRequest` 类型 |

#### Register.vue 状态机

```
初始表单（用户名/邮箱/密码）
  │ 点击注册 → loading → 调 POST /register
  │ 成功 → 切换到验证码输入视图
  ▼
验证码视图（显示 "验证码已发送到 xxx@email.com" + 6位输入框）
  │ 点击验证 → loading → 调 POST /verify-email
  │ 成功 → 保存 token → 跳转首页
  ▼
完成
```

---

## 3. 配置

```yaml
# application.yml
resend:
  api-key: ${resend.api-key}
```

---

## 4. 错误处理

| 场景 | HTTP | message |
|------|------|---------|
| 邮箱已注册（同用户名不同邮箱） | 200 | 走正常注册流程，发验证码 |
| 验证码过期 | 400 | 验证码已过期，请重新发送 |
| 验证码错误 | 400 | 验证码不正确 |
| 重复验证 | 200 | 邮箱已验证，直接登录 |
| Resend 发送失败 | 500 | 验证码发送失败，请稍后重试 |

---

## 5. 涉及文件总清单

| # | 文件 | 操作 |
|---|------|------|
| 1 | `docs/db-schema.sql` | 修改 |
| 2 | `backend/business/user/pom.xml` | 修改 |
| 3 | `backend/business/app/src/main/resources/application.yml` | 修改 |
| 4 | `backend/business/pojo/src/main/java/.../dto/RegisterDTO.java` | 修改 |
| 5 | `backend/business/pojo/src/main/java/.../entity/User.java` | 修改 |
| 6 | `backend/business/common/src/main/java/.../ErrorType.java` | 修改 |
| 7 | `backend/business/user/src/main/java/.../service/AuthService.java` | 修改 |
| 8 | `backend/business/user/src/main/java/.../service/impl/AuthServiceImpl.java` | 修改 |
| 9 | `backend/business/user/src/main/java/.../controller/AuthController.java` | 修改 |
| 10 | `backend/business/user/src/main/java/.../service/VerificationService.java` | 新建 |
| 11 | `backend/business/user/src/main/java/.../service/impl/VerificationServiceImpl.java` | 新建 |
| 12 | `frontend/client/src/pages/Register.vue` | 修改 |
| 13 | `frontend/client/src/stores/auth.ts` | 修改 |
| 14 | `frontend/client/src/types/...` | 修改 |

---

## 6. 后续可扩展

- **密码找回**: 复用 VerificationService，发送重置密码链接
- **邮箱变更验证**: 修改邮箱时发验证码
- **未验证用户提醒**: 登录时检测 `email_verified=false`，提示验证
