import http from './client';
import type { ImportRunParams, ImportStatusVO } from '../types/api';

export const importsApi = {
  run: (params: ImportRunParams) => http.post<void>('/admin/import/run', undefined, { params }),
  status: () => http.get<ImportStatusVO>('/admin/import/status'),
};
