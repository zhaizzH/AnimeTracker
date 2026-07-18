# 未验证邮箱用户登录阻断 — 实施计划
# 使用中文commit message
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用户注册后未验证邮箱时，登录被阻断并引导至统一验证页完成验证

**Architecture:**
- 后端：`login()` 增加 `emailVerified` 检查，不通过时抛出带邮箱的 `BizException`，`GlobalExceptionHandler` 将邮箱填入响应 `data`
- 前端：新建 `VerifyEmail.vue` 作为统一验证页，Login.vue 和 Register.vue 均跳转至此页

**Tech Stack:** Java 21 + Spring Boot + Vue 3 + Pinia + Vue Router

## Global Constraints

- 不改动数据库结构（`email_verified` 字段已存在）
- 不改动 `VerificationService` / `VerificationServiceImpl`
- 不改动 `ErrorType` 枚举（`EMAIL_NOT_VERIFIED` 已存在）
- 不改动 `authStore` / `authApi` / 类型定义
- 不改动刷新 token、注销等其他认证流程

---

### Task 1: 后端 — BizException 增加 data 字段 + GlobalExceptionHandler 适配

**Files:**
- Modify: `backend/business/common/src/main/java/top/zhaizz/common/exception/BizException.java`
- Modify: `backend/business/common/src/main/java/top/zhaizz/common/exception/GlobalExceptionHandler.java`

**Interfaces:**
- Produces: `BizException` 新增 `getData()` 方法和带 `Object data` 的构造器；`GlobalExceptionHandler.handleBizException` 返回 `Result<Object>`，将 `e.getData()` 传入 `Result.error()`

- [ ] **Step 1: BizException 增加 data 字段**

```java
// BizException.java — 在 private final int code; 之后加一行
@Getter
public class BizException extends RuntimeException {

    private final int code;
    private final Object data;  // 新增

    public BizException(ErrorType errorType) {
        super(errorType.getMessage());
        this.code = errorType.getCode();
        this.data = null;
    }

    public BizException(ErrorType errorType, String message) {
        super(message);
        this.code = errorType.getCode();
        this.data = null;
    }

    // 新增构造器
    public BizException(ErrorType errorType, String message, Object data) {
        super(message);
        this.code = errorType.getCode();
        this.data = data;
    }

    public BizException(int code, String message) {
        super(message);
        this.code = code;
        this.data = null;
    }
}
```

- [ ] **Step 2: GlobalExceptionHandler 返回 data**

```java
// GlobalExceptionHandler.java — 修改 handleBizException 方法
@ExceptionHandler(BizException.class)
public Result<Object> handleBizException(BizException e) {
    log.warn("业务异常: code={}, message={}", e.getCode(), e.getMessage());
    return Result.error(e.getCode(), e.getMessage(), e.getData());
}
```

- [ ] **Step 3: 编译验证**

```bash
cd backend
mvn compile -pl business/common -am -q
```

- [ ] **Step 4: Commit**

```bash
git add backend/business/common/src/main/java/top/zhaizz/common/exception/BizException.java backend/business/common/src/main/java/top/zhaizz/common/exception/GlobalExceptionHandler.java
git commit -m "feat: BizException 增加 data 字段, GlobalExceptionHandler 返回 data"
```

---

### Task 2: 后端 — AuthServiceImpl.login() 检查邮箱验证状态

**Files:**
- Modify: `backend/business/user/src/main/java/top/zhaizz/user/service/impl/AuthServiceImpl.java`

**Interfaces:**
- Consumes: `BizException(ErrorType, String, Object)` 构造器，`ErrorType.EMAIL_NOT_VERIFIED`
- Produces: `login()` 在未验证时抛出 `BizException(EMAIL_NOT_VERIFIED, ...)` 携带 `Map.of("email", email)`

- [ ] **Step 1: login() 增加 emailVerified 检查**

```java
// AuthServiceImpl.java — login() 方法中，在密码校验之后、generateLoginVO 之前插入
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

        // 2. 检查邮箱是否已验证
        if (Boolean.FALSE.equals(user.getEmailVerified())) {
            throw new BizException(ErrorType.EMAIL_NOT_VERIFIED,
                    "邮箱未验证，请先验证邮箱",
                    Map.of("email", user.getEmail()));
        }

        return generateLoginVO(user);
    }
```

- [ ] **Step 2: 编译验证**

```bash
cd backend
mvn compile -pl business/user -am -q
```

Expected: BUILD SUCCESS

- [ ] **Step 3: Commit**

```bash
git add backend/business/user/src/main/java/top/zhaizz/user/service/impl/AuthServiceImpl.java
git commit -m "feat: login 时检查 emailVerified, 未验证时返回 403 + 邮箱"
```

