import { expect, test, vi, afterEach } from 'vitest';
import { renderHook, waitFor, act, cleanup } from '@testing-library/react';
import { useAgentChat } from './useAgentChat';
import { useAuthStore } from '../store/auth';

const { streamSseMock } = vi.hoisted(() => ({ streamSseMock: vi.fn().mockResolvedValue(undefined) }));
vi.mock('../sse', () => ({ streamSse: streamSseMock }));

const login = { token: 't', refreshToken: 'r', user: { id: 1, username: 'u', email: 'e@x.com', role: 'USER', createdAt: '' } };

afterEach(() => { cleanup(); useAuthStore.getState().logout(); streamSseMock.mockClear(); });

test('admin api（无 health）→ 调用 admin 会话函数，health 保持 n/a', async () => {
  useAuthStore.getState().setLogin(login as never);
  const listSessions = vi.fn().mockResolvedValue([{ id: 'a1', title: 'admin会话' }]);
  const createSession = vi.fn().mockResolvedValue({ id: 'a2' });
  const history = vi.fn().mockResolvedValue([]);
  const deleteSession = vi.fn().mockResolvedValue(undefined);
  const streamBody = vi.fn().mockReturnValue({ message: 'x' });
  const api = { listSessions, createSession, history, deleteSession, streamBody, streamUrl: '/api/admin/agent/chat/stream' };

  const { result } = renderHook(() => useAgentChat(api));
  await waitFor(() => expect(result.current.sessions).toEqual([{ id: 'a1', title: 'admin会话' }]));
  expect(listSessions).toHaveBeenCalled();
  expect(result.current.health).toBe('n/a');

  await act(async () => { await result.current.create(); });
  expect(createSession).toHaveBeenCalled();
});

test('后端会话字段为 session_id 时归一化为 id，create 后 select 正确的会话', async () => {
  useAuthStore.getState().setLogin(login as never);
  const listSessions = vi.fn().mockResolvedValue([{ session_id: 's-1', title: '对话' }]);
  const createSession = vi.fn().mockResolvedValue({ session_id: 's-2' });
  const history = vi.fn().mockResolvedValue([]);
  const deleteSession = vi.fn().mockResolvedValue(undefined);
  const streamBody = vi.fn().mockReturnValue({ message: 'x' });
  const api = { listSessions, createSession, history, deleteSession, streamBody, streamUrl: '/api/admin/agent/chat/stream' };

  const { result } = renderHook(() => useAgentChat(api));
  await waitFor(() => expect(result.current.sessions).toEqual([{ session_id: 's-1', title: '对话', id: 's-1' }]));

  await act(async () => { await result.current.create(); });
  expect(result.current.activeId).toBe('s-2');
  expect(history).toHaveBeenCalledWith('s-2');
});

test('client api（含 health）→ health 有值且发送消息进入 messages', async () => {
  useAuthStore.getState().setLogin(login as never);
  const listSessions = vi.fn().mockResolvedValue([{ id: 's1', title: '对话1' }]);
  const createSession = vi.fn().mockResolvedValue({ id: 's2' });
  const history = vi.fn().mockResolvedValue([{ role: 'assistant', content: 'hi' }]);
  const deleteSession = vi.fn().mockResolvedValue(undefined);
  const streamBody = vi.fn().mockReturnValue({ message: 'x' });
  const health = vi.fn().mockResolvedValue('ok');
  const api = { listSessions, createSession, history, deleteSession, streamBody, streamUrl: '/api/client/agent/stream', health };

  const { result } = renderHook(() => useAgentChat(api));
  await waitFor(() => expect(result.current.health).toBe('ok'));
  await waitFor(() => expect(result.current.sessions.length).toBeGreaterThan(0));

  await act(async () => { await result.current.send('你好'); });
  expect(result.current.messages.some((m) => m.role === 'user' && m.content === '你好')).toBe(true);
  expect(streamSseMock).toHaveBeenCalledWith(expect.objectContaining({ url: '/api/client/agent/stream' }));
});

function fireOne(ev: Record<string, unknown>) {
  const cb = streamSseMock.mock.calls.at(-1)![0].onEvent as (data: string) => void;
  cb(JSON.stringify(ev));
}

test('send 按事件类型分流:thinking 累积、function_call 记工具、answer 流式累加', async () => {
  useAuthStore.getState().setLogin(login as never);
  const api = {
    listSessions: vi.fn().mockResolvedValue([]),
    createSession: vi.fn().mockResolvedValue({ session_id: 's1' }),
    history: vi.fn().mockResolvedValue([]),
    deleteSession: vi.fn().mockResolvedValue(undefined),
    streamBody: vi.fn().mockReturnValue({ content: 'x', session_id: 's1' }),
    streamUrl: '/api/admin/agent/chat/stream',
  };
  const { result } = renderHook(() => useAgentChat(api));
  await waitFor(() => expect(result.current.sessions).toEqual([]));

  let fulfill!: () => void;
  streamSseMock.mockImplementationOnce(() => new Promise<void>((r) => { fulfill = r; }));
  let sendPromise!: Promise<void>;
  await act(async () => { sendPromise = result.current.send('帮我搜索'); });

  await act(async () => { fireOne({ type: 'thinking', content: { text: '我在' } }); });
  expect(result.current.thinking).toBe('我在');

  await act(async () => { fireOne({ type: 'function_call', content: { state: 'start', name: '搜索番剧', message: '正在调用' } }); });
  expect(result.current.tools).toEqual([{ name: '搜索番剧', status: 'running', message: '正在调用' }]);

  await act(async () => { fireOne({ type: 'answer', content: { text: '找到' } }); });
  await act(async () => { fireOne({ type: 'answer', content: { text: '结果' } }); });
  await act(async () => { fireOne({ type: 'function_call', content: { state: 'end', name: '搜索番剧', message: '成功' } }); });
  await act(async () => { fireOne({ type: 'answer', is_end: true, content: {} }); });

  const asst = result.current.messages.filter((m) => m.role === 'assistant').pop();
  expect(asst?.content).toBe('找到结果');
  expect(result.current.tools[0]).toEqual({ name: '搜索番剧', status: 'done', message: '成功' });

  fulfill(); await act(async () => { await sendPromise; });
});
