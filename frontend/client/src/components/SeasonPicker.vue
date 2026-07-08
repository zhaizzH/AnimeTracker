<script setup lang="ts">
import { ChevronLeft, ChevronRight } from '@lucide/vue'

const props = defineProps<{
  year: number
  quarter: string
}>()

const emit = defineEmits<{
  'update:year': [year: number]
  'update:quarter': [quarter: string]
}>()

const quarters = [
  { key: 'winter', label: '冬季' },
  { key: 'spring', label: '春季' },
  { key: 'summer', label: '夏季' },
  { key: 'fall', label: '秋季' },
]

function prevYear() {
  emit('update:year', props.year - 1)
}

function nextYear() {
  emit('update:year', props.year + 1)
}

function selectQuarter(key: string) {
  emit('update:quarter', key)
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-3 sm:gap-4">
    <!-- Year selector -->
    <div class="flex items-center gap-1">
      <button
        class="inline-flex items-center justify-center w-8 h-8 rounded-lg transition-colors duration-200"
        style="color: var(--color-text-secondary)"
        @click="prevYear"
        aria-label="上一年"
      >
        <ChevronLeft :size="16" />
      </button>

      <span
        class="inline-flex items-center justify-center min-w-[4rem] h-8 px-3 rounded-lg text-sm font-semibold tabular-nums"
        style="color: var(--color-text)"
      >
        {{ year }}年
      </span>

      <button
        class="inline-flex items-center justify-center w-8 h-8 rounded-lg transition-colors duration-200"
        style="color: var(--color-text-secondary)"
        @click="nextYear"
        aria-label="下一年"
      >
        <ChevronRight :size="16" />
      </button>
    </div>

    <!-- Quarter tabs -->
    <div class="flex items-center gap-1 p-1 rounded-xl" style="background: var(--color-hover)">
      <button
        v-for="q in quarters"
        :key="q.key"
        class="inline-flex items-center px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all duration-200"
        :class="quarter === q.key
          ? 'bg-primary-600 text-white shadow-sm shadow-primary-600/20'
          : ''"
        :style="quarter !== q.key ? 'color: var(--color-text-secondary)' : ''"
        @click="selectQuarter(q.key)"
      >
        {{ q.label }}
      </button>
    </div>
  </div>
</template>
