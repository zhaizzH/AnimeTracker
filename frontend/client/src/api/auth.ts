import http from './client';
import type { LoginVO, LoginDTO, RegisterDTO, VerifyEmailDTO, ResendCodeDTO, ForgotPasswordDTO, ResetPasswordDTO, RefreshTokenDTO } from '@/types';

export const authApi = {
  register: (data: RegisterDTO) => http.post('/user/auth/register', data),
  verifyEmail: (data: VerifyEmailDTO) => http.post<LoginVO>('/user/auth/verify-email', data),
  resendCode: (data: ResendCodeDTO) => http.post('/user/auth/resend-code', data),
  login: (data: LoginDTO) => http.post<LoginVO>('/user/auth/login', data),
  forgotPassword: (data: ForgotPasswordDTO) => http.post('/user/auth/forgot-password', data),
  resetPassword: (data: ResetPasswordDTO) => http.post('/user/auth/reset-password', data),
  refresh: (data: RefreshTokenDTO) => http.post<LoginVO>('/user/auth/refresh', data),
  logout: () => http.post('/user/auth/logout'),
};
