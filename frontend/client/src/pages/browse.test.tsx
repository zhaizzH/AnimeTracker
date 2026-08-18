import { expect, test, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import AnimeIndex from './AnimeIndex';

vi.mock('@shared', async (importOriginal) => {
  const mod = await importOriginal<typeof import('@shared')>();
  // subjectsApi 是命名空间导出，替换其内部 search 函数
  return { ...mod, subjectsApi: { ...mod.subjectsApi, search: vi.fn().mockResolvedValue({ content: [{ id: 1, name: 'n', nameCn: '测试番', score: 8, rank: 1, eps: 12, type: 2, airWeekday: 1, collectionTotal: 5 }], total: 1, page: 1, size: 20 }) } };
});

test('AnimeIndex 渲染搜索结果标题', async () => {
  const { subjectsApi } = await import('@shared');
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter initialEntries={['/anime']}><AnimeIndex /></MemoryRouter>
    </QueryClientProvider>,
  );
  expect(await screen.findByText('测试番')).toBeTruthy();
  expect(subjectsApi.search).toHaveBeenCalled();
});
