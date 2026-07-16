<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  Search, Sun, Moon, Menu, X, User, LogOut,
  ChevronDown,
} from '@lucide/vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

// --- Theme toggle ---
const isDark = ref(document.documentElement.classList.contains('dark'))

function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

onMounted(() => {
  const saved = localStorage.getItem('theme')
  if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
})

// --- Mobile menu ---
const mobileMenuOpen = ref(false)

function closeMobile() {
  mobileMenuOpen.value = false
}

// Lock body scroll when mobile menu is open
watch(mobileMenuOpen, (open) => {
  document.body.style.overflow = open ? 'hidden' : ''
})

onBeforeUnmount(() => {
  document.body.style.overflow = ''
})

// --- User dropdown ---
const dropdownOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

function toggleDropdown() {
  dropdownOpen.value = !dropdownOpen.value
}

function handleClickOutside(e: MouseEvent) {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target as Node)) {
    dropdownOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('click', handleClickOutside))

async function handleLogout() {
  dropdownOpen.value = false
  await auth.logout()
  router.push('/')
}

// --- Navigation ---
const navLinks = [
  { label: '首页', to: '/', name: 'Home' },
  { label: '本季新番', to: '/season', name: 'Season' },
  { label: '番剧索引', to: '/search', name: 'Search' },
]

function isActive(link: typeof navLinks[number]) {
  if (link.name === 'Home') return route.path === '/'
  return route.path.startsWith(link.to)
}

function navigateTo(path: string) {
  router.push(path)
  closeMobile()
  dropdownOpen.value = false
}
</script>

