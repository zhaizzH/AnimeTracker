import http from './client';
import type { TagVO } from '@/types';

export const tagsApi = {
  list: () => http.get<TagVO[]>('/client/tags'),
};
