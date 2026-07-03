<script setup lang="ts">
import { ref } from 'vue'
import { useSubjectsStore } from '@/stores/subjects'
import { useRouter } from 'vue-router'
import SubjectCard from '@/components/SubjectCard.vue'
import ListSkeleton from '@/components/ListSkeleton.vue'
import EmptyState from '@/components/EmptyState.vue'
import Pagination from '@/components/Pagination.vue'

const store = useSubjectsStore()
const router = useRouter()
const keyword = ref('')
const searched = ref(false)

async function search() {
  if (!keyword.value.trim()) return
  searched.value = true
  await store.searchSubjects(keyword.value)
}

function onPageChange(page: number) {
  store.searchSubjects(keyword.value, page)
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-4">搜索</h1>

    <div class="flex gap-2 mb-6">
      <input
        v-model="keyword"
        placeholder="输入关键词搜索条目..."
        class="flex-1 border rounded px-3 py-2 text-sm focus:outline-none focus:border-indigo-400"
        @keyup.enter="search"
      />
      <button @click="search" class="bg-indigo-600 text-white px-4 py-2 rounded text-sm hover:bg-indigo-700">
        搜索
      </button>
    </div>

    <ListSkeleton v-if="store.loading" />

    <EmptyState v-else-if="searched && store.subjects.length === 0" message="没有找到匹配的条目" />

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
