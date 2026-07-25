<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search, TrendingUp, Flame, CalendarDays,
  ChevronRight, Heart, XCircle,
  Hash, Calendar,
} from '@lucide/vue'
import { subjectsApi } from '@/api/subjects'
import { tagsApi } from '@/api/tags'
import { collectionsApi } from '@/api/collections'
import { useAuthStore } from '@/stores/auth'
import type { SubjectListItem } from '@/types'
import SubjectCard from '@/components/SubjectCard.vue'
import SubjectCardSkeleton from '@/components/SubjectCardSkeleton.vue'

const router = useRouter()
const authStore = useAuthStore()

const searchQuery = ref('')

// Data
const popularItems = ref<SubjectListItem[]>([])
const latestItems = ref<SubjectListItem[]>([])
const seasonalItems = ref<SubjectListItem[]>([])
const totalSubjects = ref(0)
const totalTags = ref(0)
const seasonTotal = ref(0)

// Loading states
const loadingPopular = ref(true)
const loadingLatest = ref(true)
const loadingSeasonal = ref(true)

// Current season computation
const currentYear = new Date().getFullYear()
const currentQuarter = computed(() => {
  const month = new Date().getMonth() + 1
  if (month <= 3) return 'winter'
  if (month <= 6) return 'spring'
  if (month <= 9) return 'summer'
  return 'fall'
})
const seasonLabel = computed(() => {
  const map: Record<string, string> = {
    winter: '冬季', spring: '春季', summer: '夏季', fall: '秋季',
  }
  return `${currentYear}年${map[currentQuarter.value]}`
})

// Weekday schedule
const weekdayLabels = ['一', '二', '三', '四', '五', '六', '日']
const weekdayValues  = [1, 2, 3, 4, 5, 6, 0] // Mon-Sun
const todayWeekday = new Date().getDay()

type ScheduleTab = 'today' | 'all' | 'my' | `${number}`
const scheduleTabs: Array<{ key: ScheduleTab; label: string }> = [
  { key: 'today', label: '今日放送' },
  { key: 'all', label: '全部' },
  { key: 'my', label: '我的' },
  ...weekdayValues.map((wd, idx) => ({ key: String(wd) as ScheduleTab, label: `周${weekdayLabels[idx]}` })),
]
const activeScheduleTab = ref<ScheduleTab>('today')
const scheduleItems = ref<SubjectListItem[]>([])
const loadingSchedule = ref(true)
const scheduleCache = new Map<number, SubjectListItem[]>()

const collectedSubjectIds = ref<Set<number>>(new Set())
const userCollectionsLoaded = ref(false)
const collectionError = ref('')

const allScheduleItems = computed(() => {
  const map = new Map<number, SubjectListItem>()
  for (const wd of weekdayValues) {
    const items = scheduleCache.get(wd) || []
    for (const item of items) map.set(item.id, item)
  }
  // 全部缓存(-1)已经包含去重后的数据，优先使用
  const allCached = scheduleCache.get(-1)
  if (allCached?.length) return allCached
  return Array.from(map.values())
})

const myScheduleItems = computed(() => {
  return allScheduleItems.value.filter(item => collectedSubjectIds.value.has(item.id))
})

const currentScheduleItems = computed(() => {
  if (activeScheduleTab.value === 'all') return allScheduleItems.value
  if (activeScheduleTab.value === 'my') return myScheduleItems.value
  if (activeScheduleTab.value === 'today') return scheduleCache.get(todayWeekday) || []
  const wd = parseInt(activeScheduleTab.value, 10)
  return scheduleCache.get(wd) || []
})

const currentScheduleCount = computed(() => currentScheduleItems.value.length)

async function fetchSchedule(weekday: number = -1) {
  if (scheduleCache.has(weekday)) {
    if (
      activeScheduleTab.value === (weekday === -1 ? 'all' : String(weekday)) ||
      (weekday === todayWeekday && activeScheduleTab.value === 'today') ||
      (activeScheduleTab.value === 'my' && weekday === -1)
    ) {
      scheduleItems.value = scheduleCache.get(weekday)!
    }
    return
  }
  loadingSchedule.value = true
  try {
    const params: Record<string, any> = {
      year: currentYear,
      quarter: currentQuarter.value,
      page: 1,
      size: 200,
    }
    if (weekday !== -1) params.weekday = weekday
    const res = await subjectsApi.getSchedule(params)
    const items = res.data.data.content || []
    scheduleCache.set(weekday, items)
    if (
      activeScheduleTab.value === (weekday === -1 ? 'all' : String(weekday)) ||
      (weekday === todayWeekday && activeScheduleTab.value === 'today') ||
      (activeScheduleTab.value === 'my' && weekday === -1)
    ) {
      scheduleItems.value = items
    }
  } catch {
    if (activeScheduleTab.value === (weekday === -1 ? 'all' : String(weekday))) {
      scheduleItems.value = []
    }
  } finally {
    loadingSchedule.value = false
  }
}

