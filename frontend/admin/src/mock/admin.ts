export interface AdminSubjectTag {
  id: number;
  name: string;
  count: number;
}

export interface AdminSubject {
  id: number;
  bangumiId: number;
  name: string;
  nameCn: string;
  summary: string;
  type: number;
  eps: number;
  airDate: string;
  airWeekday: number;
  score: number;
  rank: number;
  collectionTotal: number;
  volumes: number;
  nsfw: boolean;
  tags: AdminSubjectTag[];
  status: 'published' | 'pending' | 'hidden';
  createdAt: string;
  updatedAt: string;
  hue: number;
}

export interface AdminUser {
  id: number;
  username: string;
  email: string;
  nickname: string;
  role: 'USER' | 'ADMIN';
  createdAt: string;
  lastLoginAt: string;
  collectionCount: number;
  status: 'active' | 'disabled';
  hue: number;
}

export type ImportMode = 'full' | 'season' | 'recent' | 'since';
export type ImportStatus = 'RUNNING' | 'COMPLETED' | 'FAILED';

export interface ImportRecord {
  id: number;
  season: string;
  mode: ImportMode;
  startedAt: string;
  completedAt?: string;
  status: ImportStatus;
  subjectCount: number;
  workers: number;
  errorMessage?: string;
}

export interface AdminLog {
  id: number;
  userId: number;
  username: string;
  action: string;
  module: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  path: string;
  ip: string;
  userAgent: string;
  status: number;
  errorMsg?: string;
  durationMs: number;
  createdAt: string;
}

export interface AgentPrompt {
  key: string;
  label: string;
  description: string;
  content: string;
  defaultContent: string;
  updatedAt: string;
}

export interface AgentModelConfig {
  model: string;
  modelRoute: string;
  temperature: number;
  maxTokens: number;
  thinkingBudget: number;
}

