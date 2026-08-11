import http from './client';
import type { LogQueryParams, OperationLogStatsVO, OperationLogVO, PageResult } from '../types/api';

export const logsApi = {
  list: (params: LogQueryParams) => http.get<PageResult<OperationLogVO>>('/admin/logs', { params }),
  stats: (params: LogQueryParams) => http.get<OperationLogStatsVO>('/admin/logs/stats', { params }),
};
