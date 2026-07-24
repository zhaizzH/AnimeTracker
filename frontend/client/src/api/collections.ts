import http from './http'
import type { ApiResponse, PageResult, SubjectListItem } from '@/types'

export const COLLECTION_TYPES: Record<number, string> = {
  1: '想看',
  2: '看过',
  3: '在看',
  4: '搁置',
  5: '抛弃',
}

export interface UserCollectionVO {
  id: number
  subjectId: number
  type: number
  rate: number
  epStatus: number
  subject: SubjectListItem
}

export interface UpsertCollectionRequest {
  type: number
  rate?: number
  epStatus?: number
}

export const collectionsApi = {
  getList(params: { type?: number; page?: number; size?: number }) {
    return http.get<ApiResponse<PageResult<UserCollectionVO>>>('/api/user/collections', { params })
  },
  getDetail(subjectId: number) {
    return http.get<ApiResponse<UserCollectionVO>>(`/api/user/collections/${subjectId}`)
  },
  upsert(subjectId: number, data: UpsertCollectionRequest) {
    return http.put<ApiResponse<string>>(`/api/user/collections/${subjectId}`, data)
  },
  remove(subjectId: number) {
    return http.delete<ApiResponse<string>>(`/api/user/collections/${subjectId}`)
  },
  updateEpStatus(subjectId: number, epStatus: number) {
    return http.put<ApiResponse<string>>(`/api/user/collections/${subjectId}/ep-status`, { epStatus })
  },
}
