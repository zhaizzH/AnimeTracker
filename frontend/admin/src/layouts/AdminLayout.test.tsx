import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { useThemeStore } from '@shared';
import { AdminLayout } from './AdminLayout';

type AuthState = {
  status: 'authenticated';
  user: { username: string; role: 'ADMIN' };
};

const authState = vi.hoisted(() => ({
  current: { status: 'authenticated', user: { username: 'admin-user', role: 'ADMIN' } } as AuthState,
}));
const logoutRequest = vi.hoisted(() => vi.fn());
const completeLogout = vi.hoisted(() => vi.fn());
const toastError = vi.hoisted(() => vi.fn());

vi.mock('@shared', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@shared')>();
  return {
    ...actual,
    authApi: { ...actual.authApi, logout: logoutRequest },
    completeLogout,
    useAuthStore: (selector: (state: AuthState) => unknown) => selector(authState.current),
  };
});

vi.mock('@/lib/toast', () => ({ toastError }));

let systemDark = false;
const systemThemeListeners = new Set<() => void>();

function mockMatchMedia() {
  return (query: string) => ({
    matches: systemDark,
    media: query,
    onchange: null,
    addEventListener: vi.fn((_event: string, listener: () => void) => { systemThemeListeners.add(listener); }),
    removeEventListener: vi.fn((_event: string, listener: () => void) => { systemThemeListeners.delete(listener); }),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  });
}

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

function TestApp({ initialEntry = '/admin/subjects?tab=all' }: { initialEntry?: string }) {
  return (
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/admin/login" element={<div>登录页</div>} />
        <Route path="/admin/*" element={<AdminLayout />}>
          <Route path="dashboard" element={<div>看板内容</div>} />
          <Route path="subjects" element={<div>番剧内容</div>} />
          <Route path="users" element={<div>用户内容</div>} />
          <Route path="import" element={<div>导入内容</div>} />
          <Route path="logs" element={<div>日志内容</div>} />
          <Route path="agent-config" element={<div>Agent 配置内容</div>} />
          <Route path="agent-chat" element={<div>Agent 对话内容</div>} />
        </Route>
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  vi.stubGlobal('matchMedia', mockMatchMedia());
  vi.stubGlobal('ResizeObserver', ResizeObserverMock);
  systemDark = false;
  systemThemeListeners.clear();
  useThemeStore.setState({ mode: 'light', followSystem: false });
  authState.current = { status: 'authenticated', user: { username: 'admin-user', role: 'ADMIN' } };
  logoutRequest.mockReset();
  completeLogout.mockReset();
  toastError.mockReset();
  document.documentElement.className = '';
  document.documentElement.style.colorScheme = '';
});

afterEach(() => {
  cleanup();
  useThemeStore.setState({ mode: 'light', followSystem: false });
  vi.unstubAllGlobals();
});

describe('AdminLayout', () => {
  it('renders all seven routes and highlights the current route despite query parameters', () => {
    render(<TestApp />);

    expect(screen.getByRole('link', { name: '看板' })).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: '番剧管理' })[0]).toHaveAttribute('aria-current', 'page');
    expect(screen.getByText('番剧内容')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '用户管理' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '导入管理' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '日志审计' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Agent 配置' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Agent 对话' })).toBeInTheDocument();
  });

  it('navigates through the existing route without a full page reload', async () => {
    const user = userEvent.setup();
    render(<TestApp />);

    await user.click(screen.getByRole('link', { name: '看板' }));

    expect(await screen.findByText('看板内容')).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: '看板' })[0]).toHaveAttribute('aria-current', 'page');
  });

  it('shows the authenticated username in the user menu trigger', () => {
    render(<TestApp />);

    expect(screen.getByRole('button', { name: '打开用户菜单：admin-user' })).toBeInTheDocument();
    expect(screen.getByText('admin-user')).toBeInTheDocument();
  });

  it('logs out successfully and navigates to the login page', async () => {
    const user = userEvent.setup();
    completeLogout.mockResolvedValue(true);
    render(<TestApp />);

    await user.click(screen.getByRole('button', { name: '打开用户菜单：admin-user' }));
    await user.click(screen.getByRole('menuitem', { name: '退出' }));

    expect(completeLogout).toHaveBeenCalledTimes(1);
    expect(completeLogout.mock.calls[0][0]).toBe(logoutRequest);
    expect(await screen.findByText('登录页')).toBeInTheDocument();
  });

  it('shows the failure toast and blocks a repeated logout while pending', async () => {
    const user = userEvent.setup();
    let resolveLogout: (value: boolean) => void = () => undefined;
    completeLogout.mockImplementation(() => new Promise<boolean>((resolve) => { resolveLogout = resolve; }));
    render(<TestApp />);

    await user.click(screen.getByRole('button', { name: '打开用户菜单：admin-user' }));
    await user.click(screen.getByRole('menuitem', { name: '退出' }));
    expect(completeLogout).toHaveBeenCalledTimes(1);

    const pendingItem = screen.getByRole('menuitem', { name: '退出中…' });
    expect(pendingItem).toHaveAttribute('data-disabled');
    fireEvent.click(pendingItem);
    expect(completeLogout).toHaveBeenCalledTimes(1);

    resolveLogout(false);
    await waitFor(() => expect(toastError).toHaveBeenCalledWith('退出失败，请重试'));
  });

  it('uses the shared theme store and follows system changes without a second provider', async () => {
    const user = userEvent.setup();
    const { unmount } = render(<TestApp />);

    await user.click(screen.getByRole('button', { name: '当前浅色模式' }));
    await user.click(screen.getByRole('menuitemradio', { name: '深色' }));
    await waitFor(() => expect(document.documentElement).toHaveClass('dark'));
    expect(useThemeStore.getState()).toMatchObject({ mode: 'dark', followSystem: false });

    await user.click(screen.getByRole('button', { name: '当前深色模式' }));
    await user.click(screen.getByRole('menuitemradio', { name: '跟随系统' }));
    await waitFor(() => expect(document.documentElement).not.toHaveClass('dark'));
    expect(useThemeStore.getState()).toMatchObject({ mode: 'dark', followSystem: true });

    systemDark = true;
    systemThemeListeners.forEach((listener) => listener());
    await waitFor(() => expect(document.documentElement).toHaveClass('dark'));

    unmount();
    expect(systemThemeListeners).toHaveLength(0);
  });
});
