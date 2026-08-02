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
  schedule: (params?: { weekday?: number; year?: number; quarter?: string; page?: number; size?: number }) =>
    http.get<PageResult<SubjectListVO>>('/user/subjects/schedule', { params }),
  scheduleAll: async (params?: { weekday?: number; year?: number; quarter?: string }) => {
    const pageSize = 100;
    const content: SubjectListVO[] = [];
    const seen = new Set<number>();
    let page = 1;
    let total = 0;

    do {
      const result = await subjectsApi.schedule({ ...params, page, size: pageSize });
      total = result.total;
      (result.content || []).forEach((item) => {
        if (!seen.has(item.id)) {
          seen.add(item.id);
          content.push(item);
        }
      });
      if (!result.content?.length) break;
      page += 1;
    } while (content.length < total);

    return { content, total, page: 1, size: pageSize };
  },
  detail: (id: number) => http.get<SubjectDetailVO>(`/user/subjects/${id}`),
  episodes: (id: number) => http.get<EpisodeVO[]>(`/user/subjects/${id}/episodes`),
};
