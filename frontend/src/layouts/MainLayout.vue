<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const mobileMenuOpen = ref(false)

function logout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <!-- 导航栏 -->
    <nav class="bg-white shadow-sm border-b">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-14">
          <!-- Logo -->
          <div class="flex items-center">
            <router-link to="/" class="text-lg font-bold text-indigo-600">
              AnimeTracker
            </router-link>
            <div class="ml-8 hidden md:flex space-x-4">
              <router-link to="/" class="nav-link" :class="{ active: route.name === 'Home' }">首页</router-link>
              <router-link to="/search" class="nav-link" :class="{ active: route.name === 'Search' }">搜索</router-link>
              <router-link to="/season" class="nav-link" :class="{ active: route.name === 'Season' }">季度</router-link>
              <router-link to="/tags" class="nav-link" :class="{ active: route.name === 'Tags' }">标签</router-link>
            </div>
          </div>
          <!-- 右侧 -->
          <div class="flex items-center space-x-3">
            <template v-if="authStore.isAuthenticated">
              <router-link to="/profile" class="text-sm text-gray-600 hover:text-indigo-600">
                {{ authStore.user?.nickname || authStore.user?.username }}
              </router-link>
              <router-link v-if="authStore.isAdmin" to="/admin" class="text-sm text-gray-600 hover:text-indigo-600">
                管理
              </router-link>
              <button @click="logout" class="text-sm text-gray-500 hover:text-red-500">退出</button>
            </template>
            <template v-else>
              <router-link to="/login" class="text-sm text-gray-600 hover:text-indigo-600">登录</router-link>
              <router-link to="/register" class="text-sm text-white bg-indigo-600 px-3 py-1.5 rounded hover:bg-indigo-700">注册</router-link>
            </template>
            <!-- 移动端菜单按钮 -->
            <button @click="mobileMenuOpen = !mobileMenuOpen" class="md:hidden p-1">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
              </svg>
            </button>
          </div>
        </div>
        <!-- 移动端菜单 -->
        <div v-if="mobileMenuOpen" class="md:hidden pb-3 border-t">
          <div class="flex flex-col space-y-2 pt-2">
            <router-link to="/" class="nav-link-mobile" @click="mobileMenuOpen = false">首页</router-link>
            <router-link to="/search" class="nav-link-mobile" @click="mobileMenuOpen = false">搜索</router-link>
            <router-link to="/season" class="nav-link-mobile" @click="mobileMenuOpen = false">季度</router-link>
            <router-link to="/tags" class="nav-link-mobile" @click="mobileMenuOpen = false">标签</router-link>
          </div>
        </div>
      </div>
    </nav>

    <!-- 主内容 -->
    <main class="flex-1">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <router-view />
      </div>
    </main>

    <!-- 页脚 -->
    <FooterComp />
  </div>
</template>

<style scoped>
.nav-link {
  @apply px-3 py-2 text-sm text-gray-600 hover:text-indigo-600 transition-colors;
}
.nav-link.active {
  @apply text-indigo-600 font-medium;
}
.nav-link-mobile {
  @apply block px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded;
}
</style>
