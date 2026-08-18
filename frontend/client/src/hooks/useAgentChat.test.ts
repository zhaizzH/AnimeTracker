import { expect, test, vi, afterEach } from 'vitest';
import { renderHook, waitFor, act, cleanup } from '@testing-library/react';
import { useAgentChat } from './useAgentChat';
import { useAuthStore } from '@shared';

vi.mock('@shared', async (io) => {
  const mod = await io<typeof import('@shared')>();
  return {
    ...mod,
    agentApi: {
      ...mod.agentApi,
      health: vi.fn().mockResolvedValue('ok'),
      listSessions: vi.fn().mockResolvedValue([{ id: 's1', title: '对话1' }]),
      createSession: vi.fn().mockResolvedValue({ id: 's2' }),
      history: vi.fn().mockResolvedValue([{ role: 'assistant', content: 'hi' }]),
      deleteSession: vi.fn().mockResolvedValue(undefined),
      streamBody: mod.agentApi.streamBody,
    },
    streamSse: vi.fn(),
  };
});

afterEach(() => cleanup());

test('发送消息把用户内容加入 messages 并调用流式', async () => {
  const login = { token: 't', refreshToken: 'r', user: { id: 1, username: 'u', email: 'e@x.com', role: 'USER', createdAt: '' } };
  useAuthStore.getState().setLogin(login as never);
  const { result } = renderHook(() => useAgentChat());
  await waitFor(() => expect(result.current.sessions.length).toBeGreaterThan(0));
  await act(async () => { await result.current.send('你好'); });
  expect(result.current.messages.some((m) => m.role === 'user' && m.content === '你好')).toBe(true);
  useAuthStore.getState().logout();
});
