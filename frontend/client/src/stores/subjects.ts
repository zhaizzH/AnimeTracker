import { defineStore } from 'pinia'
import { ref } from 'vue'
import { subjectsApi } from '@/api/subjects'
import type { SubjectListItem, SubjectDetail, EpisodeVO } from '@/types'

export const useSubjectsStore = defineStore('subjects', () => {
  const list = ref<SubjectListItem[]>([])
  const detail = ref<SubjectDetail | null>(null)
  const episodes = ref<EpisodeVO[]>([])
  const total = ref(0)
  const page = ref(1)
  const size = ref(20)
  const loading = ref(false)
  const keyword = ref('')
  const scheduleList = ref<SubjectListItem[]>([])
  const scheduleLoading = ref(false)

  async function fetchList(params: {
    page?: number
    size?: number
    sort?: string
    order?: string
  } = {}) {
    loading.value = true
    try {
      const res = await subjectsApi.getList({
        page: params.page ?? page.value,
        size: params.size ?? size.value,
        sort: params.sort ?? 'score',
        order: params.order ?? 'desc',
      })
      list.value = res.data.data.content
      total.value = res.data.data.total
      page.value = res.data.data.page
    } finally {
      loading.value = false
    }
  }

  async function search(q: string, p = 1, s = 20) {
    loading.value = true
    keyword.value = q
    try {
      const res = await subjectsApi.search({ q, page: p, size: s })
      list.value = res.data.data.content
      total.value = res.data.data.total
      page.value = res.data.data.page
    } finally {
      loading.value = false
    }
  }

  async function fetchBySeason(year: number, quarter: string, p = 1, s = 20) {
    loading.value = true
    try {
      const res = await subjectsApi.getBySeason({ year, quarter, page: p, size: s })
      list.value = res.data.data.content
      total.value = res.data.data.total
      page.value = res.data.data.page
    } finally {
      loading.value = false
    }
  }

  async function fetchDetail(id: number) {
    loading.value = true
    try {
      const res = await subjectsApi.getDetail(id)
      detail.value = res.data.data
    } finally {
      loading.value = false
    }
  }

  async function fetchEpisodes(id: number) {
    try {
      const res = await subjectsApi.getEpisodes(id)
      episodes.value = res.data.data
    } catch {
      episodes.value = []
    }
  }

  async function fetchSchedule(year: number, quarter: string, weekday = -1) {
    scheduleLoading.value = true
    try {
      const res = await subjectsApi.getSchedule({ year, quarter, weekday, page: 1, size: 60 })
      scheduleList.value = res.data.data.content
    } catch {
      scheduleList.value = []
    } finally {
      scheduleLoading.value = false
    }
  }

  return {
    list, detail, episodes, total, page, size, loading, keyword,
    fetchList, search, fetchBySeason, fetchDetail, fetchEpisodes,
    scheduleList, scheduleLoading, fetchSchedule,
  }
})
