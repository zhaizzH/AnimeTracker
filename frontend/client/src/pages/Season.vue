<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { SubjectListItem } from '@/types'
import { subjectsApi } from '@/api/subjects'
import SubjectCard from '@/components/SubjectCard.vue'
import SubjectCardSkeleton from '@/components/SubjectCardSkeleton.vue'
import Pagination from '@/components/Pagination.vue'
import SeasonPicker from '@/components/SeasonPicker.vue'
import EmptyState from '@/components/EmptyState.vue'

const route = useRoute()
const router = useRouter()

const currentYear = new Date().getFullYear()
const currentMonth = new Date().getMonth()
const defaultQuarter = currentMonth < 3 ? 'winter' : currentMonth < 6 ? 'spring' : currentMonth < 9 ? 'summer' : 'fall'

const year = ref<number>(currentYear)
const quarter = ref<string>(defaultQuarter)
const results = ref<SubjectListItem[]>([])
const totalResults = ref(0)
const currentPage = ref(1)
const pageSize = 20
const totalPages = ref(0)
const loading = ref(false)

function readRouteParams() {
  const y = route.params.year ? parseInt(route.params.year as string, 10) : currentYear
  const q = (route.params.quarter as string) || defaultQuarter
  if (y !== year.value || q !== quarter.value) {
    year.value = y
    quarter.value = q
    currentPage.value = 1
  }
}

async function fetchSeason() {
  loading.value = true
  try {
    const res = await subjectsApi.getBySeason({
      year: year.value,
      quarter: quarter.value,
      page: currentPage.value,
      size: pageSize,
    })
    results.value = res.data.data.content
    totalResults.value = res.data.data.total
    totalPages.value = Math.ceil(res.data.data.total / pageSize)
  } catch {
    results.value = []
    totalResults.value = 0
    totalPages.value = 0
  } finally {
    loading.value = false
  }
}

function handleYearUpdate(newYear: number) {
  year.value = newYear
  currentPage.value = 1
  router.push({ name: 'Season', params: { year: newYear, quarter: quarter.value } })
}

function handleQuarterUpdate(newQuarter: string) {
  quarter.value = newQuarter
  currentPage.value = 1
  router.push({ name: 'Season', params: { year: year.value, quarter: newQuarter } })
}

function handlePageChange(page: number) {
  currentPage.value = page
  fetchSeason()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

watch(() => [route.params.year, route.params.quarter], () => {
  readRouteParams()
  fetchSeason()
})

onMounted(() => {
  readRouteParams()
  fetchSeason()
})

const quarterLabel = computed(() => {
  const labels: Record<string, string> = {
    winter: '冬季',
    spring: '春季',
    summer: '夏季',
    fall: '秋季',
  }
  return labels[quarter.value] || quarter.value
})
</script>

<template>
  <div class="app-container py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="page-title mb-2">{{ year }}年 {{ quarterLabel }}新番</h1>
      <p class="page-subtitle">浏览 {{ year }}年{{ quarterLabel }}播出的动画作品</p>
    </div>

    <!-- Season Picker -->
    <div class="mb-8">
      <SeasonPicker
        :year="year"
        :quarter="quarter"
        @update:year="handleYearUpdate"
        @update:quarter="handleQuarterUpdate"
      />
    </div>

    <!-- Results Count -->
    <div v-if="!loading && totalResults > 0" class="mb-6 text-sm" style="color: var(--color-text-secondary)">
      共 <strong style="color: var(--color-text)">{{ totalResults }}</strong> 部作品
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6">
      <SubjectCardSkeleton v-for="i in pageSize" :key="i" />
    </div>

    <!-- Results Grid -->
    <div v-else-if="results.length > 0">
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6 mb-8">
        <SubjectCard v-for="item in results" :key="item.id" :subject="item" />
      </div>
      <Pagination
        v-if="totalPages > 1"
        :current-page="currentPage"
        :total-pages="totalPages"
        @update:page="handlePageChange"
      />
    </div>

    <!-- Empty State -->
    <EmptyState
      v-else
      icon="calendar"
      :title="`${year}年${quarterLabel}暂无作品`"
      description="该季度暂未收录动画作品，请尝试其他季度"
    />
  </div>
</template>
