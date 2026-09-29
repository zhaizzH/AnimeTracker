import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AgentChat from './AgentChat';

type ChatState = {
  messages: { id: string; role: 'user' | 'assistant'; content: string; thinking?: string }[];
  sessions: Record<string, unknown>[];
  activeId: string | null;
  streaming: boolean;
};

const chatState = vi.hoisted(() => ({
  current: null as ChatState | null,
}));
const send = vi.hoisted(() => vi.fn());
const stop = vi.hoisted(() => vi.fn());
const select = vi.hoisted(() => vi.fn());
const create = vi.hoisted(() => vi.fn());
const remove = vi.hoisted(() => vi.fn());

vi.mock('@shared', () => ({
  adminAgentApi: {
    chatSessions: vi.fn(), chatCreateSession: vi.fn(), chatHistory: vi.fn(),
    chatDeleteSession: vi.fn(), chatStreamBody: vi.fn(),
  },
  useAgentChat: () => ({ ...chatState.current, send, stop, select, create, remove }),
}));

function renderChat(over: Partial<ChatState> = {}) {
  chatState.current = {
    messages: [], sessions: [], activeId: null, streaming: false, ...over,
  };
  return render(<AgentChat />);
}

beforeEach(() => vi.clearAllMocks());
afterEach(cleanup);

describe('AgentChat', () => {
  it('消息区使用 aria-live=polite', () => {
    renderChat({ messages: [{ id: '1', role: 'user', content: '你好' }] });
    expect(document.querySelector('[aria-live="polite"]')).not.toBeNull();
  });

  it('输入为空时发送按钮禁用，输入后可发送', async () => {
    const u = userEvent.setup();
    renderChat();
    const btn = screen.getByRole('button', { name: '发送' });
    expect(btn).toBeDisabled();

    await u.type(screen.getByLabelText('输入消息'), 'hi');
    expect(btn).toBeEnabled();
    await u.click(btn);
    expect(send).toHaveBeenCalledWith('hi');
  });

  it('流式中禁用输入、显示停止按钮，点击调用 stop', async () => {
    const u = userEvent.setup();
    renderChat({ streaming: true });
    expect(screen.getByLabelText('输入消息')).toBeDisabled();
    const btn = screen.getByRole('button', { name: '停止' });
    await u.click(btn);
    expect(stop).toHaveBeenCalled();
  });

  it('流式期间思考过程展开，结束后自动收起', async () => {
    const { rerender } = renderChat({
      streaming: true,
      messages: [{ id: '1', role: 'assistant', content: '回答', thinking: '推理中' }],
    });
    expect(screen.getByText('推理中')).not.toBeNull();
    expect(screen.getByRole('button', { name: '思考过程' })).toHaveAttribute('aria-expanded', 'true');

    // 流式结束
    chatState.current = { ...chatState.current!, streaming: false };
    rerender(<AgentChat />);

    await waitFor(() => expect(screen.queryByText('推理中')).toBeNull());
    expect(screen.getByRole('button', { name: '思考过程' })).toHaveAttribute('aria-expanded', 'false');
  });

  it('会话列表点击切换，删除按钮 stopPropagation', async () => {
    const u = userEvent.setup();
    renderChat({
      activeId: '2',
      sessions: [{ id: 1, title: '会话一' }, { id: 2, title: '会话二' }],
    });

    await u.click(screen.getByText('会话一'));
    expect(select).toHaveBeenCalledWith('1');

    // 仅激活会话显示删除按钮；点击不应触发 select
    const del = screen.getByRole('button', { name: '删' });
    select.mockClear();
    await u.click(del);
    expect(remove).toHaveBeenCalledWith('2');
    expect(select).not.toHaveBeenCalled();
  });

  it('新建会话按钮调用 create', async () => {
    const u = userEvent.setup();
    renderChat();
    await u.click(screen.getByRole('button', { name: '新建会话' }));
    expect(create).toHaveBeenCalled();
  });
});
