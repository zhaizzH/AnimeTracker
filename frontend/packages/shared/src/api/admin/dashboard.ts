import { get } from '../http';
import type { CollectionStatsVO, DashboardOverview, HotItemVO, SubjectStatsVO, TrendPointVO } from '../../types';
export const overview = () => get<DashboardOverview>('/admin/dashboard/overview');
export const trends = (days: number) => get<TrendPointVO[]>('/admin/dashboard/trends', { days });
export const collectionStats = () => get<CollectionStatsVO>('/admin/dashboard/collection-stats');
export const subjectStats = () => get<SubjectStatsVO>('/admin/dashboard/subject-stats');
export const hot = (limit = 10) => get<HotItemVO[]>('/admin/dashboard/hot', { limit });
