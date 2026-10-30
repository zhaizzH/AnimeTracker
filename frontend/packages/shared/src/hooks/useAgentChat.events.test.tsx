import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { type AgentChatApi, useAgentChat } from './useAgentChat';
import { SseAbortError, SseError } from '../sse';

/** 真实 404 来自 axios，一定带 status；裸 Error 会被 hook 当成「状态未知」。 */
const notFound = () => Object.assign(new Error('404'), { status: 404 });

// streamSse 被替换成可控桩：测试直接拿到 onEvent 手动喂帧；两个错误类保留真实实现。
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
const frame = (type: string, content: Record<string, unknown>, isEnd = false) =>
  JSON.stringify({ type, content, ...(isEnd ? { is_end: true } : {}) });

/** 渲染 hook、等它进入 ready，再发一条消息，返回喂帧与读取当前状态的能力。 */
async function setup(options?: Parameters<typeof useAgentChat>[1]) {
  const api = createApi();
  const { result } = renderHook(() => useAgentChat(api, options));
  await waitFor(() => expect(result.current.ready).toBe(true));

  let onEvent: OnEvent = () => {};
  streamSseMock.mockImplementation((opts: { onEvent: OnEvent }) => {
    onEvent = opts.onEvent;
    return new Promise<void>(() => {});
  });

  await act(async () => { void result.current.send('你好'); });
  await waitFor(() => expect(streamSseMock).toHaveBeenCalled());

  const feed = (...frames: string[]) => {
    act(() => { frames.forEach((f) => onEvent(f)); });
  };
  const lastAssistant = () => result.current.messages.filter((m) => m.role === 'assistant').at(-1);
  return { result, feed, lastAssistant };
}

beforeEach(() => {
  streamSseMock.mockReset();
});

describe('useAgentChat 事件分发', () => {
  it('answer 累加正文、thinking 累加思考区，互不串扰', async () => {
    const { feed, lastAssistant } = await setup();

    feed(frame('thinking', { text: '先想想' }), frame('answer', { text: '你' }), frame('answer', { text: '好' }));

    expect(lastAssistant()?.content).toBe('你好');
    expect(lastAssistant()?.thinking).toBe('先想想');
  });

  it('status 事件带 content.text 时正文不被污染，只有 state=error 才追加提示', async () => {
    const { feed, lastAssistant } = await setup();

    feed(frame('answer', { text: '正文' }), frame('status', { text: '工具执行中' }));

    expect(lastAssistant()?.content).toBe('正文');
  });

  it('is_end=true 之后到达的帧被锁住，不再追加', async () => {
    const { feed, lastAssistant } = await setup();

    feed(frame('answer', { text: '前半' }), JSON.stringify({ content: {}, is_end: true }));
    feed(frame('answer', { text: '脏帧' }));

    expect(lastAssistant()?.content).toBe('前半');
  });

  it('function_call 的 start/end 推演，失败以 end + result=error 标为 error 而非 done', async () => {
    const { result, feed } = await setup();

    feed(
      frame('function_call', { name: 'search_subjects', state: 'start' }),
      frame('function_call', { name: 'search_subjects', state: 'end', result: 'ok', message: '3 条结果' }),
      frame('function_call', { name: 'fetch_detail', state: 'start' }),
      frame('function_call', { name: 'fetch_detail', state: 'end', result: 'error', message: '详情获取失败' }),
    );

    expect(result.current.tools).toEqual([
      { name: 'search_subjects', status: 'done', message: '3 条结果' },
      { name: 'fetch_detail', status: 'error', message: '详情获取失败' },
    ]);
  });

  it('status 的 state=error 携带用户可见文案，追加而不静默丢弃', async () => {
    const { feed, lastAssistant } = await setup();

    feed(
      frame('answer', { text: '回答' }),
      frame('status', { state: 'error', message: '回答保存失败，请稍后重试' }),
    );

    expect(lastAssistant()?.content).toBe('回答\n\n回答保存失败，请稍后重试');
  });

  it('status 的非 error 状态不写正文', async () => {
    const { feed, lastAssistant } = await setup();

    feed(frame('answer', { text: '正文' }), frame('status', { text: '工具执行中' }));

    expect(lastAssistant()?.content).toBe('正文');
  });
});

