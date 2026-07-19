# 邮箱修改验证 + 邮箱唯一性 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 Profile 页邮箱修改添加验证流程，补充注册时的邮箱唯一性检查和 DB 唯一约束。

**Architecture:** 后端 VerificationService 新增两个方法（发码/校验），UserController 新增两个端点，注册流程加邮箱唯一性检查。前端 Profile.vue 内嵌验证码发送/输入 UI，保存时先验证再更新。Redis 用独立 key 前缀 `auth:email-change:` 隔离邮箱修改验证码。

**Tech Stack:** Spring Boot + MyBatis-Plus + Redis + Resend (后端), Vue 3 + Pinia (前端)

**Spec:** `docs/superpowers/specs/2026-07-19-email-change-verification-design.md`

## Global Constraints

- Redis key 注册验证保持 `auth:email:<email>` 不变，邮箱修改用 `auth:email-change:<userId>:<email>`
- `sendVerificationCode(email)` 签名不变
- `verifyEmailChangeCode` 必须用 `@Transactional`，旧邮箱通知失败不回滚 email 更新
- 旧邮箱为 null 时跳过通知
- `UpdateUserDTO` 移除 email 字段，邮箱改由验证端点处理
- 注册验证流程不受影响（AuthController、VerifyEmail.vue 等不动）

---

### Task 1: 数据库加唯一索引 + UserMapper 加 existsByEmail

**Files:**
- Modify: `docs/db-schema.sql:130`
- Modify: `backend/business/user/src/main/java/top/zhaizz/user/mapper/UserMapper.java`

**Interfaces:**
- Consumes: 无
- Produces: `UserMapper.existsByEmail(email)` — 供 AuthServiceImpl.register() 使用

- [ ] **Step 1: db-schema.sql 加 email 唯一索引**

在 `uk_username` 行后插入：

```sql
UNIQUE INDEX `uk_email`(`email` ASC) USING BTREE,
```

- [ ] **Step 2: UserMapper 加 existsByEmail default 方法**

```java
default boolean existsByEmail(String email) {
    return selectCount(new LambdaQueryWrapper<User>()
            .eq(User::getEmail, email)) > 0;
}
```

- [ ] **Step 3: Commit**

```bash
git add docs/db-schema.sql backend/business/user/src/main/java/top/zhaizz/user/mapper/UserMapper.java
git commit -m "feat: email 加唯一索引 + existsByEmail 方法"
```

---

### Task 2: VerificationService 新增邮箱修改验证方法

**Files:**
- Modify: `backend/business/user/src/main/java/top/zhaizz/user/service/VerificationService.java`
- Modify: `backend/business/user/src/main/java/top/zhaizz/user/service/impl/VerificationServiceImpl.java`

**Interfaces:**
- Consumes: 无（依赖已有的 UserMapper、RedisClient、Resend）
- Produces:
  - `VerificationService.sendEmailChangeCode(Long userId, String newEmail)` — 发码
  - `VerificationService.verifyEmailChangeCode(Long userId, String newEmail, String code)` — 校验 + 更新邮箱

- [ ] **Step 1: VerificationService 接口加两个方法**

```java
/**
 * 发送邮箱修改验证码（检查新邮箱唯一性）
 *
 * @param userId   当前用户 ID
 * @param newEmail 新邮箱
 */
void sendEmailChangeCode(Long userId, String newEmail);

/**
 * 校验邮箱修改验证码
 * <p>校验成功后更新 email、email_verified=true，发送通知到旧邮箱</p>
 *
 * @param userId   当前用户 ID
 * @param newEmail 新邮箱
 * @param code     用户输入的验证码
 */
void verifyEmailChangeCode(Long userId, String newEmail, String code);
```

- [ ] **Step 2: VerificationServiceImpl 实现 sendEmailChangeCode**

