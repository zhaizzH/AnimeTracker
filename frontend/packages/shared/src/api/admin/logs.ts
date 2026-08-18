import { get } from '../http';
import type { LogsPage } from '../../types';
export const list = (params: { action?: string; module?: string; username?: string; userId?: number; status?: number; start?: string; end?: string; page?: number; size?: number } = {}) => get<LogsPage>('/admin/logs', params);
