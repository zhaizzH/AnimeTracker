<script setup lang="ts">
import { ref, computed } from 'vue'
import { Clock, Calendar } from '@lucide/vue'
import { EPISODE_TYPES } from '@/types'
import type { EpisodeVO } from '@/types'

const props = defineProps<{
  episodes: EpisodeVO[]
}>()

// Group episodes by type
const grouped = computed(() => {
  const map = new Map<number, EpisodeVO[]>()
  for (const ep of props.episodes) {
    const list = map.get(ep.type) || []
    list.push(ep)
    map.set(ep.type, list)
  }
  // Sort types in order: 0, 1, 2, 3, 4
  return new Map([...map.entries()].sort((a, b) => a[0] - b[0]))
})

// Available type tabs
const typeTabs = computed(() => {
  const tabs: Array<{ type: number; label: string }> = []
  for (const typeKey of grouped.value.keys()) {
    tabs.push({ type: typeKey, label: EPISODE_TYPES[typeKey] || `类型${typeKey}` })
  }
  return tabs
})

const activeTab = ref<number | null>(null)

// Set initial tab to first available type
if (typeTabs.value.length > 0) {
  activeTab.value = typeTabs.value[0].type
}

const visibleEpisodes = computed(() => {
  if (activeTab.value === null) return []
  return grouped.value.get(activeTab.value) || []
})

function statusColor(status: string) {
  switch (status) {
    case 'Air': return 'bg-emerald-400'
    case 'Today': return 'bg-amber-400 animate-pulse'
    default: return 'bg-gray-400'
  }
}

function statusLabel(status: string) {
  switch (status) {
    case 'Air': return '已放送'
    case 'Today': return '今日'
    default: return '未放送'
  }
}

// Compute actual status based on airdate vs today
function computeStatus(ep: EpisodeVO): string {
  if (!ep.airdate) return ep.status || 'NA'
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const air = new Date(ep.airdate)
  if (isNaN(air.getTime())) return ep.status || 'NA'
  air.setHours(0, 0, 0, 0)
  const diff = air.getTime() - today.getTime()
  const dayDiff = diff / (1000 * 60 * 60 * 24)
  if (dayDiff < 0) return 'Air'
  if (dayDiff === 0) return 'Today'
  return 'NA'
}
</script>

<template>
  <div class="space-y-4">
    <!-- Type tabs -->
    <div v-if="typeTabs.length > 1" class="flex items-center gap-1 p-1 rounded-xl overflow-x-auto scrollbar-hide" style="background: var(--color-hover)">
      <button
        v-for="tab in typeTabs"
        :key="tab.type"
        class="inline-flex items-center shrink-0 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all duration-200"
        :class="activeTab === tab.type
          ? 'bg-primary-600 text-white shadow-sm shadow-primary-600/20'
          : ''"
        :style="activeTab !== tab.type ? 'color: var(--color-text-secondary)' : ''"
        @click="activeTab = tab.type"
      >
        {{ tab.label }}
        <span class="ml-1.5 text-xs opacity-70">{{ grouped.get(tab.type)?.length || 0 }}</span>
      </button>
    </div>

    <!-- Episode list -->
    <div class="divide-y" style="border: 1px solid var(--color-border); border-radius: 0.875rem; overflow: hidden; divide-color: var(--color-border)">
      <div
        v-for="ep in visibleEpisodes"
        :key="ep.id"
        class="flex items-center gap-3 sm:gap-4 px-4 py-3 transition-colors duration-150"
        :class="computeStatus(ep) === 'NA' ? 'opacity-60' : ''"
        style="background: var(--color-card)"
        @mouseenter="($event.currentTarget as HTMLElement).style.background = 'var(--color-hover)'"
        @mouseleave="($event.currentTarget as HTMLElement).style.background = 'var(--color-card)'"
      >
        <!-- Episode sort number -->
        <div
          class="flex items-center justify-center w-9 h-9 rounded-lg shrink-0 text-sm font-bold tabular-nums"
          :class="computeStatus(ep) === 'Air' ? 'bg-primary-500/15 text-primary-500' : ''"
          :style="computeStatus(ep) !== 'Air' ? 'background: var(--color-hover); color: var(--color-text)' : ''"
        >
          {{ ep.sort }}
        </div>

        <!-- Episode info -->
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium truncate" style="color: var(--color-text)">
            {{ ep.nameCn || ep.name || `第${ep.sort}话` }}
          </div>
          <div class="flex items-center gap-3 mt-1 text-xs" style="color: var(--color-text-secondary)">
            <span v-if="ep.duration" class="inline-flex items-center gap-1">
              <Clock :size="11" class="shrink-0 opacity-60" />
              <span>{{ ep.duration }}</span>
            </span>
            <span v-if="ep.airdate" class="inline-flex items-center gap-1">
              <Calendar :size="11" class="shrink-0 opacity-60" />
              <span>{{ ep.airdate }}</span>
            </span>
          </div>
        </div>

        <!-- Status badge -->
        <div class="flex items-center gap-1.5 shrink-0">
          <span class="w-2 h-2 rounded-full" :class="statusColor(computeStatus(ep))" />
          <span class="text-xs font-medium" style="color: var(--color-text-secondary)">
            {{ statusLabel(computeStatus(ep)) }}
          </span>
        </div>
      </div>

      <!-- Empty state within list -->
      <div
        v-if="visibleEpisodes.length === 0"
        class="flex items-center justify-center py-10 text-sm"
        style="color: var(--color-text-secondary); background: var(--color-card)"
      >
        暂无剧集数据
      </div>
    </div>
  </div>
</template>
