# 验证页优化 Implementation Plan
# 使用中文 commit message
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复验证页显示问题（移除 auth-tabs）+ 将 email 传递方式从 URL query 改为 sessionStorage

**Architecture:** 纯前端改动，涉及 3 个 Vue 组件。不做新依赖、不改后端、不改路由。

**Tech Stack:** Vue 3 + TypeScript + Vue Router

**File Structure**
- `frontend/client/src/pages/VerifyEmail.vue` — 主改动页
- `frontend/client/src/pages/Register.vue` — 跳转前写入 sessionStorage
- `frontend/client/src/pages/Login.vue` — 403 跳转前写入 sessionStorage

---

### Task 1: VerifyEmail.vue — 移除 auth-tabs + 改用 sessionStorage

**Files:**
- Modify: `frontend/client/src/pages/VerifyEmail.vue`

**Interfaces:**
- Consumes: sessionStorage key `verifyEmail`
- Produces: 清理后的验证页

- [ ] **Step 1: 修改 VerifyEmail.vue 的 script 部分**

改动点：
1. 移除 `import { useRoute } from 'vue-router'` 和 `const route = useRoute()`
2. 从 `sessionStorage.getItem('verifyEmail')` 获取 email，而非 `route.query.email`
3. 获取后立即 `sessionStorage.removeItem('verifyEmail')`
4. 无 email 时 `router.replace('/login')`

修改第 1-8 行和第 11-21 行：

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Mail } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref(sessionStorage.getItem('verifyEmail') || '')
sessionStorage.removeItem('verifyEmail')

const code = ref('')
const error = ref('')
const loading = ref(false)
const resending = ref(false)
const cooldown = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

if (!email.value) {
  router.replace('/login')
}
```

- [ ] **Step 2: 移除 template 中的 auth-tabs 区块**

删除第 59-63 行（auth-tabs 的整个 `div` 块）：

```diff
-      <div class="auth-tabs">
-        <router-link to="/login" class="auth-tab">登录</router-link>
-        <router-link to="/register" class="auth-tab">注册</router-link>
-      </div>
```

同时调整标题 `mt-6` 间距。将验证页模板中 `h1` 的 `class` 从 `"text-[24px] font-bold mt-6 mb-6"` 改为 `"text-[24px] font-bold mb-6"`，移除 `mt-6`（因为顶栏没了，不需要顶部间距）。

- [ ] **Step 3: 移除 style 中的 auth-tabs 相关样式**

删除第 120-150 行（`.auth-tabs`、`.auth-tab`、`.auth-tab--active` 样式）。

- [ ] **Step 4: 验证改动**

检查 VerifyEmail.vue 没有引用 `route`、没有 `auth-tabs` 相关代码、`email` 来自 `sessionStorage`。

```bash
grep -n 'route\|auth-tab\|auth-tabs' frontend/client/src/pages/VerifyEmail.vue
```
Expected: no matches (除了 `router` 自身)。

- [ ] **Step 5: Commit**

```bash
git add frontend/client/src/pages/VerifyEmail.vue
git commit -m "fix: 移除 VerifyEmail 页 auth-tabs，email 从 URL query 改为 sessionStorage"
```

---

### Task 2: Register.vue — 跳转前写入 sessionStorage

**Files:**
- Modify: `frontend/client/src/pages/Register.vue`

**Interfaces:**
- Consumes: 注册成功后获取 email
- Produces: sessionStorage key `verifyEmail`

- [ ] **Step 1: 注册成功后写入 sessionStorage**

在 Register.vue 第 29 行 `router.push` 前加一行：

```diff
    await authStore.register({ username: username.value.trim(), password: password.value, email: email.value.trim() })
+   sessionStorage.setItem('verifyEmail', email.value.trim())
    router.push({ name: 'VerifyEmail', query: { email: email.value.trim() } })
```

还将 `router.push` 的 query 移除，因为不再需要 URL 传参：

```diff
-   router.push({ name: 'VerifyEmail', query: { email: email.value.trim() } })
+   router.push({ name: 'VerifyEmail' })
```

- [ ] **Step 2: Commit**

```bash
git add frontend/client/src/pages/Register.vue
git commit -m "fix: 注册成功后 email 写入 sessionStorage 再跳转验证页"
```

---

### Task 3: Login.vue — 403 跳转前写入 sessionStorage

**Files:**
- Modify: `frontend/client/src/pages/Login.vue`

**Interfaces:**
- Consumes: 登录 403 时从响应中获取 email
- Produces: sessionStorage key `verifyEmail`

- [ ] **Step 1: 403 跳转前写入 sessionStorage**

在 Login.vue 第 31 行 `router.push` 前加一行：

```diff
    if (data?.code === 403 && data?.data?.email) {
+     sessionStorage.setItem('verifyEmail', data.data.email)
-     router.push({ name: 'VerifyEmail', query: { email: data.data.email } })
+     router.push({ name: 'VerifyEmail' })
      return
    }
```

- [ ] **Step 2: Commit**

```bash
git add frontend/client/src/pages/Login.vue
git commit -m "fix: 登录 403 跳转前 email 写入 sessionStorage 再跳转验证页"
```
