<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search, X } from '@lucide/vue'
import { subjectsApi } from '@/api/subjects'
import type { SubjectListItem } from '@/types'
import SubjectCard from '@/components/SubjectCard.vue'
import SubjectCardSkeleton from '@/components/SubjectCardSkeleton.vue'
import Pagination from '@/components/Pagination.vue'
import EmptyState from '@/components/EmptyState.vue'

const route = useRoute()
const router = useRouter()

const searchQuery = ref('')
const results = ref<SubjectListItem[]>([])
const totalResults = ref(0)
const currentPage = ref(1)
const pageSize = 20
const totalPages = ref(0)
const loading = ref(false)
const hasSearched = ref(false)

let debounceTimer: ReturnType<typeof setTimeout> | null = null

function updateQueryFromRoute() {
  const q = (route.query.q as string) || ''
  if (q !== searchQuery.value) {
    searchQuery.value = q
    currentPage.value = 1
    if (q) {
      performSearch()
    }
  }
}

async function performSearch() {
  const q = searchQuery.value.trim()
  if (!q) {
    results.value = []
    totalResults.value = 0
    totalPages.value = 0
    hasSearched.value = false
    return
  }

  loading.value = true
  hasSearched.value = true
  try {
    const res = await subjectsApi.search({
      q,
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

function handleInput() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    currentPage.value = 1
    const q = searchQuery.value.trim()
    router.replace({ query: q ? { q } : {} })
    performSearch()
  }, 300)
}

function handleClear() {
  searchQuery.value = ''
  results.value = []
  totalResults.value = 0
  totalPages.value = 0
  hasSearched.value = false
  router.replace({ query: {} })
}

function handlePageChange(page: number) {
  currentPage.value = page
  performSearch()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

watch(() => route.query.q, updateQueryFromRoute)

onMounted(() => {
  updateQueryFromRoute()
  if (!searchQuery.value) {
    hasSearched.value = false
  }
})
</script>

<template>
  <div class="app-container py-8">
    <!-- Search Input -->
    <div class="max-w-2xl mx-auto mb-8">
      <div class="relative">
        <Search class="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5" style="color: var(--color-text-secondary)" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索动画作品名称..."
          class="input-field pl-12 pr-12 py-4 text-base rounded-2xl"
          autofocus
          @input="handleInput"
        />
        <button
          v-if="searchQuery"
          class="absolute right-4 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
          style="color: var(--color-text-secondary)"
          @click="handleClear"
        >
          <X class="h-4 w-4" />
        </button>
      </div>
    </div>

    <!-- Results Count -->
    <div v-if="hasSearched && !loading" class="mb-6 text-sm" style="color: var(--color-text-secondary)">
      <span v-if="totalResults > 0">找到 <strong style="color: var(--color-text)">{{ totalResults }}</strong> 个结果</span>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="card-grid-responsive grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 md:gap-6">
      <SubjectCardSkeleton v-for="i in pageSize" :key="i" />
    </div>

    <!-- Results Grid -->
    <div v-else-if="results.length > 0">
      <div class="card-grid-responsive grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 md:gap-6 mb-8">
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
      v-else-if="hasSearched"
      icon="search"
      title="未找到相关作品"
      description="尝试使用不同的关键词搜索"
    />

    <!-- Initial State -->
    <div v-else class="text-center py-20" style="color: var(--color-text-secondary)">
      <Search class="h-12 w-12 mx-auto mb-4 opacity-30" />
      <p class="text-base">输入关键词开始搜索</p>
    </div>
  </div>
</template>
