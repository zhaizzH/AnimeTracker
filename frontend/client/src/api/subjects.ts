import http from './http'
import type { ApiResponse, PageResult, SubjectListItem, SubjectDetail, EpisodeVO } from '@/types'

export const subjectsApi = {
  getList(params: { page?: number; size?: number; sort?: string; order?: string }) {
    return http.get<ApiResponse<PageResult<SubjectListItem>>>('/api/user/subjects', { params })
  },
  search(params: { q: string; page?: number; size?: number }) {
    return http.get<ApiResponse<PageResult<SubjectListItem>>>('/api/user/subjects/search', { params })
  },
  getBySeason(params: { year: number; quarter: string; page?: number; size?: number }) {
    return http.get<ApiResponse<PageResult<SubjectListItem>>>('/api/user/subjects/season', { params })
  },
  getSchedule(params: { weekday?: number; year?: number; quarter?: string; page?: number; size?: number }) {
    return http.get<ApiResponse<PageResult<SubjectListItem>>>('/api/user/subjects/schedule', { params })
  },
  getDetail(id: number) {
    return http.get<ApiResponse<SubjectDetail>>(`/api/user/subjects/${id}`)
  },
  getEpisodes(id: number) {
    return http.get<ApiResponse<EpisodeVO[]>>(`/api/user/subjects/${id}/episodes`)
  },
}
