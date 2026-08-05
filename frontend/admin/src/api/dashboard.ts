import http from './client';
import type {
  CollectionStatsVO,
  DashboardOverviewVO,
  HotSubjectVO,
  SubjectStatsVO,
  TrendPointVO,
} from '../types/api';

export const dashboardApi = {
  overview: () => http.get<DashboardOverviewVO>('/admin/dashboard/overview'),
  trends: (days: number) =>
    http.get<TrendPointVO[]>('/admin/dashboard/trends', { params: { days } }),
  collectionStats: () => http.get<CollectionStatsVO>('/admin/dashboard/collection-stats'),
  subjectStats: () => http.get<SubjectStatsVO>('/admin/dashboard/subject-stats'),
  hot: (limit = 5) => http.get<HotSubjectVO[]>('/admin/dashboard/hot', { params: { limit } }),
};
