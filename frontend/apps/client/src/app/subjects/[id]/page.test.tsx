import { describe, expect, it } from 'vitest';
import { detailExcerpt, parseSubjectId } from '@/features/subjects/detail-meta';

describe('parseSubjectId', () => {
  it('accepts positive integers and rejects non-integers or non-positive values', () => {
    expect(parseSubjectId('7')).toBe(7);
    expect(Number.isNaN(parseSubjectId('0'))).toBe(true);
    expect(Number.isNaN(parseSubjectId('-3'))).toBe(true);
    expect(Number.isNaN(parseSubjectId('1.5'))).toBe(true);
    expect(Number.isNaN(parseSubjectId('abc'))).toBe(true);
  });
});

describe('detailExcerpt', () => {
  it('returns a short summary untouched', () => {
    expect(detailExcerpt('短简介。')).toBe('短简介。');
  });

  it('cuts a long summary at a sentence boundary near 150 chars', () => {
    const sum = `${'很长的一句话。'.repeat(40)}尾部。`;
    const out = detailExcerpt(sum);
    expect(out.length).toBeLessThanOrEqual(151);
    expect(out.endsWith('…')).toBe(true);
  });
});