export const subjects: AdminSubject[] = [
  {
    id: 498,
    bangumiId: 495123,
    name: 'ウマ娘 シンデレラグレイ',
    nameCn: '赛马娘 芦毛灰姑娘',
    summary: '以 Oguri Cap 的职业生涯为线索，讲述芦毛灰姑娘与赛马娘们奔跑的故事。',
    type: 2,
    eps: 24,
    airDate: '2026-07-02',
    airWeekday: 4,
    score: 8.6,
    rank: 12,
    collectionTotal: 3295,
    volumes: 12,
    nsfw: false,
    tags: [
      { id: 1, name: '运动', count: 1820 },
      { id: 2, name: '青春', count: 1430 },
      { id: 3, name: '竞技', count: 960 },
    ],
    status: 'published',
    createdAt: '2026-06-28 01:02:00',
    updatedAt: '2026-08-04 22:10:00',
    hue: 24,
  },
  {
    id: 484,
    bangumiId: 482901,
    name: 'BanG Dream! Ave Mujica',
    nameCn: 'BanG Dream! Ave Mujica',
    summary: '乐队少女们的舞台再度拉开，真实与虚构在演出中交织。',
    type: 2,
    eps: 13,
    airDate: '2026-01-03',
    airWeekday: 6,
    score: 8.9,
    rank: 4,
    collectionTotal: 4218,
    volumes: 7,
    nsfw: false,
    tags: [
      { id: 4, name: '音乐', count: 2210 },
      { id: 5, name: '原创', count: 1580 },
      { id: 6, name: '校园', count: 1240 },
    ],
    status: 'published',
    createdAt: '2025-12-20 03:15:00',
    updatedAt: '2026-08-03 19:02:00',
    hue: 175,
  },
  {
    id: 487,
    bangumiId: 486702,
    name: '葬送のフリーレン 第二期',
    nameCn: '葬送的芙莉莲 第二季',
    summary: '芙莉莲一行继续向北，在旅途中面对过去与未来的告别。',
    type: 2,
    eps: 24,
    airDate: '2026-01-09',
    airWeekday: 5,
    score: 9.1,
    rank: 2,
    collectionTotal: 3987,
    volumes: 12,
    nsfw: false,
    tags: [
      { id: 7, name: '奇幻', count: 2640 },
      { id: 8, name: '冒险', count: 1890 },
      { id: 9, name: '治愈', count: 1510 },
    ],
    status: 'published',
    createdAt: '2025-12-25 02:40:00',
    updatedAt: '2026-08-04 12:33:00',
    hue: 205,
  },
  {
    id: 492,
    bangumiId: 490115,
    name: '推しの子 サードシーズン',
    nameCn: '我推的孩子 第三季',
    summary: '聚光灯再次亮起，偶像与制作人面对新的舞台与风暴。',
    type: 2,
    eps: 13,
    airDate: '2026-04-08',
    airWeekday: 3,
    score: 8.4,
    rank: 18,
    collectionTotal: 3746,
    volumes: 7,
    nsfw: false,
    tags: [
      { id: 10, name: '偶像', count: 2010 },
      { id: 11, name: '演艺圈', count: 1420 },
      { id: 12, name: '悬疑', count: 860 },
    ],
    status: 'published',
    createdAt: '2026-03-30 05:22:00',
    updatedAt: '2026-08-02 10:14:00',
    hue: 330,
  },
  {
    id: 495,
    bangumiId: 491208,
    name: '機動戦士ガンダム GQuuuuuuX',
    nameCn: '机动战士高达 GQuuuuuuX',
    summary: '新类型驾驶员与神秘机体相遇，宇宙世纪重新展开。',
    type: 2,
    eps: 12,
    airDate: '2026-04-10',
    airWeekday: 5,
    score: 8.1,
    rank: 32,
    collectionTotal: 3512,
    volumes: 6,
    nsfw: false,
    tags: [
      { id: 13, name: '机战', count: 1860 },
      { id: 14, name: '科幻', count: 1730 },
      { id: 15, name: '原创', count: 980 },
    ],
    status: 'published',
    createdAt: '2026-04-01 08:30:00',
    updatedAt: '2026-08-01 16:40:00',
    hue: 258,
  },
  {
    id: 503,
    bangumiId: 493201,
    name: 'ぼっち・ざ・ろっく！ 第2期',
    nameCn: '孤独摇滚! 第二季',
    summary: '结束乐队继续排练、演出，少女们的夏天比想象中更喧闹。',
    type: 2,
    eps: 12,
    airDate: '2026-07-05',
    airWeekday: 0,
    score: 8.8,
    rank: 9,
    collectionTotal: 3021,
    volumes: 6,
    nsfw: false,
    tags: [
      { id: 16, name: '音乐', count: 1740 },
      { id: 17, name: '日常', count: 1310 },
      { id: 18, name: '喜剧', count: 990 },
    ],
    status: 'published',
    createdAt: '2026-06-30 04:11:00',
    updatedAt: '2026-08-05 08:18:00',
    hue: 322,
  },
  {
    id: 510,
    bangumiId: 497302,
    name: '劇場版 魔法少女まどか☆マギカ ワルプルギスの廻天',
    nameCn: '魔法少女小圆 剧场版 瓦尔普吉斯的回天',
    summary: '剧场版终章，圆与焰在轮回尽头做出的选择。',
    type: 2,
    eps: 1,
    airDate: '2026-04-19',
    airWeekday: 0,
    score: 9.0,
    rank: 6,
    collectionTotal: 2764,
    volumes: 1,
    nsfw: false,
    tags: [
      { id: 19, name: '魔法少女', count: 1680 },
      { id: 20, name: '剧场版', count: 1520 },
      { id: 21, name: '悬疑', count: 810 },
    ],
    status: 'pending',
    createdAt: '2026-07-12 06:45:00',
    updatedAt: '2026-08-05 07:55:00',
    hue: 285,
  },
  {
    id: 512,
    bangumiId: 498015,
    name: '薬屋のひとりごと 第2期',
    nameCn: '药屋少女的呢喃 第二季',
    summary: '猫猫继续在后宫与市井之间解开一桩桩谜案。',
    type: 2,
    eps: 24,
    airDate: '2026-01-11',
    airWeekday: 0,
    score: 8.7,
    rank: 15,
    collectionTotal: 2641,
    volumes: 12,
    nsfw: false,
    tags: [
      { id: 22, name: '推理', count: 1390 },
      { id: 23, name: '古风', count: 1120 },
      { id: 24, name: '日常', count: 780 },
    ],
    status: 'published',
    createdAt: '2025-12-30 09:05:00',
    updatedAt: '2026-07-30 14:26:00',
    hue: 45,
  },
  {
    id: 515,
    bangumiId: 499036,
    name: 'サマータイムレンダ：光陰編',
    nameCn: '夏日重现:光阴篇',
    summary: '和歌山夏日轮回的后续，潮与慎平的日常之后又起波澜。',
    type: 2,
    eps: 13,
    airDate: '2026-07-08',
    airWeekday: 3,
    score: 8.2,
    rank: 27,
    collectionTotal: 1893,
    volumes: 7,
    nsfw: false,
    tags: [
      { id: 25, name: '悬疑', count: 1220 },
      { id: 26, name: '轮回', count: 1080 },
      { id: 27, name: '冒险', count: 640 },
    ],
    status: 'published',
    createdAt: '2026-07-02 02:18:00',
    updatedAt: '2026-08-04 20:09:00',
    hue: 160,
  },
  {
    id: 520,
    bangumiId: 501204,
    name: 'ダンジョン飯 第2期',
    nameCn: '迷宫饭 第二季',
    summary: '莱欧斯一行在迷宫更深处继续寻找魔物料理与失落的真相。',
    type: 2,
    eps: 24,
    airDate: '2026-01-06',
    airWeekday: 2,
    score: 8.5,
    rank: 21,
    collectionTotal: 1725,
    volumes: 12,
    nsfw: false,
    tags: [
      { id: 28, name: '奇幻', count: 1330 },
      { id: 29, name: '美食', count: 1190 },
      { id: 30, name: '冒险', count: 710 },
    ],
    status: 'hidden',
    createdAt: '2025-12-18 07:20:00',
    updatedAt: '2026-07-29 18:42:00',
    hue: 95,
  },
];

