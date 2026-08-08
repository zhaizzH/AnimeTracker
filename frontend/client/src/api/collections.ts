import http from './client';
import type { UserCollectionVO, CollectionUpdateDTO, EpStatusDTO, PageResult } from '@/types';

export const collectionsApi = {
  list: (params?: { type?: number; page?: number; size?: number }) =>
    http.get<PageResult<UserCollectionVO>>('/client/collections', { params }),
  get: (subjectId: number) =>
    http.get<UserCollectionVO>(`/client/collections/${subjectId}`),
  save: (subjectId: number, data: CollectionUpdateDTO) =>
    http.post(`/client/collections/${subjectId}/save`, data),
  remove: (subjectId: number) =>
    http.post(`/client/collections/${subjectId}/remove`),
  schedule: (params?: { weekday?: number; year?: number; quarter?: number; page?: number; size?: number }) =>
    http.get<PageResult<UserCollectionVO>>('/client/collections/schedule', { params }),
  updateEpStatus: (subjectId: number, data: EpStatusDTO) =>
    http.post(`/client/collections/${subjectId}/ep-status`, data),
};
