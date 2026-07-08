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
  <div class="min-h-[80vh] flex items-center justify-center app-container">
    <div class="w-full max-w-md">
      <div class="app-card p-8">
        <!-- Header -->
        <div class="text-center mb-8">
          <h1 class="page-title mb-2">欢迎回来</h1>
          <p class="page-subtitle">登录你的账户</p>
        </div>

        <!-- Error -->
        <Transition name="fade">
          <div
            v-if="error"
            class="mb-6 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-600 dark:text-red-400 text-center"
          >
            {{ error }}
          </div>
        </Transition>

        <!-- Form -->
        <form @submit.prevent="handleLogin" class="space-y-5">
          <!-- Username -->
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">用户名</label>
            <div class="relative">
              <User class="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4" style="color: var(--color-text-secondary)" />
              <input
                v-model="username"
                type="text"
                placeholder="输入用户名"
                class="input-field pl-10"
                autocomplete="username"
              />
            </div>
          </div>

          <!-- Password -->
          <div>
            <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">密码</label>
            <div class="relative">
              <Lock class="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4" style="color: var(--color-text-secondary)" />
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="输入密码"
                class="input-field pl-10 pr-10"
                autocomplete="current-password"
              />
              <button
                type="button"
                class="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 rounded-md hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
                style="color: var(--color-text-secondary)"
                @click="showPassword = !showPassword"
                tabindex="-1"
              >
                <EyeOff v-if="showPassword" class="h-4 w-4" />
                <Eye v-else class="h-4 w-4" />
              </button>
            </div>
          </div>

          <!-- Submit -->
          <button
            type="submit"
            class="btn-primary w-full py-3"
            :disabled="loading"
          >
            <svg v-if="loading" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>

        <!-- Footer -->
        <div class="mt-6 text-center text-sm" style="color: var(--color-text-secondary)">
          还没有账户？
          <router-link to="/register" class="text-primary-500 hover:text-primary-600 font-medium transition-colors">
            注册
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