export const users: AdminUser[] = [
  {
    id: 1,
    username: 'admin',
    email: 'admin@animetracker.local',
    nickname: '站点管理员',
    role: 'ADMIN',
    createdAt: '2025-11-02 09:12:00',
    lastLoginAt: '2026-08-05 08:42:11',
    collectionCount: 86,
    status: 'active',
    hue: 170,
  },
  {
    id: 10086,
    username: 'sakura_mikan',
    email: 'sakura@example.com',
    nickname: '樱庭美柑',
    role: 'USER',
    createdAt: '2026-08-05 07:02:00',
    lastLoginAt: '2026-08-05 09:10:44',
    collectionCount: 218,
    status: 'active',
    hue: 330,
  },
  {
    id: 10071,
    username: 'kaito_otaku',
    email: 'kaito@example.com',
    nickname: '海斗',
    role: 'USER',
    createdAt: '2026-08-05 05:36:00',
    lastLoginAt: '2026-08-05 05:36:00',
    collectionCount: 4,
    status: 'active',
    hue: 210,
  },
  {
    id: 10042,
    username: 'hanabi_rina',
    email: 'rina@example.com',
    nickname: '花火莉奈',
    role: 'USER',
    createdAt: '2026-08-02 14:22:00',
    lastLoginAt: '2026-08-04 22:18:30',
    collectionCount: 156,
    status: 'active',
    hue: 24,
  },
  {
    id: 9931,
    username: 'taro_hikari',
    email: 'taro@example.com',
    nickname: '光太郎',
    role: 'USER',
    createdAt: '2026-07-28 11:40:00',
    lastLoginAt: '2026-08-03 20:05:12',
    collectionCount: 89,
    status: 'active',
    hue: 95,
  },
  {
    id: 9805,
    username: 'mika_star',
    email: 'mika@example.com',
    nickname: '美嘉',
    role: 'USER',
    createdAt: '2026-07-20 16:02:00',
    lastLoginAt: '2026-08-02 12:44:51',
    collectionCount: 264,
    status: 'active',
    hue: 285,
  },
  {
    id: 9663,
    username: 'yuki_noel',
    email: 'yuki@example.com',
    nickname: '雪乃',
    role: 'USER',
    createdAt: '2026-07-11 03:28:00',
    lastLoginAt: '2026-08-01 09:22:40',
    collectionCount: 73,
    status: 'active',
    hue: 195,
  },
  {
    id: 9527,
    username: 'kenji_zero',
    email: 'kenji@example.com',
    nickname: '健二',
    role: 'USER',
    createdAt: '2026-07-03 21:55:00',
    lastLoginAt: '2026-07-30 18:02:19',
    collectionCount: 41,
    status: 'disabled',
    hue: 140,
  },
  {
    id: 9402,
    username: 'haru_sakura',
    email: 'haru@example.com',
    nickname: '春日',
    role: 'ADMIN',
    createdAt: '2026-06-25 10:09:00',
    lastLoginAt: '2026-08-04 17:30:08',
    collectionCount: 302,
    status: 'active',
    hue: 45,
  },
  {
    id: 9210,
    username: 'aoi_umi',
    email: 'aoi@example.com',
    nickname: '苍井',
    role: 'USER',
    createdAt: '2026-06-15 08:47:00',
    lastLoginAt: '2026-07-28 15:11:02',
    collectionCount: 128,
    status: 'active',
    hue: 205,
  },
];

