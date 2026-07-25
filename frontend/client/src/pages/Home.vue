<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search, TrendingUp, Flame,
  ChevronRight, Star, Heart,
} from '@lucide/vue'
import { subjectsApi } from '@/api/subjects'
import { tagsApi } from '@/api/tags'
import { collectionsApi } from '@/api/collections'
import { useAuthStore } from '@/stores/auth'
import type { SubjectListItem } from '@/types'

const router = useRouter()
const authStore = useAuthStore()

const searchQuery = ref('')

// Data
const popularItems = ref<SubjectListItem[]>([])
const latestItems = ref<SubjectListItem[]>([])
const totalSubjects = ref(0)
const totalTags = ref(0)

// Loading states
const loadingPopular = ref(true)
const loadingLatest = ref(true)

// Current season computation
const currentYear = new Date().getFullYear()
const currentQuarter = computed(() => {
  const month = new Date().getMonth() + 1
  if (month <= 3) return 'winter'
  if (month <= 6) return 'spring'
  if (month <= 9) return 'summer'
  return 'fall'
})
// Weekday schedule
const weekdayLabels = ['一', '二', '三', '四', '五', '六', '日']
const weekdayValues  = [1, 2, 3, 4, 5, 6, 0] // Mon-Sun
const todayWeekday = new Date().getDay()
const activeWeekday = ref(todayWeekday) // default: today
const scheduleItems = ref<SubjectListItem[]>([])
const loadingSchedule = ref(true)
const scheduleCache = new Map<number, SubjectListItem[]>()

async function fetchSchedule(weekday: number) {
  if (scheduleCache.has(weekday)) {
    scheduleItems.value = scheduleCache.get(weekday)!
    return
  }
  loadingSchedule.value = true
  try {
    const res = await subjectsApi.getSchedule({
      weekday,
      year: currentYear,
      quarter: currentQuarter.value,
      page: 1,
      size: 50,
    })
    const items = res.data.data.content || []
    scheduleCache.set(weekday, items)
    if (activeWeekday.value === weekday) {
      scheduleItems.value = items
    }
  } catch {
    scheduleItems.value = []
  } finally {
    loadingSchedule.value = false
  }
}

const currentDaySchedule = computed(() => scheduleItems.value)

// Schedule filter: all / mine
const scheduleFilter = ref<'all' | 'mine'>('all')

const filteredSchedule = computed(() => {
  if (scheduleFilter.value === 'mine') {
    return currentDaySchedule.value.filter((item) => favoriteIds.value.has(item.id))
  }
  return currentDaySchedule.value
})

// Favorite (collect) state for the schedule cards
const favoriteIds = ref<Set<number>>(new Set())
const favLoading = ref<Set<number>>(new Set())

async function loadFavorites() {
  if (!authStore.isAuthenticated) return
  try {
    const res = await collectionsApi.getList({ page: 1, size: 200 })
    favoriteIds.value = new Set(res.data.data.content.map((c) => c.subjectId))
  } catch { /* silently fail */ }
}

function toggleFavorite(item: SubjectListItem) {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'Login' })
    return
  }
  if (favLoading.value.has(item.id)) return
  favLoading.value = new Set(favLoading.value).add(item.id)
  const isFav = favoriteIds.value.has(item.id)
  const action = isFav
    ? collectionsApi.remove(item.id)
    : collectionsApi.upsert(item.id, { type: 3 })
  action
    .then(() => {
      const next = new Set(favoriteIds.value)
      if (isFav) next.delete(item.id)
      else next.add(item.id)
      favoriteIds.value = next
    })
    .catch(() => { /* silently fail */ })
    .finally(() => {
      const next = new Set(favLoading.value)
      next.delete(item.id)
      favLoading.value = next
    })
}

function handleSearch() {
  const q = searchQuery.value.trim()
  if (q) router.push({ name: 'Search', query: { q } })
}

function formatCount(n: number): string {
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return n.toLocaleString()
}

// --- Fetch functions ---

async function fetchPopular() {
  loadingPopular.value = true
  try {
    const res = await subjectsApi.getList({ page: 1, size: 10, sort: 'collectionTotal', order: 'desc' })
    popularItems.value = res.data.data.content
    totalSubjects.value = res.data.data.total
  } catch {
    try {
      const res = await subjectsApi.getList({ page: 1, size: 10, sort: 'score', order: 'desc' })
      popularItems.value = res.data.data.content
      totalSubjects.value = res.data.data.total
    } catch { /* silently fail */ }
  } finally {
    loadingPopular.value = false
  }
}

