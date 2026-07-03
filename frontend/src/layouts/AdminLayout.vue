<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const adminLinks = [
  { name: 'Dashboard', label: '仪表盘', path: '/admin' },
  { name: 'SubjectManage', label: '条目管理', path: '/admin/subjects' },
  { name: 'AdminUsers', label: '用户管理', path: '/admin/users' },
  { name: 'ImportStatus', label: '导入状态', path: '/admin/import' },
]
</script>

<template>
  <div class="min-h-screen flex">
    <!-- 侧边栏 -->
    <aside class="w-56 bg-gray-900 text-white flex flex-col">
      <div class="p-4 border-b border-gray-700">
        <router-link to="/" class="text-lg font-bold text-indigo-400">AnimeTracker</router-link>
        <div class="text-xs text-gray-400 mt-1">管理后台</div>
      </div>
      <nav class="flex-1 p-3 space-y-1">
        <router-link
          v-for="link in adminLinks"
          :key="link.name"
          :to="link.path"
          class="block px-3 py-2 text-sm rounded transition-colors"
          :class="route.name === link.name ? 'bg-indigo-600 text-white' : 'text-gray-300 hover:bg-gray-700'"
        >
          {{ link.label }}
        </router-link>
      </nav>
      <div class="p-3 border-t border-gray-700">
        <button @click="authStore.logout(); router.push('/')" class="text-sm text-gray-400 hover:text-white w-full text-left">
          返回前台
        </button>
      </div>
    </aside>

    <!-- 主内容 -->
    <main class="flex-1 bg-gray-50 overflow-auto">
      <div class="p-6">
        <router-view />
      </div>
    </main>
  </div>
</template>
