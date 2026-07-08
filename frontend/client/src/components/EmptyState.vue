<script setup lang="ts">
import { type Component } from 'vue'
import { Inbox } from '@lucide/vue'

const props = withDefaults(defineProps<{
  icon?: Component
  title: string
  description?: string
  actionText?: string
  actionTo?: string
}>(), {
  icon: Inbox,
})
</script>

<template>
  <div class="flex flex-col items-center justify-center py-16 px-6 text-center">
    <!-- Icon -->
    <div
      class="flex items-center justify-center w-16 h-16 rounded-2xl mb-5"
      style="background: var(--color-hover)"
    >
      <component :is="icon" :size="28" style="color: var(--color-text-secondary)" class="opacity-50" />
    </div>

    <!-- Title -->
    <h3 class="text-lg font-semibold mb-1.5" style="color: var(--color-text)">
      {{ title }}
    </h3>

    <!-- Description -->
    <p v-if="description" class="text-sm max-w-sm mb-5" style="color: var(--color-text-secondary)">
      {{ description }}
    </p>

    <!-- Action button -->
    <router-link
      v-if="actionText && actionTo"
      :to="actionTo"
      class="btn-primary"
    >
      {{ actionText }}
    </router-link>
    <button
      v-else-if="actionText"
      class="btn-primary"
      @click="$emit('action')"
    >
      {{ actionText }}
    </button>
  </div>
</template>
