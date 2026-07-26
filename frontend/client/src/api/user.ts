import http from './client';
import type { UserVO, UpdateUserDTO, ChangePasswordDTO } from '@/types';

export const userApi = {
  profile: () => http.get<UserVO>('/user/me'),
  update: (data: UpdateUserDTO) => http.post<UserVO>('/user/me/update', data),
  changePassword: (data: ChangePasswordDTO) => http.post('/user/me/update-password', data),
  sendEmailCode: (newEmail: string) => http.post('/user/me/send-email-code', { newEmail }),
  verifyEmailCode: (newEmail: string, code: string) => http.post('/user/me/verify-email-code', { newEmail, code }),
};
