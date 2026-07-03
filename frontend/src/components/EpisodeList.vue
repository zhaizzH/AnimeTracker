<script setup lang="ts">
import type { EpisodeVO } from '@/types'

defineProps<{
  episodes: EpisodeVO[]
}>()
</script>

<template>
  <div class="space-y-1">
    <div v-for="ep in episodes" :key="ep.id" class="flex items-center justify-between py-2 px-3 bg-gray-50 rounded text-sm">
      <div class="flex items-center gap-3">
        <span class="text-gray-400 w-8 text-right font-mono text-xs">
          {{ ep.sort ? `#${ep.sort}` : '?' }}
        </span>
        <span class="text-gray-700 truncate">{{ ep.nameCn || ep.name || '未知标题' }}</span>
      </div>
      <div class="flex items-center gap-2 text-xs text-gray-400">
        <span v-if="ep.airdate">{{ ep.airdate }}</span>
        <span :class="{
          'text-green-500': ep.status === 'Air',
          'text-blue-500': ep.status === 'Today',
          'text-gray-400': ep.status === 'NA',
        }">
          {{ ep.status === 'Air' ? '已播出' : ep.status === 'Today' ? '今日' : '未播出' }}
        </span>
      </div>
    </div>
  </div>
</template>
