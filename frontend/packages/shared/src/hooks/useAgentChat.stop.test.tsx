import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
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
  listSessions: vi.fn().mockResolvedValue([{ session_id: 'session-1' }]),
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

type OnEvent = (data: string) => void;

/**
 * 渲染 hook → ready → 发一条消息，返回喂帧能力与调用序列。
 * 序列同时记录 stopRun 与 abort 事件，用于断言「先停 run 再断连」。
 */
async function setup() {
  const seq: string[] = [];
  const api = createApi();
  vi.mocked(api.stopRun).mockImplementation(() => {
    seq.push('stopRun');
    return Promise.resolve();
  });

  let onEvent: OnEvent = () => {};
  streamSseMock.mockImplementation((opts: { onEvent: OnEvent; signal?: AbortSignal }) => {
    onEvent = opts.onEvent;
    opts.signal?.addEventListener('abort', () => seq.push('abort'));
    return new Promise<void>(() => {});
  });

  const { result } = renderHook(() => useAgentChat(api));
  await waitFor(() => expect(result.current.ready).toBe(true));
  await act(async () => { void result.current.send('你好'); });
  await waitFor(() => expect(streamSseMock).toHaveBeenCalled());

  const feed = (...frames: string[]) => act(() => { frames.forEach((f) => onEvent(f)); });
  const stop = () => act(async () => { await result.current.stop(); });
  return { api, result, feed, stop, seq };
}

const firstFrame = (runId: string) =>
  JSON.stringify({ type: 'answer', content: { text: '答' }, meta: { run_id: runId } });

beforeEach(() => {
  streamSseMock.mockReset();
});

describe('useAgentChat 停止的顺序与 run_id 生命周期', () => {
  it('首帧记录 run_id：点停止先 stopRun(run_id) 再 abort 本地连接', async () => {
    const { api, feed, stop, seq } = await setup();

    feed(firstFrame('run-1'));
    await stop();

    expect(api.stopRun).toHaveBeenCalledWith('run-1');
    expect(seq).toEqual(['stopRun', 'abort']);
  });

  it('首帧之前点停止只 abort，不调用停 run（后端还没有 run 可停）', async () => {
    const { api, stop, seq } = await setup();

    await stop();

    expect(api.stopRun).not.toHaveBeenCalled();
    expect(seq).toEqual(['abort']);
  });

  it('run 正常结束后清空 run_id：再点停止不再停 run，只 abort', async () => {
    const { api, feed, stop, seq } = await setup();

    feed(firstFrame('run-1'), JSON.stringify({ content: {}, is_end: true }));
    await stop();

    expect(api.stopRun).not.toHaveBeenCalled();
    expect(seq).toEqual(['abort']);
  });

  it('停 run 抛错时仍然 abort，用户不会卡在停止中', async () => {
    const { api, feed, stop, seq } = await setup();
    vi.mocked(api.stopRun).mockImplementation(() => {
      seq.push('stopRun');
      return Promise.reject(new Error('503'));
    });

    feed(firstFrame('run-1'));
    await stop();

    expect(api.stopRun).toHaveBeenCalledWith('run-1');
    expect(seq).toEqual(['stopRun', 'abort']);
  });
});
