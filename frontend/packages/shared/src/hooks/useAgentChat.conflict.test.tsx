import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { type AgentChatApi, useAgentChat } from './useAgentChat';
import { SseError } from '../sse';

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

type OnEvent = (data: string) => void;

const createApi = (): AgentChatApi => ({
  listSessions: vi.fn().mockResolvedValue([{ session_id: 'session-1' }]),
  createSession: vi.fn().mockResolvedValue({ session_id: 'session-1' }),
  history: vi.fn().mockResolvedValue([]),
  deleteSession: vi.fn().mockResolvedValue(undefined),
  streamBody: vi.fn((text: string) => ({ content: text })),
  streamUrl: '/agent/stream',
  sessionRun: vi.fn().mockRejectedValue(notFound()),
  stopRun: vi.fn().mockResolvedValue(undefined),
  runStreamUrl: (id: string, after: number) => `/agent/runs/${id}/stream?after=${after}`,
  health: vi.fn().mockResolvedValue('ok'),
});

/** 后端并发拒绝：同一会话已有 running run。 */
const conflictError = () =>
  new SseError('Agent 流式请求失败（409）', {
    status: 409,
    body: {
      code: 409,
      message: '当前会话已有进行中的对话',
      data: { active_run_id: 'run-active', status: 'running', capabilities: ['interrupt'] },
    },
  });

/**
 * 首条 /stream 以 409 拒绝，之后的重发挂起不结束（模拟新 run 正常生成中）。
 * 这样「发送相关请求次数」可以直接用 streamSseMock 的调用次数断言。
 */
async function setupConflict(history: Array<{ role: string; content: string }> = []) {
  const api = createApi();
  vi.mocked(api.history).mockResolvedValue(history as never);
  streamSseMock.mockImplementation((opts: { onEvent: OnEvent }) => {
    if (streamSseMock.mock.calls.length === 1) return Promise.reject(conflictError());
    return new Promise<void>(() => {});
  });

  const { result } = renderHook(() => useAgentChat(api));
  await waitFor(() => expect(result.current.ready).toBe(true));
  await act(async () => { void result.current.send('被拒绝的问题'); });
  await waitFor(() => expect(result.current.conflict).not.toBeNull());
  return { api, result };
}

const choose = (result: { current: ReturnType<typeof useAgentChat> }, choice: 'interrupt' | 'wait' | 'cancel') =>
  act(async () => { await result.current.resolveConflict(choice); });

beforeEach(() => {
  streamSseMock.mockReset();
});

