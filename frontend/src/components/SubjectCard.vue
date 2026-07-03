<script setup lang="ts">
import type { SubjectListVO } from '@/types'

defineProps<{
  subject: SubjectListVO
}>()
</script>

<template>
  <router-link :to="`/subject/${subject.id}`" class="block bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow overflow-hidden">
    <!-- 封面图 -->
    <div class="aspect-[3/4] bg-gray-100 overflow-hidden">
      <img
        v-if="subject.image"
        :src="subject.image"
        :alt="subject.nameCn || subject.name"
        class="w-full h-full object-cover"
        loading="lazy"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-gray-400 text-sm">
        无封面
      </div>
    </div>
    <!-- 信息 -->
    <div class="p-2.5">
      <h3 class="text-sm font-medium text-gray-900 truncate" :title="subject.nameCn || subject.name">
        {{ subject.nameCn || subject.name }}
      </h3>
      <p v-if="subject.score" class="text-xs text-yellow-600 mt-0.5">
        {{ subject.score.toFixed(1) }} 分
      </p>
    </div>
  </router-link>
</template>
