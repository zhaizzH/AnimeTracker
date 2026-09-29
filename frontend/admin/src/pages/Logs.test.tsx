import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Logs from './Logs';

const adminLogsApi = vi.hoisted(() => ({ list: vi.fn() }));
vi.mock('@shared', () => ({ adminLogsApi }));

const LOG = {
  id: 1, username: 'alice', module: 'AUTH', action: 'LOGIN', path: '/api/login',
  ip: '127.0.0.1', status: 0, durationMs: 12, createdAt: '2026-07-01 10:00',
};

function renderLogs() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <Logs />
    </QueryClientProvider>,
  );
}

beforeEach(() => vi.clearAllMocks());
afterEach(cleanup);

describe('Logs', () => {
  it('渲染 4 个统计卡与日志行', async () => {
    adminLogsApi.list.mockResolvedValue({
      content: [LOG], total: 1,
      stats: { total: 1, successCount: 1, failedCount: 0, avgDurationMs: 12 },
    });
    renderLogs();

    expect(await screen.findByText('alice')).not.toBeNull();
    expect(screen.getByText('平均耗时(ms)')).not.toBeNull();
    expect(screen.getByText('总数')).not.toBeNull();
  });

  it('action 列点击回填筛选并重置页码', async () => {
    adminLogsApi.list.mockResolvedValue({
      content: [LOG], total: 100,
      stats: { total: 100, successCount: 90, failedCount: 10, avgDurationMs: 8 },
    });
    const u = userEvent.setup();
    renderLogs();

    await waitFor(() => expect(screen.getByText('LOGIN')).not.toBeNull());
    await u.click(screen.getByRole('button', { name: '下一页' }));
    await waitFor(() =>
      expect(adminLogsApi.list).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 2 }),
      ),
    );

    await u.click(screen.getByRole('button', { name: 'LOGIN' }));

    // 点击 action 后：筛选带回 action，页码重置为 1
    await waitFor(() =>
      expect(adminLogsApi.list).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 1, action: 'LOGIN' }),
      ),
    );
  });

  it('用户名 onBlur 才触发筛选', async () => {
    adminLogsApi.list.mockResolvedValue({ content: [], total: 0 });
    const u = userEvent.setup();
    renderLogs();
    await screen.findByText('暂无日志');
    const before = adminLogsApi.list.mock.calls.length;

    const input = screen.getByLabelText('用户名/邮箱');
    await u.type(input, 'bob');
    expect(adminLogsApi.list.mock.calls.length).toBe(before);

    await u.tab();
    await waitFor(() =>
      expect(adminLogsApi.list).toHaveBeenLastCalledWith(
        expect.objectContaining({ username: 'bob' }),
      ),
    );
  });

  it('空数据显示空态', async () => {
    adminLogsApi.list.mockResolvedValue({ content: [], total: 0 });
    renderLogs();
    expect(await screen.findByText('暂无日志')).not.toBeNull();
  });
});
