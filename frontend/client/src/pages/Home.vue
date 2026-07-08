<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Search, TrendingUp, Flame, CalendarDays,
  ChevronRight, Radio, Users,
} from '@lucide/vue'
import { subjectsApi } from '@/api/subjects'
import { tagsApi } from '@/api/tags'
import type { SubjectListItem, SubjectDetail } from '@/types'
import SubjectCard from '@/components/SubjectCard.vue'
import SubjectCardSkeleton from '@/components/SubjectCardSkeleton.vue'

const router = useRouter()

const searchQuery = ref('')

// Data
const popularItems = ref<SubjectListItem[]>([])
const latestItems = ref<SubjectListItem[]>([])
const seasonalItems = ref<SubjectListItem[]>([])
const scheduleItems = ref<SubjectDetail[]>([])
const totalSubjects = ref(0)
const totalTags = ref(0)
const seasonTotal = ref(0)

// Loading states
const loadingPopular = ref(true)
const loadingLatest = ref(true)
const loadingSeasonal = ref(true)
const loadingSchedule = ref(true)

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
const weekdayLabels = ['全部', '一', '二', '三', '四', '五', '六', '日']
const weekdayValues  = [-1, 1, 2, 3, 4, 5, 6, 0] // -1=all, then Mon-Sun
const todayWeekday = new Date().getDay()
const activeWeekday = ref(-1) // default: show all

const scheduleByWeekday = computed(() => {
  const groups: Record<number, SubjectDetail[]> = { 0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [] }
  for (const item of scheduleItems.value) {
    if (item.airWeekday != null && item.airWeekday >= 0 && item.airWeekday <= 6) {
      groups[item.airWeekday].push(item)
    }
  }
  for (const key of Object.keys(groups)) {
    groups[Number(key)].sort((a, b) => (b.score || 0) - (a.score || 0))
  }
  return groups
})

const currentDaySchedule = computed(() => {
  if (activeWeekday.value === -1) {
    // "全部" - return all schedule items sorted by score
    return [...scheduleItems.value].sort((a, b) => (b.score || 0) - (a.score || 0))
  }
  return scheduleByWeekday.value[activeWeekday.value] || []
})

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

async function fetchSchedule() {
  loadingSchedule.value = true
  try {
    // Fetch seasonal anime list to get IDs
    const res = await subjectsApi.getBySeason({
      year: currentYear,
      quarter: currentQuarter.value,
      page: 1,
      size: 60,
    })
    // Fetch details in parallel to get airWeekday
    const details = await Promise.all(
      res.data.data.content.map(item =>
        subjectsApi.getDetail(item.id).then(r => r.data.data).catch(() => null)
      )
    )
    scheduleItems.value = details.filter((d): d is SubjectDetail => d !== null)
  } catch { /* silently fail */ }
  finally {
    loadingSchedule.value = false
  }
}

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
  fetchSchedule()
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
              class="input-field pl-12 pr-28 py-4 text-base rounded-full"
              @keyup.enter="handleSearch"
            />
            <button
              class="btn-primary absolute right-2 top-1/2 -translate-y-1/2 px-5 py-2"
              @click="handleSearch"
            >
              搜索
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats Row -->
    <section class="app-container -mt-4 mb-12 relative z-20">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 max-w-3xl mx-auto">
        <div class="app-card p-4 text-center" style="background: var(--color-card); border: 1px solid var(--color-border)">
          <div class="text-2xl font-bold text-primary-600 dark:text-primary-400">{{ formatCount(totalSubjects) }}</div>
          <div class="text-xs mt-1" style="color: var(--color-text-secondary)">番剧条目</div>
        </div>
        <div class="app-card p-4 text-center" style="background: var(--color-card); border: 1px solid var(--color-border)">
          <div class="text-2xl font-bold" style="color: var(--color-text)">{{ seasonTotal }}</div>
          <div class="text-xs mt-1" style="color: var(--color-text-secondary)">本季新番</div>
        </div>
        <div class="app-card p-4 text-center" style="background: var(--color-card); border: 1px solid var(--color-border)">
          <div class="text-2xl font-bold" style="color: var(--color-text)">{{ totalTags.toLocaleString() }}</div>
          <div class="text-xs mt-1" style="color: var(--color-text-secondary)">标签分类</div>
        </div>
        <div class="app-card p-4 text-center" style="background: var(--color-card); border: 1px solid var(--color-border)">
          <div class="text-2xl font-bold" style="color: var(--color-text)">1+</div>
          <div class="text-xs mt-1" style="color: var(--color-text-secondary)">数据来源</div>
        </div>
      </div>
    </section>

    <!-- 每周追番 -->
    <section class="app-container mb-14">
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <Radio class="h-5 w-5 text-accent-pink" />
          <h2 class="section-title">每周追番</h2>
          <span class="badge" style="background: rgba(241,121,146,0.1); color: #f17992">{{ seasonLabel }}</span>
        </div>
      </div>

      <!-- Weekday tabs -->
      <div class="flex items-center gap-1.5 mb-5 overflow-x-auto scrollbar-hide">
        <button
          v-for="(label, idx) in weekdayLabels"
          :key="idx"
          class="relative shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200"
          :class="activeWeekday === weekdayValues[idx]
            ? 'bg-primary-600 text-white shadow-sm'
            : ''"
          :style="activeWeekday !== weekdayValues[idx] ? 'background: var(--color-hover); color: var(--color-text-secondary)' : ''"
          @click="activeWeekday = weekdayValues[idx]"
        >
          {{ label }}
          <span
            v-if="weekdayValues[idx] === todayWeekday"
            class="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-accent-pink"
          />
        </button>
        <span class="ml-2 text-xs" style="color: var(--color-text-secondary)">
          {{ currentDaySchedule.length }} 部
        </span>
      </div>

      <!-- Schedule list -->
      <div v-if="loadingSchedule" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        <div v-for="i in 9" :key="i" class="app-skeleton h-[72px] rounded-xl" />
      </div>
      <div v-else-if="currentDaySchedule.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        <router-link
          v-for="item in currentDaySchedule"
          :key="item.id"
          :to="`/subject/${item.id}`"
          class="group app-card flex items-center gap-3 p-3 rounded-xl transition-all duration-200"
        >
          <!-- Thumbnail -->
          <div class="shrink-0 w-12 h-16 rounded-lg overflow-hidden">
            <img
              v-if="item.image"
              :src="item.image"
              :alt="item.nameCn || item.name"
              class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-110"
            />
            <div
              v-else
              class="h-full w-full flex items-center justify-center text-xs font-bold opacity-20"
              style="background: var(--color-hover); color: var(--color-text)"
            >
              {{ (item.nameCn || item.name)?.charAt(0) || '?' }}
            </div>
          </div>
          <!-- Info -->
          <div class="flex-1 min-w-0">
            <h4
              class="text-sm font-medium truncate group-hover:text-primary-600 transition-colors"
              style="color: var(--color-text)"
              :title="item.nameCn || item.name"
            >
              {{ item.nameCn || item.name }}
            </h4>
            <div class="flex items-center gap-3 mt-1.5">
              <span v-if="item.collectionTotal" class="inline-flex items-center gap-1 text-[11px]" style="color: var(--color-text-secondary)">
                <Users class="h-3 w-3" />
                {{ formatCount(item.collectionTotal) }}
              </span>
              <span v-if="item.score > 0" class="badge-score text-[11px]">
                {{ item.score.toFixed(1) }}分
              </span>
            </div>
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
      <div v-else-if="seasonalItems.length" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
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
