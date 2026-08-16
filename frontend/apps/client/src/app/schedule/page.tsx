import type { Metadata } from 'next';
import { copy } from '@/content/zh-CN';
import { getPublicApi } from '@/lib/api/public-client';
import type { SubjectListItem } from '@/features/subjects/model';
import {
  fetchAllSchedulePages,
  getTodayIsoWeekday,
  groupScheduleByWeekday,
  parseSeasonParams,
  type Weekday,
} from '@/features/schedule/season';
import { ScheduleView } from '@/features/schedule/schedule-view';

export const metadata: Metadata = {
  title: `${copy.schedule.title} · ${copy.brand}`,
  description: copy.home.tagline,
};

type PageProps = { searchParams: Promise<Record<string, string | string[] | undefined>> };

/**
 * 放送时间表：URL 驱动季度与强调星期，一次取回全部星期数据（有界分页）。
 * 取数失败不 500：渲染完整周布局 + 安全错误提示。
 */
export default async function SchedulePage({ searchParams }: PageProps) {
  const params = parseSeasonParams(await searchParams, new Date());
  const api = getPublicApi();

  let subjects: SubjectListItem[] = [];
  let errorMessage: string | undefined;
  try {
    subjects = await fetchAllSchedulePages(async (page, size) => {
      const data = await api.getSchedule({ year: params.year, quarter: params.quarter, page, size });
      return data ?? {};
    });
  } catch {
    errorMessage = copy.schedule.loadError;
  }

  const grouped = groupScheduleByWeekday(subjects);
  const selectedWeekday: Weekday = params.weekday ?? getTodayIsoWeekday();

  return (
    <ScheduleView params={params} selectedWeekday={selectedWeekday} grouped={grouped} errorMessage={errorMessage} />
  );
}
