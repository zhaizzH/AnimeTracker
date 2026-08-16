import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import DiscoverPage from './page';
import { ApiError } from '@/lib/api/errors';

// 单个稳定的 adapter mock：listSubjects/listSearch/listTags 可重置/注入拒绝。
const { listSubjectsMock, searchSubjectsMock, listTagsMock } = vi.hoisted(() => ({
  listSubjectsMock: vi.fn(),
  searchSubjectsMock: vi.fn(),
  listTagsMock: vi.fn(),
}));

vi.mock('@/lib/api/public-client', () => ({
  getPublicApi: () => ({
    listSubjects: listSubjectsMock,
    searchSubjects: searchSubjectsMock,
    listTags: listTagsMock,
  }),
}));

describe('DiscoverPage (SSR)', () => {
  beforeEach(() => {
    listSubjectsMock.mockReset();
    searchSubjectsMock.mockReset();
    listTagsMock.mockReset();
    listSubjectsMock.mockResolvedValue({ content: [], total: 0 });
    listTagsMock.mockResolvedValue([]);
  });

  it('renders no error banner when the list succeeds', async () => {
    render(await DiscoverPage({ searchParams: Promise.resolve({}) }));
    expect(screen.queryByRole('alert')).toBeNull();
    expect(screen.getByRole('heading', { name: /发现/ })).toBeTruthy();
  });

  it('shows the backend message and requestId for a business ApiError', async () => {
    listSubjectsMock.mockRejectedValue(new ApiError(400, '筛选参数无效', undefined, 'req-d1'));
    render(await DiscoverPage({ searchParams: Promise.resolve({}) }));
    expect(screen.getByRole('alert')).toBeTruthy();
    expect(screen.getByText('筛选参数无效')).toBeTruthy();
    expect(screen.getByText('请求编号: req-d1')).toBeTruthy();
  });
});
