import http from './http'
import type { UserVO, PageResult, SubjectDetailVO, ImportStatusVO } from '@/types'

export const usersApi = {
  list(page = 1, size = 20) {
    return http.get<any, { code: number; message: string; data: PageResult<UserVO> }>('/admin/users', { params: { page, size } })
      .then(r => r.data)
  },
  updateRole(id: number, role: string) {
    return http.put<any, { code: number; message: string; data: UserVO }>(`/admin/users/${id}/role`, { role })
      .then(r => r.data)
  },
}

export const adminSubjectsApi = {
  create(data: any) {
    return http.post<any, { code: number; message: string; data: SubjectDetailVO }>('/admin/subjects', data)
      .then(r => r.data)
  },
  update(id: number, data: any) {
    return http.put<any, { code: number; message: string; data: SubjectDetailVO }>(`/admin/subjects/${id}`, data)
      .then(r => r.data)
  },
  delete(id: number) {
    return http.delete<any, { code: number; message: string; data: null }>(`/admin/subjects/${id}`)
      .then(r => r.data)
  },
}

export const importApi = {
  run(mode?: string, seasonKey?: string) {
    return http.post<any, { code: number; message: string; data: ImportStatusVO }>('/admin/import/run', { mode, season_key: seasonKey })
      .then(r => r.data)
  },
  status() {
    return http.get<any, { code: number; message: string; data: ImportStatusVO }>('/admin/import/status')
      .then(r => r.data)
  },
}

export const cacheApi = {
  clear(key: string) {
    return http.delete<any, { code: number; message: string; data: null }>(`/admin/cache/${key}`)
      .then(r => r.data)
  },
}
