import { describe, expect, it } from 'vitest';
import {
  backendToIsoWeekday,
  fetchAllSchedulePages,
  groupScheduleByWeekday,
  parseSeasonParams,
  quarterLabel,
  SCHEDULE_PAGE_SIZE,
  weekdayHref,
} from './season';
import type { SubjectListItem } from '@/features/subjects/model';

const NOW = new Date('2026-08-16T00:00:00Z'); // 2026-08-16 为周日

function subject(id: number, airWeekday: number, name?: string): SubjectListItem {
  return { id, name: name ?? `番剧${id}`, nameCn: name ?? `番剧${id}`, airWeekday } as SubjectListItem;
}

describe('parseSeasonParams', () => {
  it('maps August to the summer quarter', () => {
    expect(parseSeasonParams({}, NOW)).toMatchObject({ year: 2026, quarter: 'summer' });
  });

  it('accepts explicit year and quarter and keeps a valid weekday', () => {
    expect(parseSeasonParams({ year: '2024', quarter: 'winter', weekday: '7' }, NOW)).toMatchObject({
      year: 2024,
      quarter: 'winter',
      weekday: 7,
    });
  });

  it('falls back to current season on invalid year, quarter and weekday', () => {
    expect(parseSeasonParams({ year: 'abc', quarter: 'nonsense', weekday: '99' }, NOW)).toMatchObject({
      year: 2026,
      quarter: 'summer',
      weekday: undefined,
    });
  });
});

describe('groupScheduleByWeekday', () => {
  it('groups subjects by backend weekday without duplication', () => {
    const monday = subject(1, 1, '周一番剧');
    const friday = subject(2, 5, '周五番剧');
    const grouped = groupScheduleByWeekday([monday, monday, friday]);
    expect(grouped.get(1)).toHaveLength(1);
    expect(grouped.get(5)).toHaveLength(1);
  });

  it('maps backend Sunday (0) to ISO 7', () => {
    const grouped = groupScheduleByWeekday([subject(3, 0, '周日番剧')]);
    expect(grouped.get(7)).toHaveLength(1);
  });

  it('skips subjects without a valid weekday or id', () => {
    const grouped = groupScheduleByWeekday([
      subject(1, -1, '无星期'),
      { id: undefined, name: '无ID' } as unknown as SubjectListItem,
    ]);
    expect(grouped.size).toBe(0);
  });
});

describe('backendToIsoWeekday', () => {
  it('maps backend 0=周日..6=周六 to ISO 1=周一..7=周日', () => {
    expect(backendToIsoWeekday(0)).toBe(7);
    expect(backendToIsoWeekday(1)).toBe(1);
    expect(backendToIsoWeekday(5)).toBe(5);
    expect(backendToIsoWeekday(6)).toBe(6);
    expect(backendToIsoWeekday(-1)).toBeUndefined();
    expect(backendToIsoWeekday(7)).toBeUndefined();
  });
});

describe('weekdayHref', () => {
  it('serializes year, quarter and weekday into the schedule URL', () => {
    expect(weekdayHref({ year: 2026, quarter: 'summer' }, 7)).toBe('/schedule?year=2026&quarter=summer&weekday=7');
  });
});

describe('quarterLabel', () => {
  it('maps quarters to Chinese season glyphs', () => {
    expect(quarterLabel('spring')).toBe('春');
    expect(quarterLabel('summer')).toBe('夏');
    expect(quarterLabel('autumn')).toBe('秋');
    expect(quarterLabel('winter')).toBe('冬');
  });
});

describe('fetchAllSchedulePages', () => {
  it('fetches pages until content.length >= total and dedupes ids across pages', async () => {
    const all = await fetchAllSchedulePages(async (page) => ({
      content: page === 1 ? [subject(1, 1), subject(2, 2)] : [subject(2, 2), subject(3, 3)],
      total: 103,
    }));
    expect(all.map((s) => s.id)).toEqual([1, 2, 3]);
  });

  it('stops when a page returns no new ids', async () => {
    let calls = 0;
    await fetchAllSchedulePages(async () => {
      calls += 1;
      return { content: [subject(1, 1)], total: 1_000_000 };
    });
    expect(calls).toBe(2); // 第二页无新 id 即停，不会追到 total
  });

  it('caps the loop at Math.ceil(total / size) pages', async () => {
    let calls = 0;
    const results = await fetchAllSchedulePages(async (page) => {
      calls += 1;
      return { content: [subject(page, 1)], total: 1000 };
    });
    expect(calls).toBe(Math.ceil(1000 / SCHEDULE_PAGE_SIZE));
    expect(results).toHaveLength(Math.ceil(1000 / SCHEDULE_PAGE_SIZE));
  });

  it('stops after one page when total is missing (malformed API)', async () => {
    let calls = 0;
    await fetchAllSchedulePages(async () => {
      calls += 1;
      return { content: [subject(1, 1)] }; // 无 total
    });
    expect(calls).toBe(1);
  });
});
