import { post } from '../http';
import type { SubjectDetail } from '../../types';
export interface SubjectForm { bangumiId?: number; name: string; nameCn?: string; summary?: string; type?: number; eps?: number; airDate?: string; image?: string }
export const create = (d: SubjectForm) => post<SubjectDetail>('/admin/subjects', d);
export const update = (id: number | string, d: Partial<SubjectForm>) => post<SubjectDetail>(`/admin/subjects/${id}/update`, d);
export const remove = (id: number | string) => post<void>(`/admin/subjects/${id}/remove`);
