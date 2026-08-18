import { get } from './http';
import type { Paged, SubjectListItem, TagVO } from '../types';
export const list = () => get<TagVO[]>('/client/tags');
export const subjects = (tag: string, params: { page?: number; size?: number } = {}) => get<Paged<SubjectListItem>>(`/client/tags/${encodeURIComponent(tag)}/subjects`, params);
