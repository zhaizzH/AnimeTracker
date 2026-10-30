import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Link, MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { ClientLayout } from '@/layouts/ClientLayout';
import Agent from '@/pages/Agent';
import { AgentChatProvider, AgentConversation } from '@/components/AgentChat';
import { clearNavHint, consumeAgentNavigation, markAgentNavigation, showNavHint } from '@/components/agentNavigation';
import { useAgentChat } from '@shared';

const chat = {
  messages: [],
  sessions: [],
  activeId: 'session-1',
  health: 'ok',
  streaming: false,
  ready: true,
  tools: [],
  conflict: null,
  notice: null,
  runFailed: false,
  resolveConflict: vi.fn().mockResolvedValue(undefined),
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
  } as unknown,
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
      toggleFollowSystem: vi.fn(),
    }),
  };
});

const realGetComputedStyle = window.getComputedStyle;
beforeAll(() => {
  vi.spyOn(window, 'getComputedStyle').mockImplementation((element) => realGetComputedStyle(element));
});
beforeEach(() => {
  chat.streaming = false;
  chat.stop.mockClear();
  vi.mocked(useAgentChat).mockClear();
  vi.mocked(useAgentChat).mockImplementation(() => chat);
});
afterEach(() => {
  cleanup();
  // agentNavigation 是模块级 store，跨用例残留会让「提示已清空」类断言随机通过
  clearNavHint();
  consumeAgentNavigation();
  authState.user = { ...(authState.user as Record<string, unknown>), id: 1, username: 'tester' };
});
afterAll(() => vi.restoreAllMocks());

function Page({ name }: { name: string }) {
  return <><span>{name}</span><Link to="/schedule">前往日程</Link><Link to="/collections">前往收藏</Link></>;
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
          <Route path="collections" element={<Page name="收藏" />} />
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
    await user.click(screen.getAllByRole('link', { name: '前往日程' })[0]);
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

    authState.user = { ...(authState.user as Record<string, unknown>), id: 2, username: 'another-user' };
    view.rerender(app());

    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'AI 助手' })).toBeNull());
  });

  it('在带尾斜杠的完整助手页面隐藏浮动入口并激活共享聊天', async () => {
    renderApp('/agent/');
    expect(screen.queryByRole('button', { name: '打开 AI 助手' })).toBeNull();
    await waitFor(() => expect(vi.mocked(useAgentChat).mock.calls.some(([, options]) => options?.enabled === true)).toBe(true));
  });

  it('流式期间显示停止按钮并调用 stop', async () => {
    const user = userEvent.setup();
    vi.mocked(useAgentChat).mockImplementation(() => ({ ...chat, streaming: true }));
    render(<AgentChatProvider><AgentConversation /></AgentChatProvider>);

    const stopButton = await screen.findByRole('button', { name: /停\s*止/ });
    await user.click(stopButton);

    expect(chat.stop).toHaveBeenCalledTimes(1);
  });
});

describe('全局 AI 助手浮窗 · agent 导航保持与系统提示', () => {
  const hint = () => screen.queryByText(/已跳转到/);

  it('标记 agent 导航后，路由变化不关面板', async () => {
    const user = userEvent.setup();
    renderApp();
    await user.click(screen.getByRole('button', { name: '打开 AI 助手' }));
    expect(screen.getByRole('dialog', { name: 'AI 助手' })).not.toBeNull();

    // child 2 的调用顺序：先标记，再 navigate
    act(() => markAgentNavigation());
    await user.click(screen.getAllByRole('link', { name: '前往日程' })[0]);

    expect(await screen.findByText('日程')).toBeInTheDocument();
    expect(screen.getByRole('dialog', { name: 'AI 助手' })).not.toBeNull();
  });

  it('标记是一次性的：用后复位，用户下一次手动导航仍照旧关闭', async () => {
    const user = userEvent.setup();
    renderApp();
    await user.click(screen.getByRole('button', { name: '打开 AI 助手' }));

    act(() => markAgentNavigation());
    await user.click(screen.getAllByRole('link', { name: '前往日程' })[0]);
    expect(await screen.findByText('日程')).toBeInTheDocument();
    expect(screen.getByRole('dialog', { name: 'AI 助手' })).not.toBeNull();

    // 第二次导航未标记，必须关
    await user.click(screen.getAllByRole('link', { name: '前往收藏' })[0]);
    expect(await screen.findByText('收藏')).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'AI 助手' })).toBeNull());
  });

  it('showNavHint 后面板内出现系统提示，且不写入会话历史', async () => {
    const user = userEvent.setup();
    const before = chat.messages;
    renderApp();
    await user.click(screen.getByRole('button', { name: '打开 AI 助手' }));

    act(() => showNavHint('番剧索引 · 2022 年'));

    expect(await screen.findByText(/番剧索引 · 2022 年/)).toBeInTheDocument();
    // 瞬时 UI 状态，不进 messages（那会持久化到后端）
    expect(chat.messages).toBe(before);
    expect(chat.messages).toHaveLength(0);
  });

  it('面板关闭时收到 hint，下次打开显示最后一条，不累积', async () => {
    const user = userEvent.setup();
    renderApp();

    act(() => showNavHint('第一次'));
    act(() => showNavHint('第二次'));
    expect(hint()).toBeNull();

    await user.click(screen.getByRole('button', { name: '打开 AI 助手' }));
    expect(await screen.findByText(/已跳转到「第二次」/)).toBeInTheDocument();
    expect(screen.queryByText(/第一次/)).toBeNull();
    expect(screen.getAllByText(/已跳转到/)).toHaveLength(1);
  });

  it('用户手动导航时作废上一条提示，再开面板不再显示', async () => {
    const user = userEvent.setup();
    renderApp();
    await user.click(screen.getByRole('button', { name: '打开 AI 助手' }));

    act(() => markAgentNavigation());
    await user.click(screen.getAllByRole('link', { name: '前往日程' })[0]);
    act(() => showNavHint('日程'));
    expect(await screen.findByText(/已跳转到「日程」/)).toBeInTheDocument();

    // 用户手动跳转：面板关，提示随之作废
    await user.click(screen.getAllByRole('link', { name: '前往收藏' })[0]);
    expect(await screen.findByText('收藏')).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'AI 助手' })).toBeNull());

    // 关键：重开面板后旧提示不得复活（不清空则会残留「日程」）
    await user.click(screen.getByRole('button', { name: '打开 AI 助手' }));
    expect(screen.getByRole('dialog', { name: 'AI 助手' })).not.toBeNull();
    expect(hint()).toBeNull();
  });
});
