import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import Dashboard from './Dashboard';

const api = vi.hoisted(() => ({
  overview: vi.fn(),
  trends: vi.fn(),
  collectionStats: vi.fn(),
  subjectStats: vi.fn(),
  hot: vi.fn(),
}));

vi.mock('@shared', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@shared')>();
  return { ...actual, adminDashboardApi: api };
});

// recharts 在 jsdom 下没有真实尺寸；把 ResponsiveContainer 降级为固定尺寸容器。
vi.mock('recharts', async (importOriginal) => {
  const actual = await importOriginal<typeof import('recharts')>();
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div style={{ width: 320, height: 200 }}>{children}</div>
    ),
  };
});

const overview = {
  userCount: 10,
  subjectCount: 20,
  collectionCount: 30,
  episodeCount: 40,
  importCount: 100,
  todayNewUsers: 3,
  todayNewCollections: 4,
  todayLogins: 5,
};

const trends = [
  { date: '2026-09-01', newUsers: 1, newCollections: 2, logins: 3 },
  { date: '2026-09-02', newUsers: 4, newCollections: 5, logins: 6 },
];

const collectionStats = {
  types: [
    { type: 1, count: 11 },
    { type: 5, count: 3 },
  ],
  ratings: [{ rate: 8, count: 7 }],
};

const subjectStats = {
  seasons: [{ seasonKey: '2026Q3', count: 12 }],
  importStatuses: [
    { importStatus: 0, count: 5 },
    { importStatus: 1, count: 15 },
  ],
  importStat: { importTotal: 20, importSucceeded: 18, importFailed: 2 },
  scoreCounts: [{ rate: 9, count: 4 }],
};

const hot = [
  { id: 's-1', name: 'Foo', nameCn: '芙', collectionCount: 99 },
  { id: 's-2', name: 'Bar', nameCn: null, collectionCount: 42 },
];

function renderDashboard() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

function resolveAll() {
  api.overview.mockResolvedValue(overview);
  api.trends.mockResolvedValue(trends);
  api.collectionStats.mockResolvedValue(collectionStats);
  api.subjectStats.mockResolvedValue(subjectStats);
  api.hot.mockResolvedValue(hot);
}

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  cleanup();
});

describe('Dashboard 九槽位真实数据映射', () => {
  it('9 个槽位各展示对应接口字段', async () => {
    resolveAll();
    renderDashboard();

    // 1 趋势（标题 + 周期控件）
    expect(await screen.findByText('新增趋势')).toBeInTheDocument();
    // 2 今日运营
    expect(screen.getByText('今日运营')).toBeInTheDocument();
    const todayCard = screen.getByText('今日运营').closest('[data-slot="card"]') as HTMLElement;
    await waitFor(() => expect(within(todayCard).getByText('3')).toBeInTheDocument()); // todayNewUsers
    expect(within(todayCard).getByText('4')).toBeInTheDocument(); // todayNewCollections
    expect(within(todayCard).getByText('5')).toBeInTheDocument(); // todayLogins
    // 3 热门番剧
    expect(screen.getByText('热门番剧')).toBeInTheDocument();
    expect(await screen.findByText('芙')).toBeInTheDocument();
    expect(screen.getByText('Bar')).toBeInTheDocument();
    expect(screen.getByText('99')).toBeInTheDocument();
    // 4 播出季度分布
    expect(screen.getByText('播出季度分布')).toBeInTheDocument();
    expect(await screen.findByText('2026Q3')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    // 5 收藏类型分布
    expect(screen.getByText('收藏类型分布')).toBeInTheDocument();
    expect(await screen.findByText('想看')).toBeInTheDocument();
    expect(screen.getByText('抛弃')).toBeInTheDocument();
    // 6 用户收藏评分分布
    expect(screen.getByText('用户收藏评分分布')).toBeInTheDocument();
    expect(await screen.findByText('8 分')).toBeInTheDocument();
    // 7 番剧自身评分分布（与 6 不同口径）
    expect(screen.getByText('番剧自身评分分布')).toBeInTheDocument();
    expect(await screen.findByText('9 分')).toBeInTheDocument();
    // 8 番剧导入状态分布
    expect(screen.getByText('番剧导入状态分布')).toBeInTheDocument();
    expect(await screen.findByText('待导入')).toBeInTheDocument();
    expect(screen.getByText('已导入')).toBeInTheDocument();
    // 9 导入记录
    expect(screen.getByText('导入记录')).toBeInTheDocument();
    expect(await screen.findByText('导入记录总数')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument(); // overview.importCount
    expect(screen.getByText('18')).toBeInTheDocument(); // importSucceeded
    expect(screen.getByText('2')).toBeInTheDocument(); // importFailed
  });

  it('默认 30 天，切换 7/90 天发起对应 trends(days) 请求并刷新描述', async () => {
    resolveAll();
    renderDashboard();
    await screen.findByText('新增趋势');
    expect(screen.getByText('近 30 天的新增用户、新增收藏与登录次数')).toBeInTheDocument();
    await waitFor(() => expect(api.trends).toHaveBeenCalledWith(30));

    const user = userEvent.setup();
    await user.click(screen.getByRole('button', { name: '7 天' }));
    await waitFor(() => expect(api.trends).toHaveBeenCalledWith(7));
    expect(await screen.findByText('近 7 天的新增用户、新增收藏与登录次数')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: '90 天' }));
    await waitFor(() => expect(api.trends).toHaveBeenCalledWith(90));
    expect(await screen.findByText('近 90 天的新增用户、新增收藏与登录次数')).toBeInTheDocument();
  });

  it('零值是有效统计值，不显示为空态', async () => {
    api.overview.mockResolvedValue({ ...overview, todayNewUsers: 0, importCount: 0 });
    api.trends.mockResolvedValue([]);
    api.collectionStats.mockResolvedValue({ types: [], ratings: [] });
    api.subjectStats.mockResolvedValue({
      ...subjectStats,
      importStat: { importTotal: 0, importSucceeded: 0, importFailed: 0 },
    });
    api.hot.mockResolvedValue([]);
    renderDashboard();

    expect(await screen.findByText('导入记录总数')).toBeInTheDocument();
    // 导入卡片已有值（0），不是空态
    expect(screen.queryByText('暂无数据')).not.toBeInTheDocument();
  });
});

