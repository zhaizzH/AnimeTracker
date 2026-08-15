import http from './client';
import type { LoginVO, LoginDTO, RegisterDTO, VerifyEmailDTO, ResendCodeDTO, ForgotPasswordDTO, ResetPasswordDTO } from '@/types';

export const authApi = {
  register: (data: RegisterDTO) => http.post('/client/auth/register', data),
  verifyEmail: (data: VerifyEmailDTO) => http.post<LoginVO>('/client/auth/verify-email', data),
  resendCode: (data: ResendCodeDTO) => http.post('/client/auth/resend-code', data),
  login: (data: LoginDTO) => http.post<LoginVO>('/client/auth/login', data),
  forgotPassword: (data: ForgotPasswordDTO) => http.post('/client/auth/forgot-password', data),
  resetPassword: (data: ResetPasswordDTO) => http.post('/client/auth/reset-password', data),
  logout: () => http.post('/client/auth/logout'),
};
