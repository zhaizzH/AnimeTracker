<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft, Star, Trophy, Calendar, Tv, Hash, ExternalLink,
  Heart, ChevronDown, ChevronUp, Plus, Minus, Trash2, Bookmark, XCircle,
} from '@lucide/vue'
import { subjectsApi } from '@/api/subjects'
import { collectionsApi, type UserCollectionVO, type UpsertCollectionRequest } from '@/api/collections'
import { useAuthStore } from '@/stores/auth'
import type { SubjectDetail, EpisodeVO } from '@/types'
import { SUBJECT_TYPES, WEEKDAYS } from '@/types'
import TagBadge from '@/components/TagBadge.vue'
import EpisodeList from '@/components/EpisodeList.vue'

const route = useRoute()
const router = useRouter()

const subject = ref<SubjectDetail | null>(null)
const episodes = ref<EpisodeVO[]>([])
const loading = ref(true)
const error = ref('')
const summaryExpanded = ref(false)

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

// --- Collection ---
const authStore = useAuthStore()

const collection = ref<UserCollectionVO | null>(null)
const collectionLoading = ref(false)
const collectionError = ref('')
const showDeleteConfirm = ref(false)

const COLLECTION_ACTIONS = [
  { type: 1, label: '想看' },
  { type: 3, label: '在看' },
  { type: 2, label: '看过' },
  { type: 4, label: '搁置' },
  { type: 5, label: '抛弃' },
]

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
  if (!collection.value) return
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

