import http from './http'
import type { ApiResponse, AuthResult, LoginRequest, RegisterRequest, UserVO, UpdateProfileRequest, VerifyEmailRequest, SendEmailCodeRequest, VerifyEmailCodeRequest } from '@/types'

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
    return http.post<ApiResponse<string>>('/api/user/auth/logout')
  },
  refresh(refreshToken: string) {
    return http.post<ApiResponse<AuthResult>>('/api/user/auth/refresh', { refreshToken })
  },
  getMe() {
    return http.get<ApiResponse<UserVO>>('/api/user/me')
  },
  updateProfile(data: UpdateProfileRequest) {
    return http.put<ApiResponse<UserVO>>('/api/user/me', data)
  },
  sendEmailCode(data: SendEmailCodeRequest) {
    return http.post<ApiResponse<null>>('/api/user/me/send-email-code', data)
  },
  verifyEmailCode(data: VerifyEmailCodeRequest) {
    return http.post<ApiResponse<null>>('/api/user/me/verify-email-code', data)
  },
}
