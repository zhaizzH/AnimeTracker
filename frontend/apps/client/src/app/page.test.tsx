import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import HomePage from './page';

// 服务端首页在渲染时并行取数，这里拦截 public 适配器返回固定信封，
// 以验证 SSR 输出三个板块标题（JS 执行前即存在）。
vi.mock('@/lib/api/public-client', () => ({
  getPublicApi: () => ({
    getSeason: vi.fn().mockResolvedValue({ content: [], total: 0, page: 1, size: 6 }),
    listSubjects: vi.fn().mockResolvedValue({ content: [], total: 0, page: 1, size: 6 }),
    getSchedule: vi.fn().mockResolvedValue({ content: [], total: 0, page: 1, size: 6 }),
  }),
}));

// jsdom 下 next/image 无需真实加载，mock 为普通 <img>。
vi.mock('next/image', () => ({
  default: (props: { alt: string; src: string }) => <img alt={props.alt} src={props.src} />,
}));

describe('HomePage (SSR)', () => {
  it('renders the three section headings in order in server HTML', async () => {
    render(await HomePage());
    const headings = screen.getAllByRole('heading', { level: 2 }).map((node) => node.textContent);
    expect(headings).toEqual(['本季新番', '热门作品', '今日放送']);
  });

  it('still renders the section headings when the backend is unavailable', async () => {
    const api = (await import('@/lib/api/public-client')).getPublicApi();
    vi.mocked(api.getSeason).mockRejectedValue(new Error('backend down'));
    vi.mocked(api.listSubjects).mockRejectedValue(new Error('backend down'));
    vi.mocked(api.getSchedule).mockRejectedValue(new Error('backend down'));

    render(await HomePage());
    const headings = screen.getAllByRole('heading', { level: 2 }).map((node) => node.textContent);
    expect(headings).toEqual(['本季新番', '热门作品', '今日放送']);
  });
});