async function fetchUserCollections() {
  if (!authStore.isAuthenticated) return
  try {
    const res = await collectionsApi.getList({ page: 1, size: 1000 })
    const ids = new Set<number>()
    for (const c of res.data.data.content || []) {
      ids.add(c.subjectId)
    }
    collectedSubjectIds.value = ids
    userCollectionsLoaded.value = true
  } catch { /* silently fail */ }
}

async function toggleCollection(item: SubjectListItem, event: MouseEvent) {
  event.preventDefault()
  event.stopPropagation()
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  collectionError.value = ''
  try {
    if (collectedSubjectIds.value.has(item.id)) {
      await collectionsApi.remove(item.id)
      collectedSubjectIds.value.delete(item.id)
    } else {
      await collectionsApi.upsert(item.id, { type: 3 })
      collectedSubjectIds.value.add(item.id)
    }
  } catch (e: any) {
    collectionError.value = e?.response?.data?.message || '操作失败'
    setTimeout(() => { collectionError.value = '' }, 3000)
  }
}

function isTabActive(tab: { key: ScheduleTab }) {
  return activeScheduleTab.value === tab.key
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

async function fetchSeasonal() {
  loadingSeasonal.value = true
  try {
    const res = await subjectsApi.getBySeason({
      year: currentYear,
      quarter: currentQuarter.value,
      page: 1,
      size: 12,
    })
    seasonalItems.value = res.data.data.content
    seasonTotal.value = res.data.data.total
  } catch { /* silently fail */ }
  finally {
    loadingSeasonal.value = false
  }
}

watch(activeScheduleTab, (tab) => {
  if (tab === 'all') fetchSchedule(-1)
  else if (tab === 'today') fetchSchedule(todayWeekday)
  else if (tab === 'my') {
    if (!userCollectionsLoaded.value) fetchUserCollections()
    fetchSchedule(-1)
  }
  else fetchSchedule(parseInt(tab, 10))
})

async function fetchTags() {
  try {
    const res = await tagsApi.getList()
    totalTags.value = res.data.data.length
  } catch { /* silently fail */ }
}

onMounted(() => {
  fetchPopular()
  fetchLatest()
  fetchSeasonal()
  fetchSchedule(todayWeekday)
  fetchUserCollections()
  fetchTags()
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
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 max-w-3xl mx-auto">
        <div class="app-card p-3 sm:p-4 text-center">
          <div class="text-xl sm:text-2xl font-bold text-primary-600 dark:text-primary-400">{{ formatCount(totalSubjects) }}</div>
          <div class="text-xs mt-1" style="color: var(--color-text-secondary)">番剧条目</div>
        </div>
        <div class="app-card p-3 sm:p-4 text-center">
          <div class="text-xl sm:text-2xl font-bold" style="color: var(--color-text)">{{ seasonTotal }}</div>
          <div class="text-xs mt-1" style="color: var(--color-text-secondary)">本季新番</div>
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
      <!-- Collection error toast -->
      <Transition name="slide-fade">
        <div
          v-if="collectionError"
          class="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center gap-2 text-sm text-red-600 dark:text-red-400"
        >
          <XCircle class="h-4 w-4 shrink-0" />
          {{ collectionError }}
        </div>
      </Transition>

      <!-- Header -->
      <div class="flex items-center justify-between mb-4 gap-4">
        <div class="flex items-center gap-1.5 overflow-x-auto scrollbar-hide pb-1">
          <button
            v-for="tab in scheduleTabs"
            :key="tab.key"
            class="schedule-tab"
            :class="{
              active: isTabActive(tab),
              today: tab.key !== 'today' && tab.key !== 'all' && tab.key !== 'my' && parseInt(tab.key, 10) === todayWeekday,
            }"
            @click="activeScheduleTab = tab.key"
          >
            {{ tab.label }}
          </button>
          <span class="schedule-count">{{ currentScheduleCount }}部</span>
        </div>
        <router-link
          :to="`/season/${currentYear}/${currentQuarter}`"
          class="hidden sm:inline-flex items-center gap-0.5 text-sm shrink-0 transition-colors hover:text-primary-500"
          style="color: var(--color-text-secondary)"
        >
          查看全部
          <ChevronRight class="h-4 w-4" />
        </router-link>
      </div>

      <!-- Schedule grid -->
      <div v-if="loadingSchedule" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
        <div v-for="i in 10" :key="i" class="schedule-card-skeleton">
          <div class="app-skeleton aspect-poster rounded-xl" />
          <div class="app-skeleton h-4 w-3/4 rounded mt-2" />
          <div class="app-skeleton h-3 w-1/2 rounded mt-1" />
        </div>
      </div>
      <div v-else-if="currentScheduleItems.length" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
        <router-link
          v-for="item in currentScheduleItems"
          :key="item.id"
          :to="`/subject/${item.id}`"
          class="schedule-card group"
        >
          <!-- Poster -->
          <div class="relative aspect-poster rounded-xl overflow-hidden mb-2">
            <img
              v-if="item.image"
              :src="item.image"
              :alt="item.nameCn || item.name"
              class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
            />
            <div
              v-else
              class="absolute inset-0 flex items-center justify-center"
              style="background: var(--color-hover)"
            >
              <span class="text-3xl font-bold opacity-20" style="color: var(--color-text)">{{ (item.nameCn || item.name)?.charAt(0) || '?' }}</span>
            </div>
            <!-- Favorite button -->
            <button
              class="favorite-btn"
              :class="{ active: collectedSubjectIds.has(item.id) }"
              @click="toggleCollection(item, $event)"
            >
              <Heart class="h-4 w-4" :class="collectedSubjectIds.has(item.id) ? 'fill-current' : ''" />
            </button>
          </div>
          <!-- Info -->
          <h3 class="schedule-title" :title="item.nameCn || item.name">
            {{ item.nameCn || item.name }}
          </h3>
          <div class="schedule-meta">
            <span v-if="item.eps" class="inline-flex items-center gap-1">
              <Hash class="h-3 w-3" />
              第 {{ item.eps }} 话
            </span>
            <span v-else-if="item.airDate" class="inline-flex items-center gap-1">
              <Calendar class="h-3 w-3" />
              {{ item.airDate }}
            </span>
          </div>
        </router-link>
      </div>
      <div v-else class="app-card p-8 text-center" style="background: var(--color-card); border: 1px solid var(--color-border)">
        <p style="color: var(--color-text-secondary)">暂无追番数据</p>
      </div>
    </section>

    <!-- 本季新番 -->
    <section class="app-container mb-14">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <CalendarDays class="h-5 w-5 text-primary-500" />
          <h2 class="section-title">本季新番</h2>
          <span class="badge">{{ seasonLabel }}</span>
        </div>
        <router-link
          :to="`/season/${currentYear}/${currentQuarter}`"
          class="inline-flex items-center gap-1 text-sm text-primary-600 dark:text-primary-400 hover:underline"
        >
          查看全部 <ChevronRight class="h-4 w-4" />
        </router-link>
      </div>
      <div v-if="loadingSeasonal" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
        <SubjectCardSkeleton v-for="i in 12" :key="i" />
      </div>
      <div v-else-if="seasonalItems.length" class="card-grid-responsive grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
        <SubjectCard v-for="item in seasonalItems" :key="item.id" :subject="item" />
      </div>
      <div v-else class="app-card p-8 text-center" style="background: var(--color-card); border: 1px solid var(--color-border)">
        <p style="color: var(--color-text-secondary)">暂无本季新番数据</p>
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

.schedule-tab {
  @apply shrink-0 px-3.5 py-1.5 rounded-full text-sm font-medium transition-all duration-200;
  background: var(--color-hover);
  color: var(--color-text-secondary);
}
.schedule-tab:hover {
  color: var(--color-text);
}
.schedule-tab.active {
  background: rgba(241, 121, 146, 0.9);
  color: white;
}
.schedule-tab.today:not(.active) {
  color: #f17992;
}

.schedule-count {
  @apply shrink-0 text-xs font-medium px-2 py-1 rounded-full;
  background: rgba(241, 121, 146, 0.1);
  color: #f17992;
}

.schedule-card {
  @apply block transition-transform duration-200;
}
.schedule-card:hover {
  transform: translateY(-2px);
}

.schedule-title {
  @apply text-sm font-medium leading-snug line-clamp-2;
  color: var(--color-text);
}

.schedule-meta {
  @apply flex items-center gap-2 mt-1 text-xs;
  color: var(--color-text-secondary);
}

.favorite-btn {
  @apply absolute top-2 right-2 w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200;
  background: rgba(0, 0, 0, 0.35);
  color: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(2px);
}
.favorite-btn:hover {
  background: rgba(0, 0, 0, 0.5);
  transform: scale(1.1);
}
.favorite-btn.active {
  background: rgba(241, 121, 146, 0.9);
  color: white;
}

.schedule-card-skeleton {
  @apply flex flex-col;
}

.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>
