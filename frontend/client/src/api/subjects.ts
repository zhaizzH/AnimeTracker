import http from './client';
import type { SubjectListVO, SubjectDetailVO, EpisodeVO, PageResult } from '@/types';

export interface SubjectSearchParams {
  q?: string;
  page?: number;
  size?: number;
  tag?: string[];
  scoreMin?: number;
  scoreMax?: number;
  year?: number;
  weekday?: number;
  sort?: string;
  order?: string;
}

export const subjectsApi = {
  list: (params?: { page?: number; size?: number; sort?: string; order?: string }) =>
    http.get<PageResult<SubjectListVO>>('/user/subjects', { params }),
  search: (params: SubjectSearchParams) =>
    http.get<PageResult<SubjectListVO>>('/user/subjects/search', { params }),
  season: (year: number, quarter: string, page?: number, size?: number) =>
    http.get<PageResult<SubjectListVO>>('/user/subjects/season', { params: { year, quarter, page, size } }),
  schedule: (params?: { weekday?: number; year?: number; quarter?: number; page?: number; size?: number }) =>
    http.get<PageResult<SubjectListVO>>('/user/subjects/schedule', { params }),
  detail: (id: number) => http.get<SubjectDetailVO>(`/user/subjects/${id}`),
  episodes: (id: number) => http.get<EpisodeVO[]>(`/user/subjects/${id}/episodes`),
};
