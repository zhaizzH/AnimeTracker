import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { type AgentChatApi, useAgentChat } from './useAgentChat';

const streamSseMock = vi.hoisted(() => vi.fn());
vi.mock('../sse', () => ({ streamSse: streamSseMock }));

const createApi = (): AgentChatApi => ({
  listSessions: vi.fn().mockResolvedValue([]),
  createSession: vi.fn().mockResolvedValue({ session_id: 'session-1' }),
  history: vi.fn().mockResolvedValue([]),
  deleteSession: vi.fn().mockResolvedValue(undefined),
  streamBody: vi.fn().mockReturnValue({}),
  streamUrl: '/agent/stream',
  health: vi.fn().mockResolvedValue('ok'),
});

describe('useAgentChat 延迟初始化', () => {
  it('禁用时不访问 Agent API，启用后只初始化一次', async () => {
    const api = createApi();
    const { rerender } = renderHook(
      ({ enabled }) => useAgentChat(api, { enabled }),
      { initialProps: { enabled: false } },
    );

    expect(api.listSessions).not.toHaveBeenCalled();
    expect(api.createSession).not.toHaveBeenCalled();

    rerender({ enabled: true });

    await waitFor(() => expect(api.listSessions).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(api.createSession).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(api.health).toHaveBeenCalledTimes(1));
    const listCallsAfterInitialization = vi.mocked(api.listSessions).mock.calls.length;

    rerender({ enabled: true });
    expect(api.listSessions).toHaveBeenCalledTimes(listCallsAfterInitialization);
    expect(api.createSession).toHaveBeenCalledTimes(1);
    expect(api.health).toHaveBeenCalledTimes(1);
  });

  it('历史加载完成前拒绝发送，完成后进入 ready 状态', async () => {
    let resolveHistory!: (messages: Record<string, unknown>[]) => void;
    const api = createApi();
    vi.mocked(api.listSessions).mockResolvedValue([{ session_id: 'session-1' }]);
    vi.mocked(api.history).mockReturnValue(new Promise((resolve) => { resolveHistory = resolve; }));
    const { result } = renderHook(() => useAgentChat(api));

    await waitFor(() => expect(result.current.activeId).toBe('session-1'));
    expect(result.current.ready).toBe(false);

    await act(async () => { await result.current.send('过早发送'); });
    expect(api.streamBody).not.toHaveBeenCalled();

    resolveHistory([]);
    await waitFor(() => expect(result.current.ready).toBe(true));
  });

  it('卸载时中止尚未完成的流式请求', async () => {
    streamSseMock.mockImplementation(() => new Promise(() => {}));
    const api = createApi();
    vi.mocked(api.listSessions).mockResolvedValue([{ session_id: 'session-1' }]);
    const { result, unmount } = renderHook(() => useAgentChat(api));
    await waitFor(() => expect(api.history).toHaveBeenCalledWith('session-1'));
    await act(async () => {});

    act(() => { void result.current.send('继续生成'); });
    await waitFor(() => expect(streamSseMock).toHaveBeenCalledTimes(1));
    const signal = streamSseMock.mock.calls[0][0].signal as AbortSignal;

    unmount();
    expect(signal.aborted).toBe(true);
  });
});
