<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { User, Lock, Eye, EyeOff } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  if (!username.value.trim() || !password.value) {
    error.value = '请填写用户名和密码'
    return
  }
  loading.value = true
  try {
    await authStore.login({ username: username.value.trim(), password: password.value })
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (e: any) {
    error.value = e?.response?.data?.message || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-[calc(100vh-64px)] items-center justify-center px-4">
    <div class="w-full max-w-md">
      <!-- Tab switcher (pill style) -->
      <div class="auth-tabs">
        <router-link to="/login" class="auth-tab auth-tab--active">
          登录
        </router-link>
        <router-link to="/register" class="auth-tab">
          注册
        </router-link>
      </div>

      <!-- Title -->
      <h1 class="text-[24px] font-bold mt-6 mb-6" style="color: var(--color-text)">
        欢迎回来
      </h1>

      <!-- Error -->
      <Transition name="fade">
        <div
          v-if="error"
          class="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-500 text-center"
        >
          {{ error }}
        </div>
      </Transition>

      <!-- Form -->
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div class="relative">
          <User class="absolute left-3.5 top-1/2 -translate-y-1/2 h-[18px] w-[18px]" style="color: var(--color-text-secondary)" />
          <input
            v-model="username"
            type="text"
            placeholder="用户名"
            class="auth-input"
            autocomplete="username"
          />
        </div>

        <div class="relative">
          <Lock class="absolute left-3.5 top-1/2 -translate-y-1/2 h-[18px] w-[18px]" style="color: var(--color-text-secondary)" />
          <input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="密码"
            class="auth-input pr-11"
            autocomplete="current-password"
          />
          <button
            type="button"
            class="absolute right-3 top-1/2 -translate-y-1/2 p-0.5"
            style="color: var(--color-text-secondary)"
            @click="showPassword = !showPassword"
            tabindex="-1"
          >
            <EyeOff v-if="showPassword" class="h-4 w-4" />
            <Eye v-else class="h-4 w-4" />
          </button>
        </div>

        <button type="submit" class="auth-submit" :disabled="loading">
          <svg v-if="loading" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
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
  background: rgba(0,0,0,0.2);
  border: 1px solid var(--color-border);
  box-shadow: inset 0 0 0 1px rgba(241,121,146,0.15);
}
:root:not(.dark) .auth-tabs {
  background: rgba(0,0,0,0.05);
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
.auth-submit:hover { opacity: 0.9; }
.auth-submit:disabled { opacity: 0.5; cursor: not-allowed; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
