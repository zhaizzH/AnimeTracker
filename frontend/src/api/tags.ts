import http from './http'
import type { TagVO, PageResult } from '@/types'

export const tagsApi = {
  list(page = 1, size = 50) {
    return http.get<any, { code: number; message: string; data: TagVO[] }>('/user/tags', { params: { page, size } })
      .then(r => r.data)
  },
  subjects(tag: string, page = 1, size = 20) {
    return http.get<any, { code: number; message: string; data: PageResult<SubjectListVO> }>(`/user/tags/${tag}/subjects`, { params: { page, size } })
      .then(r => r.data)
  },
}
