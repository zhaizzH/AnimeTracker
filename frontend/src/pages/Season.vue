<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSubjectsStore } from '@/stores/subjects'
import SeasonPicker from '@/components/SeasonPicker.vue'
import SubjectCard from '@/components/SubjectCard.vue'
import ListSkeleton from '@/components/ListSkeleton.vue'
import EmptyState from '@/components/EmptyState.vue'
import Pagination from '@/components/Pagination.vue'

const store = useSubjectsStore()
const route = useRoute()
const router = useRouter()
const error = ref('')

onMounted(() => {
  loadSeason()
})

async function loadSeason() {
  const year = parseInt(route.params.year as string) || new Date().getFullYear()
  const quarter = (route.params.quarter as string) || 'spring'
  if (year < 2000 || year > 2099) {
    error.value = '年份无效'
    return
  }
  if (!['winter', 'spring', 'summer', 'autumn'].includes(quarter)) {
    error.value = '季度无效'
    return
  }
  error.value = ''
  await store.fetchSeasonSubjects(year, quarter)
}

function onPageChange(page: number) {
  const year = parseInt(route.params.year as string) || new Date().getFullYear()
  const quarter = (route.params.quarter as string) || 'spring'
  store.fetchSeasonSubjects(year, quarter, page)
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">季度浏览</h1>
      <SeasonPicker />
    </div>

    <p v-if="error" class="text-sm text-red-500 mb-4">{{ error }}</p>

    <ListSkeleton v-if="store.loading" />

    <EmptyState v-else-if="store.subjects.length === 0 && !error" message="该季度暂无数据" />

    <div v-else-if="store.subjects.length > 0">
      <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        <SubjectCard v-for="item in store.subjects" :key="item.id" :subject="item" />
      </div>
      <Pagination
        :current-page="store.currentPage"
        :total="store.total"
        :page-size="store.pageSize"
        @page-change="onPageChange"
      />
    </div>
  </div>
</template>
