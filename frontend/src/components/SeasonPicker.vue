<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ref } from 'vue'

const router = useRouter()
const currentYear = new Date().getFullYear()
const currentQuarter = ref(getCurrentQuarter())

const seasons = [
  { value: 'winter', label: '冬季 (1-3月)' },
  { value: 'spring', label: '春季 (4-6月)' },
  { value: 'summer', label: '夏季 (7-9月)' },
  { value: 'autumn', label: '秋季 (10-12月)' },
]

const years = ref(Array.from({ length: 10 }, (_, i) => currentYear - 5 + i))

function getCurrentQuarter(): string {
  const m = new Date().getMonth() + 1
  if (m <= 3) return 'winter'
  if (m <= 6) return 'spring'
  if (m <= 9) return 'summer'
  return 'autumn'
}

function goToSeason(year: number, quarter: string) {
  router.push(`/season/${year}/${quarter}`)
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-2">
    <select v-model="currentQuarter" class="text-sm border rounded px-2 py-1.5">
      <option v-for="s in seasons" :key="s.value" :value="s.value">{{ s.label }}</option>
    </select>
    <select v-model.number="currentYear" class="text-sm border rounded px-2 py-1.5">
      <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
    </select>
    <button @click="goToSeason(currentYear, currentQuarter)" class="text-sm bg-indigo-600 text-white px-3 py-1.5 rounded hover:bg-indigo-700">
      浏览
    </button>
  </div>
</template>
