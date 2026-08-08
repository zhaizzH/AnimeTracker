import http from './client';
import type { TagVO, SubjectListVO, PageResult } from '@/types';

export const tagsApi = {
  list: () => http.get<TagVO[]>('/client/tags'),
  subjects: (tag: string, params?: { page?: number; size?: number }) =>
    http.get<PageResult<SubjectListVO>>(`/client/tags/${tag}/subjects`, { params }),
};
