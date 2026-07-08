<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft, Star, Trophy, Calendar, Tv, Hash, ExternalLink,
  Heart, ChevronDown, ChevronUp,
} from '@lucide/vue'
import { subjectsApi } from '@/api/subjects'
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

onMounted(fetchDetail)
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
