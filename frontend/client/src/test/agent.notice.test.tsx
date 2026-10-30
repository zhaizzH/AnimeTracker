import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AgentChatProvider, AgentConversation } from '@/components/AgentChat';
import { useAgentChat } from '@shared';

type State = ReturnType<typeof useAgentChat>;

const toastWarning = vi.hoisted(() => vi.fn());
const base = {
  messages: [], sessions: [], activeId: 'session-1', health: 'ok', streaming: false, ready: true, tools: [],
  conflict: null as State['conflict'],
  notice: null as State['notice'],
  runFailed: false,
  send: vi.fn(), stop: vi.fn(), select: vi.fn(), create: vi.fn(), remove: vi.fn(), resolveConflict: vi.fn(),
};

vi.mock('@shared', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@shared')>();
  return {
    ...actual,
    agentApi: {},
    useAgentChat: vi.fn(() => base),
    useAuthStore: (selector: (state: Record<string, unknown>) => unknown) => selector({ token: 'token' }),
  };
});
vi.mock('sonner', () => ({ toast: { warning: toastWarning, success: vi.fn(), error: vi.fn() } }));

// provider 内的 onUiAction 用 useNavigate，必须放在 Router 里
const chat = () => <MemoryRouter><AgentChatProvider><AgentConversation /></AgentChatProvider></MemoryRouter>;

beforeEach(() => {
  vi.clearAllMocks();
  // base 是跨用例共享对象，必须显式复位，否则上一条的 notice 会漏进下一条
  base.notice = null;
  base.runFailed = false;
});
afterEach(cleanup);

describe('一次性提示与会话级状态', () => {
  it('notice 变成 toast，不写进消息列表', () => {
    base.notice = { text: '部分实时内容已过期' };
    render(chat());

    expect(toastWarning).toHaveBeenCalledWith('部分实时内容已过期');
    expect(screen.queryByText('部分实时内容已过期')).toBeNull();
  });

  it('对话面板重挂载不会把同一条旧提示再弹一次', () => {
    base.notice = { text: '部分实时内容已过期' };
    const { rerender } = render(<MemoryRouter><AgentChatProvider><AgentConversation key="a" /></AgentChatProvider></MemoryRouter>);
    expect(toastWarning).toHaveBeenCalledTimes(1);

    // 模拟离开对话页再回来：provider 不动，只有面板换了一次实例
    rerender(<MemoryRouter><AgentChatProvider><AgentConversation key="b" /></AgentChatProvider></MemoryRouter>);

    expect(toastWarning).toHaveBeenCalledTimes(1);
  });

  it('runFailed 渲染成会话内横幅（刷新后仍在），不是 toast', () => {
    base.runFailed = true;
    render(chat());

    expect(screen.getByRole('status').textContent).toContain('上次回答未完成');
    expect(toastWarning).not.toHaveBeenCalled();
  });
});