```java
private static final String REDIS_EMAIL_CHANGE_PREFIX = "auth:email-change:";

@Override
public void sendEmailChangeCode(Long userId, String newEmail) {
    // 1. 检查新邮箱唯一性
    if (userMapper.existsByEmail(newEmail)) {
        throw new BizException(ErrorType.CONFLICT, "该邮箱已被其他账号使用");
    }

    // 2. 生成验证码（复用相同生成逻辑）
    StringBuilder code = new StringBuilder(CODE_LENGTH);
    for (int i = 0; i < CODE_LENGTH; i++) {
        code.append(ALPHANUMERIC.charAt(RANDOM.nextInt(ALPHANUMERIC.length())));
    }

    // 3. 存入 Redis（不同 key 前缀）
    redisClient.set(REDIS_EMAIL_CHANGE_PREFIX + userId + ":" + newEmail, code.toString(), CODE_TTL_MINUTES, TimeUnit.MINUTES);

    // 4. 通过 Resend 发送邮件
    Resend resend = new Resend(resendApiKey);
    CreateEmailOptions params = CreateEmailOptions.builder()
            .from("admin@zhaizz.top")
            .to(newEmail)
            .subject("[AnimeTracker] 邮箱修改验证码")
            .text("你正在修改邮箱绑定，验证码是：" + code + "\n\n此验证码5分钟内有效，请勿泄露给他人。")
            .build();

    try {
        resend.emails().send(params);
    } catch (ResendException e) {
        redisClient.del(REDIS_EMAIL_CHANGE_PREFIX + userId + ":" + newEmail);
        throw new BizException(ErrorType.INTERNAL_ERROR, "验证码发送失败，请稍后重试");
    }
}
```

- [ ] **Step 3: VerificationServiceImpl 实现 verifyEmailChangeCode**

```java
@Override
@Transactional
public void verifyEmailChangeCode(Long userId, String newEmail, String code) {
    // 1. 从 Redis 获取存储的验证码
    String storedCode = redisClient.get(REDIS_EMAIL_CHANGE_PREFIX + userId + ":" + newEmail);
    if (storedCode == null) {
        throw new BizException(ErrorType.VERIFICATION_FAILED, "验证码已过期，请重新发送");
    }
    if (!storedCode.equals(code)) {
        throw new BizException(ErrorType.VERIFICATION_FAILED, "验证码不正确");
    }

    // 2. 校验通过，删除 Redis key
    redisClient.del(REDIS_EMAIL_CHANGE_PREFIX + userId + ":" + newEmail);

    // 3. 再次检查新邮箱唯一性（防并发注册占用）
    if (userMapper.existsByEmail(newEmail)) {
        throw new BizException(ErrorType.CONFLICT, "该邮箱已被其他账号使用");
    }

    // 4. 查询当前用户，获取旧邮箱
    User user = userMapper.selectById(userId);
    if (user == null) {
        throw new BizException(ErrorType.NOT_FOUND, "用户不存在");
    }
    String oldEmail = user.getEmail();

    // 5. 更新 email + email_verified
    user.setEmail(newEmail);
    user.setEmailVerified(true);
    user.setUpdatedAt(LocalDateTime.now());
    userMapper.updateById(user);

    // 6. 通知旧邮箱（失败不抛异常，不回滚）
    if (oldEmail != null && !oldEmail.isEmpty()) {
        try {
            Resend resend = new Resend(resendApiKey);
            CreateEmailOptions params = CreateEmailOptions.builder()
                    .from("admin@zhaizz.top")
                    .to(oldEmail)
                    .subject("[AnimeTracker] 邮箱变更通知")
                    .text("你的 AnimeTracker 账号邮箱已变更为：" + newEmail + "\n\n如非本人操作，请立即联系管理员。")
                    .build();
            resend.emails().send(params);
        } catch (ResendException e) {
            // ponytail: 通知失败不干扰主流程，静默记日志
            log.warn("旧邮箱通知发送失败: {}", oldEmail, e);
        }
    }
}
```

类级别加注解和导入：

```java
import org.springframework.transaction.annotation.Transactional;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
@RequiredArgsConstructor
public class VerificationServiceImpl implements VerificationService {
```

- [ ] **Step 4: Commit**

```bash
git add backend/business/user/src/main/java/top/zhaizz/user/service/VerificationService.java backend/business/user/src/main/java/top/zhaizz/user/service/impl/VerificationServiceImpl.java
git commit -m "feat: VerificationService 新增邮箱修改验证方法"
```

