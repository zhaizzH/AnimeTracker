import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { SubjectCard } from './subject-card';
import type { SubjectCardModel } from './model';

// jsdom 下 next/image 无需真实加载，mock 为普通 <img> 以便断言 alt。
vi.mock('next/image', () => ({
  default: (props: { alt: string; src: string }) => <img alt={props.alt} src={props.src} />,
}));

const fixture: SubjectCardModel = {
  id: 7,
  title: '葬送的芙莉莲',
  originalTitle: 'Sousou no Frieren',
  imageUrl: 'https://lain.bgm.tv/pic/cover/l/aa.jpg',
  scoreLabel: '9.1 分',
  seasonLabel: '2023 秋',
  episodeLabel: '全 28 集',
  href: '/subjects/7',
};

describe('SubjectCard', () => {
  it('exposes one descriptive link and image alternative', () => {
    render(<SubjectCard subject={fixture} />);
    expect(screen.getByRole('link', { name: /葬送的芙莉莲/ })).toHaveAttribute('href', '/subjects/7');
    expect(screen.getByRole('img')).toHaveAttribute('alt', '葬送的芙莉莲 封面');
  });
});
