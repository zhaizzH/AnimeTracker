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
