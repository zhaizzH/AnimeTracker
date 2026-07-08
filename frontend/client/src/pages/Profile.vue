<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { User, Mail, Image, Save, Shield, Calendar, CheckCircle, XCircle } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const nickname = ref('')
const email = ref('')
const avatar = ref('')
const loading = ref(false)
const success = ref('')
const error = ref('')

function initForm() {
  if (authStore.user) {
    nickname.value = authStore.user.nickname || ''
    email.value = authStore.user.email || ''
    avatar.value = authStore.user.avatar || ''
  }
}

async function handleSave() {
  success.value = ''
  error.value = ''
  loading.value = true
  try {
    await authStore.updateProfile({
      nickname: nickname.value.trim() || undefined,
      email: email.value.trim() || undefined,
      avatar: avatar.value.trim() || undefined,
    })
    success.value = '个人资料已更新'
    setTimeout(() => { success.value = '' }, 3000)
  } catch (e: any) {
    error.value = e?.response?.data?.message || '更新失败，请稍后重试'
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
    <div class="app-card p-6 mb-6">
      <div class="flex items-center gap-5">
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
    <div class="app-card p-6">
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
            />
          </div>
        </div>

        <!-- Avatar URL -->
        <div>
          <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text)">头像 URL</label>
          <div class="relative">
            <Image class="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4" style="color: var(--color-text-secondary)" />
            <input
              v-model="avatar"
              type="url"
              placeholder="输入头像图片链接"
              class="input-field pl-10"
            />
          </div>
          <!-- Avatar Preview -->
          <div v-if="avatar" class="mt-3 flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl overflow-hidden" style="background: var(--color-hover)">
              <img :src="avatar" alt="Preview" class="w-full h-full object-cover" />
            </div>
            <span class="text-xs" style="color: var(--color-text-secondary)">头像预览</span>
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
