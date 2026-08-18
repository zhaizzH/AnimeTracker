import { expect, test, vi, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import Subjects from './Subjects';

const { row, searchMock, createMock, updateMock, removeMock } = vi.hoisted(() => {
  const row = { id: 1, name: 'n', nameCn: '测试番', score: 8, rank: 1, eps: 12, type: 2, airWeekday: 1, collectionTotal: 5 };
  return {
    row,
    searchMock: vi.fn().mockResolvedValue({ content: [row], total: 1, page: 1, size: 20 }),
    createMock: vi.fn().mockResolvedValue({}),
    updateMock: vi.fn().mockResolvedValue({}),
    removeMock: vi.fn().mockResolvedValue(undefined),
  };
});

vi.mock('@shared', async (io) => {
  const mod = await io<typeof import('@shared')>();
  return {
    ...mod,
    subjectsApi: { ...mod.subjectsApi, search: searchMock },
    adminSubjectsApi: { ...mod.adminSubjectsApi, create: createMock, update: updateMock, remove: removeMock },
  };
});

afterEach(() => cleanup());

// antd 组件（Grid/Modal 的 useBreakpoint）在 jsdom 需要 matchMedia
window.matchMedia = window.matchMedia || function matchMedia() {
  return { matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {}, dispatchEvent() {} } as any;
};

test('删除触发确认后调用 remove', async () => {
  render(<QueryClientProvider client={new QueryClient()}><ConfigProvider locale={zhCN}><Subjects /></ConfigProvider></QueryClientProvider>);
  await userEvent.click(await screen.findByRole('button', { name: /删\s*除/ }));
  await userEvent.click(await screen.findByRole('button', { name: /确\s*定/ }));
  await waitFor(() => expect(removeMock).toHaveBeenCalledWith(1));
});