export const importStatus = {
  lastImportedAt: '2026-08-05 02:41:18',
  totalLogs: 21,
};

export const importRecords: ImportRecord[] = [
  {
    id: 40,
    season: '2026-summer',
    mode: 'season',
    startedAt: '2026-08-05 02:12:30',
    status: 'RUNNING',
    subjectCount: 0,
    workers: 4,
  },
  {
    id: 39,
    season: '2026-spring',
    mode: 'season',
    startedAt: '2026-08-02 03:20:11',
    completedAt: '2026-08-02 03:47:02',
    status: 'COMPLETED',
    subjectCount: 74,
    workers: 4,
  },
  {
    id: 38,
    season: 'since 2026-01-01',
    mode: 'since',
    startedAt: '2026-07-30 02:05:44',
    completedAt: '2026-07-30 02:51:20',
    status: 'COMPLETED',
    subjectCount: 132,
    workers: 6,
  },
  {
    id: 37,
    season: '2025-autumn',
    mode: 'season',
    startedAt: '2026-07-24 04:02:19',
    completedAt: '2026-07-24 04:16:38',
    status: 'FAILED',
    subjectCount: 21,
    workers: 4,
    errorMessage: '部分条目抓取超时：Bangumi API 响应过慢',
  },
  {
    id: 36,
    season: 'ALL',
    mode: 'full',
    startedAt: '2026-07-18 01:10:00',
    completedAt: '2026-07-18 03:24:11',
    status: 'COMPLETED',
    subjectCount: 1206,
    workers: 8,
  },
  {
    id: 35,
    season: 'ALL',
    mode: 'recent',
    startedAt: '2026-07-12 02:48:36',
    completedAt: '2026-07-12 02:57:05',
    status: 'COMPLETED',
    subjectCount: 46,
    workers: 4,
  },
];

