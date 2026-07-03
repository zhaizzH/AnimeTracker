<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ErrorState from '@/components/ErrorState.vue'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  error.value = ''
  loading.value = true
  try {
    await authStore.login(username.value, password.value)
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch {
    error.value = '用户名或密码错误'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-sm mx-auto mt-12">
    <h1 class="text-2xl font-bold text-center mb-6">登录</h1>
    <form @submit.prevent="handleLogin" class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
        <input v-model="username" type="text" class="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:border-indigo-400" placeholder="请输入用户名" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
        <input v-model="password" type="password" class="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:border-indigo-400" placeholder="请输入密码" />
      </div>
      <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
      <button type="submit" :disabled="loading" class="w-full bg-indigo-600 text-white py-2 rounded text-sm hover:bg-indigo-700 disabled:opacity-50">
        {{ loading ? '登录中...' : '登录' }}
      </button>
      <p class="text-center text-sm text-gray-500">
        还没有账号？<router-link to="/register" class="text-indigo-600 hover:text-indigo-700">注册</router-link>
      </p>
    </form>
  </div>
</template>
