import { copy } from '@/content/zh-CN';
import { toSubjectCardModel, type SubjectCardModel, type SubjectListItem } from '@/features/subjects/model';

/**
 * 放送时间表 —— 星期/季度解析与分桶（纯函数，便于单测与 SSR 复用）。
 *
 * 星期语义（关键决策）：URL 与视图统一采用 ISO 8601 星期，1=周一 … 7=周日。
 * 后端 getSchedule 的 weekday 查询参数与返回的 airWeekday 均为 0=周日 … 6=周六，
 * 换算见 backendToIsoWeekday / isoWeekdayToBackend，groupScheduleByWeekday 与
 * 页面取数均以同一换算保持一致。
 */

export type Quarter = 'spring' | 'summer' | 'autumn' | 'winter';
export type Weekday = 1 | 2 | 3 | 4 | 5 | 6 | 7;

export type SeasonParams = {
  year: number;
  quarter: Quarter;
  /** 移动端强调的星期；缺省取今天 */
  weekday?: Weekday;
};

export const ALL_WEEKDAYS: readonly Weekday[] = [1, 2, 3, 4, 5, 6, 7];

const QUARTERS: readonly Quarter[] = ['spring', 'summer', 'autumn', 'winter'];

/** copy.subject.seasons = ['冬','春','夏','秋']，按季度取值。 */
const QUARTER_COPY_INDEX: Record<Quarter, number> = { spring: 1, summer: 2, autumn: 3, winter: 0 };

export function quarterFromMonth(month: number): Quarter {
  if (month >= 3 && month <= 5) return 'spring';
  if (month >= 6 && month <= 8) return 'summer';
  if (month >= 9 && month <= 11) return 'autumn';
  return 'winter';
}

/** 季度中文标签，如 summer → '夏'。 */
export function quarterLabel(quarter: Quarter): string {
  return copy.subject.seasons[QUARTER_COPY_INDEX[quarter]];
}

/** 后端星期列 0=周日 … 6=周六 → ISO 星期 1=周一 … 7=周日；非法值返回 undefined。 */
export function backendToIsoWeekday(backend: number): Weekday | undefined {
  if (!Number.isInteger(backend) || backend < 0 || backend > 6) return undefined;
  return backend === 0 ? 7 : (backend as Weekday);
}

/** ISO 星期 1=周一 … 7=周日 → 后端星期列 0=周日 … 6=周六（与 public-home 的换算一致）。 */
export function isoWeekdayToBackend(iso: number): number {
  return iso % 7;
}

function first(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

/**
 * 归一化 /schedule 的 searchParams。非法年份/季度/星期一律回落，绝不抛错：
 * 非法参数渲染归一页而不是 500（与发现页的归一策略一致）。
 */
export function parseSeasonParams(
  input: Record<string, string | string[] | undefined>,
  now: Date,
): SeasonParams {
  const rawYear = first(input.year);
  const year = rawYear !== undefined && /^\d{4}$/.test(rawYear) ? Number(rawYear) : now.getFullYear();

  const rawQuarter = first(input.quarter);
  const quarter = (QUARTERS as readonly string[]).includes(rawQuarter ?? '')
    ? (rawQuarter as Quarter)
    : quarterFromMonth(now.getMonth() + 1);

  const rawWeekday = first(input.weekday);
  let weekday: Weekday | undefined;
  if (rawWeekday !== undefined && rawWeekday !== '') {
    const n = Number(rawWeekday);
    if (Number.isInteger(n) && n >= 1 && n <= 7) weekday = n as Weekday;
  }

  return { year, quarter, weekday };
}

/** 当前 ISO 星期（1=周一 … 7=周日），用于移动端默认强调“今天”。 */
export function getTodayIsoWeekday(now: Date = new Date()): Weekday {
  return (((now.getDay() + 6) % 7) + 1) as Weekday;
}

/** 由季度参数与目标星期生成可分享的 /schedule 链接。 */
export function weekdayHref(params: SeasonParams, weekday: Weekday): string {
  const q = new URLSearchParams();
  q.set('year', String(params.year));
  q.set('quarter', params.quarter);
  q.set('weekday', String(weekday));
  return `/schedule?${q.toString()}`;
}

/**
 * 按后端 airWeekday 分桶为 ISO 星期 → 卡片列表。
 * 同一 id 只保留首次出现（跨页/重复数据不重复渲染）。
 */
export function groupScheduleByWeekday(subjects: SubjectListItem[]): Map<Weekday, SubjectCardModel[]> {
  const grouped = new Map<Weekday, SubjectCardModel[]>();
  const seen = new Set<number>();
  for (const subject of subjects) {
    if (subject.id === undefined) continue;
    const weekday = backendToIsoWeekday(subject.airWeekday ?? -1);
    if (weekday === undefined || seen.has(subject.id)) continue;
    seen.add(subject.id);
    const list = grouped.get(weekday) ?? [];
    list.push(toSubjectCardModel(subject));
    grouped.set(weekday, list);
  }
  return grouped;
}

/** 单页取数信封。 */
export type SchedulePage = { content?: SubjectListItem[]; total?: number };
export type SchedulePageFetcher = (page: number, size: number) => Promise<SchedulePage>;

/** 时间表请求的文档化最大页大小（后端默认 20，此处放宽到 50 减少请求数）。 */
export const SCHEDULE_PAGE_SIZE = 50;

/**
 * 有界取数：连续请求到 content.length >= total 或某页没有新 id 为止。
 * 首响应后即用 Math.ceil(total / size) 封顶页码；total 缺失时按已取数量封顶为 1 页，
 * 确保畸形 API 不可能触发无界请求循环。
 */
export async function fetchAllSchedulePages(fetchPage: SchedulePageFetcher): Promise<SubjectListItem[]> {
  const seen = new Set<number>();
  const all: SubjectListItem[] = [];
  let page = 1;
  let maxPages = Number.POSITIVE_INFINITY;

  while (page <= maxPages) {
    const { content = [], total } = await fetchPage(page, SCHEDULE_PAGE_SIZE);
    const fresh = content.filter(
      (s): s is SubjectListItem & { id: number } => s.id !== undefined && !seen.has(s.id),
    );
    for (const s of fresh) {
      seen.add(s.id);
      all.push(s);
    }
    if (page === 1) {
      maxPages = Math.max(1, Math.ceil((total ?? all.length) / SCHEDULE_PAGE_SIZE));
    }
    if (fresh.length === 0) break;
    if (total !== undefined && all.length >= total) break;
    page += 1;
  }
  return all;
}
