<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Heart } from '@lucide/vue'
import { collectionsApi, type UserCollectionVO } from '@/api/collections'
import SubjectCard from '@/components/SubjectCard.vue'
import SubjectCardSkeleton from '@/components/SubjectCardSkeleton.vue'
import Pagination from '@/components/Pagination.vue'
import EmptyState from '@/components/EmptyState.vue'

const TABS = [
  { label: '全部', value: undefined },
  { label: '想看', value: 1 },
  { label: '在看', value: 3 },
  { label: '看过', value: 2 },
  { label: '搁置', value: 4 },
  { label: '抛弃', value: 5 },
]

const activeTab = ref<number | undefined>(undefined)
const page = ref(1)
const size = 24
const items = ref<UserCollectionVO[]>([])
const total = ref(0)
const loading = ref(false)
const error = ref('')

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / size)))

function switchTab(tabValue: number | undefined) {
  activeTab.value = tabValue
  page.value = 1
}

async function fetchCollections() {
  loading.value = true
  error.value = ''
  try {
    const res = await collectionsApi.getList({
      type: activeTab.value,
      page: page.value,
      size,
    })
    items.value = res.data.data.content
    total.value = res.data.data.total
  } catch (e: any) {
    error.value = e?.response?.data?.message || '加载失败'
  } finally {
    loading.value = false
  }
}

function onPageChange(newPage: number) {
  page.value = newPage
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

watch([activeTab, page], fetchCollections)
onMounted(fetchCollections)
</script>

<template>
  <div class="app-container py-8">
    <!-- Page Header -->
    <div class="mb-8">
      <h1 class="page-title mb-2">我的收藏</h1>
      <p class="page-subtitle">管理你所有追番记录</p>
    </div>

    <!-- Tabs -->
    <div class="flex items-center gap-2 mb-8 overflow-x-auto scrollbar-hide">
      <button
        v-for="tab in TABS"
        :key="tab.label"
        class="shrink-0 px-5 py-2 rounded-full text-sm font-medium transition-all duration-200"
        :class="activeTab === tab.value
          ? 'bg-primary-600 text-white shadow-sm'
          : ''"
        :style="activeTab !== tab.value ? 'background: var(--color-hover); color: var(--color-text-secondary)' : ''"
        @click="switchTab(tab.value)"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
      <SubjectCardSkeleton v-for="i in 12" :key="i" />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-20">
      <p class="text-lg mb-4" style="color: var(--color-text-secondary)">{{ error }}</p>
      <button class="btn-primary" @click="fetchCollections">重试</button>
    </div>

    <!-- Empty: no collections at all -->
    <EmptyState
      v-else-if="!loading && total === 0 && activeTab === undefined"
      :icon="Heart"
      title="还没有收藏任何番剧"
      description="去发现番剧，开始建立你的追番列表吧"
      action-text="去发现番剧"
      action-to="/"
    />

    <!-- Empty: tab has no items -->
    <EmptyState
      v-else-if="!loading && items.length === 0"
      :icon="Heart"
      title="该分类下还没有收藏"
    />

    <!-- Collection Grid -->
    <template v-else>
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4 mb-8">
        <SubjectCard v-for="item in items" :key="item.id" :subject="item.subject" />
      </div>

      <!-- Pagination -->
      <Pagination
        v-if="totalPages > 1"
        :current-page="page"
        :total-pages="totalPages"
        @update:page="onPageChange"
      />
    </template>
  </div>
</template>
