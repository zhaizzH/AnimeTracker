import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import SchedulePage from './page';
import { parseSeasonParams, weekdayHref } from '@/features/schedule/season';

// 单个稳定的 getSchedule mock：测试可对其重置/注入返回值或拒绝，
// 服务端页面在渲染时通过 getPublicApi() 取到的就是同一实例。
const { getScheduleMock } = vi.hoisted(() => ({ getScheduleMock: vi.fn() }));

vi.mock('@/lib/api/public-client', () => ({
  getPublicApi: () => ({ getSchedule: getScheduleMock }),
}));

vi.mock('next/image', () => ({
  default: (props: { alt: string; src: string }) => <img alt={props.alt} src={props.src} />,
}));

const MOCK_ENVELOPE = {
  content: [
    { id: 1, name: '周日番剧', nameCn: '周日番剧', airWeekday: 0 },
    { id: 2, name: '周一番剧', nameCn: '周一番剧', airWeekday: 1 },
    { id: 1, name: '周日番剧', nameCn: '周日番剧', airWeekday: 0 }, // 重复 id
  ],
  total: 3,
  page: 1,
  size: 50,
};

describe('SchedulePage (SSR)', () => {
  beforeEach(() => {
    getScheduleMock.mockReset();
    getScheduleMock.mockResolvedValue(MOCK_ENVELOPE);
  });

  it('renders the selected year, quarter, Sunday heading and deduped subject links', async () => {
    render(
      await SchedulePage({
        searchParams: Promise.resolve({ year: '2026', quarter: 'summer', weekday: '7' }),
      }),
    );
    expect(screen.getByText('2026 夏', { selector: 'p' })).toBeTruthy();
    expect(screen.getByRole('heading', { name: '周日' })).toBeTruthy();
    expect(screen.getByRole('link', { name: /周日番剧/ })).toHaveAttribute('href', '/subjects/1');
    // 同一 id 只渲染一次，服务器 HTML 中无重复卡片链接
    expect(screen.getAllByRole('link', { name: /周日番剧/ })).toHaveLength(1);
  });

  it('normalizes invalid params to the current season and keeps the layout', async () => {
    render(await SchedulePage({ searchParams: Promise.resolve({ year: 'abc', quarter: 'nonsense', weekday: '99' }) }));
    expect(screen.getByRole('heading', { name: '周日' })).toBeTruthy();
    const fallback = parseSeasonParams({}, new Date());
    expect(screen.getByRole('link', { name: '周日' })).toHaveAttribute('href', weekdayHref(fallback, 7));
  });

  it('renders the weekday layout with an error banner when the backend is down', async () => {
    getScheduleMock.mockRejectedValue(new Error('backend down'));
    render(await SchedulePage({ searchParams: Promise.resolve({}) }));
    expect(screen.getByRole('alert')).toBeTruthy();
    expect(screen.getByRole('heading', { name: '周日' })).toBeTruthy();
    expect(screen.queryByText('当天暂无更新')).toBeNull();
  });
});
