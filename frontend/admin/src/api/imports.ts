import http from './client';
import type { ImportRecordVO, ImportRunParams, ImportStatusVO, PageResult } from '../types/api';

export const importsApi = {
  run: (params: ImportRunParams) => http.post<void>('/admin/import/run', undefined, { params }),
  status: () => http.get<ImportStatusVO>('/admin/import/status'),
  records: (params?: { page?: number; size?: number; status?: string }) =>
    http.get<PageResult<ImportRecordVO>>('/admin/import/records', { params }),
};
