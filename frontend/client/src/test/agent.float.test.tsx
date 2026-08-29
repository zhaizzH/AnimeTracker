import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Link, MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { ClientLayout } from '../layouts/ClientLayout';
import Agent from '../pages/Agent';
import { useAgentChat } from '@shared';

const chat = {
  messages: [],
  sessions: [],
  activeId: 'session-1',
  health: 'ok',
  streaming: false,
  ready: true,
  tools: [],
  send: vi.fn(),
  stop: vi.fn(),
  select: vi.fn(),
  create: vi.fn(),
  remove: vi.fn(),
};

const authState = vi.hoisted(() => ({
  user: {
    id: 1, username: 'tester', email: 'tester@example.com', nickname: '测试用户',
    role: 'USER', enabled: true, createdAt: '2026-01-01',
  },
}));

vi.mock('@shared', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@shared')>();
  return {
    ...actual,
    agentApi: {},
    authApi: {},
    completeLogout: vi.fn().mockResolvedValue(true),
    resolveMode: () => 'light',
    useAgentChat: vi.fn(() => chat),
    useAuthStore: (selector: (state: Record<string, unknown>) => unknown) => selector({
      token: 'token',
      status: 'authenticated',
      user: authState.user,
    }),
    useThemeStore: (selector: (state: Record<string, unknown>) => unknown) => selector({
      mode: 'light',
      followSystem: false,
      setMode: vi.fn(),
    }),
  };
});

const realGetComputedStyle = window.getComputedStyle;
beforeAll(() => {
  vi.spyOn(window, 'getComputedStyle').mockImplementation((element) => realGetComputedStyle(element));
});
beforeEach(() => vi.mocked(useAgentChat).mockClear());
afterEach(() => {
  cleanup();
  authState.user = { ...authState.user, id: 1, username: 'tester' };
});
afterAll(() => vi.restoreAllMocks());

function Page({ name }: { name: string }) {
  return <><span>{name}</span><Link to="/schedule">前往日程</Link></>;
}

function Pathname() {
  return <output aria-label="当前路径">{useLocation().pathname}</output>;
}

function TestApp() {
  return (
    <>
      <Routes>
        <Route path="/" element={<ClientLayout />}>
          <Route index element={<Page name="首页" />} />
          <Route path="schedule" element={<Page name="日程" />} />
          <Route path="agent" element={<Agent />} />
        </Route>
      </Routes>
      <Pathname />
    </>
  );
}

const app = (path = '/') => <MemoryRouter initialEntries={[path]}><TestApp /></MemoryRouter>;
const renderApp = (path = '/') => render(app(path));

describe('全局 AI 助手浮窗', () => {
  it('从右下角按钮打开，并可用图标或 Esc 关闭', async () => {
    const user = userEvent.setup();
    renderApp();
    expect(vi.mocked(useAgentChat).mock.calls.some(([, options]) => options?.enabled === false)).toBe(true);

    await user.click(screen.getByRole('button', { name: '打开 AI 助手' }));
    await waitFor(() => expect(vi.mocked(useAgentChat).mock.calls.some(([, options]) => options?.enabled === true)).toBe(true));
    const dialog = screen.getByRole('dialog', { name: 'AI 助手' });
    expect(dialog).not.toBeNull();
    expect(dialog.getAttribute('aria-modal')).toBe('false');

    await user.click(screen.getByRole('button', { name: '关闭 AI 助手对话框' }));
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'AI 助手' })).toBeNull());

    await user.click(screen.getByRole('button', { name: '打开 AI 助手' }));
    await user.click(screen.getByRole('button', { name: '关闭 AI 助手' }));
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'AI 助手' })).toBeNull());

    await user.click(screen.getByRole('button', { name: '打开 AI 助手' }));
    await user.keyboard('{Escape}');
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'AI 助手' })).toBeNull());
  });

  it('路由切换时关闭浮窗，并能跳转完整助手', async () => {
    const user = userEvent.setup();
    renderApp();

    await user.click(screen.getByRole('button', { name: '打开 AI 助手' }));
    await user.click(screen.getByRole('link', { name: '前往日程' }));
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'AI 助手' })).toBeNull());

    await user.click(screen.getByRole('button', { name: '打开 AI 助手' }));
    await user.click(screen.getByRole('button', { name: '打开完整助手' }));
    expect(screen.getByRole('status', { name: '当前路径' }).textContent).toBe('/agent');
  });

  it('切换登录用户时销毁上一位用户的浮窗状态', async () => {
    const user = userEvent.setup();
    const view = renderApp();
    await user.click(screen.getByRole('button', { name: '打开 AI 助手' }));
    expect(screen.getByRole('dialog', { name: 'AI 助手' })).not.toBeNull();

    authState.user = { ...authState.user, id: 2, username: 'another-user' };
    view.rerender(app());

    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'AI 助手' })).toBeNull());
  });

  it('在带尾斜杠的完整助手页面隐藏浮动入口并激活共享聊天', async () => {
    renderApp('/agent/');
    expect(screen.queryByRole('button', { name: '打开 AI 助手' })).toBeNull();
    await waitFor(() => expect(vi.mocked(useAgentChat).mock.calls.some(([, options]) => options?.enabled === true)).toBe(true));
  });
});
