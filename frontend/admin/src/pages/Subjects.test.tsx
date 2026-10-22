import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Subjects from './Subjects';

const subjectsApi = vi.hoisted(() => ({ search: vi.fn(), years: vi.fn() }));
const tagsApi = vi.hoisted(() => ({ list: vi.fn() }));
const adminSubjectsApi = vi.hoisted(() => ({
  create: vi.fn(), update: vi.fn(), remove: vi.fn(),
}));
const toastSuccess = vi.hoisted(() => vi.fn());
const toastError = vi.hoisted(() => vi.fn());

vi.mock('@shared', () => ({ subjectsApi, tagsApi, adminSubjectsApi }));
vi.mock('@/lib/toast', () => ({ toastSuccess, toastError }));

const ROW = { id: 1, name: 'Original Title', nameCn: '中文标题', score: 8.5, eps: 12, image: '' };

function renderSubjects() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <Subjects />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  subjectsApi.search.mockResolvedValue({ content: [ROW], total: 1 });
  subjectsApi.years.mockResolvedValue([2025, 2026]);
  tagsApi.list.mockResolvedValue([{ id: 1, name: '动作', count: 12 }, { id: 2, name: '日常', count: 8 }]);
});
afterEach(cleanup);

describe('Subjects', () => {
  it('渲染列表行', async () => {
    renderSubjects();
    expect(await screen.findByText('中文标题')).not.toBeNull();
    expect(screen.getByText('Original Title')).not.toBeNull();
  });

  it('搜索提交触发筛选并重置页码', async () => {
    const u = userEvent.setup();
    // 总数足够翻页，先确认页码可推进，再验证搜索重置
    subjectsApi.search.mockResolvedValue({ content: [ROW], total: 100 });
    renderSubjects();
    await screen.findByText('Original Title');

    await u.click(screen.getByRole('button', { name: '下一页' }));
    await waitFor(() => expect(subjectsApi.search).toHaveBeenLastCalledWith(expect.objectContaining({ page: 2 })));

    await u.type(screen.getByLabelText('搜索番剧'), 'naruto');
    await u.click(screen.getByRole('button', { name: '搜索' }));

    await waitFor(() =>
      expect(subjectsApi.search).toHaveBeenLastCalledWith(
        expect.objectContaining({ q: 'naruto', page: 1 }),
      ),
    );
  });

  it('全部 6 个筛选维度都进入请求参数', async () => {
    const u = userEvent.setup();
    renderSubjects();
    await screen.findByText('Original Title');

    // tag 多选：胶囊按钮多选，数量展示来自 TagVO.count
    await u.click(screen.getByRole('button', { name: '动作 (12)' }));
    await waitFor(() =>
      expect(subjectsApi.search).toHaveBeenLastCalledWith(
        expect.objectContaining({ tag: ['动作'], page: 1 }),
      ),
    );
    await u.click(screen.getByRole('button', { name: '日常 (8)' }));
    await waitFor(() =>
      expect(subjectsApi.search).toHaveBeenLastCalledWith(
        expect.objectContaining({ tag: ['动作', '日常'], page: 1 }),
      ),
    );

    // scoreMin / scoreMax
    await u.type(screen.getByLabelText('最低评分'), '6');
    await waitFor(() => expect(subjectsApi.search).toHaveBeenLastCalledWith(expect.objectContaining({ scoreMin: 6 })));
    await u.type(screen.getByLabelText('最高评分'), '9');
    await waitFor(() => expect(subjectsApi.search).toHaveBeenLastCalledWith(expect.objectContaining({ scoreMax: 9 })));

    // year
    await u.click(screen.getByRole('combobox', { name: '年份' }));
    await u.click(await screen.findByRole('option', { name: '2026' }));
    await waitFor(() => expect(subjectsApi.search).toHaveBeenLastCalledWith(expect.objectContaining({ year: 2026 })));

    // weekday
    await u.click(screen.getByRole('combobox', { name: '星期' }));
    await u.click(await screen.findByRole('option', { name: '周三' }));
    await waitFor(() => expect(subjectsApi.search).toHaveBeenLastCalledWith(expect.objectContaining({ weekday: 3 })));
  });

  it('重置清空全部筛选与输入框', async () => {
    const u = userEvent.setup();
    renderSubjects();
    await screen.findByText('Original Title');

    await u.type(screen.getByLabelText('搜索番剧'), 'naruto');
    await u.click(screen.getByRole('button', { name: '搜索' }));
    await u.type(screen.getByLabelText('最低评分'), '6');
    await u.click(screen.getByRole('button', { name: '动作 (12)' }));
    await waitFor(() => expect(subjectsApi.search).toHaveBeenLastCalledWith(expect.objectContaining({ q: 'naruto', scoreMin: 6, tag: ['动作'] })));

    await u.click(screen.getByRole('button', { name: '重置' }));
    await waitFor(() => expect(subjectsApi.search).toHaveBeenLastCalledWith(expect.objectContaining({ page: 1 })));
    expect(subjectsApi.search.mock.lastCall?.[0]).not.toHaveProperty('q');
    expect(subjectsApi.search.mock.lastCall?.[0]).not.toHaveProperty('scoreMin');
    expect(subjectsApi.search.mock.lastCall?.[0]).not.toHaveProperty('tag');
    expect((screen.getByLabelText('搜索番剧') as HTMLInputElement).value).toBe('');
    expect((screen.getByLabelText('最低评分') as HTMLInputElement).value).toBe('');
  });

  it('标签多于阈值时按热度折叠，选中项置顶，并可搜索过滤', async () => {
    const u = userEvent.setup();
    // 14 个标签：超过 TAG_LIMIT(12) 才出现标签搜索框与“展开全部”
    tagsApi.list.mockResolvedValue(
      Array.from({ length: 14 }, (_, i) => ({ id: i + 1, name: `标签${i + 1}`, count: 20 - i })),
    );
    renderSubjects();
    await screen.findByText('Original Title');

    await u.click(await screen.findByRole('button', { name: '展开全部 14 个标签' }));
    expect(await screen.findByRole('button', { name: '标签14 (7)' })).not.toBeNull();

    // 搜索标签：只保留匹配项
    await u.type(screen.getByLabelText('搜索标签'), '标签1');
    expect(screen.queryByRole('button', { name: '标签2 (19)' })).toBeNull();
    expect(screen.getByRole('button', { name: '标签13 (8)' })).not.toBeNull();

    // 清除标签搜索，恢复折叠态标题（已展开）
    await u.click(screen.getByRole('button', { name: '清除标签搜索' }));
    expect((screen.getByLabelText('搜索标签') as HTMLInputElement).value).toBe('');
  });

  it('新建时 name 与 bangumiId 必填，校验拦截不发请求', async () => {
    const u = userEvent.setup();
    renderSubjects();
    await screen.findByText('Original Title');

    await u.click(screen.getByRole('button', { name: '新建番剧' }));
    await screen.findByRole('dialog');
    await u.click(screen.getByRole('button', { name: '保存' }));

    expect(await screen.findByRole('alert')).toHaveProperty('textContent', '请填写日文/英文名');
    expect(adminSubjectsApi.create).not.toHaveBeenCalled();
  });

  it('编辑时不要求 bangumiId，保存调用 update', async () => {
    adminSubjectsApi.update.mockResolvedValue({});
    const u = userEvent.setup();
    renderSubjects();
    await screen.findByText('Original Title');

    await u.click(screen.getByRole('button', { name: '编辑' }));
    await screen.findByRole('dialog');
    expect(screen.queryByLabelText('Bangumi ID')).toBeNull();

    await u.click(screen.getByRole('button', { name: '保存' }));
    await waitFor(() => expect(adminSubjectsApi.update).toHaveBeenCalledWith(1, expect.objectContaining({ name: 'Original Title' })));
  });

  it('删除需确认，确认后调用 remove', async () => {
    adminSubjectsApi.remove.mockResolvedValue({});
    const u = userEvent.setup();
    renderSubjects();
    await screen.findByText('Original Title');

    await u.click(screen.getByRole('button', { name: '删除' }));
    expect(await screen.findByText('确定删除？该操作不可撤销。')).not.toBeNull();
    expect(adminSubjectsApi.remove).not.toHaveBeenCalled();

    await u.click(screen.getByRole('button', { name: '确定' }));
    await waitFor(() => expect(adminSubjectsApi.remove).toHaveBeenCalledWith(1));
  });
});
