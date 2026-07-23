<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { User, Mail, Save, Shield, Calendar, CheckCircle, XCircle, Upload } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'
import { uploadFile } from '@/api/upload'

const authStore = useAuthStore()

const nickname = ref('')
const email = ref('')
const avatar = ref('')
const loading = ref(false)
const uploading = ref(false)
const success = ref('')
const error = ref('')
const emailDirty = ref(false)
const emailCode = ref('')
const codeSent = ref(false)
const codeVerified = ref(false)
const countdown = ref(0)
let countdownTimer: ReturnType<typeof setInterval> | null = null

function initForm() {
  if (authStore.user) {
    nickname.value = authStore.user.nickname || ''
    email.value = authStore.user.email || ''
    avatar.value = authStore.user.avatar || ''
  }
}

function onEmailInput() {
  const currentEmail = authStore.user?.email || ''
  const newEmail = email.value.trim()
  if (newEmail !== currentEmail) {
    emailDirty.value = true
    codeVerified.value = false
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
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(newEmail)) {
    error.value = '邮箱格式不正确'
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

async function handleFileSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  const allowed = ['image/jpeg', 'image/png', 'image/webp']
  if (!allowed.includes(file.type)) {
    error.value = '仅支持 JPG、PNG、WebP 格式'
    setTimeout(() => { error.value = '' }, 5000)
    return
  }

  if (file.size > 5 * 1024 * 1024) {
    error.value = '图片大小不能超过 5MB'
    setTimeout(() => { error.value = '' }, 5000)
    return
  }

  uploading.value = true
  error.value = ''
  try {
    const url = await uploadFile(file, 'avatar')
    avatar.value = url
  } catch (e: any) {
    error.value = e?.response?.data?.message || '上传失败，请重试'
    setTimeout(() => { error.value = '' }, 5000)
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function handleSave() {
  success.value = ''
  error.value = ''
  loading.value = true
  let emailChanged = false

  try {

    if (emailDirty.value && codeSent.value && !emailCode.value.trim()) {
      throw new Error('请先输入验证码')
    }

    if (emailDirty.value && codeSent.value && emailCode.value.trim()) {
      await authStore.verifyEmailCode(email.value.trim(), emailCode.value.trim())
      emailChanged = true
    }

    await authStore.updateProfile({
      nickname: nickname.value.trim() || undefined,
      avatar: avatar.value.trim() || undefined,
    })

    success.value = '个人资料已更新'
    setTimeout(() => { success.value = '' }, 3000)

    emailDirty.value = false
    codeVerified.value = false
    emailCode.value = ''
    codeSent.value = false
    email.value = authStore.user?.email || ''
  } catch (e: any) {
    if (emailChanged) {
      error.value = '邮箱已更新，但其他资料保存失败，请重试'
    } else {
      error.value = e?.response?.data?.message || e.message || '更新失败，请稍后重试'
    }
    setTimeout(() => { error.value = '' }, 5000)
  } finally {
    loading.value = false
  }
}

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

const memberSince = computed(() => {
  if (!authStore.user?.createdAt) return ''
  try {
    return new Date(authStore.user.createdAt).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  } catch {
    return authStore.user.createdAt
  }
})
</script>

<template>
  <div class="app-container py-8 max-w-3xl mx-auto">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="page-title mb-2">个人中心</h1>
      <p class="page-subtitle">管理你的账户信息</p>
    </div>

    <!-- Toast Messages -->
    <Transition name="slide-fade">
      <div v-if="success" class="mb-6 p-3 rounded-xl bg-green-500/10 border border-green-500/20 flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
        <CheckCircle class="h-4 w-4 shrink-0" />
        {{ success }}
      </div>
    </Transition>
    <Transition name="slide-fade">
      <div v-if="error" class="mb-6 p-3 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
        <XCircle class="h-4 w-4 shrink-0" />
        {{ error }}
      </div>
    </Transition>

    <!-- User Info Card -->
    <div class="app-card p-5 sm:p-6 mb-6">
      <div class="flex flex-col sm:flex-row items-center sm:items-center gap-4 sm:gap-5">
        <!-- Avatar -->
        <div class="shrink-0">
          <div class="w-16 h-16 rounded-2xl overflow-hidden flex items-center justify-center" style="background: var(--color-hover)">
            <img
              v-if="authStore.user?.avatar"
              :src="authStore.user.avatar"
              alt="Avatar"
              class="w-full h-full object-cover"
            />
            <User v-else class="h-8 w-8 opacity-30" style="color: var(--color-text-secondary)" />
          </div>
        </div>

        <!-- Info -->
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2 mb-1">
            <h2 class="text-lg font-semibold truncate" style="color: var(--color-text)">
              {{ authStore.user?.nickname || authStore.user?.username }}
            </h2>
            <span v-if="authStore.user?.role === 'ADMIN'" class="badge text-xs">
              <Shield class="h-3 w-3 mr-1" />
              管理员
            </span>
            <span v-else class="badge text-xs">用户</span>
          </div>
          <div class="text-sm" style="color: var(--color-text-secondary)">@{{ authStore.user?.username }}</div>
          <div v-if="memberSince" class="flex items-center gap-1 text-xs mt-1" style="color: var(--color-text-secondary)">
            <Calendar class="h-3 w-3" />
            {{ memberSince }} 加入
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Form -->
    <div class="app-card p-5 sm:p-6">
      <h3 class="text-base font-semibold mb-5" style="color: var(--color-text)">编辑资料</h3>
      <form @submit.prevent="handleSave" class="space-y-5">
        <!-- Nickname -->
        <div>
          <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">昵称</label>
          <div class="relative">
            <User class="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4" style="color: var(--color-text-secondary)" />
            <input
              v-model="nickname"
              type="text"
              placeholder="设置昵称"
              class="input-field pl-10"
            />
          </div>
        </div>

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

        <!-- 头像上传 -->
        <div>
          <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">头像</label>
          <div class="flex items-center gap-4">
            <div
              class="w-16 h-16 rounded-2xl overflow-hidden flex items-center justify-center shrink-0 border-2 border-dashed"
              :style="{ borderColor: 'var(--color-border)', background: 'var(--color-hover)' }"
            >
              <img
                v-if="avatar"
                :src="avatar"
                alt="Avatar Preview"
                class="w-full h-full object-cover"
              />
              <User v-else class="h-6 w-6 opacity-30" style="color: var(--color-text-secondary)" />
            </div>
            <div class="flex-1">
              <label class="btn-secondary cursor-pointer inline-flex items-center gap-2" :class="{ 'opacity-50 pointer-events-none': uploading }">
                <Upload v-if="!uploading" class="h-4 w-4" />
                <svg v-else class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {{ uploading ? '上传中...' : '选择图片' }}
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  class="hidden"
                  @change="handleFileSelected"
                />
              </label>
              <p class="text-xs mt-1.5" style="color: var(--color-text-secondary)">支持 JPG/PNG/WebP，最大 5MB</p>
            </div>
          </div>
        </div>

        <!-- Save Button -->
        <div class="pt-2">
          <button
            type="submit"
            class="btn-primary"
            :disabled="loading"
          >
            <svg v-if="loading" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <Save v-else class="h-4 w-4" />
            {{ loading ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}
.slide-fade-leave-active {
  transition: all 0.3s ease-in;
}
.slide-fade-enter-from {
  transform: translateY(-10px);
  opacity: 0;
}
.slide-fade-leave-to {
  opacity: 0;
}
</style>
