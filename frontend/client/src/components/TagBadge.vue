<script setup lang="ts">
import { Hash } from '@lucide/vue'
import type { TagVO } from '@/types'

const props = withDefaults(defineProps<{
  tag: TagVO | { name: string; count?: number }
  clickable?: boolean
}>(), {
  clickable: false,
})
</script>

<template>
  <router-link
    v-if="clickable"
    :to="`/tags/${tag.name}`"
    class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium transition-all duration-200 hover:shadow-sm"
    style="background: var(--color-hover); color: var(--color-text-secondary); border: 1px solid var(--color-border)"
    @mouseenter="($event.currentTarget as HTMLElement).style.borderColor = 'var(--color-primary)'"
    @mouseleave="($event.currentTarget as HTMLElement).style.borderColor = 'var(--color-border)'"
  >
    <Hash :size="12" class="opacity-60" />
    <span style="color: var(--color-text)">{{ tag.name }}</span>
    <span v-if="'count' in tag && tag.count != null" class="opacity-60 ml-0.5">{{ tag.count }}</span>
  </router-link>

  <span
    v-else
    class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium"
    style="background: var(--color-hover); color: var(--color-text-secondary); border: 1px solid var(--color-border)"
  >
    <Hash :size="12" class="opacity-60" />
    <span style="color: var(--color-text)">{{ tag.name }}</span>
    <span v-if="'count' in tag && tag.count != null" class="opacity-60 ml-0.5">{{ tag.count }}</span>
  </span>
</template>
