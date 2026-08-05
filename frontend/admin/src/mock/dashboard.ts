import dayjs from 'dayjs';

export interface TrendPoint {
  date: string;
  newUsers: number;
  newCollections: number;
  logins: number;
}

export interface TypeCount {
  label: string;
  value: number;
  color: string;
}

export interface RateCount {
  rate: number;
  count: number;
}

export interface SeasonCount {
  label: string;
  value: number;
}

export interface ImportStatusCount {
  label: 'SUCCESS' | 'FAILED' | 'RUNNING';
  value: number;
  color: string;
}

export interface HotSubject {
  id: number;
  name: string;
  nameCn: string;
  collectionCount: number;
  hue: number;
}

export interface ImportRecord {
  id: number;
  season: string;
  startedAt: string;
  completedAt: string;
  status: 'SUCCESS' | 'RUNNING' | 'FAILED';
  subjectCount: number;
  errorMessage?: string;
}

const wave = (i: number) => Math.abs(Math.sin(i * 12.9898) * 43758.5453) % 1;

function buildTrend(days: number): TrendPoint[] {
  const end = dayjs('2026-08-05');
  return Array.from({ length: days }, (_, i) => {
    const date = end.subtract(days - 1 - i, 'day');
    const seed = i * 0.73;
    return {
      date: date.format('MM-DD'),
      newUsers: Math.round(34 + wave(seed) * 46 + (i === days - 1 ? 12 : 0)),
      newCollections: Math.round(520 + wave(seed + 2.1) * 720),
      logins: Math.round(120 + wave(seed + 4.7) * 170),
    };
  });
}

export const trends7 = buildTrend(7);
export const trends30 = buildTrend(30);

export const overview = {
  userCount: 18432,
  subjectCount: 12068,
  collectionCount: 86341,
  episodeCount: 43120,
  importCount: 40,
  todayNewUsers: 68,
  todayNewCollections: 1240,
  todayLogins: 231,
};

export const collectionTypes: TypeCount[] = [
  { label: '看过', value: 2140, color: '#00b3a4' },
  { label: '在看', value: 316, color: '#2f7fe8' },
  { label: '想看', value: 428, color: '#e99b2f' },
  { label: '搁置', value: 158, color: '#8fa3b3' },
  { label: '抛弃', value: 73, color: '#d84a3f' },
];

export const ratings: RateCount[] = [
  { rate: 1, count: 18 },
  { rate: 2, count: 32 },
  { rate: 3, count: 61 },
  { rate: 4, count: 108 },
  { rate: 5, count: 236 },
  { rate: 6, count: 412 },
  { rate: 7, count: 826 },
  { rate: 8, count: 1280 },
  { rate: 9, count: 946 },
  { rate: 10, count: 512 },
];

export const seasons: SeasonCount[] = [
  { label: '2026-07', value: 86 },
  { label: '2026-04', value: 74 },
  { label: '2026-01', value: 69 },
  { label: '2025-10', value: 63 },
  { label: '2025-07', value: 58 },
];

export const importStatuses: ImportStatusCount[] = [
  { label: 'SUCCESS', value: 34, color: '#1f9d6f' },
  { label: 'FAILED', value: 5, color: '#d84a3f' },
  { label: 'RUNNING', value: 1, color: '#00b3a4' },
];

export const importStat = {
  importTotal: 40,
  importSucceeded: 34,
  importFailed: 5,
};

export const hotSubjects: HotSubject[] = [
  { id: 484, name: 'BanG Dream! Ave Mujica', nameCn: 'BanG Dream! Ave Mujica', collectionCount: 4218, hue: 175 },
  { id: 487, name: '葬送的芙莉莲 第二季', nameCn: '葬送的芙莉莲 第二季', collectionCount: 3987, hue: 205 },
  { id: 492, name: '我推的孩子 第三季', nameCn: '我推的孩子 第三季', collectionCount: 3746, hue: 330 },
  { id: 495, name: '机动战士高达 GQuuuuuuX', nameCn: '机动战士高达 GQuuuuuuX', collectionCount: 3512, hue: 258 },
  { id: 498, name: '赛马娘 芦毛灰姑娘', nameCn: '赛马娘 芦毛灰姑娘', collectionCount: 3295, hue: 24 },
];

export const importRecords: ImportRecord[] = [
  { id: 40, season: '2026-07', startedAt: '2026-08-05 02:12', completedAt: '2026-08-05 02:41', status: 'RUNNING', subjectCount: 86 },
  { id: 39, season: '2026-04', startedAt: '2026-08-02 03:20', completedAt: '2026-08-02 03:47', status: 'SUCCESS', subjectCount: 74 },
  { id: 38, season: '2026-01', startedAt: '2026-07-28 01:55', completedAt: '2026-07-28 02:12', status: 'SUCCESS', subjectCount: 69 },
  { id: 37, season: '2025-10', startedAt: '2026-07-24 04:02', completedAt: '2026-07-24 04:16', status: 'FAILED', subjectCount: 21, errorMessage: '部分条目抓取超时' },
];
