import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { SubjectDetail } from './subject-detail';
import type { SubjectDetailModel, EpisodeModel } from './subject-detail';

// jsdom 下 next/image 无需真实加载，mock 为普通 <img> 以便断言 alt。
vi.mock('next/image', () => ({
  default: (props: { alt: string; src: string }) => <img alt={props.alt} src={props.src} />,
}));

const detailFixture: SubjectDetailModel = {
  id: 7,
  name: 'Sousou no Frieren',
  nameCn: '葬送的芙莉莲',
  image: 'https://lain.bgm.tv/pic/cover/l/aa.jpg',
  score: 9.1,
  rank: 1,
  eps: 28,
  airDate: '2023-09-29',
  type: 2,
  airWeekday: 5,
  collectionTotal: 183923,
  summary:
    '寿命超过一千年的精灵族魔法使芙莉莲，曾经与勇者一行一同讨伐了魔王。在勇者离去之后，她独自一人踏上旅程，去了解人类，去了解世界。芙莉莲以魔王肉体的腐烂为线索，探索死后的世界，讲述了一个关于时间、离别与重逢的故事。',
  tags: [
    { id: 1, name: '奇幻', count: 8923 },
    { id: 2, name: '冒险', count: 6411 },
  ],
  relations: [
    {
      relation: 'related_subject',
      relatedSubject: { id: 8, name: 'Dungeon Meshi', nameCn: '迷宫饭', image: '', score: 8.5, eps: 24 },
    },
  ],
};

const episodeFixtures: EpisodeModel[] = [
  { id: 1001, subjectId: 7, sort: 1, name: '旅の始まり', nameCn: '旅程的开始', airdate: '2023-09-29', status: 'Air' },
  { id: 1002, subjectId: 7, sort: 2, name: '葬送のフリーレン', nameCn: '葬送的芙莉莲', airdate: '2023-10-06', status: 'Air' },
];

describe('SubjectDetail', () => {
  it('renders core metadata and related works as navigable content', () => {
    render(<SubjectDetail subject={detailFixture} episodes={episodeFixtures} />);
    expect(screen.getByRole('heading', { level: 1, name: '葬送的芙莉莲' })).toBeInTheDocument();
    expect(screen.getByRole('region', { name: '剧集' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /关联作品/ })).toHaveAttribute('href', '/subjects/8');
  });
});
