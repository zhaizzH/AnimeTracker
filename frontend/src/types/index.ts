// ===================================================================
// AnimeTracker — 通用 TypeScript 类型定义
// ===================================================================

// 统一响应格式
export interface ApiResponse<T> {
  code: number
  message: string
  data: T | null
}

// 分页结果
export interface PageResult<T> {
  content: T[]
  total: number
  page: number
  size: number
}

// 条目列表 VO
export interface SubjectListVO {
  id: number
  bangumiId: number
  name: string
  nameCn: string | null
  type: number
  eps: number | null
  airDate: string | null
  image: string | null
  score: number | null
  rank: number | null
}

// 条目详情 VO
export interface SubjectDetailVO {
  id: number
  bangumiId: number
  name: string
  nameCn: string | null
  summary: string | null
  type: number
  eps: number | null
  volumes: number | null
  airDate: string | null
  airWeekday: number | null
  image: string | null
  score: number | null
  rank: number | null
  nsfw: boolean
  tags: TagVO[]
  createdAt: string
  updatedAt: string
}

// 剧集 VO
export interface EpisodeVO {
  id: number
  subjectId: number
  bangumiEpId: number | null
  type: number
  sort: number | null
  name: string | null
  nameCn: string | null
  duration: string | null
  airdate: string | null
  status: 'Air' | 'Today' | 'NA'
}

// 标签 VO
export interface TagVO {
  id: number
  name: string
  count: number
}

// 用户 VO
export interface UserVO {
  id: number
  username: string
  email: string | null
  nickname: string | null
  avatar: string | null
  role: 'USER' | 'ADMIN'
}

// 登录结果
export interface LoginResult {
  token: string
  user: UserVO
}

// 导入状态 VO
export interface ImportStatusVO {
  id: number
  mode: string
  seasonKey: string | null
  status: 'RUNNING' | 'COMPLETED' | 'FAILED'
  subjectCount: number
  startedAt: string
  completedAt: string | null
  errorMessage: string | null
}

// 聊天相关
export interface ChatSession {
  sessionId: string
  createdAt: string
  messageCount: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  toolsUsed?: string[]
}