export const logs: AdminLog[] = [
  {
    id: 10241,
    userId: 1,
    username: 'admin',
    action: 'LOGIN_SUCCESS',
    module: 'AUTH',
    method: 'POST',
    path: '/api/auth/login',
    ip: '127.0.0.1',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/138.0',
    status: 200,
    durationMs: 86,
    createdAt: '2026-08-05 08:42:11',
  },
  {
    id: 10240,
    userId: 1,
    username: 'admin',
    action: 'UPDATE_SUBJECT',
    module: 'SUBJECT',
    method: 'POST',
    path: '/api/admin/subjects/484/update',
    ip: '127.0.0.1',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/138.0',
    status: 200,
    durationMs: 142,
    createdAt: '2026-08-05 08:39:27',
  },
  {
    id: 10239,
    userId: 9402,
    username: 'haru_sakura',
    action: 'UPDATE_PROMPT',
    module: 'AGENT',
    method: 'POST',
    path: '/api/admin/agent/prompts/client_search_agent_prompt/update',
    ip: '10.24.8.19',
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15',
    status: 200,
    durationMs: 58,
    createdAt: '2026-08-05 08:31:02',
  },
  {
    id: 10238,
    userId: 1,
    username: 'admin',
    action: 'RUN_IMPORT',
    module: 'IMPORT',
    method: 'POST',
    path: '/api/admin/import/run?mode=season&key=2026-summer',
    ip: '127.0.0.1',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/138.0',
    status: 200,
    durationMs: 2310,
    createdAt: '2026-08-05 02:12:30',
  },
  {
    id: 10237,
    userId: 1,
    username: 'admin',
    action: 'UPDATE_MODEL_CONFIG',
    module: 'AGENT',
    method: 'POST',
    path: '/api/admin/agent/config/update',
    ip: '127.0.0.1',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/138.0',
    status: 200,
    durationMs: 47,
    createdAt: '2026-08-04 21:50:16',
  },
  {
    id: 10236,
    userId: 10086,
    username: 'sakura_mikan',
    action: 'LOGIN_SUCCESS',
    module: 'AUTH',
    method: 'POST',
    path: '/api/auth/login',
    ip: '103.42.18.92',
    userAgent: 'Mozilla/5.0 (Linux; Android 14) Mobile Safari/537.36',
    status: 200,
    durationMs: 102,
    createdAt: '2026-08-04 22:18:30',
  },
  {
    id: 10235,
    userId: 9931,
    username: 'taro_hikari',
    action: 'CREATE_COLLECTION',
    module: 'COLLECTION',
    method: 'POST',
    path: '/api/collections',
    ip: '58.33.201.7',
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_4 like Mac OS X) Mobile Safari/604.1',
    status: 200,
    durationMs: 64,
    createdAt: '2026-08-04 20:05:12',
  },
  {
    id: 10234,
    userId: 1,
    username: 'admin',
    action: 'REMOVE_SUBJECT',
    module: 'SUBJECT',
    method: 'POST',
    path: '/api/admin/subjects/521/remove',
    ip: '127.0.0.1',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/138.0',
    status: 400,
    errorMsg: '条目仍被 3 个用户收藏，禁止直接删除',
    durationMs: 38,
    createdAt: '2026-08-04 19:44:58',
  },
  {
    id: 10233,
    userId: 9527,
    username: 'kenji_zero',
    action: 'QUERY_SUBJECTS',
    module: 'SUBJECT',
    method: 'GET',
    path: '/api/subjects?type=2&sort=rank',
    ip: '113.108.65.14',
    userAgent: 'curl/8.5.0',
    status: 200,
    durationMs: 121,
    createdAt: '2026-08-04 18:02:19',
  },
  {
    id: 10232,
    userId: 9402,
    username: 'haru_sakura',
    action: 'UPDATE_ROLE',
    module: 'USER',
    method: 'POST',
    path: '/api/admin/users/10042/update-role',
    ip: '10.24.8.19',
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15',
    status: 200,
    durationMs: 52,
    createdAt: '2026-08-03 17:30:08',
  },
  {
    id: 10231,
    userId: 9805,
    username: 'mika_star',
    action: 'LOGIN_FAILED',
    module: 'AUTH',
    method: 'POST',
    path: '/api/auth/login',
    ip: '112.90.77.31',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/126.0',
    status: 401,
    errorMsg: '用户名或密码错误',
    durationMs: 96,
    createdAt: '2026-08-03 12:44:51',
  },
  {
    id: 10230,
    userId: 1,
    username: 'admin',
    action: 'RESET_PROMPT',
    module: 'AGENT',
    method: 'POST',
    path: '/api/admin/agent/prompts/client_gateway_prompt/reset',
    ip: '127.0.0.1',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/138.0',
    status: 200,
    durationMs: 41,
    createdAt: '2026-08-03 10:12:36',
  },
];

