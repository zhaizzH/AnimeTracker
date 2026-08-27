export interface ApiResult<T> { code: number; message: string; data: T }
export interface Paged<T> { content: T[]; total: number; page: number; size: number }
export type CollectionType = 1 | 2 | 3 | 4 | 5;
export type UserRole = 'USER' | 'ADMIN';

export interface UserVO { id: number; username: string; email: string; nickname?: string | null; avatar?: string | null; role: UserRole; enabled: boolean; createdAt: string }
export interface LoginVO { token: string; user: UserVO }

export interface SubjectListItem { id: string; name: string; nameCn?: string | null; image?: string | null; score: number; rank: number; eps: number; airDate?: string | null; type: number; airWeekday: number; collectionTotal: number }
export interface TagVO { id: number; name: string; count: number }
export interface RelationVO { relation: string; relatedSubject: SubjectListItem }
export interface SubjectDetail extends SubjectListItem { bangumiId: number; summary?: string | null; volumes?: number | null; nsfw: boolean; tags: TagVO[]; relations: RelationVO[]; createdAt: string; updatedAt: string }
export interface EpisodeVO { id: number; subjectId: string; type: number; sort: number; name: string; nameCn?: string | null; duration?: string | null; airdate?: string | null; description?: string | null; status: 'Air' | 'Today' | 'NA' }

export interface CollectionVO { id: number; subjectId: string; type: CollectionType; rate: number; epStatus: number; subject: SubjectListItem }
export type CollectionCounts = Record<string, number>; // keys '0'..'5'

export interface ImportRecordVO { id: number; season: string; startedAt: string; completedAt?: string | null; status: 'RUNNING' | 'COMPLETED' | 'FAILED'; subjectCount: number; errorMessage?: string | null }
export interface LogVO { id: number; userId?: number | null; username?: string | null; action: string; module: string; method?: string | null; path?: string | null; params?: string | null; ip?: string | null; userAgent?: string | null; status: 0 | 1; errorMsg?: string | null; durationMs: number; createdAt: string }
export interface LogStatsVO { total: number; failedCount: number; successCount: number; avgDurationMs: number }
export interface LogInner { content: LogVO[]; total: number; page: number; size: number; stats: LogStatsVO }
export interface LogsPage { content: LogInner; total: number; page: number; size: number }

export interface DashboardOverview { userCount: number; subjectCount: number; collectionCount: number; episodeCount: number; importCount: number; todayNewUsers: number; todayNewCollections: number; todayLogins: number }
export interface TrendPointVO { date: string; newUsers: number; newCollections: number; logins: number }
export interface CollectionStatsVO { types: Array<{ type: number; count: number }>; ratings: Array<{ rate: number; count: number }> }
export interface SubjectStatsVO { seasons: Array<{ seasonKey: string; count: number }>; importStatuses: Array<{ importStatus: number; count: number }>; importStat: { importTotal: number; importSucceeded: number; importFailed: number }; scoreCounts: Array<{ rate: number; count: number }> }
export interface HotItemVO { id: string; name: string; nameCn?: string | null; image?: string | null; collectionCount: number }

export interface WishlistResult { state: 'ADDED' | 'ALREADY_COLLECTED'; existingType?: CollectionType }
export interface PreviewItemVO { subjectId: string; subjectName: string; currentEpStatus: number; targetEpStatus: number; completedAfterUpdate: boolean; suggestMarkAsWatched: boolean }
export interface ProgressPreviewVO { previewId: string; state: 'PENDING' | 'PREVIEW_CHANGED' | 'COMPLETED'; expiresAt: unknown; weekStart: string; cutoffDate: string; items: PreviewItemVO[] }
export interface ExecutedItemVO { subjectId: string; subjectName: string; currentEpStatus: number; targetEpStatus: number; completedAfterUpdate: boolean; suggestMarkAsWatched: boolean }
export interface SkippedItemVO { subjectId: string; subjectName: string; currentEpStatus: number; targetEpStatus: number; reason: string }
export interface ExecuteResultVO { state: 'PENDING' | 'PREVIEW_CHANGED' | 'COMPLETED'; replayed: boolean; preview: ProgressPreviewVO | null; succeeded: ExecutedItemVO[]; skipped: SkippedItemVO[]; failed: SkippedItemVO[] }
