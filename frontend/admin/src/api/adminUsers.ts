import http from './client';
import type { PageResult, UserVO } from '../types/api';

export const adminUsersApi = {
  list: (params: { page?: number; size?: number }) =>
    http.get<PageResult<UserVO>>('/admin/users', { params }),
  updateRole: (id: number, role: 'ADMIN' | 'USER') =>
    http.post<void>(`/admin/users/${id}/update-role`, { role }),
};
