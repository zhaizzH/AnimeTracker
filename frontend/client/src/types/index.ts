// 通用响应包装
export interface ApiResult<T> {
  code: number;
  message: string;
  data: T;
}

// 分页结果
export interface PageResult<T> {
  content: T[];
  total: number;
  page: number;
  size: number;
}

// 用户相关
export interface UserVO {
  id: number;
  username: string;
  email: string;
  nickname: string;
  avatar: string;
  role: 'USER' | 'ADMIN';
  createdAt: string;
}

export interface LoginVO {
  token: string;
  refreshToken: string;
  user: UserVO;
}

export interface LoginDTO {
  username: string;
  password: string;
}

export interface RegisterDTO {
  username: string;
  password: string;
  email: string;
}

export interface VerifyEmailDTO {
  email: string;
  code: string;
}

export interface ResendCodeDTO {
  email: string;
}

export interface ForgotPasswordDTO {
  email: string;
}

export interface ResetPasswordDTO {
  email: string;
  code: string;
  newPassword: string;
}

export interface RefreshTokenDTO {
  refreshToken: string;
}

export interface UpdateUserDTO {
  nickname?: string;
  avatar?: string;
}

export interface ChangePasswordDTO {
  oldPassword: string;
  newPassword: string;
}

export interface SendEmailCodeDTO {
  newEmail: string;
}

export interface VerifyEmailCodeDTO {
  newEmail: string;
  code: string;
}

// 番剧相关
export interface SubjectListVO {
  id: number;
  name: string;
  nameCn: string;
  image: string;
  score: number;
  rank: number;
  eps: number;
  airDate: string;
  type: number;
  airWeekday: number;
  collectionTotal: number;
}

export interface TagVO {
  id: number;
  name: string;
  count: number;
}

export interface SubjectRelationVO {
  relation: string;
  relatedSubject: SubjectListVO;
}

export interface SubjectDetailVO {
  id: number;
  name: string;
  nameCn: string;
  image: string;
  score: number;
  rank: number;
  eps: number;
  airDate: string;
  type: number;
  airWeekday: number;
  collectionTotal: number;
  bangumiId: number;
  summary: string;
  volumes: number;
  nsfw: boolean;
  tags: TagVO[];
  relations: SubjectRelationVO[];
  createdAt: string;
  updatedAt: string;
}

export interface EpisodeVO {
  id: number;
  subjectId: number;
  type: number;
  sort: number;
  name: string;
  nameCn: string;
  duration: string;
  airdate: string;
  description: string;
  status: 'Air' | 'Today' | 'NA';
}

// 收藏相关
export const CollectionType = {
  WISH: 1,     // 想看
  DONE: 2,     // 看过
  DOING: 3,    // 在看
  ON_HOLD: 4,  // 搁置
  DROPPED: 5,  // 抛弃
} as const;

export interface UserCollectionVO {
  id: number;
  subjectId: number;
  type: 1 | 2 | 3 | 4 | 5;
  rate: number;
  epStatus: number;
  subject: SubjectListVO;
}

export interface CollectionUpdateDTO {
  type: 1 | 2 | 3 | 4 | 5;
  rate?: number;
  epStatus?: number;
}

export interface EpStatusDTO {
  epStatus: number;
}
