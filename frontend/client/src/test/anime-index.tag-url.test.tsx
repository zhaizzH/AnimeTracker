import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ReactNode } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useLocation, useNavigate } from 'react-router-dom';
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

// 真实 router 暴露当前地址：断言「地址栏同步」而不是只看 mock 参数。
function LocationProbe() {
  return <output aria-label="当前地址">{useLocation().search}</output>;
}

// 模拟 SPA 内的外部导航（如详情页标签链、agent 导航）：组件不重挂载，只换 params
function NavButton({ to }: { to: string }) {
  const navigate = useNavigate();
  return <button type="button" onClick={() => navigate(to)}>外部跳转</button>;
}

function renderAt(path: string, extra?: ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <AnimeIndex />
        <LocationProbe />
        {extra}
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const urlSearch = () => screen.getByRole('status', { name: '当前地址' }).textContent ?? '';
const lastSearchArg = () => search.mock.calls[search.mock.calls.length - 1]![0] as Record<string, unknown>;
const card = (name: string) => ({ id: name, name, nameCn: name, score: 8, rank: 1, eps: 12, type: 1, airWeekday: 1, collectionTotal: 0 });

const tagArg = () => search.mock.calls[search.mock.calls.length - 1]![0].tag;

describe('AnimeIndex 筛选以 URL 为唯一来源', () => {
  beforeEach(() => {
    vi.mocked(tagsApi.list).mockResolvedValue(tags as never);
    vi.mocked(subjectsApi.years).mockResolvedValue([2021, 2022, 2023] as never);
    search.mockReset().mockResolvedValue({ content: [], total: 0, page: 1, size: 24 });
  });

  it('直接打开带筛选的 URL 时四个字段全部进入查询，控件同步回显', async () => {
    renderAt('/anime?year=2022&weekday=5&sort=rank&order=asc&page=2');

    await waitFor(() =>
      expect(lastSearchArg()).toMatchObject({ year: 2022, weekday: 5, sort: 'rank', order: 'asc', page: 2 }),
    );
    expect(await screen.findByText('2022')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole('combobox', { name: '年份' })).toHaveTextContent('2022'));
    expect(screen.getByRole('combobox', { name: '播出星期' })).toHaveTextContent('周五');
    expect(screen.getByRole('combobox', { name: '排序' })).toHaveTextContent('排名');
    expect(screen.getByRole('combobox', { name: '方向' })).toHaveTextContent('升序');
  });

  it('切标签也把页码重置回 1（筛选变更统一复位）', async () => {
    const user = userEvent.setup();
    renderAt('/anime?page=3');
    await waitFor(() => expect(lastSearchArg().page).toBe(3));

    await user.click(await screen.findByRole('button', { name: '日常 (5)' }));

    await waitFor(() => expect(lastSearchArg()).toMatchObject({ tag: ['日常'], page: 1 }));
    expect(urlSearch()).toContain('page=1');
  });

  it('URL 缺省时默认值生效，且不把默认值塞进请求', async () => {
    renderAt('/anime');

    await waitFor(() => expect(lastSearchArg()).toMatchObject({ sort: 'score', order: 'desc', page: 1 }));
    expect(lastSearchArg().year).toBeUndefined();
    expect(lastSearchArg().weekday).toBeUndefined();
  });

  it('改年份写回 URL、控件回显新值，并把页码重置回 1', async () => {
    const user = userEvent.setup();
    renderAt('/anime?page=3');
    await waitFor(() => expect(lastSearchArg().page).toBe(3));

    await user.click(screen.getByRole('combobox', { name: '年份' }));
    await user.click(await screen.findByRole('option', { name: '2022' }));

    await waitFor(() => expect(lastSearchArg()).toMatchObject({ year: 2022, page: 1 }));
    expect(screen.getByRole('combobox', { name: '年份' })).toHaveTextContent('2022');
    expect(urlSearch()).toContain('year=2022');
    expect(urlSearch()).toContain('page=1');
    expect(urlSearch()).not.toContain('page=3');
  });

  it('排序改回默认值时从 URL 移除该键，地址栏保持干净', async () => {
    const user = userEvent.setup();
    renderAt('/anime?sort=rank');
    expect(await screen.findByRole('combobox', { name: '排序' })).toHaveTextContent('排名');

    await user.click(screen.getByRole('combobox', { name: '排序' }));
    await user.click(await screen.findByRole('option', { name: '评分' }));

    await waitFor(() => expect(lastSearchArg().sort).toBe('score'));
    expect(urlSearch()).not.toContain('sort=');
  });

  it('翻页不算筛选变更，页码不会被重置回 1', async () => {
    const user = userEvent.setup();
    search.mockResolvedValue({ content: [card('旧番')], total: 100, page: 1, size: 24 });
    renderAt('/anime');

    await user.click(await screen.findByRole('button', { name: '下一页' }));

    await waitFor(() => expect(lastSearchArg().page).toBe(2));
    expect(urlSearch()).toContain('page=2');
  });
});

