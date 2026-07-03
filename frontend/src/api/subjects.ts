import http from './http'
import type { SubjectListVO, SubjectDetailVO, EpisodeVO, PageResult } from '@/types'

export const subjectsApi = {
  list(page = 1, size = 20, sort = 'created_at', order = 'desc') {
    return http.get<any, { code: number; message: string; data: PageResult<SubjectListVO> }>('/user/subjects', { params: { page, size, sort, order } })
      .then(r => r.data)
  },
  search(q: string, page = 1, size = 20) {
    return http.get<any, { code: number; message: string; data: PageResult<SubjectListVO> }>('/user/subjects/search', { params: { q, page, size } })
      .then(r => r.data)
  },
  season(year: number, quarter: string, page = 1, size = 20) {
    return http.get<any, { code: number; message: string; data: PageResult<SubjectListVO> }>('/user/subjects/season', { params: { year, quarter, page, size } })
      .then(r => r.data)
  },
  detail(id: number) {
    return http.get<any, { code: number; message: string; data: SubjectDetailVO }>(`/user/subjects/${id}`)
      .then(r => r.data)
  },
  episodes(id: number) {
    return http.get<any, { code: number; message: string; data: EpisodeVO[] }>(`/user/subjects/${id}/episodes`)
      .then(r => r.data)
  },
}
