# 邮箱验证页显示优化 + Email 传递方式变更

> 优化 VerifyEmail 页面顶部导航显示问题，将 email 传递方式从 URL query 改为 sessionStorage。

---

## 1. 改动概述

两个改动：
1. **移除验证页上的"登录/注册"tab 导航** — 该页面应专注于验证操作，不需要切换到登录/注册
2. **Email 传递方式从 URL query 改为 sessionStorage** — 不把 email 暴露在浏览器地址栏中

---

## 2. 改动详情

### 2.1 Email 传递流程

```
注册成功 (Register.vue)
  → email 存入 sessionStorage
  → router.push({ name: 'VerifyEmail' })
  → VerifyEmail.vue 从 sessionStorage 读取 email
  → 立即 sessionStorage.removeItem('verifyEmail')
  → 无 email 则 router.replace('/login')

登录 403 (Login.vue)  
  → email 存入 sessionStorage
  → router.push({ name: 'VerifyEmail' })
  → 同上
```

### 2.2 VerifyEmail.vue 变更

| 项目 | 改前 | 改后 |
|------|------|------|
| 获取 email | `route.query.email` | `sessionStorage.getItem('verifyEmail')` |
| 无 email 处理 | `router.replace('/login')` | 同上 |
| 页面顶栏 | auth-tabs（登录/注册切换） | 移除 |
| 标题 | 保留"验证邮箱" | 不变 |
| email 展示 | 保留 | 不变（readonly input + 说明文字） |

### 2.3 涉及文件

| 文件 | 改动 |
|------|------|
| `frontend/client/src/pages/VerifyEmail.vue` | 移除 auth-tabs，改用 sessionStorage 获取 email |
| `frontend/client/src/pages/Register.vue` | 跳转前将 email 写入 sessionStorage |
| `frontend/client/src/pages/Login.vue` | 403 跳转前将 email 写入 sessionStorage |

### 2.4 sessionStorage key

统一使用 key `verifyEmail`。

---

## 3. 不作改动

- 后端完全不动
- 路由配置不动（`/verify-email` 继续保留）
- API 调用方式不动（已是请求体传参）
- 验证逻辑、重发逻辑、错误提示不动