describe('useAgentChat 409 并发冲突', () => {
  it('409 进入选择态：带出后端 active_run_id，不留半条气泡，也不吞掉原文', async () => {
    const { api, result } = await setupConflict();

    // 判据来自结构化字段，不依赖中文文案
    expect(result.current.conflict).toEqual({ activeRunId: 'run-active', status: 'running', capabilities: ['interrupt'], text: '被拒绝的问题' });
    // 用户气泡与空气泡都不留；也没有把「中断」文案写进正文
    expect(result.current.messages).toEqual([]);
    expect(result.current.streaming).toBe(false);
    expect(api.stopRun).not.toHaveBeenCalled();
    expect(streamSseMock).toHaveBeenCalledTimes(1);
  });

  it('停止并发送：先 stopRun(active_run_id) 再用同一段文本重发（共 2 次发送）', async () => {
    const { api, result } = await setupConflict();
    const order: string[] = [];
    vi.mocked(api.stopRun).mockImplementation(() => {
      order.push('stopRun');
      return Promise.resolve();
    });
    streamSseMock.mockImplementation((opts: { url: string; onEvent: OnEvent }) => {
      order.push(`stream:${opts.url}`);
      return new Promise<void>(() => {});
    });

    await choose(result, 'interrupt');
    await waitFor(() => expect(streamSseMock).toHaveBeenCalledTimes(2));

    expect(api.stopRun).toHaveBeenCalledWith('run-active');
    expect(order).toEqual(['stopRun', 'stream:/agent/stream']);
    // 重发用的是同一段文本
    expect(api.streamBody).toHaveBeenLastCalledWith('被拒绝的问题', 'session-1');
    expect(result.current.conflict).toBeNull();
  });

  it('等待：不发任何请求，退出选择态且原文可恢复', async () => {
    const { api, result } = await setupConflict();

    await choose(result, 'wait');

    expect(api.stopRun).not.toHaveBeenCalled();
    expect(streamSseMock).toHaveBeenCalledTimes(1);
    expect(result.current.conflict).toBeNull();
    expect(result.current.messages).toEqual([]);
  });

  it('取消面板：不发请求，也不留空气泡', async () => {
    const { api, result } = await setupConflict();

    await choose(result, 'cancel');

    expect(api.stopRun).not.toHaveBeenCalled();
    expect(streamSseMock).toHaveBeenCalledTimes(1);
    expect(result.current.conflict).toBeNull();
    expect(result.current.messages).toEqual([]);
  });

  // 语义反转：活跃 run 还在时重发必然再 409，只能原地重试，不能自动再发。
  it('停活跃 run 失败时不重发：面板与原文保留，并给出内联错误', async () => {
    const { api, result } = await setupConflict();
    vi.mocked(api.stopRun).mockRejectedValue(new Error('503'));
    streamSseMock.mockImplementation(() => new Promise<void>(() => {}));

    await choose(result, 'interrupt');

    expect(api.stopRun).toHaveBeenCalledWith('run-active');
    expect(streamSseMock).toHaveBeenCalledTimes(1);
    expect(result.current.conflict).toEqual({
      activeRunId: 'run-active',
      status: 'running',
      capabilities: ['interrupt'],
      text: '被拒绝的问题',
      error: '无法打断当前回答，请稍后重试',
    });
  });

  it('停 run 失败后可原地重试：重试成功时清掉内联错误并重发一次', async () => {
    const { api, result } = await setupConflict();
    vi.mocked(api.stopRun).mockRejectedValueOnce(new Error('503'));
    streamSseMock.mockImplementation(() => new Promise<void>(() => {}));

    await choose(result, 'interrupt');
    await waitFor(() => expect(result.current.conflict?.error).toBe('无法打断当前回答，请稍后重试'));

    // 重试挂起期间清 error 那一行只能在 act 内部观察到，这里不做断言（属已知不可测窗口）。
    await choose(result, 'interrupt');
    await waitFor(() => expect(streamSseMock).toHaveBeenCalledTimes(2));
    expect(api.stopRun).toHaveBeenCalledTimes(2);
    expect(result.current.conflict).toBeNull();
  });

  it('双击「停止并发送」只产生一次 stopRun 与一次重发', async () => {
    const { api, result } = await setupConflict();
    let releaseStop: () => void = () => {};
    vi.mocked(api.stopRun).mockImplementation(() => new Promise<void>((resolve) => { releaseStop = resolve; }));
    streamSseMock.mockImplementation(() => new Promise<void>(() => {}));

    // setConflict(null) 是异步 state：两次同步点击都会读到旧 conflict，同步锁必须拦住第二次。
    await act(async () => {
      const first = result.current.resolveConflict('interrupt');
      const second = result.current.resolveConflict('interrupt');
      releaseStop();
      await Promise.all([first, second]);
    });

    expect(api.stopRun).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(streamSseMock).toHaveBeenCalledTimes(2));
  });

  it('409 缺 active_run_id 时只提供等待/取消，打断不会空转', async () => {
    const api = createApi();
    streamSseMock.mockImplementationOnce(() =>
      Promise.reject(new SseError('Agent 流式请求失败（409）', { status: 409 })));
    const { result } = renderHook(() => useAgentChat(api));
    await waitFor(() => expect(result.current.ready).toBe(true));
    await act(async () => { void result.current.send('问题'); });
    await waitFor(() => expect(result.current.conflict).not.toBeNull());

    expect(result.current.conflict).toEqual({ activeRunId: null, status: null, capabilities: null, text: '问题' });

    await choose(result, 'interrupt');
    expect(result.current.conflict).toBeNull();
    expect(streamSseMock).toHaveBeenCalledTimes(1);
  });
});

describe('409 收回的范围', () => {
  it('只收回本次发出的 user + 空 assistant 气泡，不动会话里已有的历史消息', async () => {
    const { result } = await setupConflict([
      { role: 'user', content: '更早的问题' },
      { role: 'assistant', content: '更早的回答' },
    ]);

    expect(result.current.conflict?.activeRunId).toBe('run-active');
    // 历史两条仍在，本次的半成品被收回（否则 history 会被 setMessages([]) 抹掉也能过测）
    expect(result.current.messages.map((m) => m.content)).toEqual(['更早的问题', '更早的回答']);
  });
});
