import http from './http'
import type { ApiResponse, AuthResult, LoginRequest, RegisterRequest, UserVO, UpdateProfileRequest, VerifyEmailRequest } from '@/types'

export const authApi = {
  login(data: LoginRequest) {
    return http.post<ApiResponse<AuthResult>>('/api/user/auth/login', data)
  },
  register(data: RegisterRequest) {
    return http.post<ApiResponse<string>>('/api/user/auth/register', data)
  },
  verifyEmail(data: VerifyEmailRequest) {
    return http.post<ApiResponse<AuthResult>>('/api/user/auth/verify-email', data)
  },
  resendCode(email: string) {
    return http.post<ApiResponse<null>>('/api/user/auth/resend-code', { email })
  },
  logout() {
    return http.get<ApiResponse<string>>('/api/user/auth/logout')
  },
  getMe() {
    return http.get<ApiResponse<UserVO>>('/api/user/me')
  },
  updateProfile(data: UpdateProfileRequest) {
    return http.put<ApiResponse<UserVO>>('/api/user/me', data)
  },
}
