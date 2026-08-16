/**
 * 发现页 URL 解析与序列化 —— 纯函数，便于单测与 SSR 复用。
 *
 * 原则：搜索词、筛选、排序、分页全部放在 URL 中，页面可分享、无需 JS 即可翻页。
 * 非法值一律归一到合法值，绝不向外抛错（服务端渲染时非法参数返回归一页而不是 500）。
 */

/** 后端 listSubjects/searchSubjects 可用的排序白名单（进 SQL 走白名单）。 */
export const SORT_FIELDS = ['score', 'rank', 'collection_total'] as const;
export type SortField = (typeof SORT_FIELDS)[number];

export const DEFAULT_SIZE = 24;
export const MAX_SIZE = 72;

export type DiscoveryQuery = {
  /** 关键词（已 trim） */
  q: string;
  /** 页码，从 1 起 */
  page: number;
  /** 每页条数，1..72 */
  size: number;
  /** 标签筛选（URL 中可重复出现 tag 参数） */
  tag: string[];
  /** 最低评分（后端按字符串接收） */
  scoreMin?: string;
  /** 最高评分（后端按字符串接收） */
  scoreMax?: string;
  /** 年份（整数） */
  year?: number;
  /** 播出星期 0=周日 … 6=周六 */
  weekday?: number;
  /** 排序字段：score/rank/collection_total */
  sort?: SortField;
  /** 排序方向 */
  order: 'asc' | 'desc';
};

/** Next.js App Router 的 searchParams 形状。 */
export type DiscoveryParams = Record<string, string | string[] | undefined>;

/** 用于构造新查询串的部分覆盖；空串/undefined 视为“该筛选未生效”。 */
export type DiscoveryPatch = Partial<DiscoveryQuery>;

/** 除 page 之外的字段都算“筛选”——任一变化都需回到第 1 页。 */
const FILTER_KEYS: readonly (keyof DiscoveryQuery)[] = [
  'q', 'tag', 'scoreMin', 'scoreMax', 'year', 'weekday', 'sort', 'order', 'size',
];

function first(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

function toPosInt(v: string | undefined, fallback: number): number {
  if (v === undefined) return fallback;
  const n = Number.parseInt(v, 10);
  return Number.isNaN(n) || n < 1 ? fallback : n;
}

function toOptInt(v: string | undefined): number | undefined {
  if (v === undefined || v === '') return undefined;
  const n = Number.parseInt(v, 10);
  return Number.isNaN(n) ? undefined : n;
}

function toOptStr(v: string | undefined): string | undefined {
  const t = v?.trim();
  return t ? t : undefined;
}

export function parseDiscoveryParams(input: DiscoveryParams): DiscoveryQuery {
  const rawTags = Array.isArray(input.tag) ? input.tag : input.tag === undefined ? [] : [input.tag];
  const weekday = toOptInt(first(input.weekday));

  return {
    q: first(input.q)?.trim() ?? '',
    page: toPosInt(first(input.page), 1),
    size: Math.min(MAX_SIZE, Math.max(1, toPosInt(first(input.size), DEFAULT_SIZE))),
    tag: rawTags.map((t) => t.trim()).filter((t) => t.length > 0),
    scoreMin: toOptStr(first(input.scoreMin)),
    scoreMax: toOptStr(first(input.scoreMax)),
    year: toOptInt(first(input.year)),
    weekday: weekday !== undefined && weekday >= 0 && weekday <= 6 ? weekday : undefined,
    sort: (SORT_FIELDS as readonly string[]).includes(first(input.sort) ?? '')
      ? (first(input.sort) as SortField)
      : undefined,
    order: first(input.order) === 'asc' ? 'asc' : 'desc',
  };
}

/** 是否设置过筛选：q 为空且无 tag/评分/年份/星期/排序时返回 false（此时应走 listSubjects）。 */
export function hasFilters(query: DiscoveryQuery): boolean {
  return !(query.q === '' && query.tag.length === 0 && query.scoreMin === undefined &&
    query.scoreMax === undefined && query.year === undefined && query.weekday === undefined &&
    query.sort === undefined);
}

/**
 * 基于当前 query，覆盖 patch 生成新查询串。
 * 任一“筛选”（除 page 外的字段）变化时，页码强制回到 1；仅只改 page 时保留。
 */
export function toDiscoverySearchParams(query: Partial<DiscoveryQuery>, patch: DiscoveryPatch): string {
  const filterChanged = FILTER_KEYS.some((key) => patch[key] !== undefined);
  const merged: Partial<DiscoveryQuery> = { ...query, ...patch };
  const page = patch.page ?? (filterChanged ? 1 : query.page ?? 1);

  const params = new URLSearchParams();
  params.set('page', String(page));
  // 缺省值（undefined / 默认 size / 空串）一律不写入 URL，保持规范化、可分享。
  if (merged.size !== undefined && merged.size !== DEFAULT_SIZE) params.set('size', String(merged.size));
  if (merged.q) params.set('q', merged.q);
  for (const t of merged.tag ?? []) params.append('tag', t);
  if (merged.scoreMin !== undefined) params.set('scoreMin', merged.scoreMin);
  if (merged.scoreMax !== undefined) params.set('scoreMax', merged.scoreMax);
  if (merged.year !== undefined) params.set('year', String(merged.year));
  if (merged.weekday !== undefined) params.set('weekday', String(merged.weekday));
  if (merged.sort !== undefined) params.set('sort', merged.sort);
  if (merged.order !== undefined) params.set('order', merged.order);
  return params.toString();
}