async function fetchLatest() {
  loadingLatest.value = true
  try {
    const res = await subjectsApi.getList({ page: 1, size: 10, sort: 'airDate', order: 'desc' })
    latestItems.value = res.data.data.content
  } catch { /* silently fail */ }
  finally {
    loadingLatest.value = false
  }
}

watch(activeWeekday, (wd) => fetchSchedule(wd))

async function fetchTags() {
  try {
    const res = await tagsApi.getList()
    totalTags.value = res.data.data.length
  } catch { /* silently fail */ }
}

onMounted(() => {
  fetchPopular()
  fetchLatest()
  fetchSchedule(todayWeekday)
  fetchTags()
  loadFavorites()
})
</script>

<template>
  <div>
    <!-- Hero Section -->
    <section class="relative overflow-hidden py-16 md:py-24">
      <div class="app-container relative z-10">
        <div class="mx-auto max-w-2xl text-center">
          <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-4 text-balance" style="color: var(--color-text)">
            发现你的下一部番剧
          </h1>
          <p class="text-base md:text-lg mb-8 text-balance" style="color: var(--color-text-secondary)">
            聚合 Bangumi 等数据源，帮助你全面了解每一部番剧
          </p>
          <div class="relative mx-auto max-w-xl">
            <Search class="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5" style="color: var(--color-text-secondary)" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索动画作品..."
              class="input-field pl-12 pr-14 sm:pr-28 py-4 text-sm sm:text-base rounded-full"
              @keyup.enter="handleSearch"
            />
            <button
              class="btn-primary absolute right-2 top-1/2 -translate-y-1/2 px-3 sm:px-5 py-2"
              @click="handleSearch"
            >
              <Search class="sm:hidden h-4 w-4" />
              <span class="hidden sm:inline">搜索</span>
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats Row -->
    <section class="app-container -mt-4 mb-12 relative z-20">
      <div class="grid grid-cols-3 md:grid-cols-3 gap-3 md:gap-4 max-w-3xl mx-auto">
        <div class="app-card p-3 sm:p-4 text-center">
          <div class="text-xl sm:text-2xl font-bold text-primary-600 dark:text-primary-400">{{ formatCount(totalSubjects) }}</div>
          <div class="text-xs mt-1" style="color: var(--color-text-secondary)">番剧条目</div>
        </div>
        <div class="app-card p-3 sm:p-4 text-center">
          <div class="text-xl sm:text-2xl font-bold" style="color: var(--color-text)">{{ totalTags.toLocaleString() }}</div>
          <div class="text-xs mt-1" style="color: var(--color-text-secondary)">标签分类</div>
        </div>
        <div class="app-card p-3 sm:p-4 text-center">
          <div class="text-xl sm:text-2xl font-bold" style="color: var(--color-text)">1+</div>
          <div class="text-xs mt-1" style="color: var(--color-text-secondary)">数据来源</div>
        </div>
      </div>
    </section>

    <!-- 每周追番 -->
    <section class="app-container mb-14">
      <div class="flex items-center justify-between mb-5">
        <h2 class="section-title">每周追番</h2>
        <router-link
          :to="`/season/${currentYear}/${currentQuarter}`"
          class="inline-flex items-center gap-0.5 text-sm transition-colors hover:text-[var(--color-primary)]"
          style="color: var(--color-text-secondary)"
        >
          查看全部 <ChevronRight class="h-4 w-4" />
        </router-link>
      </div>

      <!-- Weekday tabs + filter tabs -->
      <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
        <!-- Filter tabs + count -->
        <div class="flex items-center gap-2">
          <div class="inline-flex items-center gap-1 rounded-full p-1" style="background: var(--color-hover)">
            <button
              class="rounded-full px-3 py-1 text-xs font-medium transition-colors duration-150 sm:px-4 sm:text-sm"
              :class="scheduleFilter === 'all'
                ? 'bg-primary-600 text-white shadow-sm'
                : ''"
              :style="scheduleFilter !== 'all' ? 'color: var(--color-text-secondary)' : ''"
              @click="scheduleFilter = 'all'"
            >
              全部
            </button>
            <button
              class="rounded-full px-3 py-1 text-xs font-medium transition-colors duration-150 sm:px-4 sm:text-sm"
              :class="scheduleFilter === 'mine'
                ? 'bg-primary-600 text-white shadow-sm'
                : ''"
              :style="scheduleFilter !== 'mine' ? 'color: var(--color-text-secondary)' : ''"
              @click="scheduleFilter = 'mine'"
            >
              我的
            </button>
          </div>
          <span class="text-xs font-medium sm:text-sm" style="color: var(--color-text-secondary)">
            {{ filteredSchedule.length }} 部
          </span>
        </div>

        <!-- Weekday tabs -->
        <div class="flex items-center gap-1 flex-wrap">
          <button
            v-for="(label, idx) in weekdayLabels"
            :key="idx"
            class="relative rounded-full px-2.5 py-1.5 text-sm font-medium transition-colors duration-150 sm:px-3"
            :class="activeWeekday === weekdayValues[idx]
              ? 'bg-primary-600 text-white shadow-sm'
              : 'hover:text-[var(--color-primary)]'"
            :style="activeWeekday !== weekdayValues[idx] ? 'background: var(--color-hover); color: var(--color-text-secondary)' : ''"
            @click="activeWeekday = weekdayValues[idx]"
          >
            <span class="sm:hidden">{{ label }}</span>
            <span class="hidden sm:inline">周{{ label }}</span>
          </button>
        </div>
      </div>

      <!-- Schedule poster grid -->
      <div v-if="loadingSchedule" class="grid grid-cols-2 gap-x-4 gap-y-5 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        <div v-for="i in 10" :key="i" class="app-skeleton aspect-[2/3] rounded-xl" />
      </div>
      <div v-else-if="filteredSchedule.length" class="grid grid-cols-2 gap-x-4 gap-y-5 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        <article v-for="item in filteredSchedule" :key="item.id" class="group relative flex flex-col">
          <div class="relative w-full shrink-0">
            <router-link
              :to="`/subject/${item.id}`"
              class="relative block w-full overflow-hidden rounded-xl aspect-[2/3]"
              style="background: var(--color-hover)"
            >
              <img
                v-if="item.image"
                :src="item.image"
                :alt="item.nameCn || item.name"
                class="absolute inset-0 h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
              />
              <div
                v-else
                class="absolute inset-0 flex items-center justify-center text-3xl font-bold opacity-20"
                style="color: var(--color-text)"
              >
                {{ (item.nameCn || item.name)?.charAt(0) || '?' }}
              </div>
            </router-link>
            <!-- Favorite button -->
            <button
              type="button"
              class="absolute right-2 top-2 z-20 inline-flex h-9 w-9 items-center justify-center rounded-full border shadow-md shadow-black/10 backdrop-blur-sm transition-colors hover:border-[var(--color-primary)]"
              :style="favoriteIds.has(item.id)
                ? 'background: var(--color-card); border-color: var(--color-primary); color: var(--color-primary)'
                : 'background: var(--color-card); border-color: var(--color-border); color: var(--color-text-secondary)'"
              :title="favoriteIds.has(item.id) ? '取消收藏' : '加入收藏'"
              @click.stop="toggleFavorite(item)"
            >
              <Heart class="h-5 w-5" :fill="favoriteIds.has(item.id) ? 'currentColor' : 'none'" />
            </button>
          </div>
          <router-link
            :to="`/subject/${item.id}`"
            class="mt-2 truncate text-base font-normal leading-snug transition-colors duration-150 group-hover:text-[var(--color-primary)]"
            style="color: var(--color-text)"
            :title="item.nameCn || item.name"
          >
            {{ item.nameCn || item.name }}
          </router-link>
          <div class="mt-1 flex items-center justify-between text-sm" style="color: var(--color-text-secondary)">
            <span class="min-w-0 truncate">{{ item.eps ? '全 ' + item.eps + ' 话' : (item.airDate || '') }}</span>
            <span v-if="item.score > 0" class="inline-flex shrink-0 items-center gap-1">
              <Star class="h-3.5 w-3.5" />
              {{ item.score.toFixed(1) }}
            </span>
          </div>
        </article>
      </div>
      <div v-else class="app-card p-8 text-center" style="background: var(--color-card); border: 1px solid var(--color-border)">
        <p style="color: var(--color-text-secondary)">
          {{ scheduleFilter === 'mine' ? '当天暂无我的收藏' : '暂无追番数据' }}
        </p>
      </div>
    </section>

    <!-- Rankings: 热度榜 + 评分榜 -->
    <section class="app-container mb-16">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- 热度榜 -->
        <div class="app-card p-5">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
              <Flame class="h-5 w-5 text-orange-500" />
              <h2 class="text-lg font-bold" style="color: var(--color-text)">热度榜</h2>
            </div>
            <router-link
              to="/search?sort=collectionTotal"
              class="inline-flex items-center gap-1 text-xs text-primary-600 dark:text-primary-400 hover:underline"
            >
              查看全部 <ChevronRight class="h-3 w-3" />
            </router-link>
          </div>
          <div v-if="loadingPopular" class="space-y-3">
            <div v-for="i in 10" :key="i" class="flex items-center gap-3">
              <div class="app-skeleton w-6 h-6 rounded-md" />
              <div class="app-skeleton h-4 flex-1 rounded" />
              <div class="app-skeleton w-12 h-4 rounded" />
            </div>
          </div>
          <ol v-else class="space-y-1">
            <li v-for="(item, index) in popularItems" :key="item.id">
              <router-link
                :to="`/subject/${item.id}`"
                class="flex items-center gap-3 py-2 px-2 -mx-2 rounded-lg transition-colors duration-150"
                style="color: var(--color-text)"
              >
                <span
                  class="shrink-0 w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold"
                  :class="index < 3 ? 'bg-gradient-to-br from-orange-400 to-red-500 text-white' : ''"
                  :style="index >= 3 ? 'background: var(--color-hover); color: var(--color-text-secondary)' : ''"
                >
                  {{ index + 1 }}
                </span>
                <span class="flex-1 text-sm truncate" :title="item.nameCn || item.name">
                  {{ item.nameCn || item.name }}
                </span>
                <span class="shrink-0 text-xs tabular-nums" style="color: var(--color-text-secondary)">
                  {{ formatCount(item.score > 0 ? item.score * 1000 : 0) }}
                </span>
              </router-link>
            </li>
          </ol>
        </div>

        <!-- 评分榜 -->
        <div class="app-card p-5">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-2">
              <TrendingUp class="h-5 w-5 text-primary-500" />
              <h2 class="text-lg font-bold" style="color: var(--color-text)">评分榜</h2>
            </div>
            <router-link
              to="/search?sort=score"
              class="inline-flex items-center gap-1 text-xs text-primary-600 dark:text-primary-400 hover:underline"
            >
              查看全部 <ChevronRight class="h-3 w-3" />
            </router-link>
          </div>
          <div v-if="loadingLatest" class="space-y-3">
            <div v-for="i in 10" :key="i" class="flex items-center gap-3">
              <div class="app-skeleton w-6 h-6 rounded-md" />
              <div class="app-skeleton h-4 flex-1 rounded" />
              <div class="app-skeleton w-12 h-4 rounded" />
            </div>
          </div>
          <ol v-else class="space-y-1">
            <li v-for="(item, index) in latestItems" :key="item.id">
              <router-link
                :to="`/subject/${item.id}`"
                class="flex items-center gap-3 py-2 px-2 -mx-2 rounded-lg transition-colors duration-150"
                style="color: var(--color-text)"
              >
                <span
                  class="shrink-0 w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold"
                  :class="index < 3 ? 'bg-gradient-to-br from-primary-400 to-primary-600 text-white' : ''"
                  :style="index >= 3 ? 'background: var(--color-hover); color: var(--color-text-secondary)' : ''"
                >
                  {{ index + 1 }}
                </span>
                <span class="flex-1 text-sm truncate" :title="item.nameCn || item.name">
                  {{ item.nameCn || item.name }}
                </span>
                <span v-if="item.score > 0" class="shrink-0 badge-score text-[11px]">
                  {{ item.score.toFixed(1) }}
                </span>
              </router-link>
            </li>
          </ol>
        </div>
      </div>
    </section>

    <!-- Disclaimer -->
    <section class="app-container mb-8">
      <p class="text-center text-xs" style="color: var(--color-text-secondary); opacity: 0.6">
        本站仅提供番剧信息查询，不提供任何视频播放或下载服务
      </p>
    </section>
  </div>
</template>
