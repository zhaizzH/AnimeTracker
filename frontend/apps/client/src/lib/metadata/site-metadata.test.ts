import { describe, expect, it } from 'vitest';
import { buildCanonicalUrl } from './site-metadata';

describe('buildCanonicalUrl', () => {
  it('builds an absolute canonical URL', () => {
    expect(buildCanonicalUrl('https://anime.example.com', '/schedule')).toBe('https://anime.example.com/schedule');
  });

  it('strips a trailing slash from the base and adds a missing leading slash to the path', () => {
    expect(buildCanonicalUrl('https://anime.example.com/', 'subjects/1')).toBe('https://anime.example.com/subjects/1');
  });
});
