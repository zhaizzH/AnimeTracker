import http from './client';
import type { TagVO, SubjectListVO, PageResult } from '@/types';

export const tagsApi = {
  list: () => http.get<TagVO[]>('/user/tags'),
  subjects: (tag: string, params?: { page?: number; size?: number }) =>
    http.get<PageResult<SubjectListVO>>(`/user/tags/${tag}/subjects`, { params }),
};
