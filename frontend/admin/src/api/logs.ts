import http from './client';
import type { LogPageResult, LogQueryParams } from '../types/api';

export const logsApi = {
  list: (params: LogQueryParams) => http.get<LogPageResult>('/admin/logs', { params }),
};
