import { describe, expect, it } from 'vitest';
import { parseDiscoveryParams, toDiscoverySearchParams, SORT_FIELDS } from './search-params';

describe('parseDiscoveryParams', () => {
  it('normalizes invalid page and preserves repeated tags', () => {
    expect(parseDiscoveryParams({ page: '-4', tag: ['奇幻', '冒险'], order: 'sideways' })).toMatchObject({
      page: 1,
      tag: ['奇幻', '冒险'],
      order: 'desc',
    });
  });

  it('defaults when input is empty', () => {
    const query = parseDiscoveryParams({});
    expect(query).toMatchObject({ q: '', page: 1, size: 24, tag: [], order: 'desc', sort: undefined });
  });

  it('keeps valid numbers for year and weekday and drops out-of-range weekday', () => {
    expect(parseDiscoveryParams({ year: '2026', weekday: '3' })).toMatchObject({ year: 2026, weekday: 3 });
    expect(parseDiscoveryParams({ weekday: '9' }).weekday).toBeUndefined();
  });

  it('whitelists sort fields and passes blank strings through as undefined', () => {
    expect(parseDiscoveryParams({ sort: 'rank', q: ' 魔法 ' })).toMatchObject({ sort: 'rank', q: '魔法' });
    expect(parseDiscoveryParams({ sort: 'bogus' }).sort).toBeUndefined();
    expect(parseDiscoveryParams({ sort: SORT_FIELDS[0] }).sort).toBe(SORT_FIELDS[0]);
  });

  it('keeps scoreMin/scoreMax as string passthrough', () => {
    expect(parseDiscoveryParams({ scoreMin: '7', scoreMax: '9' })).toMatchObject({ scoreMin: '7', scoreMax: '9' });
  });
});

describe('toDiscoverySearchParams', () => {
  it('resets pagination when a filter changes', () => {
    expect(toDiscoverySearchParams({ q: '魔法', page: 8, tag: [] }, { year: 2026 })).toContain('page=1');
  });

  it('preserves unrelated filters and the chosen page when only page changes', () => {
    const qs = toDiscoverySearchParams({ q: '魔法', page: 2, tag: ['冒险'] }, { page: 3 });
    expect(qs).toContain('q=%E9%AD%94%E6%B3%95');
    expect(qs).toContain('tag=%E5%86%92%E9%99%A9');
    expect(qs).toContain('page=3');
    expect(qs).not.toContain('year');
  });
});
