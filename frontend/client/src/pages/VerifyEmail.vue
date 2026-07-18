<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Mail } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const storedEmail = sessionStorage.getItem('verifyEmail')
sessionStorage.removeItem('verifyEmail')
const email = ref(storedEmail || '')
const code = ref('')
const error = ref('')
const loading = ref(false)
const resending = ref(false)
const cooldown = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

if (!email.value) {
  router.replace('/login')
} else {
  startCooldown()
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
      <h1 class="text-[24px] font-bold mb-6" style="color: var(--color-text)">
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
