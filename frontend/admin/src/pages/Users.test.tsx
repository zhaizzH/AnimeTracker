import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Users from './Users';
import type { UserVO } from '@shared';

const adminUsersApi = vi.hoisted(() => ({
  list: vi.fn(),
  updateRole: vi.fn(),
  updateEnabled: vi.fn(),
}));
const toastSuccess = vi.hoisted(() => vi.fn());
const toastError = vi.hoisted(() => vi.fn());

vi.mock('@shared', () => ({ adminUsersApi }));
vi.mock('@/lib/toast', () => ({ toastSuccess, toastError }));

const user = (over: Partial<UserVO> = {}): UserVO =>
  ({
    id: 1,
    username: 'alice',
    email: 'a@b.c',
    nickname: 'Alice',
    createdAt: '2026-01-01',
    enabled: true,
    role: 'USER',
    ...over,
  }) as UserVO;

function renderUsers() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <Users />
    </QueryClientProvider>,
  );
}

beforeEach(() => vi.clearAllMocks());
afterEach(cleanup);

describe('Users', () => {
  it('渲染用户行', async () => {
    adminUsersApi.list.mockResolvedValue({ content: [user()], total: 1 });
    renderUsers();
    expect(await screen.findByText('alice')).not.toBeNull();
    expect(screen.getByText('a@b.c')).not.toBeNull();
  });

  it('禁用需确认，确认文案逐字一致', async () => {
    adminUsersApi.list.mockResolvedValue({ content: [user()], total: 1 });
    const u = userEvent.setup();
    renderUsers();
    await screen.findByText('alice');

    await u.click(screen.getByRole('switch', { name: '禁用用户 alice' }));

    expect(
      await screen.findByText('禁用后，该用户将在所有设备上立即退出。确定继续吗？'),
    ).not.toBeNull();
    expect(adminUsersApi.updateEnabled).not.toHaveBeenCalled();

    await u.click(screen.getByRole('button', { name: '确定' }));
    await waitFor(() => expect(adminUsersApi.updateEnabled).toHaveBeenCalledWith(1, false));
  });

  it('连续快速点击开关只产生一次请求（防重复切换）', async () => {
    adminUsersApi.list.mockResolvedValue({ content: [user({ enabled: false })], total: 1 });
    let resolveUpdate: (v: unknown) => void = () => {};
    adminUsersApi.updateEnabled.mockImplementation(
      () => new Promise((res) => { resolveUpdate = res; }),
    );
    const u = userEvent.setup();
    renderUsers();
    await screen.findByText('alice');

    const sw = screen.getByRole('switch', { name: '启用用户 alice' });
    await Promise.all([u.click(sw), u.click(sw), u.click(sw)]);

    expect(adminUsersApi.updateEnabled).toHaveBeenCalledTimes(1);
    resolveUpdate(undefined);
    await waitFor(() => expect(toastSuccess).toHaveBeenCalledWith('用户已启用'));
  });

  it('角色变更直接触发 mutation，无确认弹窗', async () => {
    adminUsersApi.list.mockResolvedValue({ content: [user()], total: 1 });
    adminUsersApi.updateRole.mockResolvedValue(undefined);
    const u = userEvent.setup();
    renderUsers();
    await screen.findByText('alice');

    await u.click(screen.getByRole('combobox', { name: '用户 alice 的角色' }));
    await u.click(await screen.findByRole('option', { name: 'ADMIN' }));

    await waitFor(() => expect(adminUsersApi.updateRole).toHaveBeenCalledWith(1, 'ADMIN'));
    expect(screen.queryByText('确定继续吗？')).toBeNull();
  });

  it('空数据显示空态', async () => {
    adminUsersApi.list.mockResolvedValue({ content: [], total: 0 });
    renderUsers();
    expect(await screen.findByText('暂无用户数据')).not.toBeNull();
  });

  it('分页控件随总数禁用/启用', async () => {
    adminUsersApi.list.mockResolvedValue({ content: [user()], total: 1 });
    renderUsers();
    await screen.findByText('alice');
    const row = screen.getByText('共 1 条').parentElement!;
    expect(within(row).getByRole('button', { name: '上一页' })).toHaveProperty('disabled', true);
    expect(within(row).getByRole('button', { name: '下一页' })).toHaveProperty('disabled', true);
  });
});