describe('Dashboard 逐卡三态', () => {
  it('各卡独立加载态，互不影响', async () => {
    api.overview.mockReturnValue(new Promise(() => {}));
    api.trends.mockReturnValue(new Promise(() => {}));
    api.collectionStats.mockReturnValue(new Promise(() => {}));
    api.subjectStats.mockReturnValue(new Promise(() => {}));
    api.hot.mockReturnValue(new Promise(() => {}));
    renderDashboard();

    expect(await screen.findByText('趋势加载中…')).toBeInTheDocument();
    expect(screen.getByText('今日数据加载中…')).toBeInTheDocument();
    expect(screen.getByText('热门番剧加载中…')).toBeInTheDocument();
    expect(screen.getByText('季度分布加载中…')).toBeInTheDocument();
    expect(screen.getByText('收藏类型加载中…')).toBeInTheDocument();
    expect(screen.getByText('用户评分加载中…')).toBeInTheDocument();
    expect(screen.getByText('番剧评分加载中…')).toBeInTheDocument();
    expect(screen.getByText('导入状态加载中…')).toBeInTheDocument();
    expect(screen.getByText('导入记录加载中…')).toBeInTheDocument();
  });

  it('单查询失败只影响消费它的卡片', async () => {
    api.overview.mockResolvedValue(overview);
    api.trends.mockRejectedValue(new Error('boom'));
    api.collectionStats.mockResolvedValue(collectionStats);
    api.subjectStats.mockResolvedValue(subjectStats);
    api.hot.mockResolvedValue(hot);
    renderDashboard();

    // 趋势卡失败
    expect(await screen.findByText('趋势加载中…')).toBeInTheDocument();
    expect(await screen.findByText('加载失败，请稍后重试')).toBeInTheDocument();
    // 其他卡仍有数据
    expect(await screen.findByText('芙')).toBeInTheDocument();
    expect(await screen.findByText('今日运营')).toBeInTheDocument();
  });

  it('空数组显示空态而非留白', async () => {
    api.overview.mockResolvedValue(overview);
    api.trends.mockResolvedValue([]);
    api.collectionStats.mockResolvedValue({ types: [], ratings: [] });
    api.subjectStats.mockResolvedValue({
      ...subjectStats,
      seasons: [],
      importStatuses: [],
      scoreCounts: [],
    });
    api.hot.mockResolvedValue([]);
    renderDashboard();

    expect(await screen.findByText('暂无收藏数据')).toBeInTheDocument();
    expect(screen.getByText('暂无季度数据')).toBeInTheDocument();
    expect(screen.getByText('暂无收藏记录')).toBeInTheDocument();
    expect(screen.getByText('暂无评分记录')).toBeInTheDocument();
    expect(screen.getByText('暂无评分数据')).toBeInTheDocument();
    expect(screen.getByText('暂无导入状态数据')).toBeInTheDocument();
  });
});

describe('导入卡片双依赖状态', () => {
  it('overview 失败时导入卡片显示失败，即使 subjectStats 成功', async () => {
    api.overview.mockRejectedValue(new Error('boom'));
    api.trends.mockResolvedValue(trends);
    api.collectionStats.mockResolvedValue(collectionStats);
    api.subjectStats.mockResolvedValue(subjectStats);
    api.hot.mockResolvedValue(hot);
    renderDashboard();

    const card = (await screen.findByText('导入记录')).closest('[data-slot="card"]')!;
    expect(await within(card as HTMLElement).findByText('加载失败，请稍后重试')).toBeInTheDocument();
    // 不拼出误导性的部分总览
    expect(within(card as HTMLElement).queryByText('导入记录总数')).not.toBeInTheDocument();
  });
});
