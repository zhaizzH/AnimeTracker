export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface PageResult<T> {
  content: T[]
  total: number
  page: number
  size: number
}

export interface TagVO {
  id: number
  name: string
  count: number
}

export interface SubjectListItem {
  id: number
  name: string
  nameCn: string
  image: string
  score: number
  rank: number
  eps: number
  airDate: string
  type: number
}

export interface SubjectDetail extends SubjectListItem {
  bangumiId: number
  summary: string
  volumes: number
  airWeekday: number
  collectionTotal: number
  nsfw: boolean
  tags: TagVO[]
  createdAt: string
  updatedAt: string
}

export interface EpisodeVO {
  id: number
  subjectId: number
  type: number // 0=本篇 1=SP 2=OP 3=ED 4=预告
  sort: number
  name: string
  nameCn: string
  duration: string
  airdate: string
  description: string
  status: 'Air' | 'Today' | 'NA'
}

export interface UserVO {
  id: number
  username: string
  email: string
  nickname: string
  avatar: string
  role: 'USER' | 'ADMIN'
  createdAt: string
}

export interface AuthResult {
  token: string
  user: UserVO
}

export interface ImportRecordVO {
  id: number
  season: string
  startedAt: string
  completedAt: string | null
  status: 'RUNNING' | 'COMPLETED' | 'FAILED'
  subjectCount: number
  errorMessage: string | null
}

export interface ImportStatusVO {
  lastImportedAt: string | null
  totalSubjects: number
  recentRecords: ImportRecordVO[]
}

export interface CreateSubjectRequest {
  bangumiId?: number
  name: string
  nameCn?: string
  summary?: string
  type?: number
  eps?: number
  airDate?: string
  image?: string
}

export interface UpdateSubjectRequest {
  name?: string
  nameCn?: string
  summary?: string
  type?: number
  eps?: number
  airDate?: string
  image?: string
}

export interface UpdateProfileRequest {
  nickname?: string
  avatar?: string
  email?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string
}

export const EPISODE_TYPES: Record<number, string> = {
  0: '本篇',
  1: 'SP',
  2: 'OP',
  3: 'ED',
  4: '预告',
}

export const SUBJECT_TYPES: Record<number, string> = {
  1: '书籍',
  2: '动画',
  3: '音乐',
  4: '游戏',
  6: '三次元',
}

export const WEEKDAYS: Record<number, string> = {
  0: '周日',
  1: '周一',
  2: '周二',
  3: '周三',
  4: '周四',
  5: '周五',
  6: '周六',
}

export const QUARTERS: Record<string, string> = {
  winter: '冬季 (1月)',
  spring: '春季 (4月)',
  summer: '夏季 (7月)',
  fall: '秋季 (10月)',
}
