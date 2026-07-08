import http from './http'
import type { ApiResponse, TagVO, PageResult, SubjectListItem } from '@/types'

export const tagsApi = {
  getList() {
    return http.get<ApiResponse<TagVO[]>>('/api/user/tags')
  },
  getSubjects(tag: string, params: { page?: number; size?: number }) {
    return http.get<ApiResponse<PageResult<SubjectListItem>>>(`/api/user/tags/${tag}/subjects`, { params })
  },
}
