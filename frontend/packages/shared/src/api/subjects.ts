import { get } from './http';
import type { EpisodeVO, Paged, SubjectDetail, SubjectListItem } from '../types';
export interface SubjectListParams { page?: number; size?: number; sort?: string; order?: 'asc' | 'desc' }
export interface SubjectSearchParams extends SubjectListParams { q?: string; tag?: string[]; scoreMin?: number; scoreMax?: number; year?: number; weekday?: number }
export const list = (params: SubjectListParams = {}) => get<Paged<SubjectListItem>>('/client/subjects', params);
export const search = (params: SubjectSearchParams = {}) => get<Paged<SubjectListItem>>('/client/subjects/search', params);
export const season = (params: { year: number; quarter: string; page?: number; size?: number }) => get<Paged<SubjectListItem>>('/client/subjects/season', params);
export const schedule = (params: { weekday?: number; year?: number; quarter?: string; page?: number; size?: number } = {}) => get<Paged<SubjectListItem>>('/client/subjects/schedule', params);
export const detail = (id: number | string) => get<SubjectDetail>(`/client/subjects/${id}`);
export const episodes = (id: number | string) => get<EpisodeVO[]>(`/client/subjects/${id}/episodes`);