---

### Task 3: AuthServiceImpl.register() 加邮箱唯一性检查

**Files:**
- Modify: `backend/business/user/src/main/java/top/zhaizz/user/service/impl/AuthServiceImpl.java`

**Interfaces:**
- Consumes: `UserMapper.existsByEmail(email)`

- [ ] **Step 1: 在 register() 方法中用户名检查后新增邮箱检查**

在用户名唯一性检查之后、创建用户之前插入：

```java
// 1.5 检查邮箱唯一性
if (userMapper.existsByEmail(request.getEmail())) {
    throw new BizException(ErrorType.CONFLICT, "邮箱已被注册");
}
```

- [ ] **Step 2: Commit**

```bash
git add backend/business/user/src/main/java/top/zhaizz/user/service/impl/AuthServiceImpl.java
git commit -m "feat: 注册时检查邮箱唯一性"
```

---

### Task 4: UserController 新增端点 + UpdateUserDTO 移除 email

**Files:**
- Modify: `backend/business/user/src/main/java/top/zhaizz/user/controller/UserController.java`
- Modify: `backend/business/pojo/src/main/java/top/zhaizz/pojo/dto/UpdateUserDTO.java`

**Interfaces:**
- Consumes: `VerificationService.sendEmailChangeCode()`, `VerificationService.verifyEmailChangeCode()`
- Produces:
  - `POST /api/user/me/send-email-code` — 请求体 `{ newEmail }`
  - `POST /api/user/me/verify-email-code` — 请求体 `{ newEmail, code }`

- [ ] **Step 1: UpdateUserDTO 移除 email 字段**

删除 `@Email` 和 `@Size` 标注的 email 字段及其 getter/setter（Lombok @Data 自动移除）。

```java
// 删掉以下字段及相关注解
// @Email(message = "邮箱格式不正确")
// @Size(max = 128, message = "邮箱长度不能超过128")
// private String email;
```

- [ ] **Step 2: UserController 新增内部 DTO 类**

```java
@Data
public static class SendEmailCodeRequest {
    @NotBlank(message = "新邮箱不能为空")
    @Email(message = "邮箱格式不正确")
    private String newEmail;
}

@Data
public static class VerifyEmailCodeRequest {
    @NotBlank(message = "新邮箱不能为空")
    @Email(message = "邮箱格式不正确")
    private String newEmail;

    @NotBlank(message = "验证码不能为空")
    @Size(min = 6, max = 6, message = "验证码为6位")
    private String code;
}
```

- [ ] **Step 3: UserController 注入 VerificationService 加两个端点**

需先注入 `VerificationService`：

```java
private final VerificationService verificationService;
```

新增端点：

```java
/**
 * 发送邮箱修改验证码
 */
@PostMapping("/me/send-email-code")
public Result<Void> sendEmailCode(@Valid @RequestBody SendEmailCodeRequest request) {
    Long userId = getCurrentUserId();
    verificationService.sendEmailChangeCode(userId, request.getNewEmail());
    return Result.success(null);
}

/**
 * 校验邮箱修改验证码 → 更新邮箱
 */
@PostMapping("/me/verify-email-code")
public Result<Void> verifyEmailCode(@Valid @RequestBody VerifyEmailCodeRequest request) {
    Long userId = getCurrentUserId();
    verificationService.verifyEmailChangeCode(userId, request.getNewEmail(), request.getCode());
    return Result.success(null);
}
```

- [ ] **Step 4: Commit**

```bash
git add backend/business/pojo/src/main/java/top/zhaizz/pojo/dto/UpdateUserDTO.java backend/business/user/src/main/java/top/zhaizz/user/controller/UserController.java
git commit -m "feat: 新增邮箱修改验证端点，UpdateUserDTO 移除 email"
```

---

### Task 5: 前端 types + api + store 新增邮箱修改验证方法

**Files:**
- Modify: `frontend/client/src/types/index.ts`
- Modify: `frontend/client/src/api/auth.ts`
- Modify: `frontend/client/src/stores/auth.ts`

