import { expect, test, vi, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import Users from './Users';

const { listMock, updateRoleMock } = vi.hoisted(() => {
  return {
    listMock: vi.fn().mockResolvedValue({ content: [{ id: 1, username: 'u', email: 'e@x.com', role: 'USER', createdAt: '' }], total: 1, page: 1, size: 20 }),
    updateRoleMock: vi.fn().mockResolvedValue({}),
  };
});

vi.mock('@shared', async (io) => {
  const mod = await io<typeof import('@shared')>();
  return { ...mod, adminUsersApi: { ...mod.adminUsersApi, list: listMock, updateRole: updateRoleMock } };
});

afterEach(() => cleanup());

// antd 组件（Grid/Modal 的 useBreakpoint）在 jsdom 需要 matchMedia
window.matchMedia = window.matchMedia || function matchMedia() {
  return { matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {}, dispatchEvent() {} } as any;
};

test('变更角色提交 update-role', async () => {
  render(<QueryClientProvider client={new QueryClient()}><ConfigProvider locale={zhCN}><Users /></ConfigProvider></QueryClientProvider>);
  await userEvent.click(await screen.findByRole('combobox'));
  // antd 下拉选项的真实可点击元素是 .ant-select-item-option（带 title），
  // role=option 是 rc-virtual-list 的外层包装，点击它不会触发 onChange。
  await userEvent.click(await screen.findByTitle('ADMIN'));
  await waitFor(() => expect(updateRoleMock).toHaveBeenCalledWith(1, 'ADMIN'));
});
