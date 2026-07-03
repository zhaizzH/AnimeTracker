<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const email = ref('')
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  if (!username.value || !password.value) {
    error.value = '请填写用户名和密码'
    return
  }
  if (password.value.length < 6) {
    error.value = '密码至少 6 位'
    return
  }
  error.value = ''
  loading.value = true
  try {
    await authStore.register(username.value, password.value, email.value || undefined)
    router.push('/')
  } catch {
    error.value = '注册失败，用户名可能已存在'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-sm mx-auto mt-12">
    <h1 class="text-2xl font-bold text-center mb-6">注册</h1>
    <form @submit.prevent="handleRegister" class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
        <input v-model="username" type="text" class="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:border-indigo-400" placeholder="3-32位字母、数字或下划线" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
        <input v-model="password" type="password" class="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:border-indigo-400" placeholder="至少 6 位" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">邮箱（可选）</label>
        <input v-model="email" type="email" class="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:border-indigo-400" placeholder="example@email.com" />
      </div>
      <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
      <button type="submit" :disabled="loading" class="w-full bg-indigo-600 text-white py-2 rounded text-sm hover:bg-indigo-700 disabled:opacity-50">
        {{ loading ? '注册中...' : '注册' }}
      </button>
      <p class="text-center text-sm text-gray-500">
        已有账号？<router-link to="/login" class="text-indigo-600 hover:text-indigo-700">登录</router-link>
      </p>
    </form>
  </div>
</template>
