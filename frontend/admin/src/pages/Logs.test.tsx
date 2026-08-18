import { expect, test, vi, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import Logs from './Logs';

const { listMock } = vi.hoisted(() => {
  const page = { content: { content: [{ id: 1, username: 'u', action: 'LOGIN', module: 'AUTH', status: 0, durationMs: 12, createdAt: '' }], total: 1, page: 1, size: 20, stats: { total: 1, failedCount: 0, successCount: 1, avgDurationMs: 12 } }, total: 1, page: 1, size: 20 };
  return { listMock: vi.fn().mockResolvedValue(page) };
});

vi.mock('@shared', async (io) => {
  const mod = await io<typeof import('@shared')>();
  return { ...mod, adminLogsApi: { ...mod.adminLogsApi, list: listMock } };
});

afterEach(() => cleanup());

// antd 组件（Grid/Modal 的 useBreakpoint）在 jsdom 需要 matchMedia
window.matchMedia = window.matchMedia || function matchMedia() {
  return { matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {}, dispatchEvent() {} } as any;
};

test('筛选动作后请求带 action', async () => {
  render(<QueryClientProvider client={new QueryClient()}><ConfigProvider locale={zhCN}><Logs /></ConfigProvider></QueryClientProvider>);
  await userEvent.click(await screen.findByText('LOGIN'));
  await waitFor(() => expect(listMock).toHaveBeenCalledWith(expect.objectContaining({ action: 'LOGIN' })));
});
