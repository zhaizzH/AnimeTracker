---
name: 登录流程优化设计
description: 认证服务代码质量改进——Logout 改 POST、删除死代码、抽取 token 生成逻辑
metadata:
  type: spec
---

# 登录流程优化设计

## 背景

代码审查发现认证模块三个明确问题：

1. **Logout 使用 GET 方法** — 改变服务端状态（删除 Redis 白名单）但 GET 是非幂等方法，浏览器预加载可能触发意外登出
2. **AuthService.generateToken() 死代码** — 完全委托给 JwtTokenProvider，无任何调用者
3. **verifyEmail() BCrypt 自比较短路** — 将数据库中的 BCrypt hash 当密码传给 login()，依赖 matches(hash, hash) 永远返回 true，阅读代码时极其困惑

## 改动方案

范围限定在认证模块，不涉及安全架构变更（Token 刷新、限流等后续按需添加）。

### 1. Logout GET → POST

- **后端:** `AuthController.java` — `@GetMapping` → `@PostMapping`
- **前端:** `auth.ts` — `http.get` → `http.post`

### 2. 删除 generateToken() 死代码

- **AuthService.java** — 删除接口方法声明
- **AuthServiceImpl.java** — 删除实现方法

### 3. 抽取 token 生成逻辑

- **AuthServiceImpl.java** — 新增私有方法 `generateLoginVO(User user)`
- `login()` 和 `verifyEmail()` 都调用 `generateLoginVO()` 生成 token 和 LoginVO
- `verifyEmail()` 不再伪造密码调用 `login()`

## 影响范围

| 文件 | 改动 |
|------|------|
| backend/.../controller/AuthController.java | 1 行（注解） |
| backend/.../service/AuthService.java | 删 1 行 |
| backend/.../service/impl/AuthServiceImpl.java | ~15 行重构 |
| frontend/client/src/api/auth.ts | 1 行（method 名） |
