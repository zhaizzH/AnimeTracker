import { get, post } from '../http';
import type { ImportRecordVO, Paged } from '../../types';
export const run = (params: { mode: 'full' | 'season' | 'recent' | 'since'; key?: string; since?: string; workers?: number }) => post<string>('/admin/import/run?' + new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined && v !== '').map(([k, v]) => [k, String(v)])).toString());
export const status = () => get<{ lastImportedAt?: string | null; totalLogs: number; completedCount: number; failedCount: number }>('/admin/import/status');
export const records = (params: { page?: number; size?: number; status?: string } = {}) => get<Paged<ImportRecordVO>>('/admin/import/records', params);