<template>
  <header class="sticky top-0 z-50 glass border-b" style="border-color: var(--color-border);">
    <div class="app-container">
      <div class="flex items-center justify-between h-16">
        <!-- Left: Logo -->
        <router-link to="/" class="flex items-center gap-1 text-xl font-bold shrink-0 select-none">
          <span class="text-primary-500">Anime</span>
          <span style="color: var(--color-text);">Tracker</span>
        </router-link>

        <!-- Center: Desktop nav links -->
        <nav class="hidden md:flex items-center gap-1">
          <router-link
            v-for="link in navLinks"
            :key="link.name"
            :to="link.to"
            class="px-4 py-2 rounded-full text-sm font-medium transition-colors duration-200"
            :class="isActive(link)
              ? 'bg-primary-500/10 text-primary-500'
              : 'hover:bg-[var(--color-hover)]'"
            :style="!isActive(link) ? 'color: var(--color-text-secondary)' : ''"
          >
            {{ link.label }}
          </router-link>
        </nav>

        <!-- Right: Actions -->
        <div class="flex items-center gap-2">
          <!-- Search icon -->
          <router-link
            to="/search"
            class="hidden sm:flex items-center justify-center w-9 h-9 rounded-full transition-colors duration-200"
            style="color: var(--color-text-secondary);"
            :class="'hover:bg-[var(--color-hover)]'"
            title="搜索"
          >
            <Search :size="18" />
          </router-link>

          <!-- Theme toggle -->
          <button
            @click="toggleTheme"
            class="flex items-center justify-center w-9 h-9 rounded-full transition-colors duration-200"
            style="color: var(--color-text-secondary);"
            :class="'hover:bg-[var(--color-hover)]'"
            :title="isDark ? '切换亮色' : '切换暗色'"
          >
            <Moon v-if="isDark" :size="18" />
            <Sun v-else :size="18" />
          </button>

          <!-- User area (desktop) -->
          <template v-if="auth.isAuthenticated && auth.user">
            <div ref="dropdownRef" class="hidden md:block relative">
              <button
                @click.stop="toggleDropdown"
                class="flex items-center gap-2 pl-1 pr-3 py-1 rounded-full transition-colors duration-200 hover:bg-[var(--color-hover)]"
              >
                <img
                  v-if="auth.user.avatar"
                  :src="auth.user.avatar"
                  :alt="auth.user.nickname"
                  class="w-7 h-7 rounded-full object-cover bg-surface-200"
                />
                <div
                  v-else
                  class="w-7 h-7 rounded-full bg-primary-500/15 text-primary-500 flex items-center justify-center"
                >
                  <User :size="14" />
                </div>
                <span class="text-sm font-medium max-w-[100px] truncate" style="color: var(--color-text);">
                  {{ auth.user.nickname || auth.user.username }}
                </span>
                <ChevronDown :size="14" class="transition-transform duration-200" :class="{ 'rotate-180': dropdownOpen }" style="color: var(--color-text-secondary);" />
              </button>

              <!-- Dropdown menu -->
              <Transition
                enter-active-class="transition duration-150 ease-out"
                enter-from-class="opacity-0 scale-95 -translate-y-1"
                enter-to-class="opacity-100 scale-100 translate-y-0"
                leave-active-class="transition duration-100 ease-in"
                leave-from-class="opacity-100 scale-100"
                leave-to-class="opacity-0 scale-95"
              >
                <div
                  v-if="dropdownOpen"
                  class="absolute right-0 mt-2 w-48 rounded-xl overflow-hidden shadow-lg border origin-top-right"
                  style="background: var(--color-card); border-color: var(--color-border);"
                >
                  <button
                    @click="navigateTo('/profile')"
                    class="flex items-center gap-3 w-full px-4 py-2.5 text-sm transition-colors duration-150 hover:bg-[var(--color-hover)]"
                    style="color: var(--color-text);"
                  >
                    <User :size="16" style="color: var(--color-text-secondary);" />
                    个人中心
                  </button>
                  <div class="border-t" style="border-color: var(--color-border);"></div>
                  <button
                    @click="handleLogout"
                    class="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-red-500 transition-colors duration-150 hover:bg-red-50 dark:hover:bg-red-500/10"
                  >
                    <LogOut :size="16" />
                    退出登录
                  </button>
                </div>
              </Transition>
            </div>
          </template>

          <!-- Not authenticated (desktop) -->
          <template v-else>
            <div class="hidden md:flex items-center gap-2">
              <router-link to="/login" class="btn-ghost text-sm">登录</router-link>
              <router-link to="/register" class="btn-primary text-sm !py-2 !px-4">注册</router-link>
            </div>
          </template>

          <!-- Mobile hamburger -->
          <button
            @click="mobileMenuOpen = !mobileMenuOpen"
            class="md:hidden flex items-center justify-center w-9 h-9 rounded-full transition-colors duration-200 hover:bg-[var(--color-hover)]"
            style="color: var(--color-text-secondary);"
          >
            <X v-if="mobileMenuOpen" :size="20" />
            <Menu v-else :size="20" />
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile drawer (teleported to body to escape sticky header stacking context) -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="mobileMenuOpen"
          class="md:hidden fixed inset-0 top-16 z-[60]"
          style="background: rgba(0,0,0,0.5);"
          @click.self="closeMobile"
        >
          <Transition
            enter-active-class="transition duration-250 ease-out"
            enter-from-class="translate-x-full"
            enter-to-class="translate-x-0"
            leave-active-class="transition duration-200 ease-in"
            leave-from-class="translate-x-0"
            leave-to-class="translate-x-full"
          >
            <div
              v-if="mobileMenuOpen"
              class="absolute right-0 top-0 bottom-0 w-72 flex flex-col border-l shadow-2xl"
              style="background: var(--color-card); border-color: var(--color-border);"
            >
              <!-- Mobile user info -->
              <div
                v-if="auth.isAuthenticated && auth.user"
                class="flex items-center gap-3 px-5 py-4 border-b"
                style="border-color: var(--color-border);"
              >
                <img
                  v-if="auth.user.avatar"
                  :src="auth.user.avatar"
                  :alt="auth.user.nickname"
                  class="w-10 h-10 rounded-full object-cover bg-surface-200"
                />
                <div
                  v-else
                  class="w-10 h-10 rounded-full bg-primary-500/15 text-primary-500 flex items-center justify-center"
                >
                  <User :size="18" />
                </div>
                <div class="min-w-0">
                  <div class="text-sm font-semibold truncate" style="color: var(--color-text);">
                    {{ auth.user.nickname || auth.user.username }}
                  </div>
                  <div class="text-xs truncate" style="color: var(--color-text-secondary);">
                    {{ auth.user.email }}
                  </div>
                </div>
              </div>

              <!-- Mobile nav links -->
              <nav class="flex-1 py-3 px-3 space-y-1 overflow-y-auto scrollbar-hide">
                <router-link
                  v-for="link in navLinks"
                  :key="link.name"
                  :to="link.to"
                  @click="closeMobile"
                  class="flex items-center px-4 py-2.5 rounded-xl text-sm font-medium transition-colors duration-200"
                  :class="isActive(link)
                    ? 'bg-primary-500/10 text-primary-500'
                    : 'hover:bg-[var(--color-hover)]'"
                  :style="!isActive(link) ? 'color: var(--color-text)' : ''"
                >
                  {{ link.label }}
                </router-link>

                <div class="border-t my-3" style="border-color: var(--color-border);"></div>

                <template v-if="auth.isAuthenticated && auth.user">
                  <router-link
                    to="/profile"
                    @click="closeMobile"
                    class="flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm transition-colors duration-200 hover:bg-[var(--color-hover)]"
                    style="color: var(--color-text);"
                  >
                    <User :size="16" style="color: var(--color-text-secondary);" />
                    个人中心
                  </router-link>
                  <button
                    @click="handleLogout(); closeMobile()"
                    class="flex items-center gap-3 w-full px-4 py-2.5 rounded-xl text-sm text-red-500 transition-colors duration-200 hover:bg-red-50 dark:hover:bg-red-500/10"
                  >
                    <LogOut :size="16" />
                    退出登录
                  </button>
                </template>

                <template v-else>
                  <router-link
                    to="/login"
                    @click="closeMobile"
                    class="flex items-center px-4 py-2.5 rounded-xl text-sm font-medium transition-colors duration-200 hover:bg-[var(--color-hover)]"
                    style="color: var(--color-text);"
                  >
                    登录
                  </router-link>
                  <div class="px-3 pt-1">
                    <router-link
                      to="/register"
                      @click="closeMobile"
                      class="btn-primary w-full text-sm !py-2.5"
                    >
                      注册
                    </router-link>
                  </div>
                </template>
              </nav>
            </div>
          </Transition>
        </div>
      </Transition>
    </Teleport>
  </header>
</template>
