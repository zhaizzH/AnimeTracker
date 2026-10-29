import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { type AgentChatApi, useAgentChat } from './useAgentChat';
import { SseAbortError } from '../sse';

/** 真实 404 来自 axios，一定带 status；裸 Error 会被 hook 当成「状态未知」。 */
const notFound = () => Object.assign(new Error('404'), { status: 404 });

const streamSseMock = vi.hoisted(() => vi.fn());
vi.mock('../sse', async () => {
  const actual = await vi.importActual<typeof import('../sse')>('../sse');
  return { ...actual, streamSse: streamSseMock };
});

type OnEvent = (data: string) => void;

/** 历史里已有一条 user + 一条 assistant，模拟「刷新前已落库的部分回答」。 */
const HISTORY = [
  { role: 'user', content: '你好' },
  { role: 'assistant', content: '历史正文' },
];

const createApi = (runStatus?: { run_id: string; status: string }): AgentChatApi => ({
  listSessions: vi.fn().mockResolvedValue([{ session_id: 'session-1' }, { session_id: 'session-2' }]),
  createSession: vi.fn().mockResolvedValue({ session_id: 'session-1' }),
  history: vi.fn().mockResolvedValue(HISTORY),
  deleteSession: vi.fn().mockResolvedValue(undefined),
  streamBody: vi.fn().mockReturnValue({}),
  streamUrl: '/agent/stream',
  sessionRun: runStatus ? vi.fn().mockResolvedValue(runStatus) : vi.fn().mockRejectedValue(notFound()),
  stopRun: vi.fn().mockResolvedValue(undefined),
  runStreamUrl: (id: string, after: number) => `/agent/runs/${id}/stream?after=${after}`,
  health: vi.fn().mockResolvedValue('ok'),
});

const answer = (text: string) => JSON.stringify({ type: 'answer', content: { text } });
const end = () => JSON.stringify({ content: {}, is_end: true });

/** 挂载 hook，把 streamSse 每次订阅的 onEvent 收进数组，等回放订阅建立后返回。 */
async function setup(api: AgentChatApi) {
  const fed: OnEvent[] = [];
  const ends: (() => void)[] = [];
  streamSseMock.mockImplementation((opts: { onEvent: OnEvent }) => {
    fed.push(opts.onEvent);
    return new Promise<void>((resolve) => { ends.push(() => resolve()); });
  });
  const { result, unmount } = renderHook(() => useAgentChat(api));
  await waitFor(() => expect(result.current.ready).toBe(true));
  const feed = (data: string, index = 0) => act(() => { fed[index](data); });
  /** 让第 index 次订阅正常结束（无 is_end），模拟中间层掐断。 */
  const finish = (index = 0) => act(() => { ends[index](); });
  const assistants = () => result.current.messages.filter((m) => m.role === 'assistant');
  return { api, result, unmount, feed, finish, assistants, fed };
}

beforeEach(() => {
  streamSseMock.mockReset();
});

