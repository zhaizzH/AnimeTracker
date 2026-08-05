export interface ApiResult<T> {
  code: number;
  message: string;
  data: T;
}

export interface PageResult<T> {
  content: T[];
  total: number;
  page: number;
  size: number;
}

export interface LoginDTO {
  username: string;
  password: string;
}

export interface LoginVO {
  token: string;
  refreshToken: string;
  user: UserVO;
}

export interface UserVO {
  id: number;
  username: string;
  email: string;
  nickname: string;
  avatar: string | null;
  role: 'ADMIN' | 'USER';
  createdAt: string;
}

export interface SubjectListVO {
  id: number;
  name: string;
  nameCn: string;
  image: string | null;
  score: number;
  rank: number;
  eps: number;
  airDate: string;
  type: number;
  airWeekday: number;
  collectionTotal: number;
}

export interface SubjectDetailVO extends SubjectListVO {
  summary: string;
}

export interface SubjectUpsertDTO {
  bangumiId?: number;
  name: string;
  nameCn?: string;
  summary?: string;
  type?: number;
  eps?: number;
  airDate?: string;
  image?: string;
}

export interface SubjectQueryParams {
  q?: string;
  page?: number;
  size?: number;
  sort?: string;
  order?: string;
  tag?: string[];
  scoreMin?: number;
  scoreMax?: number;
  year?: number;
  weekday?: number;
}

export interface ImportRecordVO {
  id: number;
  season: string;
  startedAt: string;
  completedAt: string | null;
  status: 'RUNNING' | 'COMPLETED' | 'FAILED';
  subjectCount: number;
  errorMessage: string | null;
}

export interface ImportStatusVO {
  lastImportedAt: string | null;
  totalSubjects: number;
  recentRecords: ImportRecordVO[];
}

export type ImportMode = 'full' | 'season' | 'recent' | 'since';

export interface ImportRunParams {
  mode: ImportMode;
  key?: string;
  since?: string;
  workers?: number;
}

export interface OperationLogVO {
  id: number;
  userId: number;
  username: string;
  action: string;
  module: string;
  method: string;
  path: string;
  ip: string;
  userAgent: string;
  status: number;
  errorMsg: string | null;
  durationMs: number;
  createdAt: string;
}

export interface LogQueryParams {
  action?: string;
  module?: string;
  username?: string;
  userId?: number;
  start?: string;
  end?: string;
  page?: number;
  size?: number;
}

export interface DashboardOverviewVO {
  userCount: number;
  subjectCount: number;
  collectionCount: number;
  episodeCount: number;
  importCount: number;
  todayNewUsers: number;
  todayNewCollections: number;
  todayLogins: number;
}

export interface TrendPointVO {
  date: string;
  newUsers: number;
  newCollections: number;
  logins: number;
}

export interface CollectionStatsVO {
  types: { type: number; count: number }[];
  ratings: { rate: number; count: number }[];
}

export interface SubjectStatsVO {
  seasons: { seasonKey: string; count: number }[];
  importStatuses: { importStatus: number; count: number }[];
  importStat: { importTotal: number; importSucceeded: number; importFailed: number };
}

export interface HotSubjectVO {
  id: number;
  name: string;
  nameCn: string;
  image: string | null;
  collectionCount: number;
}

export interface AgentPrompt {
  promptKey: string;
  promptContent: string;
}

export interface AgentModelConfig {
  model: string;
  modelRoute: string;
  temperature: number;
  maxTokens: number;
  thinkingBudget: number;
}

export interface PromptUpdateDTO {
  promptContent: string;
}
