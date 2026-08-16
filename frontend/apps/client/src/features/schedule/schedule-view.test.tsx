import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ScheduleView } from './schedule-view';
import type { SubjectCardModel } from '@/features/subjects/model';
import type { SeasonParams, Weekday } from './season';

const base: SubjectCardModel = {
  id: 1,
  title: '作品',
  scoreLabel: '8.0 分',
  seasonLabel: '2026 夏',
  episodeLabel: '全 12 集',
  href: '/subjects/1',
};

const monday: SubjectCardModel = { ...base, id: 7, title: '周一番剧', href: '/subjects/7' };
const sunday: SubjectCardModel = { ...base, id: 8, title: '周日番剧', href: '/subjects/8' };

const grouped = new Map<Weekday, SubjectCardModel[]>([
  [1, [monday]],
  [7, [sunday]],
]);

const params: SeasonParams = { year: 2026, quarter: 'summer', weekday: 7 };

describe('ScheduleView', () => {
  it('renders the selected year and quarter', () => {
    render(<ScheduleView params={params} selectedWeekday={7} grouped={grouped} />);
    expect(screen.getByText('2026 夏', { selector: 'p' })).toBeTruthy();
  });

  it('renders all seven weekday headings in the server HTML', () => {
    render(<ScheduleView params={params} selectedWeekday={7} grouped={grouped} />);
    for (const name of ['周一', '周二', '周三', '周四', '周五', '周六', '周日']) {
      expect(screen.getByRole('heading', { name })).toBeTruthy();
    }
  });

  it('renders subject links under their weekday and marks the selected day', () => {
    render(<ScheduleView params={params} selectedWeekday={7} grouped={grouped} />);
    expect(screen.getByRole('link', { name: /周日番剧/ })).toHaveAttribute('href', '/subjects/8');
    expect(screen.getByRole('link', { name: /周一番剧/ })).toHaveAttribute('href', '/subjects/7');
    expect(screen.getByRole('link', { name: '周日' })).toHaveAttribute('aria-current', 'page');
  });

  it('renders empty state for weekdays without subjects', () => {
    render(<ScheduleView params={params} selectedWeekday={7} grouped={grouped} />);
    expect(screen.getAllByText('当天暂无更新')).toHaveLength(5); // 7 列 - 2 列有内容
  });

  it('shows the error banner but keeps the weekday layout', () => {
    render(
      <ScheduleView params={params} selectedWeekday={7} grouped={grouped} errorMessage="时间表加载失败，请稍后重试" />,
    );
    expect(screen.getByRole('alert')).toBeTruthy();
    expect(screen.getByRole('heading', { name: '周日' })).toBeTruthy();
    expect(screen.queryByText('当天暂无更新')).toBeNull(); // 失败时不渲染误导性空态
  });
});
