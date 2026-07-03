<script setup lang="ts">
defineProps<{
  currentPage: number
  total: number
  pageSize: number
}>()

const emit = defineEmits<{
  'page-change': [page: number]
}>()

function totalPages(): number {
  return Math.ceil(total / pageSize) || 1
}
</script>

<template>
  <div v-if="total > pageSize" class="flex items-center justify-center gap-2 mt-6">
    <button
      :disabled="currentPage <= 1"
      @click="emit('page-change', currentPage - 1)"
      class="px-3 py-1.5 text-sm border rounded disabled:opacity-40 hover:bg-gray-50"
    >
      上一页
    </button>
    <span class="text-sm text-gray-500">
      第 {{ currentPage }} / {{ totalPages() }} 页（共 {{ total }} 条）
    </span>
    <button
      :disabled="currentPage >= totalPages()"
      @click="emit('page-change', currentPage + 1)"
      class="px-3 py-1.5 text-sm border rounded disabled:opacity-40 hover:bg-gray-50"
    >
      下一页
    </button>
  </div>
</template>
