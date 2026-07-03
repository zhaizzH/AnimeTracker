<script setup lang="ts">
import { useSubjectsStore } from '@/stores/subjects'
import { onMounted } from 'vue'
import SubjectCard from '@/components/SubjectCard.vue'
import ListSkeleton from '@/components/ListSkeleton.vue'
import EmptyState from '@/components/EmptyState.vue'
import Pagination from '@/components/Pagination.vue'

const store = useSubjectsStore()

onMounted(() => {
  store.fetchSubjects()
})

function onPageChange(page: number) {
  store.fetchSubjects(page)
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">动漫列表</h1>

    <ListSkeleton v-if="store.loading && store.subjects.length === 0" />

    <div v-else-if="store.subjects.length === 0">
      <EmptyState message="暂无动漫数据，请先导入数据" />
    </div>

    <div v-else>
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
