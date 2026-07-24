<script setup lang="ts">
import { computed } from 'vue'
import { ChevronLeft, ChevronRight } from '@lucide/vue'

const props = withDefaults(defineProps<{
  currentPage: number
  totalPages: number
  variant?: 'solid' | 'bordered'
  maxVisible?: number
}>(), {
  variant: 'solid',
  maxVisible: 7,
})

const emit = defineEmits<{
  'update:page': [page: number]
}>()

const pages = computed(() => {
  const total = props.totalPages
  const current = props.currentPage
  const maxVisible = props.maxVisible

  if (total <= maxVisible) {
    return Array.from({ length: total }, (_, i) => ({ type: 'page' as const, value: i + 1 }))
  }

  const result: Array<{ type: 'page' | 'ellipsis'; value: number }> = []

  // Always show first page
  result.push({ type: 'page', value: 1 })

  let start = Math.max(2, current - 2)
  let end = Math.min(total - 1, current + 2)

  // Adjust range to keep consistent window size
  if (current <= 3) {
    end = Math.min(total - 1, maxVisible - 2)
  } else if (current >= total - 2) {
    start = Math.max(2, total - (maxVisible - 3))
  }

  if (start > 2) {
    result.push({ type: 'ellipsis', value: -1 })
  }

  for (let i = start; i <= end; i++) {
    result.push({ type: 'page', value: i })
  }

  if (end < total - 1) {
    result.push({ type: 'ellipsis', value: -2 })
  }

  // Always show last page
  result.push({ type: 'page', value: total })

  return result
})

function goTo(page: number) {
  if (page >= 1 && page <= props.totalPages && page !== props.currentPage) {
    emit('update:page', page)
  }
}
</script>

<template>
  <nav v-if="totalPages > 1" class="flex items-center justify-center gap-1 sm:gap-1.5" aria-label="分页导航">
    <!-- Previous button -->
    <button
      class="inline-flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-lg transition-all duration-200 disabled:opacity-30 disabled:pointer-events-none"
      style="color: var(--color-text-secondary)"
      :disabled="currentPage <= 1"
      @click="goTo(currentPage - 1)"
      aria-label="上一页"
    >
      <ChevronLeft :size="16" />
    </button>

    <!-- Page buttons -->
    <template v-for="item in pages" :key="item.value">
      <!-- Ellipsis -->
      <span
        v-if="item.type === 'ellipsis'"
        class="inline-flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 text-xs select-none"
        style="color: var(--color-text-secondary)"
      >
        ...
      </span>

      <!-- Page number -->
      <button
        v-else
        class="inline-flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-lg text-xs sm:text-sm font-medium transition-all duration-200"
        :class="{
          'bg-primary-600 text-white shadow-sm shadow-primary-600/25': variant === 'solid' && item.value === currentPage,
          'border-2 border-primary-500 text-primary-500 bg-[var(--color-card)]': variant === 'bordered' && item.value === currentPage,
          'border border-[var(--color-border)] bg-[var(--color-card)] hover:border-primary-500/50 hover:text-primary-500': variant === 'bordered' && item.value !== currentPage,
        }"
        :style="variant === 'solid' && item.value !== currentPage ? 'color: var(--color-text)' : (variant === 'bordered' && item.value !== currentPage ? 'color: var(--color-text-secondary)' : '')"
        @click="goTo(item.value)"
        :aria-label="`第 ${item.value} 页`"
        :aria-current="item.value === currentPage ? 'page' : undefined"
      >
        <span
          v-if="variant === 'solid' && item.value !== currentPage"
          class="rounded-lg w-full h-full inline-flex items-center justify-center transition-colors duration-150"
          style="background: transparent"
          @mouseenter="($event.target as HTMLElement).style.background = 'var(--color-hover)'"
          @mouseleave="($event.target as HTMLElement).style.background = 'transparent'"
        >
          {{ item.value }}
        </span>
        <template v-else>{{ item.value }}</template>
      </button>
    </template>

    <!-- Next button -->
    <button
      class="inline-flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-lg transition-all duration-200 disabled:opacity-30 disabled:pointer-events-none"
      style="color: var(--color-text-secondary)"
      :disabled="currentPage >= totalPages"
      @click="goTo(currentPage + 1)"
      aria-label="下一页"
    >
      <ChevronRight :size="16" />
    </button>
  </nav>
</template>
