import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { ClientLayout } from '@/layouts/ClientLayout';
import { RequireAuth, PublicOnly } from '@/guards';

const authState = vi.hoisted(() => ({
  status: 'authenticated' as 'checking' | 'authenticated' | 'unauthenticated' | 'retryable-error',
  user: { id: 1, username: 'tester', nickname: '测试用户', role: 'USER' } as unknown,
}));

vi.mock('@shared', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@shared')>();
  return {
    ...actual,
    authApi: { logout: vi.fn() },
    completeLogout: vi.fn().mockResolvedValue(true),
    useAgentChat: vi.fn(() => ({
      messages: [], sessions: [], activeId: null, health: 'ok', streaming: false, ready: false,
      tools: [], send: vi.fn(), stop: vi.fn(), select: vi.fn(), create: vi.fn(), remove: vi.fn(),
    })),
    useAuthStore: (selector: (s: Record<string, unknown>) => unknown) =>
      selector({ token: 'token', status: authState.status, user: authState.user }),
    useThemeStore: (selector: (s: Record<string, unknown>) => unknown) =>
      selector({ mode: 'light', followSystem: false, setMode: vi.fn() }),
  };
});

function FromProbe() {
  const location = useLocation();
  const state = location.state as { from?: string } | null;
  return <output aria-label="来源">{state?.from ?? ''}</output>;
}

// 顶栏公开项构成桌面导航；个人项不在顶栏，只挂在头像下拉/移动抽屉中（默认不挂载）。
const linkCount = (name: string) => screen.queryAllByRole('link', { name }).length;

function renderAt(initial: string) {
  return render(
    <MemoryRouter initialEntries={[initial]}>
      <Routes>
        <Route path="/" element={<ClientLayout />}>
          <Route index element={<div data-testid="page">首页</div>} />
          <Route path="login" element={<><FromProbe /><div data-testid="page">登录页</div></>} />
          <Route path="my-collections" element={<RequireAuth><div data-testid="page">我的追番</div></RequireAuth>} />
          <Route path="agent" element={<RequireAuth><div data-testid="page">AI 助手</div></RequireAuth>} />
          <Route path="public-only" element={<PublicOnly><div data-testid="page">仅未登录</div></PublicOnly>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe('client 路由守卫与外壳', () => {
  beforeEach(() => {
    authState.status = 'authenticated';
    authState.user = { id: 1, username: 'tester', nickname: '测试用户', role: 'USER' };
  });

  it('已登录用户可进入 RequireAuth 页面（外壳渲染顶栏）', () => {
    renderAt('/my-collections');
    expect(screen.getByTestId('page')).toHaveTextContent('我的追番');
    expect(linkCount('首页')).toBeGreaterThan(0);
    expect(linkCount('每周日程')).toBeGreaterThan(0);
    expect(linkCount('番剧索引')).toBeGreaterThan(0);
  });

  it('登录后个人项收进头像菜单，展开后才出现', async () => {
    const user = userEvent.setup();
    renderAt('/');
    expect(linkCount('我的追番')).toBe(0);

    await user.click(screen.getByRole('button', { name: '账号菜单：测试用户' }));

    expect(await screen.findByRole('menuitem', { name: '我的追番' })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: 'AI 助手' })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: '个人中心' })).toBeInTheDocument();
    expect(screen.getByRole('menuitem', { name: '退出登录' })).toBeInTheDocument();
  });

  it('未登录访问 RequireAuth 页面重定向到 /login 且带 state.from', () => {
    authState.status = 'unauthenticated';
    renderAt('/my-collections');
    expect(screen.getByTestId('page')).toHaveTextContent('登录页');
    expect(screen.getByLabelText('来源')).toHaveTextContent('/my-collections');
  });

  it('已登录访问 PublicOnly 页面重定向到首页', () => {
    renderAt('/public-only');
    expect(screen.getByTestId('page')).toHaveTextContent('首页');
  });

  it('匿名访问时不渲染登录后入口', () => {
    authState.status = 'unauthenticated';
    authState.user = null;
    renderAt('/my-collections');
    expect(linkCount('我的追番')).toBe(0);
    expect(linkCount('个人中心')).toBe(0);
    expect(linkCount('每周日程')).toBeGreaterThan(0);
    expect(screen.getByRole('link', { name: '登录' })).toHaveAttribute('href', '/login');
  });

  it('外壳内页面渲染页脚，且不含 nav 段（导航项不重复）', () => {
    renderAt('/my-collections');
    const footer = screen.getByRole('contentinfo');
    expect(footer).toHaveTextContent('AnimeTracker');
    expect(linkCount('番剧索引')).toBe(1); // 仅顶栏；页脚已去掉 nav 段
    expect(linkCount('每周日程')).toBe(1);
  });

  it('对话页 /agent 不渲染页脚', () => {
    renderAt('/agent');
    expect(screen.getByTestId('page')).toHaveTextContent('AI 助手');
    expect(screen.queryByRole('contentinfo')).toBeNull();
  });
});
