import { get, post } from '../http';
import type { Paged, UserRole, UserVO } from '../../types';
export const list = (params: { page?: number; size?: number } = {}) => get<Paged<UserVO>>('/admin/users', params);
export const updateRole = (id: number | string, role: UserRole) => post<UserVO>(`/admin/users/${id}/update-role`, { role });
export const updateEnabled = (id: number | string, enabled: boolean) => post<UserVO>(`/admin/users/${id}/update-enabled`, { enabled });
