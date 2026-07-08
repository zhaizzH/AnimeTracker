<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, Tag } from '@lucide/vue'
import { tagsApi } from '@/api/tags'
import type { SubjectListItem } from '@/types'
import SubjectCard from '@/components/SubjectCard.vue'
import SubjectCardSkeleton from '@/components/SubjectCardSkeleton.vue'
import Pagination from '@/components/Pagination.vue'
import EmptyState from '@/components/EmptyState.vue'

const route = useRoute()

const tagName = computed(() => route.params.tag as string)
const results = ref<SubjectListItem[]>([])
const totalResults = ref(0)
const currentPage = ref(1)
const pageSize = 20
const totalPages = ref(0)
const loading = ref(false)

async function fetchSubjects() {
  loading.value = true
  try {
    const res = await tagsApi.getSubjects(tagName.value, {
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

function handlePageChange(page: number) {
  currentPage.value = page
  fetchSubjects()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

watch(tagName, () => {
  currentPage.value = 1
  fetchSubjects()
})

onMounted(fetchSubjects)
</script>

<template>
  <div class="app-container py-8">
    <!-- Back Link -->
    <router-link
      :to="{ name: 'Tags' }"
      class="btn-ghost mb-6 -ml-1 inline-flex no-underline"
    >
      <ArrowLeft class="h-4 w-4" />
      全部标签
    </router-link>

    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center gap-3 mb-2">
        <Tag class="h-6 w-6 text-primary-500" />
        <h1 class="page-title">标签: {{ tagName }}</h1>
      </div>
      <p v-if="!loading && totalResults > 0" class="page-subtitle">
        共 {{ totalResults }} 部作品
      </p>
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
      icon="tag"
      title="该标签下暂无作品"
      description="尝试浏览其他标签"
      action-text="浏览全部标签"
      action-to="/tags"
    />
  </div>
</template>
