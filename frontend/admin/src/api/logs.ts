import http from './client';
import type { LogQueryParams, OperationLogVO, PageResult } from '../types/api';

export const logsApi = {
  list: (params: LogQueryParams) => http.get<PageResult<OperationLogVO>>('/admin/logs', { params }),
};
