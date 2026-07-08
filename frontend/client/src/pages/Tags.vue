<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search, Tags } from '@lucide/vue'
import { tagsApi } from '@/api/tags'
import type { TagVO } from '@/types'

const tags = ref<TagVO[]>([])
const loading = ref(true)
const filterQuery = ref('')

const filteredTags = computed(() => {
  const q = filterQuery.value.trim().toLowerCase()
  if (!q) return tags.value
  return tags.value.filter(tag => tag.name.toLowerCase().includes(q))
})

async function fetchTags() {
  loading.value = true
  try {
    const res = await tagsApi.getList()
    tags.value = res.data.data
  } catch {
    // silently fail
  } finally {
    loading.value = false
  }
}

onMounted(fetchTags)
</script>

<template>
  <div class="app-container py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="page-title mb-2">标签索引</h1>
      <p class="page-subtitle">按标签浏览动画作品</p>
    </div>

    <!-- Filter Input -->
    <div class="max-w-md mb-8">
      <div class="relative">
        <Search class="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4" style="color: var(--color-text-secondary)" />
        <input
          v-model="filterQuery"
          type="text"
          placeholder="筛选标签..."
          class="input-field pl-10"
        />
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      <div v-for="i in 20" :key="i" class="app-skeleton h-24 rounded-2xl" />
    </div>

    <!-- Tags Grid -->
    <div v-else-if="filteredTags.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      <router-link
        v-for="tag in filteredTags"
        :key="tag.id"
        :to="{ name: 'TagSubjects', params: { tag: tag.name } }"
        class="app-card p-4 text-center group cursor-pointer no-underline"
      >
        <div class="flex items-center justify-center mb-2">
          <Tags class="h-4 w-4 mr-1.5 text-primary-500 opacity-60 group-hover:opacity-100 transition-opacity" />
          <span class="text-sm font-medium truncate group-hover:text-primary-500 transition-colors" style="color: var(--color-text)">
            {{ tag.name }}
          </span>
        </div>
        <div class="text-xs" style="color: var(--color-text-secondary)">
          {{ tag.count.toLocaleString() }} 部作品
        </div>
      </router-link>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-20" style="color: var(--color-text-secondary)">
      <Tags class="h-12 w-12 mx-auto mb-4 opacity-30" />
      <p class="text-base">未找到匹配的标签</p>
    </div>
  </div>
</template>
