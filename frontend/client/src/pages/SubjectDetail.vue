<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft, Star, Trophy, Calendar, Tv, Hash, ExternalLink,
  Heart, ChevronDown, ChevronUp, Plus, Minus, Trash2, Bookmark, XCircle,
  ChevronLeft, ChevronRight, Play, Info,
} from '@lucide/vue'
import { subjectsApi } from '@/api/subjects'
import { collectionsApi, type UserCollectionVO, type UpsertCollectionRequest } from '@/api/collections'
import { useAuthStore } from '@/stores/auth'
import type { SubjectDetail, EpisodeVO } from '@/types'
import { SUBJECT_TYPES, WEEKDAYS } from '@/types'
import TagBadge from '@/components/TagBadge.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const EPISODES_PER_RANGE = 100
const COLLECTION_ACTIONS = [
  { type: 1, label: '想看' },
  { type: 3, label: '在看' },
  { type: 2, label: '看过' },
  { type: 4, label: '搁置' },
  { type: 5, label: '抛弃' },
]

const subject = ref<SubjectDetail | null>(null)
const episodes = ref<EpisodeVO[]>([])
const loading = ref(true)
const error = ref('')
const summaryExpanded = ref(false)

const collection = ref<UserCollectionVO | null>(null)
const collectionLoading = ref(false)
const collectionError = ref('')
const showDeleteConfirm = ref(false)
const showCollectionMenu = ref(false)
const collectionWrapperRef = ref<HTMLElement | null>(null)

const activeEpisodeRange = ref(0)
const jumpEpisodeInput = ref('')

const subjectId = computed(() => parseInt(route.params.id as string, 10))

const typeName = computed(() => {
  if (!subject.value) return ''
  return SUBJECT_TYPES[subject.value.type] || `类型 ${subject.value.type}`
})

const weekdayName = computed(() => {
  if (!subject.value) return ''
  return WEEKDAYS[subject.value.airWeekday] || ''
})

const summaryIsLong = computed(() => {
  return subject.value?.summary ? subject.value.summary.length > 300 : false
})

const displaySummary = computed(() => {
  if (!subject.value?.summary) return ''
  if (summaryIsLong.value && !summaryExpanded.value) {
    return subject.value.summary.slice(0, 300) + '...'
  }
  return subject.value.summary
})

const bangumiUrl = computed(() => {
  if (!subject.value?.bangumiId) return ''
  return `https://bgm.tv/subject/${subject.value.bangumiId}`
})

const airYear = computed(() => {
  if (!subject.value?.airDate) return ''
  const y = new Date(subject.value.airDate).getFullYear()
  return isNaN(y) ? subject.value.airDate.slice(0, 4) : String(y)
})

const episodeRanges = computed(() => {
  const total = subject.value?.eps || episodes.value.length || 0
  if (!total) return []
  const ranges: Array<{ start: number; end: number }> = []
  for (let start = 1; start <= total; start += EPISODES_PER_RANGE) {
    const end = Math.min(start + EPISODES_PER_RANGE - 1, total)
    ranges.push({ start, end })
  }
  return ranges
})

const visibleRange = computed(() => episodeRanges.value[activeEpisodeRange.value] || null)

const visibleEpisodeNumbers = computed(() => {
  if (!visibleRange.value) return []
  const list: number[] = []
  for (let i = visibleRange.value.start; i <= visibleRange.value.end; i++) {
    list.push(i)
  }
  return list
})

const collectionLabel = computed(() => {
  if (!collection.value) return ''
  return COLLECTION_ACTIONS.find(a => a.type === collection.value!.type)?.label || ''
})

