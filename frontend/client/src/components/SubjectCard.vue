<script setup lang="ts">
import { ref } from 'vue'
import { Calendar, PlayCircle } from '@lucide/vue'
import type { SubjectListItem } from '@/types'

const props = defineProps<{
  subject: SubjectListItem
}>()

const imgFailed = ref(false)

function handleImageError() {
  imgFailed.value = true
}

const displayName = props.subject.nameCn || props.subject.name
</script>

<template>
  <router-link
    :to="`/subject/${subject.id}`"
    class="group block app-card overflow-hidden"
  >
    <!-- Poster -->
    <div class="relative aspect-poster overflow-hidden rounded-t-xl">
      <!-- Fallback gradient background -->
      <div
        v-if="imgFailed"
        class="absolute inset-0 flex items-center justify-center"
        style="background: linear-gradient(135deg, #f1799222 0%, #845ef722 50%, #00a1d622 100%); background-color: var(--color-hover)"
      >
        <span class="text-3xl font-bold opacity-20" style="color: var(--color-text)">{{ subject.name?.charAt(0) || '?' }}</span>
      </div>

      <!-- Image -->
      <img
        v-if="!imgFailed && subject.image"
        :src="subject.image"
        :alt="displayName"
        class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
        @error="handleImageError"
      />

      <!-- No-image fallback -->
      <div
        v-if="!imgFailed && !subject.image"
        class="absolute inset-0 flex items-center justify-center"
        style="background: linear-gradient(135deg, #f1799222 0%, #845ef722 50%, #00a1d622 100%); background-color: var(--color-hover)"
      >
        <span class="text-3xl font-bold opacity-20" style="color: var(--color-text)">{{ subject.name?.charAt(0) || '?' }}</span>
      </div>

      <!-- Bottom overlay gradient -->
      <div class="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-black/70 via-black/30 to-transparent pointer-events-none" />

      <!-- Score & Rank badges (overlay on image) -->
      <div class="absolute bottom-2 left-2 flex items-center gap-1.5">
        <span v-if="subject.score > 0" class="badge-score">
          ★ {{ subject.score.toFixed(1) }}
        </span>
        <span v-if="subject.rank > 0" class="badge-rank">
          #{{ subject.rank }}
        </span>
      </div>
    </div>

    <!-- Info section -->
    <div class="p-3 space-y-2">
      <!-- Title -->
      <h3
        class="text-sm font-semibold leading-snug line-clamp-2 transition-colors duration-200"
        style="color: var(--color-text)"
        :title="displayName"
      >
        {{ displayName }}
      </h3>

      <!-- Meta info -->
      <div class="flex items-center gap-3 text-xs" style="color: var(--color-text-secondary)">
        <span v-if="subject.airDate" class="inline-flex items-center gap-1">
          <Calendar :size="12" class="shrink-0" />
          <span>{{ subject.airDate }}</span>
        </span>
        <span v-if="subject.eps > 0" class="inline-flex items-center gap-1">
          <PlayCircle :size="12" class="shrink-0" />
          <span>{{ subject.eps }}话</span>
        </span>
      </div>
    </div>
  </router-link>
</template>