describe('AnimeIndex 界面随操作真实变化（D4 四条）', () => {
  beforeEach(() => {
    vi.mocked(tagsApi.list).mockResolvedValue(tags as never);
    vi.mocked(subjectsApi.years).mockResolvedValue([2021, 2022] as never);
    search.mockReset();
  });

  // mock 必须真的按 year 分支返回不同集合，否则「列表真的换了」测不出来
  const searchByYear = () =>
    search.mockImplementation((p: { year?: number }) =>
      Promise.resolve({
        content: p.year === 2022 ? [card('2022 的番')] : [card('全部年份的番')],
        total: 1,
        page: 1,
        size: 24,
      }),
    );
  // D4 指定形态：SubjectGrid 骨架卡片的 aria-hidden 容器（页面其它 aria-hidden 装饰不算，故要求容器内含 skeleton）
  const skeletons = () =>
    [...document.querySelectorAll('[aria-hidden="true"]')].filter((el) => el.querySelector('[data-slot="skeleton"]'));

  it('① 控件显示值同步：改年份后下拉立刻回显 2022', async () => {
    searchByYear();
    const user = userEvent.setup();
    renderAt('/anime');
    await waitFor(() => expect(screen.getByRole('combobox', { name: '年份' })).toHaveTextContent('全部年份'));

    await user.click(screen.getByRole('combobox', { name: '年份' }));
    await user.click(await screen.findByRole('option', { name: '2022' }));

    await waitFor(() => expect(screen.getByRole('combobox', { name: '年份' })).toHaveTextContent('2022'));
  });

  it('② 结果列表真实重查并替换：新集合出现、旧集合消失', async () => {
    searchByYear();
    const user = userEvent.setup();
    renderAt('/anime');
    expect(await screen.findByText('全部年份的番')).toBeInTheDocument();

    await user.click(screen.getByRole('combobox', { name: '年份' }));
    await user.click(await screen.findByRole('option', { name: '2022' }));

    expect(await screen.findByText('2022 的番')).toBeInTheDocument();
    expect(screen.queryByText('全部年份的番')).not.toBeInTheDocument();
  });

  it('③ 重查期间出现骨架屏，结束后不残留旧卡片', async () => {
    search.mockResolvedValueOnce({ content: [card('旧列表的番')], total: 1, page: 1, size: 24 });
    let resolveSecond: (v: unknown) => void = () => {};
    search.mockImplementationOnce(() => new Promise((resolve) => { resolveSecond = resolve; }) as never);

    const user = userEvent.setup();
    renderAt('/anime');
    expect(await screen.findByText('旧列表的番')).toBeInTheDocument();
    expect(skeletons().length).toBe(0);

    await user.click(screen.getByRole('combobox', { name: '年份' }));
    await user.click(await screen.findByRole('option', { name: '2022' }));

    // 新请求 pending 期间：骨架在场、旧卡片已撤
    await waitFor(() => expect(skeletons().length).toBeGreaterThan(0));
    expect(screen.queryByText('旧列表的番')).not.toBeInTheDocument();

    resolveSecond({ content: [card('新列表的番')], total: 1, page: 1, size: 24 });
    expect(await screen.findByText('新列表的番')).toBeInTheDocument();
    await waitFor(() => expect(skeletons().length).toBe(0));
    expect(screen.queryByText('旧列表的番')).not.toBeInTheDocument();
  });

  it('④ 无结果时显示空态，不保留上一次的列表', async () => {
    search.mockImplementation((p: { year?: number }) =>
      Promise.resolve(
        p.year === 2022
          ? { content: [], total: 0, page: 1, size: 24 }
          : { content: [card('全部年份的番')], total: 1, page: 1, size: 24 },
      ),
    );
    const user = userEvent.setup();
    renderAt('/anime');
    expect(await screen.findByText('全部年份的番')).toBeInTheDocument();

    await user.click(screen.getByRole('combobox', { name: '年份' }));
    await user.click(await screen.findByRole('option', { name: '2022' }));

    expect(await screen.findByText('暂无数据')).toBeInTheDocument();
    expect(screen.queryByText('全部年份的番')).not.toBeInTheDocument();
  });
});

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

