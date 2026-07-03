import http from './http'
import type { LoginResult, UserVO } from '@/types'

export const authApi = {
  login(username: string, password: string) {
    return http.post<any, { code: number; message: string; data: LoginResult }>('/user/auth/login', { username, password })
      .then(r => r.data)
  },
  register(username: string, password: string, email?: string) {
    return http.post<any, { code: number; message: string; data: LoginResult }>('/user/auth/register', { username, password, email })
      .then(r => r.data)
  },
  getProfile() {
    return http.get<any, { code: number; message: string; data: UserVO }>('/user/me')
      .then(r => r.data)
  },
  updateProfile(data: { nickname?: string; avatar?: string; email?: string }) {
    return http.put<any, { code: number; message: string; data: UserVO }>('/user/me', data)
      .then(r => r.data)
  },
}
