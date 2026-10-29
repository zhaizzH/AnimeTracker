import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { type AgentChatApi, useAgentChat } from './useAgentChat';

/** 真实 404 来自 axios，一定带 status；裸 Error 会被 hook 当成「状态未知」。 */
const notFound = () => Object.assign(new Error('404'), { status: 404 });

const streamSseMock = vi.hoisted(() => vi.fn());
vi.mock('../auth/stream', () => ({ streamSseWithAuth: streamSseMock }));
// 裸 streamSse 一律抛错：hook 必须走 streamSseWithAuth（带 401 刷新闭环）。
// 这样「有人把调用改回 streamSse」会立刻转红，而不是悄悄绕过刷新。
vi.mock('../sse', async () => {
  const actual = await vi.importActual<typeof import('../sse')>('../sse');
  return {
    ...actual,
    streamSse: () => { throw new Error('hook 不得直接调用 streamSse，必须走 streamSseWithAuth'); },
  };
});

const createApi = (): AgentChatApi => ({
  listSessions: vi.fn().mockResolvedValue([]),
  createSession: vi.fn().mockResolvedValue({ session_id: 'session-1' }),
  history: vi.fn().mockResolvedValue([]),
  deleteSession: vi.fn().mockResolvedValue(undefined),
  streamBody: vi.fn().mockReturnValue({}),
  streamUrl: '/agent/stream',
  sessionRun: vi.fn().mockRejectedValue(notFound()),
  stopRun: vi.fn().mockResolvedValue(undefined),
  runStreamUrl: (id: string, after: number) => `/agent/runs/${id}/stream?after=${after}`,
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

  it('删除当前(最后)会话后自动新建会话，不进入无会话悬挂态', async () => {
    const api = createApi();
    vi.mocked(api.listSessions).mockResolvedValue([{ session_id: 'session-1' }]);
    vi.mocked(api.createSession).mockResolvedValue({ session_id: 'session-2' });
    const { result } = renderHook(() => useAgentChat(api));

    await waitFor(() => expect(result.current.activeId).toBe('session-1'));
    await waitFor(() => expect(result.current.ready).toBe(true));

    vi.mocked(api.listSessions).mockResolvedValue([]);
    await act(async () => { await result.current.remove('session-1'); });

    expect(api.deleteSession).toHaveBeenCalledWith('session-1');
    expect(api.createSession).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(result.current.activeId).toBe('session-2'));
    expect(result.current.ready).toBe(true);
  });

  it('删除当前会话但还有其他会话时，选中剩余首个会话而不新建', async () => {
    const api = createApi();
    vi.mocked(api.listSessions).mockResolvedValue([
      { session_id: 'session-1' },
      { session_id: 'session-2' },
    ]);
    const { result } = renderHook(() => useAgentChat(api));

    await waitFor(() => expect(result.current.activeId).toBe('session-1'));
    await waitFor(() => expect(result.current.ready).toBe(true));

    // 删当前激活的 session-1 后，列表还剩 session-2
    vi.mocked(api.listSessions).mockResolvedValue([{ session_id: 'session-2' }]);
    vi.mocked(api.history).mockResolvedValue([]);
    await act(async () => { await result.current.remove('session-1'); });

    expect(api.deleteSession).toHaveBeenCalledWith('session-1');
    expect(api.createSession).not.toHaveBeenCalled();
    await waitFor(() => expect(result.current.activeId).toBe('session-2'));
    expect(result.current.ready).toBe(true);
  });
});