async function handleEpStatusChange(delta: number) {
  if (!collection.value) return
  const newStatus = Math.max(0, Math.min(subject.value?.eps || 999, collection.value.epStatus + delta))
  if (newStatus === collection.value.epStatus) return
  collectionLoading.value = true
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

async function handleDelete() {
  collectionLoading.value = true
  try {
    await collectionsApi.remove(subjectId.value)
    collection.value = null
    showDeleteConfirm.value = false
  } catch (e: any) {
    collectionError.value = e?.response?.data?.message || '删除失败'
    setTimeout(() => { collectionError.value = '' }, 3000)
  } finally {
    collectionLoading.value = false
  }
}

onMounted(() => {
  fetchDetail()
  fetchCollection()
})
</script>

<template>
  <div class="app-container py-8">
    <!-- Back Button -->
    <button
      class="btn-ghost mb-6 -ml-1"
      @click="goBack"
    >
      <ArrowLeft class="h-4 w-4" />
      返回
    </button>

    <!-- Loading State -->
    <div v-if="loading" class="space-y-6">
      <div class="flex flex-col md:flex-row gap-8">
        <div class="app-skeleton w-48 md:w-64 shrink-0 rounded-2xl" style="aspect-ratio: 2/3" />
        <div class="flex-1 space-y-4">
          <div class="app-skeleton h-8 w-3/4 rounded-lg" />
          <div class="app-skeleton h-5 w-1/2 rounded-lg" />
          <div class="flex gap-3 mt-4">
            <div class="app-skeleton h-7 w-16 rounded-md" />
            <div class="app-skeleton h-7 w-16 rounded-md" />
            <div class="app-skeleton h-7 w-24 rounded-md" />
          </div>
          <div class="app-skeleton h-24 w-full rounded-xl mt-6" />
          <div class="flex gap-2 mt-4">
            <div class="app-skeleton h-7 w-20 rounded-full" />
            <div class="app-skeleton h-7 w-20 rounded-full" />
            <div class="app-skeleton h-7 w-20 rounded-full" />
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
    <div v-else-if="subject">
      <div class="flex flex-col md:flex-row gap-8 mb-10">
        <!-- Cover Image -->
        <div class="shrink-0 mx-auto md:mx-0">
          <div class="w-48 md:w-64 rounded-2xl overflow-hidden shadow-xl" style="aspect-ratio: 2/3">
            <img
              v-if="subject.image"
              :src="subject.image"
              :alt="subject.nameCn || subject.name"
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex items-center justify-center" style="background: var(--color-hover)">
              <Tv class="h-12 w-12 opacity-20" style="color: var(--color-text-secondary)" />
            </div>
          </div>
        </div>

        <!-- Info Panel -->
        <div class="flex-1 min-w-0">
          <!-- Title -->
          <h1 class="text-2xl md:text-3xl font-bold mb-1" style="color: var(--color-text)">
            {{ subject.nameCn || subject.name }}
          </h1>
          <p v-if="subject.nameCn" class="text-base mb-5" style="color: var(--color-text-secondary)">
            {{ subject.name }}
          </p>

          <!-- Badges Row -->
          <div class="flex flex-wrap items-center gap-2 mb-6">
            <span v-if="subject.score" class="badge-score text-sm px-2.5 py-1">
              <Star class="inline h-3.5 w-3.5 mr-1 -mt-0.5" />{{ subject.score.toFixed(1) }}
            </span>
            <span v-if="subject.rank" class="badge-rank text-sm px-2.5 py-1">
              <Trophy class="inline h-3.5 w-3.5 mr-1 -mt-0.5" />Rank #{{ subject.rank }}
            </span>
            <span class="badge text-sm px-2.5 py-1">{{ typeName }}</span>
            <span v-if="subject.eps" class="badge text-sm px-2.5 py-1">
              {{ subject.eps }} 话
            </span>
          </div>

          <!-- Collection Section -->
          <div v-if="authStore.isAuthenticated" class="mb-6">
            <!-- Error toast -->
            <Transition name="slide-fade">
              <div
                v-if="collectionError"
                class="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center gap-2 text-sm text-red-600 dark:text-red-400"
              >
                <XCircle class="h-4 w-4 shrink-0" />
                {{ collectionError }}
              </div>
            </Transition>

            <div class="app-card p-4 sm:p-5">
              <div v-if="collectionLoading && !collection" class="app-skeleton h-12 rounded-lg" />
              <!-- Not collected -->
              <template v-else-if="!collection">
                <h3 class="text-sm font-medium mb-3" style="color: var(--color-text)">追番</h3>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="action in COLLECTION_ACTIONS"
                    :key="action.type"
                    class="px-4 py-2 rounded-full text-sm font-medium transition-all duration-200"
                    :class="'hover:bg-primary-500/10 hover:text-primary-500'"
                    style="background: var(--color-hover); color: var(--color-text-secondary);"
                    :disabled="collectionLoading"
                    @click="handleUpsert(action.type)"
                  >
                    <Bookmark class="inline h-3.5 w-3.5 mr-1 -mt-0.5" />
                    {{ action.label }}
                  </button>
                </div>
              </template>
              <!-- Collected -->
              <template v-else>
                <div class="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-6">
                  <!-- Type switcher -->
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-medium" style="color: var(--color-text)">状态：</span>
                    <div class="flex flex-wrap gap-1">
                      <button
                        v-for="action in COLLECTION_ACTIONS"
                        :key="action.type"
                        class="px-3 py-1 rounded-full text-xs font-medium transition-all duration-200"
                        :class="collection.type === action.type
                          ? 'bg-primary-600 text-white shadow-sm'
                          : ''"
                        :style="collection.type !== action.type ? 'background: var(--color-hover); color: var(--color-text-secondary)' : ''"
                        :disabled="collectionLoading"
                        @click="handleUpsert(action.type)"
                      >
                        {{ action.label }}
                      </button>
                    </div>
                  </div>

                  <!-- Rating -->
                  <div class="flex items-center gap-1">
                    <span class="text-sm font-medium mr-1" style="color: var(--color-text)">评分：</span>
                    <button
                      v-for="i in 10"
                      :key="i"
                      class="w-5 h-5 flex items-center justify-center transition-colors duration-150"
                      :class="i <= (collection.rate || 0) ? 'text-yellow-500' : 'text-gray-300 dark:text-gray-600'"
                      :disabled="collectionLoading"
                      @click="handleRate(i)"
                    >
                      <Star :size="14" :fill="i <= (collection.rate || 0) ? 'currentColor' : 'none'" />
                    </button>
                    <span v-if="collection.rate > 0" class="text-xs ml-1" style="color: var(--color-text-secondary)">{{ collection.rate }}/10</span>
                    <span v-else class="text-xs ml-1" style="color: var(--color-text-secondary)">未评分</span>
                  </div>
                </div>

                <!-- Progress + Delete -->
                <div class="flex items-center justify-between mt-4 pt-4 border-t" style="border-color: var(--color-border)">
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-medium" style="color: var(--color-text)">进度：</span>
                    <button
                      class="btn-ghost !p-1.5"
                      :disabled="collectionLoading || collection.epStatus <= 0"
                      @click="handleEpStatusChange(-1)"
                    >
                      <Minus :size="14" />
                    </button>
                    <span class="text-sm tabular-nums min-w-[4rem] text-center" style="color: var(--color-text)">
                      {{ collection.epStatus }} / {{ subject?.eps || '?' }} 话
                    </span>
                    <button
                      class="btn-ghost !p-1.5"
                      :disabled="collectionLoading || (!!subject?.eps && collection.epStatus >= subject.eps)"
                      @click="handleEpStatusChange(1)"
                    >
                      <Plus :size="14" />
                    </button>
                  </div>
                  <div class="relative">
                    <button
                      class="btn-ghost !p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10"
                      :disabled="collectionLoading"
                      @click="showDeleteConfirm = !showDeleteConfirm"
                    >
                      <Trash2 :size="14" />
                    </button>
                    <Transition name="slide-fade">
                      <div
                        v-if="showDeleteConfirm"
                        class="absolute right-0 bottom-full mb-2 flex items-center gap-2 p-2 rounded-lg shadow-lg border z-10"
                        style="background: var(--color-card); border-color: var(--color-border)"
                      >
                        <span class="text-xs whitespace-nowrap" style="color: var(--color-text-secondary)">确认删除？</span>
                        <button
                          class="px-2 py-1 rounded text-xs font-medium bg-red-500 text-white"
                          @click="handleDelete"
                        >
                          确认
                        </button>
                        <button
                          class="px-2 py-1 rounded text-xs font-medium"
                          style="background: var(--color-hover); color: var(--color-text-secondary)"
                          @click="showDeleteConfirm = false"
                        >
                          取消
                        </button>
                      </div>
                    </Transition>
                  </div>
                </div>
              </template>
            </div>
          </div>

          <!-- Meta Info -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6 text-sm">
            <div v-if="subject.airDate" class="flex items-center gap-2" style="color: var(--color-text-secondary)">
              <Calendar class="h-4 w-4 shrink-0" />
              <span>首播: {{ subject.airDate }}</span>
            </div>
            <div v-if="weekdayName" class="flex items-center gap-2" style="color: var(--color-text-secondary)">
              <Tv class="h-4 w-4 shrink-0" />
              <span>放送: {{ weekdayName }}</span>
            </div>
            <div v-if="subject.collectionTotal" class="flex items-center gap-2" style="color: var(--color-text-secondary)">
              <Heart class="h-4 w-4 shrink-0" />
              <span>{{ subject.collectionTotal.toLocaleString() }} 人收藏</span>
            </div>
            <div v-if="subject.bangumiId" class="flex items-center gap-2" style="color: var(--color-text-secondary)">
              <Hash class="h-4 w-4 shrink-0" />
              <span>Bangumi ID: {{ subject.bangumiId }}</span>
            </div>
          </div>

          <!-- Bangumi Link -->
          <a
            v-if="bangumiUrl"
            :href="bangumiUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="btn-secondary text-xs mb-6 inline-flex"
          >
            <ExternalLink class="h-3.5 w-3.5" />
            在 Bangumi 查看
          </a>

          <!-- Tags -->
          <div v-if="subject.tags && subject.tags.length > 0" class="mb-6">
            <h3 class="text-sm font-medium mb-2" style="color: var(--color-text)">标签</h3>
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
          <div v-if="subject.summary" class="mb-4">
            <h3 class="text-sm font-medium mb-2" style="color: var(--color-text)">简介</h3>
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
        </div>
      </div>

      <!-- Episodes Section -->
      <div v-if="episodes.length > 0">
        <h2 class="section-title mb-4">剧集列表</h2>
        <EpisodeList :episodes="episodes" />
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
</style>
