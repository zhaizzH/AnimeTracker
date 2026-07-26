import http from './client';
import type { UserCollectionVO, CollectionUpdateDTO, EpStatusDTO, PageResult } from '@/types';

export const collectionsApi = {
  list: (params?: { type?: number; page?: number; size?: number }) =>
    http.get<PageResult<UserCollectionVO>>('/user/collections', { params }),
  get: (subjectId: number) =>
    http.get<UserCollectionVO>(`/user/collections/${subjectId}`),
  save: (subjectId: number, data: CollectionUpdateDTO) =>
    http.post(`/user/collections/${subjectId}/save`, data),
  remove: (subjectId: number) =>
    http.post(`/user/collections/${subjectId}/remove`),
  schedule: (params?: { weekday?: number; year?: number; quarter?: number; page?: number; size?: number }) =>
    http.get<PageResult<UserCollectionVO>>('/user/collections/schedule', { params }),
  updateEpStatus: (subjectId: number, data: EpStatusDTO) =>
    http.post(`/user/collections/${subjectId}/ep-status`, data),
};
