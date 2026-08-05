import http from './client';
import type {
  PageResult,
  SubjectDetailVO,
  SubjectListVO,
  SubjectQueryParams,
  SubjectUpsertDTO,
} from '../types/api';

export const subjectsApi = {
  list: (params: SubjectQueryParams) =>
    http.get<PageResult<SubjectListVO>>('/user/subjects', { params }),
  create: (data: SubjectUpsertDTO) => http.post<SubjectDetailVO>('/admin/subjects', data),
  update: (id: number, data: SubjectUpsertDTO) =>
    http.post<SubjectDetailVO>(`/admin/subjects/${id}/update`, data),
  remove: (id: number) => http.post<void>(`/admin/subjects/${id}/remove`),
};