describe('useAgentChat 刷新/切会话回放', () => {
  it('status=running 时以 GET + after=0 订阅，新建气泡而不是复用历史气泡', async () => {
    const api = createApi({ run_id: 'run-1', status: 'running' });
    const { feed, assistants } = await setup(api);

    await waitFor(() => expect(streamSseMock).toHaveBeenCalledTimes(1));
    const opts = streamSseMock.mock.calls[0][0] as { url: string; method?: string; body?: unknown };
    expect(opts.url).toBe('/agent/runs/run-1/stream?after=0');
    expect(opts.method).toBe('GET');
    expect(opts.body).toBeUndefined();

    // 回放重推全量事件：新气泡从空开始累加，历史气泡不被改写，正文不拼两遍
    feed(answer('历史正文'));
    feed(answer('继续生成'));

    const list = assistants();
    expect(list).toHaveLength(2);
    expect(list[0].content).toBe('历史正文');
    expect(list[1].content).toBe('历史正文继续生成');
  });

  it('游标是已收到的事件帧数：长文本帧与短文本帧都只推进 1', async () => {
    const api = createApi({ run_id: 'run-1', status: 'running' });
    const { feed, finish } = await setup(api);

    await waitFor(() => expect(streamSseMock).toHaveBeenCalledTimes(1));
    feed(answer('很长'.repeat(500)));
    // 流没收到 is_end 就结束（中间层掐断）→ 用帧数 1 续订，而不是字符数 1000+
    finish(0);
    await waitFor(() => expect(streamSseMock).toHaveBeenCalledTimes(2));
    expect((streamSseMock.mock.calls[1][0] as { url: string }).url).toBe('/agent/runs/run-1/stream?after=1');

    // 第二次订阅也在没有 is_end 的情况下结束 → 续订上限生效，不会第三次订阅
    finish(1);
    await act(async () => { await Promise.resolve(); });
    expect(streamSseMock).toHaveBeenCalledTimes(2);
  });

  it('两帧增量后游标为 2：短帧与长帧各只推进 1', async () => {
    const api = createApi({ run_id: 'run-1', status: 'running' });
    const { feed, finish } = await setup(api);
    await waitFor(() => expect(streamSseMock).toHaveBeenCalledTimes(1));

    feed(answer('a'.repeat(1000)));
    feed(answer('b'));
    finish(0);
    await waitFor(() => expect(streamSseMock).toHaveBeenCalledTimes(2));
    expect((streamSseMock.mock.calls[1][0] as { url: string }).url).toBe('/agent/runs/run-1/stream?after=2');
  });

  it('回放与实时共用同一把 is_end 锁：结束后到达的帧不再累积', async () => {
    const api = createApi({ run_id: 'run-1', status: 'running' });
    const { feed, assistants } = await setup(api);

    await waitFor(() => expect(streamSseMock).toHaveBeenCalledTimes(1));
    feed(answer('前半'));
    feed(end());
    feed(answer('脏帧'));

    expect(assistants().at(-1)?.content).toBe('前半');
  });

  it('回放收到 status/warning 时提示实时内容已过期', async () => {
    const api = createApi({ run_id: 'run-1', status: 'running' });
    const { feed, result } = await setup(api);

    await waitFor(() => expect(streamSseMock).toHaveBeenCalledTimes(1));
    feed(JSON.stringify({ type: 'status', content: { state: 'warning', message: '缓冲已截断-独特标记' } }));

    // 一次性提示走 notice（两端转 toast），不再写进会话历史
    expect(result.current.notice?.text).toContain('缓冲已截断-独特标记');
    expect(result.current.messages.some((m) => m.content.includes('缓冲已截断-独特标记'))).toBe(false);
    // 截断后 after 无法再与后端 buffer_start 对齐：不再续订，避免重放已收帧
    expect(streamSseMock).toHaveBeenCalledTimes(1);
  });

  it('status=failed 不订阅，读历史并提示上次回答未完成', async () => {
    const api = createApi({ run_id: 'run-1', status: 'failed' });
    const { result } = await setup(api);

    await waitFor(() => expect(result.current.runFailed).toBe(true));
    expect(streamSseMock).not.toHaveBeenCalled();
    // 会话级状态，不掺进消息列表：历史仍只有那两条
    expect(result.current.messages).toHaveLength(2);
  });

  it('切到没有 run 的会话后收掉「上次回答未完成」横幅', async () => {
    const api = createApi({ run_id: 'run-1', status: 'failed' });
    vi.mocked(api.sessionRun).mockImplementation((id: string) =>
      id === 'session-1' ? Promise.resolve({ run_id: 'run-1', status: 'failed' }) : Promise.reject(notFound()));
    const { result } = await setup(api);
    await waitFor(() => expect(result.current.runFailed).toBe(true));

    await act(async () => { await result.current.select('session-2'); });

    expect(result.current.runFailed).toBe(false);
  });

  it('发新消息时收起横幅：上一条 failed run 不再是最近一条', async () => {
    const api = createApi({ run_id: 'run-1', status: 'failed' });
    const { result, fed } = await setup(api);
    await waitFor(() => expect(result.current.runFailed).toBe(true));

    act(() => { void result.current.send('新问题'); });
    await waitFor(() => expect(fed.length).toBe(1));

    expect(result.current.runFailed).toBe(false);
  });

  it.each(['done', 'cancelled'])('status=%s 不订阅也不提示', async (status) => {
    const api = createApi({ run_id: 'run-1', status });
    const { result } = await setup(api);

    await waitFor(() => expect(result.current.ready).toBe(true));
    expect(api.sessionRun).toHaveBeenCalledWith('session-1');
    expect(streamSseMock).not.toHaveBeenCalled();
    expect(result.current.messages).toHaveLength(2);
  });

  it('切会话取消在途回放，旧 run 的帧不写进新会话', async () => {
    const api = createApi({ run_id: 'run-1', status: 'running' });
    // session-2 没有 run：切过去只读历史，不起新订阅
    vi.mocked(api.sessionRun).mockImplementation((id: string) =>
      id === 'session-1' ? Promise.resolve({ run_id: 'run-1', status: 'running' }) : Promise.reject(notFound()));
    const { result, fed } = await setup(api);
    await waitFor(() => expect(streamSseMock).toHaveBeenCalledTimes(1));
    const signal = (streamSseMock.mock.calls[0][0] as { signal?: AbortSignal }).signal!;

    await act(async () => { await result.current.select('session-2'); });

    expect(signal.aborted).toBe(true);
    // 旧订阅的帧即便迟到也不再落进新会话
    act(() => { fed[0](answer('旧 run 的脏帧')); });
    expect(result.current.messages.map((m) => m.content)).toEqual(['你好', '历史正文']);
    expect(result.current.streaming).toBe(false);
  });

  it('回放中途主动停止会先 stopRun 再 abort', async () => {
    const api = createApi({ run_id: 'run-1', status: 'running' });
    const { result } = await setup(api);
    await waitFor(() => expect(streamSseMock).toHaveBeenCalledTimes(1));
    const signal = (streamSseMock.mock.calls[0][0] as { signal?: AbortSignal }).signal!;

    await act(async () => { await result.current.stop(); });

    expect(api.stopRun).toHaveBeenCalledWith('run-1');
    expect(signal.aborted).toBe(true);
  });

  it('回放中主动停止保留已生成正文，只收掉空气泡', async () => {
    const api = createApi({ run_id: 'run-1', status: 'running' });
    const fed: OnEvent[] = [];
    // abort 时真的以 SseAbortError 拒绝，否则走不到「收气泡」那段代码，断言会恒绿。
    streamSseMock.mockImplementation((opts: { onEvent: OnEvent; signal?: AbortSignal }) => {
      fed.push(opts.onEvent);
      return new Promise<void>((_, reject) => {
        opts.signal?.addEventListener('abort', () => reject(new SseAbortError()));
      });
    });
    const { result } = renderHook(() => useAgentChat(api));
    await waitFor(() => expect(result.current.ready).toBe(true));
    await waitFor(() => expect(fed.length).toBe(1));

    act(() => { fed[0](answer('已经生成的半截答案')); });
    await act(async () => { await result.current.stop(); });

    const list = result.current.messages.filter((m) => m.role === 'assistant');
    expect(list).toHaveLength(2);
    expect(list[1].content).toBe('已经生成的半截答案');
  });

  it('旧 send 的 finally 不会清掉回放刚接管的 streaming 与 run_id', async () => {
    const api = createApi({ run_id: 'run-1', status: 'running' });
    // session-1 无 run（纯历史），session-2 有 running run → 切过去由回放接管
    vi.mocked(api.sessionRun).mockImplementation((id: string) =>
      id === 'session-2' ? Promise.resolve({ run_id: 'run-1', status: 'running' }) : Promise.reject(notFound()));
    const fed: OnEvent[] = [];
    const ends: (() => void)[] = [];
    streamSseMock.mockImplementation((opts: { onEvent: OnEvent }) => {
      fed.push(opts.onEvent);
      return new Promise<void>((resolve) => { ends.push(() => resolve()); });
    });
    const { result } = renderHook(() => useAgentChat(api));
    await waitFor(() => expect(result.current.ready).toBe(true));

    // 起一条实时流（不会自己结束），随后切到有 running run 的会话
    act(() => { void result.current.send('问题'); });
    await waitFor(() => expect(fed.length).toBe(1));
    await act(async () => { await result.current.select('session-2'); });
    await waitFor(() => expect(fed.length).toBe(2));
    // 旧实时流这时才收尾（abort 触发的 finally）——不得把回放状态清掉
    await act(async () => { ends[0](); await Promise.resolve(); });

    expect(result.current.streaming).toBe(true);
    await act(async () => { await result.current.stop(); });
    expect(api.stopRun).toHaveBeenCalledWith('run-1');
  });

  it('回放被 abort 时不写中断文案、不留空气泡', async () => {
    const api = createApi({ run_id: 'run-1', status: 'running' });
    streamSseMock.mockImplementation(() => Promise.reject(new SseAbortError()));
    const { result } = renderHook(() => useAgentChat(api));
    await waitFor(() => expect(result.current.ready).toBe(true));

    await waitFor(() => expect(result.current.streaming).toBe(false));
    expect(result.current.messages.map((m) => m.content)).toEqual(['你好', '历史正文']);
  });
});