---

### Task 3: 前端 — 新建 VerifyEmail.vue 统一验证页面

**Files:**
- Create: `frontend/client/src/pages/VerifyEmail.vue`

**Interfaces:**
- Consumes: `authStore.verifyEmail({ email, code })` / `authStore.resendCode(email)` / `useRouter` / `useRoute`
- Produces: `<template>` with verification code UI, exports default Vue component named `VerifyEmail`

- [ ] **Step 1: 创建 VerifyEmail.vue**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Mail } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const email = ref(route.query.email as string || '')
const code = ref('')
const error = ref('')
const loading = ref(false)
const resending = ref(false)
const cooldown = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

if (!email.value) {
  router.replace('/login')
}

function startCooldown() {
  cooldown.value = 60
  timer = setInterval(() => {
    cooldown.value--
    if (cooldown.value <= 0) { if (timer) clearInterval(timer); timer = null }
  }, 1000)
}

async function handleVerify() {
  error.value = ''
  if (!code.value.trim() || code.value.length !== 6) { error.value = '请输入6位验证码'; return }
  loading.value = true
  try {
    await authStore.verifyEmail({ email: email.value, code: code.value.trim() })
    router.push('/')
  } catch (e: any) {
    error.value = e?.response?.data?.message || '验证失败，请重试'
  } finally { loading.value = false }
}

async function handleResend() {
  if (cooldown.value > 0) return
  error.value = ''
  resending.value = true
  try {
    await authStore.resendCode(email.value)
    startCooldown()
  } catch (e: any) {
    error.value = e?.response?.data?.message || '发送失败，请稍后重试'
  } finally { resending.value = false }
}
</script>

<template>
  <div class="flex min-h-[calc(100vh-64px)] items-center justify-center px-4">
    <div class="w-full max-w-md">
      <div class="auth-tabs">
        <router-link to="/login" class="auth-tab">登录</router-link>
        <router-link to="/register" class="auth-tab">注册</router-link>
      </div>

      <h1 class="text-[24px] font-bold mt-6 mb-6" style="color: var(--color-text)">
        验证邮箱
      </h1>

      <Transition name="fade">
        <div v-if="error"
          class="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-500 text-center">
          {{ error }}
        </div>
      </Transition>

      <div class="space-y-4">
        <div class="relative">
          <Mail class="absolute left-3.5 top-1/2 -translate-y-1/2 h-[18px] w-[18px]"
            style="color: var(--color-text-secondary)" />
          <input :value="email" type="email" readonly
            class="auth-input opacity-60 cursor-not-allowed" />
        </div>

        <p class="text-sm text-center" style="color: var(--color-text-secondary)">
          验证码已发送到 <strong class="text-primary-500">{{ email }}</strong>
        </p>

        <input v-model="code" type="text" maxlength="6" placeholder="输入6位验证码"
          class="auth-input text-center text-xl tracking-[0.5em] font-mono" style="padding-left:12px"
          autocomplete="one-time-code" />

        <button class="auth-submit" :disabled="loading" @click="handleVerify">
          <svg v-if="loading" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg"
            fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          {{ loading ? '验证中...' : '完成验证' }}
        </button>

        <div class="text-center text-sm" style="color: var(--color-text-secondary)">
          未收到验证码？
          <button
            class="text-primary-500 hover:text-primary-600 font-medium bg-transparent border-none cursor-pointer disabled:opacity-50"
            :disabled="cooldown > 0 || resending" @click="handleResend">
            {{ resending ? '发送中...' : cooldown > 0 ? `${cooldown}s` : '重新发送' }}
          </button>
        </div>

        <div class="text-center">
          <router-link to="/login" class="text-sm" style="color: var(--color-text-secondary)">
            返回登录
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  padding: 3px;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--color-border);
  box-shadow: inset 0 0 0 1px rgba(241, 121, 146, 0.15);
}
:root:not(.dark) .auth-tabs {
  background: rgba(0, 0, 0, 0.05);
}
.auth-tab {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 38px;
  font-size: 14px;
  font-weight: 400;
  border-radius: 10px;
  text-decoration: none;
  transition: background 0.2s, color 0.2s;
  color: var(--color-text-secondary);
  background: transparent;
}
.auth-tab--active {
  background: var(--color-card);
  color: var(--color-text);
  font-weight: 500;
}

.auth-input {
  width: 100%;
  height: 45px;
  padding: 0 12px 0 41px;
  font-size: 14px;
  border-radius: 12px;
  border: 1px solid var(--color-input-border);
  background: var(--color-input-bg);
  color: var(--color-text);
  outline: none;
  transition: border-color 0.2s;
}
.auth-input::placeholder {
  color: var(--color-text-secondary);
  opacity: 0.6;
}
.auth-input:focus {
  border-color: var(--color-primary);
}

