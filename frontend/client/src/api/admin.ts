import http from './http'
import type {
  ApiResponse, PageResult, SubjectListItem, SubjectDetail,
  CreateSubjectRequest, UpdateSubjectRequest, UserVO, ImportStatusVO,
} from '@/types'

export const adminApi = {
  // Subjects
  createSubject(data: CreateSubjectRequest) {
    return http.post<ApiResponse<SubjectDetail>>('/api/admin/subjects', data)
  },
  updateSubject(id: number, data: UpdateSubjectRequest) {
    return http.put<ApiResponse<SubjectDetail>>(`/api/admin/subjects/${id}`, data)
  },
  deleteSubject(id: number) {
    return http.delete<ApiResponse<string>>(`/api/admin/subjects/${id}`)
  },

  // Users
  getUsers(params: { page?: number; size?: number }) {
    return http.get<ApiResponse<PageResult<UserVO>>>('/api/admin/users', { params })
  },
  updateUserRole(id: number, role: string) {
    return http.put<ApiResponse<UserVO>>(`/api/admin/users/${id}/role`, { role })
  },

  // Import
  runImport() {
    return http.post<ApiResponse<string>>('/api/admin/import/run')
  },
  getImportStatus() {
    return http.get<ApiResponse<ImportStatusVO>>('/api/admin/import/status')
  },
}