async function fetchDetail() {
  loading.value = true
  error.value = ''
  try {
    const [detailRes, episodesRes] = await Promise.all([
      subjectsApi.getDetail(subjectId.value),
      subjectsApi.getEpisodes(subjectId.value),
    ])
    subject.value = detailRes.data.data
    episodes.value = episodesRes.data.data
    activeEpisodeRange.value = 0
  } catch (e: any) {
    error.value = e?.response?.data?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}

async function fetchCollection() {
  if (!authStore.isAuthenticated) return
  try {
    const res = await collectionsApi.getDetail(subjectId.value)
    collection.value = res.data.data
  } catch {
    collection.value = null
  }
}

async function handleUpsert(type: number) {
  if (!authStore.isAuthenticated) {
    collectionError.value = '请先登录'
    setTimeout(() => { collectionError.value = '' }, 3000)
    return
  }
  collectionLoading.value = true
  collectionError.value = ''
  try {
    const data: UpsertCollectionRequest = { type }
    if (collection.value) {
      data.rate = collection.value.rate
      data.epStatus = collection.value.epStatus
    }
    await collectionsApi.upsert(subjectId.value, data)
    await fetchCollection()
  } catch (e: any) {
    collectionError.value = e?.response?.data?.message || '操作失败'
    setTimeout(() => { collectionError.value = '' }, 3000)
  } finally {
    collectionLoading.value = false
  }
}

async function handleRate(rate: number) {
  if (!authStore.isAuthenticated) {
    collectionError.value = '请先登录'
    setTimeout(() => { collectionError.value = '' }, 3000)
    return
  }
  if (!collection.value) {
    // Auto collect as "在看" with this rating
    await handleUpsert(3)
    if (!collection.value) return
  }
  const newRate = collection.value.rate === rate ? 0 : rate
  collectionLoading.value = true
  try {
    await collectionsApi.upsert(subjectId.value, {
      type: collection.value.type,
      rate: newRate,
      epStatus: collection.value.epStatus,
    })
    collection.value.rate = newRate
  } catch (e: any) {
    collectionError.value = e?.response?.data?.message || '评分失败'
    setTimeout(() => { collectionError.value = '' }, 3000)
  } finally {
    collectionLoading.value = false
  }
}

async function ensureCollectionForProgress(epStatus: number) {
  if (!authStore.isAuthenticated) return false
  if (collection.value) return true
  collectionLoading.value = true
  collectionError.value = ''
  try {
    await collectionsApi.upsert(subjectId.value, { type: 3, epStatus })
    await fetchCollection()
    return true
  } catch (e: any) {
    collectionError.value = e?.response?.data?.message || '操作失败'
    setTimeout(() => { collectionError.value = '' }, 3000)
    return false
  } finally {
    collectionLoading.value = false
  }
}

async function handleEpStatusChange(delta: number) {
  const current = collection.value?.epStatus || 0
  const newStatus = Math.max(0, Math.min(subject.value?.eps || 999, current + delta))
  if (newStatus === current && collection.value) return

  if (!collection.value) {
    await ensureCollectionForProgress(newStatus)
    return
  }

  collectionLoading.value = true
  collectionError.value = ''
  try {
    await collectionsApi.updateEpStatus(subjectId.value, newStatus)
    collection.value.epStatus = newStatus
  } catch (e: any) {
    collectionError.value = e?.response?.data?.message || '更新失败'
    setTimeout(() => { collectionError.value = '' }, 3000)
  } finally {
    collectionLoading.value = false
  }
}

async function setEpStatusTo(num: number) {
  if (!subject.value) return
  if (num < 1 || num > subject.value.eps) return

  if (!collection.value) {
    await ensureCollectionForProgress(num)
    return
  }

  if (collection.value.epStatus === num) return

  collectionLoading.value = true
  collectionError.value = ''
  try {
    await collectionsApi.updateEpStatus(subjectId.value, num)
    collection.value.epStatus = num
  } catch (e: any) {
    collectionError.value = e?.response?.data?.message || '更新失败'
    setTimeout(() => { collectionError.value = '' }, 3000)
  } finally {
    collectionLoading.value = false
  }
}

async function handleDelete() {
  collectionLoading.value = true
  collectionError.value = ''
  try {
    await collectionsApi.remove(subjectId.value)
    collection.value = null
    showDeleteConfirm.value = false
    showCollectionMenu.value = false
  } catch (e: any) {
    collectionError.value = e?.response?.data?.message || '删除失败'
    setTimeout(() => { collectionError.value = '' }, 3000)
  } finally {
    collectionLoading.value = false
  }
}

function toggleCollectionMenu() {
  showCollectionMenu.value = !showCollectionMenu.value
}

function handleDocumentClick(e: MouseEvent) {
  if (collectionWrapperRef.value && !collectionWrapperRef.value.contains(e.target as Node)) {
    showCollectionMenu.value = false
    showDeleteConfirm.value = false
  }
}

function prevRange() {
  activeEpisodeRange.value = Math.max(0, activeEpisodeRange.value - 1)
}

function nextRange() {
  activeEpisodeRange.value = Math.min(episodeRanges.value.length - 1, activeEpisodeRange.value + 1)
}

function jumpToEpisode() {
  const n = parseInt(jumpEpisodeInput.value, 10)
  if (!n || !subject.value?.eps) return
  if (n < 1 || n > subject.value.eps) {
    collectionError.value = `请输入 1-${subject.value.eps} 之间的集数`
    setTimeout(() => { collectionError.value = '' }, 3000)
    return
  }
  const rangeIndex = Math.floor((n - 1) / EPISODES_PER_RANGE)
  activeEpisodeRange.value = Math.max(0, Math.min(rangeIndex, episodeRanges.value.length - 1))
  jumpEpisodeInput.value = ''
}

onMounted(() => {
  fetchDetail()
  fetchCollection()
  document.addEventListener('click', handleDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<template>
  <div class="app-container py-6 md:py-8">
    <!-- Back Button -->
    <button
      class="btn-ghost mb-5 -ml-1"
      @click="goBack"
    >
      <ArrowLeft class="h-4 w-4" />
      返回
    </button>

    <!-- Loading State -->
    <div v-if="loading" class="space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8">
        <div class="lg:col-span-3 space-y-5">
          <div class="app-skeleton w-full rounded-2xl" style="aspect-ratio: 2/3" />
          <div class="app-skeleton h-48 rounded-2xl" />
        </div>
        <div class="lg:col-span-9 space-y-5">
          <div class="app-skeleton h-24 rounded-2xl" />
          <div class="app-skeleton h-64 rounded-2xl" />
          <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div class="app-skeleton h-32 rounded-2xl" />
            <div class="app-skeleton h-32 rounded-2xl" />
          </div>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-20">
      <p class="text-lg mb-4" style="color: var(--color-text-secondary)">{{ error }}</p>
      <button class="btn-primary" @click="fetchDetail">重试</button>
    </div>

    <!-- Subject Detail -->
    <div v-else-if="subject" class="space-y-6">
      <!-- Header -->
      <header class="flex items-start gap-4 md:gap-6">
        <div class="flex-1 min-w-0">
          <h1 class="text-2xl md:text-3xl font-bold" style="color: var(--color-text)">
            {{ subject.nameCn || subject.name }}
          </h1>
          <p v-if="subject.nameCn" class="text-sm md:text-base mt-1" style="color: var(--color-text-secondary)">
            {{ subject.name }}
          </p>

          <div class="flex flex-wrap items-center gap-2 mt-3">
            <span v-if="airYear" class="header-tag year">{{ airYear }}年</span>
            <span class="header-tag type">{{ typeName }}</span>
            <span v-if="subject.eps" class="header-tag eps">{{ subject.eps }} 话</span>
            <span v-if="subject.score" class="header-tag score">
              <Star class="inline h-3 w-3 mr-1" />{{ subject.score.toFixed(1) }}
            </span>
            <span v-if="subject.rank" class="header-tag rank">
              <Trophy class="inline h-3 w-3 mr-1" />Rank #{{ subject.rank }}
            </span>
          </div>
        </div>

        <!-- Favorite / Collection -->
        <div v-if="authStore.isAuthenticated" ref="collectionWrapperRef" class="relative shrink-0">
          <button
            class="heart-btn"
            :class="{ active: collection }"
            :disabled="collectionLoading"
            @click.stop="toggleCollectionMenu"
            aria-label="收藏"
          >
            <Heart class="h-6 w-6 transition-transform duration-200" :class="collection ? 'fill-current scale-110' : ''" />
          </button>

          <Transition name="slide-fade">
            <div
              v-if="showCollectionMenu"
              class="collection-menu"
            >
              <div class="text-xs font-medium px-2 py-1.5" style="color: var(--color-text-secondary)">
                {{ collection ? '切换收藏状态' : '添加到收藏' }}
              </div>
              <button
                v-for="action in COLLECTION_ACTIONS"
                :key="action.type"
                class="menu-item"
                :class="{ active: collection?.type === action.type }"
                @click="handleUpsert(action.type); showCollectionMenu = false"
              >
                <Bookmark class="h-3.5 w-3.5" />
                {{ action.label }}
              </button>
              <div v-if="collection" class="border-t mt-1 pt-1" style="border-color: var(--color-border)">
                <button class="menu-item danger" @click="showDeleteConfirm = true">
                  <Trash2 class="h-3.5 w-3.5" />
                  删除收藏
                </button>
              </div>
            </div>
          </Transition>

          <!-- Delete confirm modal -->
          <Transition name="slide-fade">
            <div
              v-if="showDeleteConfirm"
              class="delete-confirm"
            >
              <p class="text-xs mb-2" style="color: var(--color-text-secondary)">确认删除收藏？</p>
              <div class="flex gap-2">
                <button class="px-2.5 py-1 rounded-md text-xs font-medium bg-red-500 text-white" @click="handleDelete">确认</button>
                <button class="px-2.5 py-1 rounded-md text-xs font-medium" style="background: var(--color-hover); color: var(--color-text-secondary)" @click="showDeleteConfirm = false">取消</button>
              </div>
            </div>
          </Transition>
        </div>
      </header>

      <!-- Collection Error Toast -->
      <Transition name="slide-fade">
        <div
          v-if="collectionError"
          class="p-3 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center gap-2 text-sm text-red-600 dark:text-red-400"
        >
          <XCircle class="h-4 w-4 shrink-0" />
          {{ collectionError }}
        </div>
      </Transition>

      <!-- Two Column Layout -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8">
        <!-- Left Column: Poster + Info -->
        <aside class="lg:col-span-3 space-y-5">
          <!-- Poster -->
          <div class="rounded-2xl overflow-hidden shadow-xl" style="aspect-ratio: 2/3; background: var(--color-hover)">
            <img
              v-if="subject.image"
              :src="subject.image"
              :alt="subject.nameCn || subject.name"
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex items-center justify-center">
              <Tv class="h-16 w-16 opacity-20" style="color: var(--color-text-secondary)" />
            </div>
          </div>

          <!-- Info Card -->
          <div class="app-card p-4 sm:p-5">
            <h3 class="text-sm font-semibold mb-3 flex items-center gap-2" style="color: var(--color-text)">
              <Info class="h-4 w-4" />
              详细信息
            </h3>
            <ul class="space-y-2.5 text-sm">
              <li class="info-row">
                <span class="info-label"><Hash class="h-3.5 w-3.5" />话数</span>
                <span class="info-value">{{ subject.eps || '-' }}</span>
              </li>
              <li class="info-row">
                <span class="info-label"><Calendar class="h-3.5 w-3.5" />首播</span>
                <span class="info-value">{{ subject.airDate || '-' }}</span>
              </li>
              <li class="info-row">
                <span class="info-label"><Tv class="h-3.5 w-3.5" />放送</span>
                <span class="info-value">{{ weekdayName || '-' }}</span>
              </li>
              <li class="info-row">
                <span class="info-label"><Heart class="h-3.5 w-3.5" />收藏</span>
                <span class="info-value">{{ subject.collectionTotal ? subject.collectionTotal.toLocaleString() : '-' }}</span>
              </li>
              <li class="info-row">
                <span class="info-label"><Hash class="h-3.5 w-3.5" />Bangumi</span>
                <span class="info-value">{{ subject.bangumiId || '-' }}</span>
              </li>
            </ul>
            <a
              v-if="bangumiUrl"
              :href="bangumiUrl"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-1.5 mt-4 text-xs font-medium transition-colors hover:text-primary-500"
              style="color: var(--color-text-secondary)"
            >
              <ExternalLink class="h-3 w-3" />
              在 Bangumi 查看
            </a>
          </div>

          <!-- Tags -->
          <div v-if="subject.tags && subject.tags.length > 0">
            <h3 class="text-sm font-semibold mb-2.5" style="color: var(--color-text)">标签</h3>
            <div class="flex flex-wrap gap-2">
              <TagBadge
                v-for="tag in subject.tags"
                :key="tag.id"
                :tag="tag"
                :clickable="true"
              />
            </div>
          </div>

          <!-- Summary -->
          <div v-if="subject.summary">
            <h3 class="text-sm font-semibold mb-2.5" style="color: var(--color-text)">简介</h3>
            <p class="text-sm leading-relaxed whitespace-pre-line" style="color: var(--color-text-secondary)">
              {{ displaySummary }}
            </p>
            <button
              v-if="summaryIsLong"
              class="btn-ghost text-xs mt-2 px-2 py-1"
              @click="summaryExpanded = !summaryExpanded"
            >
              <ChevronUp v-if="summaryExpanded" class="h-3.5 w-3.5" />
              <ChevronDown v-else class="h-3.5 w-3.5" />
              {{ summaryExpanded ? '收起' : '展开全部' }}
            </button>
          </div>
        </aside>

        <!-- Right Column: Episodes + Progress + Rating + Heat -->
        <main class="lg:col-span-9 space-y-5">
          <!-- Episode Selector -->
          <section v-if="episodeRanges.length > 0" class="app-card p-4 sm:p-5">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
              <div class="flex items-center gap-2">
                <Play class="h-4 w-4" style="color: var(--color-text-secondary)" />
                <h2 class="text-base font-semibold" style="color: var(--color-text)">剧集列表</h2>
              </div>
              <div class="flex items-center gap-2">
                <input
                  v-model="jumpEpisodeInput"
                  type="number"
                  min="1"
                  :max="subject.eps || 1"
                  placeholder="输入集数"
                  class="jump-input"
                  @keyup.enter="jumpToEpisode"
                />
                <button class="jump-btn" @click="jumpToEpisode">跳转</button>
              </div>
            </div>

            <!-- Range Tabs -->
            <div class="flex items-center gap-1.5 mb-4 overflow-x-auto scrollbar-hide pb-1">
              <button
                class="range-arrow"
                :disabled="activeEpisodeRange === 0"
                @click="prevRange"
              >
                <ChevronLeft class="h-4 w-4" />
              </button>
              <button
                v-for="(range, idx) in episodeRanges"
                :key="idx"
                class="range-tab"
                :class="{ active: idx === activeEpisodeRange }"
                @click="activeEpisodeRange = idx"
              >
                {{ range.start }}-{{ range.end }}
              </button>
              <button
                class="range-arrow"
                :disabled="activeEpisodeRange >= episodeRanges.length - 1"
                @click="nextRange"
              >
                <ChevronRight class="h-4 w-4" />
              </button>
            </div>

            <!-- Episode Grid -->
            <div class="ep-grid">
              <button
                v-for="num in visibleEpisodeNumbers"
                :key="num"
                class="ep-btn"
                :class="{
                  watched: collection && num <= collection.epStatus,
                  current: collection && num === collection.epStatus + 1,
                }"
                :disabled="collectionLoading"
                @click="setEpStatusTo(num)"
              >
                {{ num }}
              </button>
            </div>
          </section>

          <!-- Progress + Rating -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
            <!-- Progress Card -->
            <section class="app-card p-4 sm:p-5">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-sm font-semibold flex items-center gap-2" style="color: var(--color-text)">
                  <Play class="h-4 w-4" />
                  我的进度
                </h3>
                <span
                  class="text-xs px-2 py-0.5 rounded-full font-medium"
                  :class="collection
                    ? 'bg-primary-500/10 text-primary-500'
                    : ''"
                  :style="!collection ? 'background: var(--color-hover); color: var(--color-text-secondary)' : ''"
                >
                  {{ collection ? collectionLabel : '未追番' }}
                </span>
              </div>

              <div class="flex items-center gap-3">
                <span class="text-sm" style="color: var(--color-text-secondary)">已看</span>
                <button
                  class="step-btn"
                  :disabled="collectionLoading || (collection ? collection.epStatus <= 0 : false)"
                  @click="handleEpStatusChange(-1)"
                >
                  <Minus class="h-4 w-4" />
                </button>
                <span class="text-lg font-bold tabular-nums min-w-[3rem] text-center" style="color: var(--color-text)">
                  {{ collection?.epStatus || 0 }}
                </span>
                <button
                  class="step-btn"
                  :disabled="collectionLoading || (!!subject?.eps && !!collection && collection.epStatus >= subject.eps)"
                  @click="handleEpStatusChange(1)"
                >
                  <Plus class="h-4 w-4" />
                </button>
                <span class="text-sm" style="color: var(--color-text-secondary)">集 / 共 {{ subject?.eps || '?' }} 集</span>
              </div>

              <p class="text-xs mt-3" style="color: var(--color-text-secondary)">
                首次保存进度将自动加入追番
              </p>
            </section>

            <!-- Rating Card -->
            <section class="app-card p-4 sm:p-5">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-sm font-semibold flex items-center gap-2" style="color: var(--color-text)">
                  <Star class="h-4 w-4" />
                  我的评分
                </h3>
                <button class="text-xs font-medium inline-flex items-center gap-0.5 transition-colors hover:text-primary-500" style="color: var(--color-text-secondary)">
                  查看站内评分
                  <ChevronRight class="h-3 w-3" />
                </button>
              </div>

              <div v-if="collection" class="flex items-center gap-1">
                <button
                  v-for="i in 10"
                  :key="i"
                  class="star-btn"
                  :class="i <= (collection.rate || 0) ? 'active' : ''"
                  :disabled="collectionLoading"
                  @click="handleRate(i)"
                >
                  <Star class="h-5 w-5" />
                </button>
                <span class="text-sm font-medium ml-2" style="color: var(--color-text-secondary)">
                  {{ collection.rate ? collection.rate + '/10' : '未评分' }}
                </span>
              </div>

              <div v-else>
                <button
                  class="rate-action-btn"
                  :disabled="collectionLoading"
                  @click="handleUpsert(3)"
                >
                  <Star class="h-4 w-4" />
                  立即评分
                </button>
              </div>
            </section>
          </div>

          <!-- Score Overview -->
          <section class="app-card p-4 sm:p-5">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background: rgba(255,185,0,0.12)">
                <Star class="h-5 w-5" style="color: #ffb900" />
              </div>
              <div>
                <div class="text-2xl font-bold" style="color: var(--color-text)">{{ subject.score ? subject.score.toFixed(1) : '-' }}</div>
                <div class="text-xs" style="color: var(--color-text-secondary)">Bangumi 评分</div>
              </div>
            </div>
            <div v-if="subject.rank" class="flex items-center gap-2 mt-3 text-sm" style="color: var(--color-text-secondary)">
              <Trophy class="h-4 w-4" />
              Rank #{{ subject.rank }}
            </div>
          </section>
        </main>
      </div>
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

.header-tag {
  @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium;
}
.header-tag.year {
  background: var(--color-hover);
  color: var(--color-text-secondary);
}
.header-tag.type {
  background: rgba(0, 161, 214, 0.12);
  color: #22b8e8;
}
.dark .header-tag.type {
  color: #4dd1f7;
}
.header-tag.eps {
  background: rgba(132, 94, 247, 0.12);
  color: #845ef7;
}
.header-tag.score {
  background: rgba(255, 185, 0, 0.15);
  color: #e69d00;
}
.dark .header-tag.score {
  color: #ffb900;
}
.header-tag.rank {
  background: rgba(54, 211, 153, 0.12);
  color: #20a96d;
}
.dark .header-tag.rank {
  color: #36d399;
}

.heart-btn {
  @apply w-11 h-11 rounded-full flex items-center justify-center transition-all duration-200;
  background: var(--color-hover);
  color: var(--color-text-secondary);
  border: 1px solid transparent;
}
.heart-btn:hover {
  border-color: var(--color-border-solid);
  color: var(--color-text);
}
.heart-btn.active {
  background: rgba(241, 121, 146, 0.12);
  color: #f17992;
  border-color: rgba(241, 121, 146, 0.25);
}
.heart-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.collection-menu {
  @apply absolute right-0 top-full mt-2 p-1.5 rounded-xl shadow-lg z-20 min-w-[9rem];
  background: var(--color-card);
  border: 1px solid var(--color-border);
}
.menu-item {
  @apply w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-sm transition-colors duration-150;
  color: var(--color-text);
}
.menu-item:hover {
  background: var(--color-hover);
}
.menu-item.active {
  background: rgba(241, 121, 146, 0.1);
  color: #f17992;
}
.menu-item.danger {
  color: #ef4444;
}
.menu-item.danger:hover {
  background: rgba(239, 68, 68, 0.08);
}

.delete-confirm {
  @apply absolute right-0 top-full mt-2 p-3 rounded-xl shadow-lg z-20 w-44;
  background: var(--color-card);
  border: 1px solid var(--color-border);
}

.info-row {
  @apply flex items-center justify-between;
}
.info-label {
  @apply inline-flex items-center gap-1.5;
  color: var(--color-text-secondary);
}
.info-value {
  color: var(--color-text);
  font-weight: 500;
}

.jump-input {
  @apply w-24 px-2.5 py-1.5 rounded-lg text-sm outline-none transition-colors;
  background: var(--color-hover);
  color: var(--color-text);
  border: 1px solid transparent;
}
.jump-input:focus {
  border-color: var(--color-border-solid);
}
.jump-input::placeholder {
  color: var(--color-text-secondary);
}
.jump-input::-webkit-inner-spin-button,
.jump-input::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.jump-input[type='number'] {
  -moz-appearance: textfield;
}
.jump-btn {
  @apply px-3 py-1.5 rounded-lg text-sm font-medium transition-colors;
  background: var(--color-hover);
  color: var(--color-text);
}
.jump-btn:hover {
  background: var(--color-border-solid);
}

.range-arrow {
  @apply w-8 h-8 flex items-center justify-center rounded-lg transition-colors shrink-0;
  background: var(--color-hover);
  color: var(--color-text-secondary);
}
.range-arrow:hover:not(:disabled) {
  background: var(--color-border-solid);
  color: var(--color-text);
}
.range-arrow:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.range-tab {
  @apply px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors;
  background: var(--color-hover);
  color: var(--color-text-secondary);
}
.range-tab:hover {
  color: var(--color-text);
}
.range-tab.active {
  background: rgba(241, 121, 146, 0.12);
  color: #f17992;
}

.ep-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, 60px);
  gap: 0.5rem;
}
.ep-btn {
  @apply flex items-center justify-center rounded-lg text-xs font-medium transition-all duration-150;
  width: 60px;
  height: 60px;
  background: var(--color-hover);
  color: var(--color-text);
}
.ep-btn:hover:not(:disabled) {
  background: var(--color-border-solid);
}
.ep-btn.watched {
  background: rgba(241, 121, 146, 0.85);
  color: white;
}
.ep-btn.watched:hover:not(:disabled) {
  background: #f17992;
}
.ep-btn.current {
  border: 1px solid rgba(241, 121, 146, 0.5);
}
.ep-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.step-btn {
  @apply w-8 h-8 flex items-center justify-center rounded-lg transition-colors;
  background: var(--color-hover);
  color: var(--color-text);
}
.step-btn:hover:not(:disabled) {
  background: var(--color-border-solid);
}
.step-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.star-btn {
  @apply p-0.5 transition-colors duration-150;
  color: var(--color-border-solid);
}
.star-btn.active {
  color: #ffb900;
}
.star-btn:hover:not(:disabled) {
  color: #ffb900;
}
.star-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.rate-action-btn {
  @apply inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors;
  background: rgba(241, 121, 146, 0.1);
  color: #f17992;
}
.rate-action-btn:hover:not(:disabled) {
  background: rgba(241, 121, 146, 0.18);
}
.rate-action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>
