import http from './client';
import type {
  EpisodeVO,
  PageResult,
  SubjectDetailVO,
  SubjectListVO,
  SubjectQueryParams,
  SubjectUpsertDTO,
} from '../types/api';

export const subjectsApi = {
  search: (params: SubjectQueryParams) =>
    http.get<PageResult<SubjectListVO>>('/client/subjects/search', { params }),
  detail: (id: number) => http.get<SubjectDetailVO>(`/client/subjects/${id}`),
  episodes: (id: number) => http.get<EpisodeVO[]>(`/client/subjects/${id}/episodes`),
  create: (data: SubjectUpsertDTO) => http.post<SubjectDetailVO>('/admin/subjects', data),
  update: (id: number, data: SubjectUpsertDTO) =>
    http.post<SubjectDetailVO>(`/admin/subjects/${id}/update`, data),
  remove: (id: number) => http.post<void>(`/admin/subjects/${id}/remove`),
};

export function uploadCommonFile(file: File, type: 'avatar' | 'cover') {
  const formData = new FormData();
  formData.append('file', file);
  return http.post<string>('/common/files/upload', formData, {
    params: { type },
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}
