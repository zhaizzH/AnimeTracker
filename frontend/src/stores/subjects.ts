import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { SubjectListVO, SubjectDetailVO } from '@/types'
import { subjectsApi } from '@/api/subjects'

export const useSubjectsStore = defineStore('subjects', () => {
  const subjects = ref<SubjectListVO[]>([])
  const currentPage = ref(1)
  const total = ref(0)
  const pageSize = ref(20)
  const sort = ref('created_at')
  const order = ref('desc')
  const loading = ref(false)

  async function fetchSubjects(page = 1, size = 20) {
    loading.value = true
    try {
      const res = await subjectsApi.list(page, size, sort.value, order.value)
      subjects.value = res.content
      total.value = res.total
      currentPage.value = res.page
      pageSize.value = res.size
    } finally {
      loading.value = false
    }
  }

  async function fetchSeasonSubjects(year: number, quarter: string, page = 1, size = 20) {
    loading.value = true
    try {
      const res = await subjectsApi.season(year, quarter, page, size)
      subjects.value = res.content
      total.value = res.total
      currentPage.value = res.page
      pageSize.value = res.size
    } finally {
      loading.value = false
    }
  }

  async function searchSubjects(keyword: string, page = 1, size = 20) {
    loading.value = true
    try {
      const res = await subjectsApi.search(keyword, page, size)
      subjects.value = res.content
      total.value = res.total
      currentPage.value = res.page
      pageSize.value = res.size
    } finally {
      loading.value = false
    }
  }

  return {
    subjects, currentPage, total, pageSize, sort, order, loading,
    fetchSubjects, fetchSeasonSubjects, searchSubjects,
  }
})