const uiAction = (meta: Record<string, unknown>) =>
  JSON.stringify({ type: 'ui_action', content: {}, meta });

describe('useAgentChat ui_action 事件', () => {
  it('不写正文、不进 tools，onUiAction 收到 action/params/path/label', async () => {
    const onUiAction = vi.fn();
    const { feed, result, lastAssistant } = await setup({ onUiAction });

    // 正向基线：同一用例里 answer 帧确实落正文，后面的否定断言才有意义
    feed(frame('answer', { text: '正文' }));
    expect(lastAssistant()?.content).toBe('正文');

    feed(uiAction({ action: 'open_anime_index', params: { year: 2022 }, path: '/anime?year=2022&page=1', label: '2022 年的番' }));

    expect(lastAssistant()?.content).toBe('正文');
    expect(result.current.tools).toEqual([]);
    expect(onUiAction).toHaveBeenCalledTimes(1);
    expect(onUiAction).toHaveBeenCalledWith({
      action: 'open_anime_index',
      params: { year: 2022 },
      path: '/anime?year=2022&page=1',
      label: '2022 年的番',
    });
  });

  it('action 缺失或非字符串时静默丢弃', async () => {
    const onUiAction = vi.fn();
    const { feed } = await setup({ onUiAction });

    // 正向基线：同一条通道喂一帧合法 action 必须被调用，否则「没被调用」可能只是通道没通
    feed(uiAction({ action: 'open_profile', path: '/profile' }));
    expect(onUiAction).toHaveBeenCalledTimes(1);
    onUiAction.mockClear();

    feed(uiAction({ path: '/anime' }), uiAction({ action: 42, path: '/anime' }));

    expect(onUiAction).not.toHaveBeenCalled();
  });

  it('params 缺省时补空对象，label 缺省不传假值', async () => {
    const onUiAction = vi.fn();
    const { feed } = await setup({ onUiAction });

    feed(uiAction({ action: 'open_profile', path: '/profile' }));

    expect(onUiAction).toHaveBeenCalledWith({ action: 'open_profile', params: {}, path: '/profile' });
  });
});

describe('useAgentChat 错误分类', () => {
  it('401 进入鉴权失败文案，而不是通用中断文案', async () => {
    const api = createApi();
    streamSseMock.mockImplementation(() => Promise.reject(new SseError('unauthorized', { status: 401 })));
    const { result } = renderHook(() => useAgentChat(api));
    await waitFor(() => expect(result.current.ready).toBe(true));

    await act(async () => { await result.current.send('你好'); });

    const assistant = result.current.messages.filter((m) => m.role === 'assistant').at(-1);
    expect(assistant?.content).toBe('(未认证或无权限，请重新登录)');
  });

  it('主动 abort 不写入任何中断文案', async () => {
    const api = createApi();
    streamSseMock.mockImplementation(() => Promise.reject(new SseAbortError()));
    const { result } = renderHook(() => useAgentChat(api));
    await waitFor(() => expect(result.current.ready).toBe(true));

    await act(async () => { await result.current.send('你好'); });

    const assistant = result.current.messages.filter((m) => m.role === 'assistant').at(-1);
    expect(assistant?.content).toBe('');
    expect(result.current.streaming).toBe(false);
  });

  it('其它故障仍保留通用重试提示', async () => {
    const api = createApi();
    streamSseMock.mockImplementation(() => Promise.reject(new SseError('boom')));
    const { result } = renderHook(() => useAgentChat(api));
    await waitFor(() => expect(result.current.ready).toBe(true));

    await act(async () => { await result.current.send('你好'); });

    const assistant = result.current.messages.filter((m) => m.role === 'assistant').at(-1);
    expect(assistant?.content).toBe('(流式中断，请重试)');
  });
});
