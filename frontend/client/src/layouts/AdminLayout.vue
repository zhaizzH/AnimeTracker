<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { LayoutDashboard, Film, Users, Download, Menu, X, ArrowLeft } from '@lucide/vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

// --- Admin guard ---
onMounted(async () => {
  if (auth.token && !auth.user) {
    await auth.fetchMe()
  }
  if (!auth.isAdmin) {
    router.replace('/')
  }
})

// --- Sidebar ---
const sidebarOpen = ref(false)

const sidebarItems = [
  { label: '仪表盘', to: '/admin', icon: LayoutDashboard, exact: true },
  { label: '番剧管理', to: '/admin/subjects', icon: Film, exact: false },
  { label: '用户管理', to: '/admin/users', icon: Users, exact: false },
  { label: '数据导入', to: '/admin/import', icon: Download, exact: false },
]

function isActive(item: typeof sidebarItems[number]) {
  if (item.exact) return route.path === item.to
  return route.path.startsWith(item.to)
}

function navigateTo(path: string) {
  router.push(path)
  sidebarOpen.value = false
}

// Close sidebar on route change (mobile)
watch(() => route.path, () => {
  sidebarOpen.value = false
})

// Lock body scroll when sidebar is open on mobile
watch(sidebarOpen, (open) => {
  if (window.innerWidth < 768) {
    document.body.style.overflow = open ? 'hidden' : ''
  }
})

onBeforeUnmount(() => {
  document.body.style.overflow = ''
})
</script>

<template>
  <div class="flex min-h-screen" style="background: var(--color-bg);">
    <!-- Mobile overlay -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="sidebarOpen"
        class="fixed inset-0 z-40 md:hidden"
        style="background: rgba(0,0,0,0.5);"
        @click="sidebarOpen = false"
      />
    </Transition>

    <!-- Sidebar -->
    <aside
      class="fixed md:sticky top-0 left-0 z-50 md:z-auto h-screen w-64 flex flex-col border-r transition-transform duration-250 ease-out md:translate-x-0"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
      style="background: var(--color-card); border-color: var(--color-border);"
    >
      <!-- Sidebar header -->
      <div class="flex items-center justify-between h-16 px-5 border-b shrink-0" style="border-color: var(--color-border);">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-lg bg-primary-500 flex items-center justify-center">
            <LayoutDashboard :size="16" class="text-white" />
          </div>
          <span class="text-base font-bold" style="color: var(--color-text);">管理后台</span>
        </div>
        <button
          @click="sidebarOpen = false"
          class="md:hidden flex items-center justify-center w-8 h-8 rounded-full transition-colors duration-200 hover:bg-[var(--color-hover)]"
          style="color: var(--color-text-secondary);"
        >
          <X :size="18" />
        </button>
      </div>

      <!-- Nav items -->
      <nav class="flex-1 py-4 px-3 space-y-1 overflow-y-auto scrollbar-hide">
        <button
          v-for="item in sidebarItems"
          :key="item.to"
          @click="navigateTo(item.to)"
          class="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200"
          :class="isActive(item)
            ? 'bg-primary-500 text-white shadow-sm'
            : 'hover:bg-[var(--color-hover)]'"
          :style="!isActive(item) ? 'color: var(--color-text-secondary)' : ''"
        >
          <component :is="item.icon" :size="18" :class="isActive(item) ? 'text-white' : ''" />
          {{ item.label }}
        </button>
      </nav>

      <!-- Sidebar footer: back to site -->
      <div class="px-3 py-4 border-t shrink-0" style="border-color: var(--color-border);">
        <router-link
          to="/"
          class="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-medium transition-colors duration-200 hover:bg-[var(--color-hover)]"
          style="color: var(--color-text-secondary);"
        >
          <ArrowLeft :size="18" />
          返回前台
        </router-link>
      </div>
    </aside>

    <!-- Main content area -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Top bar -->
      <header class="sticky top-0 z-30 h-16 flex items-center justify-between px-4 md:px-6 border-b shrink-0 glass" style="border-color: var(--color-border);">
        <div class="flex items-center gap-3">
          <button
            @click="sidebarOpen = true"
            class="md:hidden flex items-center justify-center w-9 h-9 rounded-full transition-colors duration-200 hover:bg-[var(--color-hover)]"
            style="color: var(--color-text-secondary);"
          >
            <Menu :size="20" />
          </button>
          <h1 class="text-lg font-semibold" style="color: var(--color-text);">管理后台</h1>
        </div>

        <div class="flex items-center gap-3">
          <router-link
            to="/"
            class="hidden sm:inline-flex items-center gap-2 text-sm font-medium transition-colors duration-200 hover:text-primary-500"
            style="color: var(--color-text-secondary);"
          >
            <ArrowLeft :size="15" />
            返回前台
          </router-link>
          <div
            v-if="auth.user"
            class="flex items-center gap-2"
          >
            <img
              v-if="auth.user.avatar"
              :src="auth.user.avatar"
              :alt="auth.user.nickname"
              class="w-8 h-8 rounded-full object-cover bg-surface-200"
            />
            <div
              v-else
              class="w-8 h-8 rounded-full bg-primary-500/15 text-primary-500 flex items-center justify-center"
            >
              <span class="text-xs font-bold">{{ (auth.user.nickname || auth.user.username || '?')[0]?.toUpperCase() }}</span>
            </div>
          </div>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 p-4 md:p-6 lg:p-8">
        <router-view />
      </main>
    </div>
  </div>
</template>
