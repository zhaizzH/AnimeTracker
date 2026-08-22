import { expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { SubjectCard } from './SubjectCard';
import type { SubjectListItem } from '../types';

const sub: SubjectListItem = { id: 1, name: 'ソードアート・オンライン', nameCn: '刀剑神域', score: 7.8, rank: 10, eps: 25, type: 2, airWeekday: 3, collectionTotal: 120 };
test('展示中文名与评分', () => {
  render(<MemoryRouter><SubjectCard subject={sub} /></MemoryRouter>);
  expect(screen.getByText('刀剑神域')).toBeTruthy();
  expect(screen.getByText('7.8 分')).toBeTruthy();
});
test('渲染指向详情页的链接', () => {
  render(<MemoryRouter><SubjectCard subject={sub} /></MemoryRouter>);
  const link = screen.getByRole('link', { name: /刀剑神域/ });
  expect(link.getAttribute('href')).toBe('/subject/1');
});