**Interfaces:**
- Consumes: 无
- Produces:
  - `SendEmailCodeRequest`, `VerifyEmailCodeRequest` types
  - `authApi.sendEmailCode()`, `authApi.verifyEmailCode()` API 方法
  - `authStore.sendEmailCode()`, `authStore.verifyEmailCode()` store actions

- [ ] **Step 1: types/index.ts 加新类型，UpdateProfileRequest 移除 email**

```ts
export interface SendEmailCodeRequest {
  newEmail: string
}

export interface VerifyEmailCodeRequest {
  newEmail: string
  code: string
}
```

同时从 `UpdateProfileRequest` 中移除 `email?` 字段（邮箱改由验证端点处理）：

```ts
export interface UpdateProfileRequest {
  nickname?: string
  avatar?: string
  // email 已移除，邮箱修改走 /api/user/me/verify-email-code
}
```

- [ ] **Step 2: api/auth.ts 加两个 API 方法**

```ts
sendEmailCode(data: SendEmailCodeRequest) {
  return http.post<ApiResponse<null>>('/api/user/me/send-email-code', data)
},
verifyEmailCode(data: VerifyEmailCodeRequest) {
  return http.post<ApiResponse<null>>('/api/user/me/verify-email-code', data)
},
```

- [ ] **Step 3: stores/auth.ts 加两个 action**

```ts
async function sendEmailCode(newEmail: string) {
  loading.value = true
  try {
    await authApi.sendEmailCode({ newEmail })
  } finally {
    loading.value = false
  }
}

async function verifyEmailCode(newEmail: string, code: string) {
  loading.value = true
  try {
    await authApi.verifyEmailCode({ newEmail, code })
    // 更新本地 user.email，保持 UI 同步
    if (user.value) {
      user.value.email = newEmail
    }
  } finally {
    loading.value = false
  }
}
```

在 return 中追加：`sendEmailCode, verifyEmailCode`

- [ ] **Step 4: Commit**

```bash
git add frontend/client/src/types/index.ts frontend/client/src/api/auth.ts frontend/client/src/stores/auth.ts
git commit -m "feat: 前端新增邮箱修改验证 API 和 store action"
```

---

### Task 6: Profile.vue 添加验证码 UI + 保存逻辑

**Files:**
- Modify: `frontend/client/src/pages/Profile.vue`

**Interfaces:**
- Consumes: `authStore.sendEmailCode()`, `authStore.verifyEmailCode()`

- [ ] **Step 1: 新增响应式状态和 sendEmailCode 方法**

在 `<script setup>` 中追加 state：

```ts
const emailDirty = ref(false)
const emailCode = ref('')
const codeSent = ref(false)
const codeVerified = ref(false)
const countdown = ref(0)
let countdownTimer: ReturnType<typeof setInterval> | null = null

// 监听 email 变化
function onEmailInput() {
  const currentEmail = authStore.user?.email || ''
  const newEmail = email.value.trim()
  if (newEmail !== currentEmail) {
    emailDirty.value = true
    codeVerified.value = false  // 邮箱变了，之前的验证失效
  } else {
    emailDirty.value = false
    codeVerified.value = false
    emailCode.value = ''
  }
}

function startCountdown() {
  countdown.value = 60
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      if (countdownTimer) clearInterval(countdownTimer)
      countdownTimer = null
    }
  }, 1000)
}

async function handleSendCode() {
  const newEmail = email.value.trim()
  if (!newEmail) {
    error.value = '请先输入新邮箱'
    setTimeout(() => { error.value = '' }, 3000)
    return
  }
  try {
    await authStore.sendEmailCode(newEmail)
    codeSent.value = true
    startCountdown()
  } catch (e: any) {
    error.value = e?.response?.data?.message || '验证码发送失败'
    setTimeout(() => { error.value = '' }, 5000)
  }
}
```

- [ ] **Step 2: 修改 handleSave 逻辑**