describe('AnimeIndex 关键词输入框跟随 URL', () => {
  beforeEach(() => {
    vi.mocked(tagsApi.list).mockResolvedValue(tags as never);
    search.mockReset().mockResolvedValue({ content: [], total: 0, page: 1, size: 24 });
  });

  it('直接打开带 q 的 URL 时输入框回显该关键词', async () => {
    renderAt('/anime?q=2022');
    await waitFor(() => expect(screen.getByRole('textbox', { name: '关键词' })).toHaveValue('2022'));
  });

  it('外部导航改 q 后输入框跟随，再搜索不把 URL 覆盖回旧值', async () => {
    const user = userEvent.setup();
    renderAt('/anime', <NavButton to="/anime?q=2022" />);
    const input = screen.getByRole('textbox', { name: '关键词' });
    await waitFor(() => expect(input).toHaveValue(''));

    await user.click(screen.getByRole('button', { name: '外部跳转' }));

    await waitFor(() => expect(input).toHaveValue('2022'));
    await user.click(screen.getByRole('button', { name: '搜索' }));
    await waitFor(() => expect(urlSearch()).toContain('q=2022'));
  });
});

describe('AnimeIndex 非法筛选参数视为未筛选', () => {
  beforeEach(() => {
    vi.mocked(tagsApi.list).mockResolvedValue(tags as never);
    vi.mocked(subjectsApi.years).mockResolvedValue([2021, 2022] as never);
    search.mockReset().mockResolvedValue({ content: [], total: 0, page: 1, size: 24 });
  });

  it('?year=abc&weekday=xyz 时不带 NaN 进请求，控件回落到全部', async () => {
    renderAt('/anime?year=abc&weekday=xyz');

    await waitFor(() => expect(search).toHaveBeenCalled());
    const arg = lastSearchArg();
    expect(arg.year).toBeUndefined();
    expect(arg.weekday).toBeUndefined();
    expect(screen.getByRole('combobox', { name: '年份' })).toHaveTextContent('全部年份');
    expect(screen.getByRole('combobox', { name: '播出星期' })).toHaveTextContent('全部星期');
  });
});

describe('AnimeIndex 筛选写入 URL 的剩余路径', () => {
  beforeEach(() => {
    vi.mocked(tagsApi.list).mockResolvedValue(tags as never);
    vi.mocked(subjectsApi.years).mockResolvedValue([2021, 2022] as never);
    search.mockReset().mockResolvedValue({ content: [], total: 0, page: 1, size: 24 });
  });

  it('改播出星期写回 URL 并回显，页码重置回 1', async () => {
    const user = userEvent.setup();
    renderAt('/anime?page=3');
    await waitFor(() => expect(lastSearchArg().page).toBe(3));

    await user.click(screen.getByRole('combobox', { name: '播出星期' }));
    await user.click(await screen.findByRole('option', { name: '周五' }));

    await waitFor(() => expect(lastSearchArg()).toMatchObject({ weekday: 5, page: 1 }));
    expect(screen.getByRole('combobox', { name: '播出星期' })).toHaveTextContent('周五');
    expect(urlSearch()).toContain('weekday=5');
    expect(urlSearch()).toContain('page=1');
    expect(urlSearch()).not.toContain('page=3');
  });

  it('方向改回默认值 desc 时从 URL 移除该键', async () => {
    const user = userEvent.setup();
    renderAt('/anime?order=asc');
    expect(await screen.findByRole('combobox', { name: '方向' })).toHaveTextContent('升序');

    await user.click(screen.getByRole('combobox', { name: '方向' }));
    await user.click(await screen.findByRole('option', { name: '降序' }));

    await waitFor(() => expect(lastSearchArg().order).toBe('desc'));
    expect(urlSearch()).not.toContain('order=');
  });

  it('重置清空全部筛选：URL 回空、年份回全部年份、关键词清空', async () => {
    const user = userEvent.setup();
    renderAt('/anime?q=2022&year=2022&weekday=5&sort=rank&order=asc&page=2');
    await waitFor(() => expect(lastSearchArg()).toMatchObject({ year: 2022, weekday: 5, page: 2 }));
    expect(screen.getByRole('textbox', { name: '关键词' })).toHaveValue('2022');

    await user.click(screen.getByRole('button', { name: '重置' }));

    await waitFor(() => expect(lastSearchArg()).toMatchObject({ page: 1 }));
    expect(lastSearchArg().year).toBeUndefined();
    expect(lastSearchArg().weekday).toBeUndefined();
    expect(urlSearch()).toBe('');
    expect(screen.getByRole('combobox', { name: '年份' })).toHaveTextContent('全部年份');
    expect(screen.getByRole('combobox', { name: '播出星期' })).toHaveTextContent('全部星期');
    expect(screen.getByRole('textbox', { name: '关键词' })).toHaveValue('');
  });
});
