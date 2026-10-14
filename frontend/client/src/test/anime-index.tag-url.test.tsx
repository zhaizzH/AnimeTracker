import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { subjectsApi, tagsApi } from '@shared';
import AnimeIndex from '@/pages/AnimeIndex';

const search = vi.hoisted(() => vi.fn());

vi.mock('@shared', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@shared')>();
  return { ...actual, subjectsApi: { ...actual.subjectsApi, search, years: vi.fn().mockResolvedValue([]) }, tagsApi: { ...actual.tagsApi, list: vi.fn() } };
});

const tags = [
  { id: 1, name: '日常', count: 5 },
  { id: 2, name: '治愈', count: 3 },
];

function renderAt(path: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <AnimeIndex />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const tagArg = () => search.mock.calls[search.mock.calls.length - 1]![0].tag;

describe('AnimeIndex 标签筛选以 URL 为源', () => {
  beforeEach(() => {
    vi.mocked(tagsApi.list).mockResolvedValue(tags as never);
    search.mockReset().mockResolvedValue({ content: [], total: 0, page: 1, size: 24 });
  });

  it('URL ?tag= 直接作为查询条件，无需点击', async () => {
    renderAt('/anime?tag=%E6%97%A5%E5%B8%B8');
    await waitFor(() => expect(tagArg()).toEqual(['日常']));
    expect(await screen.findByRole('button', { name: '日常 (5)' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: '治愈 (3)' })).toHaveAttribute('aria-pressed', 'false');
  });

  it('点击标签累加多选并回写 URL', async () => {
    renderAt('/anime?tag=%E6%97%A5%E5%B8%B8');
    const user = userEvent.setup();
    await user.click(await screen.findByRole('button', { name: '治愈 (3)' }));
    await waitFor(() => expect(tagArg()).toEqual(['日常', '治愈']));
  });

  it('再次点击已选标签取消该标签', async () => {
    renderAt('/anime?tag=%E6%97%A5%E5%B8%B8');
    const user = userEvent.setup();
    await user.click(await screen.findByRole('button', { name: '日常 (5)' }));
    await waitFor(() => expect(tagArg()).toBeUndefined());
  });
});

describe('AnimeIndex 标签折叠', () => {
  // 16 个标签，count 递减；冷门标签 '冷门' 排在最后
  const many = Array.from({ length: 15 }, (_, i) => ({ id: i + 1, name: `标签${i}`, count: 100 - i }));
  const cold = { id: 99, name: '冷门', count: 0 };

  beforeEach(() => {
    vi.mocked(tagsApi.list).mockResolvedValue([...many, cold] as never);
    search.mockReset().mockResolvedValue({ content: [], total: 0, page: 1, size: 24 });
  });

  it('默认只展示热度前 12 个，并提供展开入口', async () => {
    renderAt('/anime');
    expect(await screen.findByRole('button', { name: '标签0 (100)' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '标签11 (89)' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '标签12 (88)' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '展开全部 16 个标签' })).toHaveAttribute('aria-expanded', 'false');
  });

  it('URL 带入的冷门标签在折叠状态下仍可见并可取消', async () => {
    renderAt('/anime?tag=%E5%86%B7%E9%97%A8');
    await waitFor(() => expect(tagArg()).toEqual(['冷门']));
    const coldChip = await screen.findByRole('button', { name: '冷门 (0)' });
    expect(coldChip).toHaveAttribute('aria-pressed', 'true');
  });

  it('展开后显示全部标签，收起后恢复折叠', async () => {
    renderAt('/anime');
    const user = userEvent.setup();
    await user.click(await screen.findByRole('button', { name: '展开全部 16 个标签' }));
    expect(screen.getByRole('button', { name: '标签12 (88)' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '冷门 (0)' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '收起' }));
    expect(screen.queryByRole('button', { name: '标签12 (88)' })).not.toBeInTheDocument();
  });
});

describe('AnimeIndex 标签搜索', () => {
  const many = Array.from({ length: 15 }, (_, i) => ({ id: i + 1, name: `标签${i}`, count: 100 - i }));
  const cold = { id: 99, name: '冷门', count: 0 };

  beforeEach(() => {
    vi.mocked(tagsApi.list).mockResolvedValue([...many, cold] as never);
    search.mockReset().mockResolvedValue({ content: [], total: 0, page: 1, size: 24 });
  });

  it('输入关键词只保留匹配项，并覆盖被 Top-N 截断的标签', async () => {
    renderAt('/anime');
    const user = userEvent.setup();
    expect(await screen.findByRole('button', { name: '标签0 (100)' })).toBeInTheDocument();

    await user.type(screen.getByRole('textbox', { name: '搜索标签' }), '冷门');
    // '冷门' 排在第 16 位、默认被折叠，搜索必须能把它捞出来
    expect(screen.getByRole('button', { name: '冷门 (0)' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '标签0 (100)' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '展开全部 16 个标签' })).not.toBeInTheDocument();
  });

  it('搜索时已选标签仍可见，即使不匹配关键词', async () => {
    renderAt('/anime?tag=%E5%86%B7%E9%97%A8');
    const user = userEvent.setup();
    await waitFor(() => expect(tagArg()).toEqual(['冷门']));

    await user.type(await screen.findByRole('textbox', { name: '搜索标签' }), '标签0');
    // 关键词不匹配 '冷门'，但它是当前筛选条件，必须钉住以便取消
    expect(screen.getByRole('button', { name: '冷门 (0)' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByRole('button', { name: '标签0 (100)' })).toBeInTheDocument();
  });

  it('无匹配时给出提示，清除按钮还原全量', async () => {
    renderAt('/anime');
    const user = userEvent.setup();
    await user.type(await screen.findByRole('textbox', { name: '搜索标签' }), 'zzz');
    expect(screen.getByText('没有匹配的标签')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '清除标签搜索' }));
    expect(screen.queryByText('没有匹配的标签')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '标签0 (100)' })).toBeInTheDocument();
  });
});
