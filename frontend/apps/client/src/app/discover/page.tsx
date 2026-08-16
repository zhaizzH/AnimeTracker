import type { Metadata } from 'next';
import { copy } from '@/content/zh-CN';
import { getPublicApi } from '@/lib/api/public-client';
import { toSubjectCardModel } from '@/features/subjects/model';
import type { SubjectCardModel } from '@/features/subjects/model';
import {
  parseDiscoveryParams,
  hasFilters,
  type DiscoveryQuery,
} from '@/features/discovery/search-params';
import { DiscoveryFilters } from '@/features/discovery/discovery-filters';
import { DiscoveryResults } from '@/features/discovery/discovery-results';
import styles from '@/features/discovery/discovery.module.css';

export const metadata: Metadata = {
  title: `${copy.discovery.title} · ${copy.brand}`,
  description: copy.home.tagline,
};

type PageProps = { searchParams: Promise<Record<string, string | string[] | undefined>> };

/** 列表页信封 data 结构（listSubjects / searchSubjects 均返回此分页结构）。 */
type PageEnvelope = { content?: unknown[]; total?: number };

const YEAR_SPAN = 12;

/**
 * 把归一化后的查询翻译成后端 adapter 参数。
 * 无筛选时走 listSubjects（只支持 page/size/sort/order）；
 * 有筛选时走 searchSubjects（额外支持 q/tag/scoreMin/scoreMax/year/weekday）。
 */
function adapterParams(query: DiscoveryQuery): Record<string, string | number | string[] | undefined> {
  const base = { page: query.page, size: query.size, sort: query.sort, order: query.order };
  if (!hasFilters(query)) return base;
  return {
    ...base,
    q: query.q || undefined,
    tag: query.tag.length > 0 ? query.tag : undefined,
    scoreMin: query.scoreMin,
    scoreMax: query.scoreMax,
    year: query.year,
    weekday: query.weekday,
  };
}

export default async function DiscoverPage({ searchParams }: PageProps) {
  const query = parseDiscoveryParams(await searchParams);
  const api = getPublicApi();
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: YEAR_SPAN + 1 }, (_, i) => currentYear - i);

  // q 为空且无筛选 → listSubjects；否则 searchSubjects。取数失败不 500，进安全错误态。
  const [listRes, tagsRes] = await Promise.allSettled([
    hasFilters(query)
      ? api.searchSubjects(adapterParams(query) as Parameters<typeof api.searchSubjects>[0])
      : api.listSubjects(adapterParams(query) as Parameters<typeof api.listSubjects>[0], [`discovery:${query.page}`]),
    api.listTags(),
  ]);

  const page = listRes.status === 'fulfilled' ? (listRes.value as unknown as PageEnvelope) : undefined;
  const subjects: SubjectCardModel[] = (page?.content ?? []).map(
    (item) => toSubjectCardModel(item as Parameters<typeof toSubjectCardModel>[0]),
  );
  const total = page?.total ?? 0;
  const errorMessage = listRes.status === 'rejected' ? copy.discovery.loadError : undefined;
  const tags =
    tagsRes.status === 'fulfilled'
      ? (tagsRes.value as unknown as { name?: string }[])
      : [];

  return (
    <main id="main" className={styles.page}>
      <DiscoveryFilters query={query} tags={tags} years={years} />
      <DiscoveryResults query={query} subjects={subjects} total={total} errorMessage={errorMessage} />
    </main>
  );
}
