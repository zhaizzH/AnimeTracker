import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { AgentChatProvider, AgentConversation } from '@/components/AgentChat';
import { useAgentChat } from '@shared';

type State = ReturnType<typeof useAgentChat>;

const resolveConflict = vi.hoisted(() => vi.fn().mockResolvedValue(undefined));

const base = {
  messages: [],
  sessions: [],
  activeId: 'session-1',
  health: 'ok',
  streaming: false,
  ready: true,
  tools: [],
  conflict: null as State['conflict'],
  notice: null as State['notice'],
  runFailed: false,
  send: vi.fn(),
  stop: vi.fn(),
  select: vi.fn(),
  create: vi.fn(),
  remove: vi.fn(),
  resolveConflict,
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

/** 后端 409 的原文：未发出的文本留在选择态里，UI 负责恢复进输入框。 */
const CONFLICT = { activeRunId: 'run-active', status: 'running', capabilities: ['interrupt'], text: '被打断的问题' } as State['conflict'];

// provider 内的 onUiAction 用 useNavigate，必须放在 Router 里
const chat = () => <MemoryRouter><AgentChatProvider><AgentConversation /></AgentChatProvider></MemoryRouter>;

beforeEach(() => vi.clearAllMocks());
afterEach(cleanup);

describe('client AgentConversation 的 409 冲突面板', () => {
  it('有冲突时显示三个选项，并把未发出的文本放回输入框', async () => {
    base.conflict = CONFLICT;
    render(chat());

    expect(screen.getByRole('group', { name: '会话已有回答在生成' })).not.toBeNull();
    expect(screen.getByRole('button', { name: '停止并发送' })).not.toBeNull();
    expect(screen.getByRole('button', { name: '等待' })).not.toBeNull();
    expect(screen.getByRole('button', { name: '取消' })).not.toBeNull();
    await waitFor(() => expect(screen.getByLabelText('发送给 AI 助手的消息')).toHaveValue('被打断的问题'));
  });

  it('停止并发送：调用 resolveConflict(interrupt) 并清空输入框（文本已重发）', async () => {
    const u = userEvent.setup();
    base.conflict = CONFLICT;
    render(chat());

    await u.click(screen.getByRole('button', { name: '停止并发送' }));

    expect(resolveConflict).toHaveBeenCalledWith('interrupt');
    await waitFor(() => expect(screen.getByLabelText('发送给 AI 助手的消息')).toHaveValue(''));
  });

  it.each([
    ['等待', 'wait'],
    ['取消', 'cancel'],
  ])('%s 保留原文在输入框，用户不会丢掉这条消息', async (label, choice) => {
    const u = userEvent.setup();
    base.conflict = CONFLICT;
    const view = render(chat());

    await u.click(screen.getByRole('button', { name: label }));
    expect(resolveConflict).toHaveBeenCalledWith(choice);

    // 选择后 hook 清掉冲突 → 面板消失、输入框仍留有原文
    base.conflict = null;
    view.rerender(chat());
    await waitFor(() => expect(screen.queryByRole('group', { name: '会话已有回答在生成' })).toBeNull());
    expect(screen.getByLabelText('发送给 AI 助手的消息')).toHaveValue('被打断的问题');
  });

  it('缺 active_run_id 时禁用「停止并发送」，且不会清空未发出的原文', async () => {
    const u = userEvent.setup();
    base.conflict = { ...CONFLICT, activeRunId: null } as State['conflict'];
    render(chat());

    const interrupt = screen.getByRole('button', { name: '停止并发送' });
    expect(interrupt).toBeDisabled();
    await u.click(interrupt);
    expect(resolveConflict).not.toHaveBeenCalled();
    await waitFor(() => expect(screen.getByLabelText('发送给 AI 助手的消息')).toHaveValue('被打断的问题'));
  });

  it('capabilities 显式为 [] 时禁用「停止并发送」并说明原因', () => {
    base.conflict = { ...CONFLICT, capabilities: [] } as State['conflict'];
    render(chat());

    const btn = screen.getByRole('button', { name: '停止并发送' });
    expect(btn).toBeDisabled();
    // title 挂在外层 span：disabled 的 button 不派发 hover，提示要由 span 承载
    expect(btn.closest('span')).toHaveAttribute('title', '当前无法打断');
  });

  it('capabilities 缺失时按可用处理：缺失是「不知道」，不是「不允许」', () => {
    base.conflict = { ...CONFLICT, capabilities: null } as State['conflict'];
    render(chat());

    expect(screen.getByRole('button', { name: '停止并发送' })).not.toBeDisabled();
  });

  it('停 run 失败的内联错误渲染在面板里，面板仍在', () => {
    base.conflict = { ...CONFLICT, error: '无法打断当前回答，请稍后重试' } as State['conflict'];
    render(chat());

    expect(screen.getByRole('group', { name: '会话已有回答在生成' })).not.toBeNull();
    expect(screen.getByRole('alert').textContent).toContain('无法打断当前回答，请稍后重试');
  });
});
