<script setup lang="ts">
defineProps<{
  tag: { id: number; name: string; count: number }
  active?: boolean
}>()
</script>

<template>
  <router-link
    :to="`/tags/${tag.name}`"
    class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm transition-colors"
    :class="active ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
  >
    <span>{{ tag.name }}</span>
    <span class="text-xs opacity-60">({{ tag.count }})</span>
  </router-link>
</template>