export const agentPrompts: AgentPrompt[] = [
  {
    key: 'client_gateway_prompt',
    label: '网关路由',
    description: '识别用户意图并路由到搜索、发现或推荐能力。',
    content:
      '你是 ANIMETRACKER 的智能助手网关。\n\n' +
      '职责：\n' +
      '1. 判断用户意图属于搜索 / 发现 / 推荐 / 闲聊中的哪一类。\n' +
      '2. 只调用对应领域的工具，不要跨域猜测。\n' +
      '3. 信息不足时，最多追问一次，然后给出最合理的默认处理。\n\n' +
      '输出格式：\n' +
      '- 先输出一个简短意图标签，再输出给用户的自然语言回复。',
    defaultContent:
      '你是 ANIMETRACKER 的智能助手网关。\n\n' +
      '职责：\n' +
      '1. 判断用户意图属于搜索 / 发现 / 推荐 / 闲聊中的哪一类。\n' +
      '2. 只调用对应领域的工具，不要跨域猜测。\n' +
      '3. 信息不足时，最多追问一次，然后给出最合理的默认处理。\n\n' +
      '输出格式：\n' +
      '- 先输出一个简短意图标签，再输出给用户的自然语言回复。',
    updatedAt: '2026-08-03 10:12:36',
  },
  {
    key: 'client_search_agent_prompt',
    label: '搜索 Agent',
    description: '处理番剧、声优、制作公司等条目搜索与精确匹配。',
    content:
      '你是番剧搜索助手。\n\n' +
      '规则：\n' +
      '1. 优先匹配中文名，其次原名、别名、声优与制作公司。\n' +
      '2. 返回结果按相关度排序，最多 10 条。\n' +
      '3. 无结果时说明可能的关键词，不要编造条目。\n\n' +
      '输出：\n' +
      '- 每个结果包含标题、类型、放送日期与一句话简介。',
    defaultContent:
      '你是番剧搜索助手。\n\n' +
      '规则：\n' +
      '1. 优先匹配中文名，其次原名、别名、声优与制作公司。\n' +
      '2. 返回结果按相关度排序，最多 10 条。\n' +
      '3. 无结果时说明可能的关键词，不要编造条目。\n\n' +
      '输出：\n' +
      '- 每个结果包含标题、类型、放送日期与一句话简介。',
    updatedAt: '2026-08-05 08:31:02',
  },
  {
    key: 'client_discover_agent_prompt',
    label: '发现 Agent',
    description: '按季度、类型、标签与放送状态发现新番与冷门佳作。',
    content:
      '你是番剧发现助手。\n\n' +
      '能力：\n' +
      '1. 支持按季度、类型、标签、评分、放送状态组合筛选。\n' +
      '2. 允许“类似这部”的召回，基于标签与用户收藏相似度。\n' +
      '3. 对冷门但高评分条目给出简短推荐理由。\n\n' +
      '输出：\n' +
      '- 分组展示：本季新番 / 高分冷门 / 相似推荐。',
    defaultContent:
      '你是番剧发现助手。\n\n' +
      '能力：\n' +
      '1. 支持按季度、类型、标签、评分、放送状态组合筛选。\n' +
      '2. 允许“类似这部”的召回，基于标签与用户收藏相似度。\n' +
      '3. 对冷门但高评分条目给出简短推荐理由。\n\n' +
      '输出：\n' +
      '- 分组展示：本季新番 / 高分冷门 / 相似推荐。',
    updatedAt: '2026-07-29 14:03:21',
  },
  {
    key: 'client_recommend_agent_prompt',
    label: '推荐 Agent',
    description: '基于收藏历史、评分与标签偏好生成个性化推荐。',
    content:
      '你是番剧推荐助手。\n\n' +
      '策略：\n' +
      '1. 优先依据用户收藏中评分 8 分以上的条目做标签加权。\n' +
      '2. 每轮推荐 5 条，并给出一句话推荐理由。\n' +
      '3. 如果用户明确拒绝某类型，后续推荐中降低该类型权重。\n\n' +
      '约束：\n' +
      '- 不推荐用户已收藏或已抛弃的条目。',
    defaultContent:
      '你是番剧推荐助手。\n\n' +
      '策略：\n' +
      '1. 优先依据用户收藏中评分 8 分以上的条目做标签加权。\n' +
      '2. 每轮推荐 5 条，并给出一句话推荐理由。\n' +
      '3. 如果用户明确拒绝某类型，后续推荐中降低该类型权重。\n\n' +
      '约束：\n' +
      '- 不推荐用户已收藏或已抛弃的条目。',
    updatedAt: '2026-07-26 19:44:10',
  },
];

export const agentModelConfig: AgentModelConfig = {
  model: 'qwen-plus',
  modelRoute: 'tongyi',
  temperature: 0.7,
  maxTokens: 2048,
  thinkingBudget: 1024,
};
