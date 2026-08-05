import http from './client';
import type { LoginDTO, LoginVO } from '../types/api';

export const authApi = {
  login: (data: LoginDTO) => http.post<LoginVO>('/user/auth/login', data),
  logout: () => http.post<void>('/user/auth/logout'),
};