```ts
async function handleSave() {
  success.value = ''
  error.value = ''
  loading.value = true

  try {
    let emailChanged = false

    // 1. 如果邮箱有变更但未验证 → 报错
    if (emailDirty.value && !codeVerified.value) {
      throw new Error('请先点击"发送验证码"验证新邮箱')
    }

    // 2. 如果邮箱已验证 → 执行邮箱变更
    if (emailDirty.value && codeVerified.value) {
      await authStore.verifyEmailCode(email.value.trim(), emailCode.value.trim())
      emailChanged = true
    }

    // 3. 保存非邮箱字段（昵称、头像）
    await authStore.updateProfile({
      nickname: nickname.value.trim() || undefined,
      avatar: avatar.value.trim() || undefined,
    })

    success.value = '个人资料已更新'
    setTimeout(() => { success.value = '' }, 3000)

    // 4. 重置验证状态
    emailDirty.value = false
    codeVerified.value = false
    emailCode.value = ''
    codeSent.value = false
    email.value = authStore.user?.email || ''
  } catch (e: any) {
    if (emailChanged) {
      // 邮箱已变更成功，但昵称/头像保存失败
      error.value = '邮箱已更新，但其他资料保存失败，请重试'
    } else {
      error.value = e?.response?.data?.message || e.message || '更新失败，请稍后重试'
    }
    setTimeout(() => { error.value = '' }, 5000)
  } finally {
    loading.value = false
  }
}
```

- [ ] **Step 3: 修改模板 — 邮箱区域添加验证码 UI**

将邮箱 input 后的模板改为（替换原有邮箱 div）：

```html
<!-- Email -->
<div>
  <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">邮箱</label>
  <div class="relative">
    <Mail class="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4" style="color: var(--color-text-secondary)" />
    <input
      v-model="email"
      type="email"
      placeholder="设置邮箱"
      class="input-field pl-10"
      :class="{ 'pr-28': true }"
      @input="onEmailInput"
    />
    <button
      v-if="emailDirty && !codeVerified"
      type="button"
      class="absolute right-1.5 top-1/2 -translate-y-1/2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
      :class="countdown > 0 ? 'bg-gray-100 dark:bg-gray-700 text-gray-500 cursor-not-allowed' : 'bg-primary/10 text-primary hover:bg-primary/20'"
      :disabled="countdown > 0 || loading"
      @click="handleSendCode"
    >
      {{ countdown > 0 ? `${countdown}s` : '发送验证码' }}
    </button>
  </div>
  <!-- 验证码输入框（邮箱变更时显示） -->
  <Transition name="slide-fade">
    <div v-if="codeSent && !codeVerified" class="mt-3">
      <div class="relative">
        <input
          v-model="emailCode"
          type="text"
          maxlength="6"
          placeholder="输入验证码"
          class="input-field pl-3 pr-20"
          @input="e => emailCode = (e.target as HTMLInputElement).value.toUpperCase()"
        />
        <span class="absolute right-3 top-1/2 -translate-y-1/2 text-xs opacity-40">6位码</span>
      </div>
    </div>
  </Transition>
  <!-- 已验证提示 -->
  <p v-if="codeVerified" class="text-xs mt-1.5 text-green-600 dark:text-green-400">✓ 新邮箱已验证</p>
</div>
```

- [ ] **Step 4: 添加 Transition 样式**

```css
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}
.slide-fade-leave-active {
  transition: all 0.3s ease-in;
}
.slide-fade-enter-from {
  transform: translateY(-8px);
  opacity: 0;
}
.slide-fade-leave-to {
  opacity: 0;
}
```

注意：Profile.vue 可能已有 `slide-fade` 样式定义（用于 toast），如已有则删除重复的，保留 toast 用的。

- [ ] **Step 5: onMounted 中重置状态**

```ts
onMounted(async () => {
  if (!authStore.user) {
    await authStore.fetchMe()
  }
  initForm()
  emailDirty.value = false
  codeVerified.value = false
  codeSent.value = false
  emailCode.value = ''
})
```

- [ ] **Step 6: Commit**

```bash
git add frontend/client/src/pages/Profile.vue
git commit -m "feat: Profile 页添加邮箱修改验证 UI"
```