.auth-submit {
  width: 100%;
  height: 45px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 400;
  border-radius: 12px;
  border: 1px solid var(--color-primary);
  cursor: pointer;
  transition: opacity 0.2s;
  background: var(--color-primary);
  color: #fff;
}
.auth-submit:hover {
  opacity: 0.9;
}
.auth-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

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
git add frontend/client/src/pages/VerifyEmail.vue
git commit -m "feat: 新建统一邮箱验证页 VerifyEmail.vue"
```

---

### Task 4: 前端 — 新增路由 + Login.vue 跳转逻辑

**Files:**
- Modify: `frontend/client/src/router/index.ts`
- Modify: `frontend/client/src/pages/Login.vue`

**Interfaces:**
- Consumes: `VerifyEmail.vue` component
- Produces: Route `/verify-email` with name `VerifyEmail`, `meta: { guest: true }`

- [ ] **Step 1: 路由新增 /verify-email**

```ts
// router/index.ts — 在 AuthLayout children 中 register 路由之后添加
      { path: 'login', name: 'Login', component: () => import('@/pages/Login.vue'), meta: { guest: true } },
      { path: 'register', name: 'Register', component: () => import('@/pages/Register.vue'), meta: { guest: true } },
      { path: 'verify-email', name: 'VerifyEmail', component: () => import('@/pages/VerifyEmail.vue'), meta: { guest: true } },
```

- [ ] **Step 2: Login.vue 捕获 403 跳转**

```ts
// Login.vue — 修改 handleLogin 的 catch 分支
  try {
    await authStore.login({ username: username.value.trim(), password: password.value })
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (e: any) {
    const data = e?.response?.data
    if (data?.code === 403 && data?.data?.email) {
      router.push({ name: 'VerifyEmail', query: { email: data.data.email } })
      return
    }
    error.value = data?.message || '登录失败，请检查用户名和密码'
  }
```

- [ ] **Step 3: Commit**

```bash
git add frontend/client/src/router/index.ts frontend/client/src/pages/Login.vue
git commit -m "feat: 新增 /verify-email 路由; Login 捕获 403 跳转验证页"
```

---

### Task 5: 前端 — 简化 Register.vue（移除内联验证码 UI）

**Files:**
- Modify: `frontend/client/src/pages/Register.vue`

**Interfaces:**
- Consumes: `authStore.register()` / `useRouter` / route `VerifyEmail`
- Produces: Simplified Register.vue — 注册成功后跳转 `/verify-email?email=xxx`

- [ ] **Step 1: 移除验证码相关状态和 import，修改 handleRegister**

Register.vue 改前 Script 区涉及的行（删除/修改）：

删除的内容（整个移除）：
- `const code = ref('')`
- `const registered = ref(false)`
- `const resending = ref(false)`
- `const cooldown = ref(0)`
- `let timer: ReturnType<typeof setInterval> | null = null`
- `function startCooldown() { ... }` 整个函数
- `async function handleVerify() { ... }` 整个函数
- `async function handleResend() { ... }` 整个函数

修改 `handleRegister` 成功后：
```ts
  try {
    await authStore.register({ username: username.value.trim(), password: password.value, email: email.value.trim() })
    router.push({ name: 'VerifyEmail', query: { email: email.value.trim() } })
  }
```

删除 Template 区验证码 UI（从 `<Transition name="fade">` 到 `</Transition>` 的 verification 块，整块删除），以及 `v-if="!registered"` 条件保留表单。

- [ ] **Step 2: 编译验证**

```bash
cd frontend/client && npx vue-tsc --noEmit --skipLibCheck 2>&1 | head -20
```

Expected: No type errors (exit 0)

- [ ] **Step 3: Commit**

```bash
git add frontend/client/src/pages/Register.vue
git commit -m "refactor: Register 注册成功后跳转验证页, 移除内联验证码 UI"
```

---

## 计划自检

- **Spec coverage:** ✅ 所有改动点都已覆盖（BizException → Task 1, GlobalExceptionHandler → Task 1, AuthServiceImpl → Task 2, VerifyEmail → Task 3, Router → Task 4, Login → Task 4, Register → Task 5）
- **Placeholder scan:** ✅ 所有步骤包含完整代码
- **Type consistency:** ✅ 构造器 `BizException(ErrorType, String, Object)` 在 Task 1 定义，Task 2 使用；路由名 `VerifyEmail` 在 Task 4 定义，Task 4 和 Task 5 使用
- **Scope:** ✅ 只覆盖 spec 中定义的范围，不涉及无关改动
