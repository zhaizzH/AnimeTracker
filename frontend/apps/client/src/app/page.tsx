import type { Metadata } from 'next';
import { copy } from '@/content/zh-CN';
import { getPublicApi } from '@/lib/api/public-client';
import { toSubjectCardModel } from '@/features/subjects/model';
import { PublicHome, getSeasonContext, isoWeekdayToBackend } from '@/features/home/public-home';
import type { SubjectCardModel } from '@/features/subjects/model';

export const metadata: Metadata = {
  title: copy.brand,
  description: copy.home.tagline,
};

// 首页必须在请求时取数：E2E 的 mock 构建不能把 fixture 数据写进 ISR 产物。
export const dynamic = 'force-dynamic';

const HOME_SECTION_LIMIT = 6;

/** 提取页信封中的数据项，无法提供数据时回退为空数组。 */
function contentOf(list?: { content?: unknown[] }): unknown[] {
  return list?.content ?? [];
}

export default async function HomePage() {
  const api = getPublicApi();
  const { year, quarter, isoWeekday } = getSeasonContext();
  const backendWeekday = isoWeekdayToBackend(isoWeekday);

  // 三板块并行取数；任一块后端不可用都不影响整页标题渲染（Promise.allSettled）。
  const [seasonRes, popularRes, todayRes] = await Promise.allSettled([
    api.getSeason({ year, quarter, size: HOME_SECTION_LIMIT }, [`season:${year}-${quarter}`]),
    api.listSubjects({ sort: 'score', order: 'desc', page: 1, size: HOME_SECTION_LIMIT }, ['subjects']),
    api.getSchedule(
      { year, quarter, weekday: backendWeekday, size: HOME_SECTION_LIMIT },
      [`schedule:${year}-${quarter}-${backendWeekday}`],
    ),
  ]);

  const toModels = (list?: { content?: unknown[] }): SubjectCardModel[] =>
    (contentOf(list) as Parameters<typeof toSubjectCardModel>[0][]).map(toSubjectCardModel);

  const season =
    seasonRes.status === 'fulfilled' ? toModels(seasonRes.value as { content?: unknown[] }) : [];
  const popular =
    popularRes.status === 'fulfilled' ? toModels(popularRes.value as { content?: unknown[] }) : [];
  const today =
    todayRes.status === 'fulfilled' ? toModels(todayRes.value as { content?: unknown[] }) : [];

  return <PublicHome season={season} popular={popular} today={today} />;
}
