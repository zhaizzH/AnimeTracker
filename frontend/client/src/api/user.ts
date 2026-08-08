import http from './client';
import type { UserVO, UpdateUserDTO, ChangePasswordDTO } from '@/types';

export const userApi = {
  profile: () => http.get<UserVO>('/client/me'),
  update: (data: UpdateUserDTO) => http.post<UserVO>('/client/me/update', data),
  changePassword: (data: ChangePasswordDTO) => http.post('/client/me/update-password', data),
  sendEmailCode: (newEmail: string) => http.post('/client/me/send-email-code', { newEmail }),
  verifyEmailCode: (newEmail: string, code: string) => http.post('/client/me/verify-email-code', { newEmail, code }),
};
