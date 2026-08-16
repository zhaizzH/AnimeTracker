import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { PublicHome, getSeasonContext, isoWeekdayToBackend } from './public-home';
import type { SubjectCardModel } from '@/features/subjects/model';

const base: SubjectCardModel = {
  id: 1,
  title: '作品',
  scoreLabel: '8.0 分',
  seasonLabel: '2026 夏',
  episodeLabel: '全 12 集',
  href: '/subjects/1',
};

const frieren: SubjectCardModel = { ...base, id: 7, title: '葬送的芙莉莲' };
const dungeon: SubjectCardModel = { ...base, id: 8, title: '迷宫饭' };
const dandadan: SubjectCardModel = { ...base, id: 9, title: '胆大党' };

describe('PublicHome', () => {
  it('renders discovery content in the approved order', () => {
    render(<PublicHome season={[frieren]} popular={[dungeon]} today={[dandadan]} />);
    const headings = screen.getAllByRole('heading', { level: 2 }).map((node) => node.textContent);
    expect(headings).toEqual(['本季新番', '热门作品', '今日放送']);
  });

  it('renders an empty state per section when no data', () => {
    render(<PublicHome season={[]} popular={[]} today={[]} />);
    expect(screen.getAllByRole('heading', { level: 2 })).toHaveLength(3);
  });
});

describe('getSeasonContext', () => {
  it('maps months to quarters and derives ISO weekday', () => {
    const ctx = getSeasonContext(new Date(2026, 7, 16)); // 2026-08-16 是周日（getDay()=0）
    expect(ctx).toMatchObject({ year: 2026, quarter: 'summer', isoWeekday: 7 });
  });
});

describe('isoWeekdayToBackend', () => {
  it('maps ISO 1(周一)…7(周日) to backend 1(周一)…0(周日)', () => {
    expect(isoWeekdayToBackend(1)).toBe(1);
    expect(isoWeekdayToBackend(7)).toBe(0);
  });
});
