import { expect, test, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SubjectCard } from './SubjectCard';
import type { SubjectListItem } from '../types';

const sub: SubjectListItem = { id: 1, name: 'ソードアート・オンライン', nameCn: '刀剑神域', score: 7.8, rank: 10, eps: 25, type: 2, airWeekday: 3, collectionTotal: 120 };
test('展示中文名与评分', () => {
  render(<SubjectCard subject={sub} />);
  expect(screen.getByText('刀剑神域')).toBeTruthy();
  expect(screen.getByText('7.8 分')).toBeTruthy();
});
test('点击触发 onClick', async () => {
  const onClick = vi.fn();
  render(<SubjectCard subject={sub} onClick={onClick} />);
  await userEvent.click(screen.getByText('刀剑神域'));
  expect(onClick).toHaveBeenCalled();
});
