import http from './client';
import type { LoginDTO, LoginVO } from '../types/api';

export const authApi = {
  login: (data: LoginDTO) => http.post<LoginVO>('/client/auth/login', data),
  logout: () => http.post<void>('/client/auth/logout'),
};
