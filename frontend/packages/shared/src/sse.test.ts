import { afterEach, describe, expect, it, vi } from 'vitest';
import { SseAbortError, SseError, streamSse } from './sse';

const encoder = new TextEncoder();

/** 按给定分片顺序产出一条可控的 SSE 流响应。 */
function sseResponse(chunks: string[], init: { status?: number; contentType?: string | null } = {}) {
  const { status = 200, contentType = 'text/event-stream; charset=utf-8' } = init;
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
      controller.close();
    },
  });
  const headers = new Headers();
  if (contentType !== null) headers.set('Content-Type', contentType);
  return new Response(status === 204 ? null : stream, { status, headers });
}

const callSse = (res: Response | (() => Promise<Response>), signal?: AbortSignal) => {
  const onEvent = vi.fn();
  vi.stubGlobal('fetch', vi.fn(() => (typeof res === 'function' ? res() : Promise.resolve(res))));
  return { onEvent, promise: streamSse({ url: '/agent/stream', body: {}, token: 't', signal, onEvent }) };
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('streamSse 帧解析', () => {
  it('按空行分帧并逐帧回调 data 载荷', async () => {
    const { onEvent, promise } = callSse(sseResponse(['data: {"a":1}\n\ndata: {"b":2}\n\n']));
    await promise;

    expect(onEvent.mock.calls.map((c) => c[0])).toEqual(['{"a":1}', '{"b":2}']);
  });

  it('一帧被拆到多个 chunk 到达时仍只回调一次', async () => {
    const { onEvent, promise } = callSse(sseResponse(['data: {"a"', ':1}\n', '\ndata: {"b":2}\n\n']));
    await promise;

    expect(onEvent.mock.calls.map((c) => c[0])).toEqual(['{"a":1}', '{"b":2}']);
  });

  it('尾帧缺少结尾空行时也会被 flush', async () => {
    const { onEvent, promise } = callSse(sseResponse(['data: {"a":1}\n\ndata: {"b":2}']));
    await promise;

    expect(onEvent.mock.calls.map((c) => c[0])).toEqual(['{"a":1}', '{"b":2}']);
  });

  it('兼容 CRLF 分帧', async () => {
    const { onEvent, promise } = callSse(sseResponse(['data: {"a":1}\r\n\r\ndata: {"b":2}\r\n\r\n']));
    await promise;

    expect(onEvent.mock.calls.map((c) => c[0])).toEqual(['{"a":1}', '{"b":2}']);
  });
});

describe('streamSse 错误分类', () => {
  it('Content-Type 不是 event-stream 时抛 SseError 且不回调', async () => {
    const { onEvent, promise } = callSse(
      sseResponse(['<html>gateway error</html>'], { contentType: 'text/html' }),
    );

    await expect(promise).rejects.toBeInstanceOf(SseError);
    await expect(promise).rejects.toMatchObject({ contentType: 'text/html' });
    expect(onEvent).not.toHaveBeenCalled();
  });

  it('非 2xx 抛带 status 的 SseError', async () => {
    const { onEvent, promise } = callSse(
      () => Promise.resolve(new Response('{"code":50001}', { status: 500, headers: { 'Content-Type': 'application/json' } })),
    );

    await expect(promise).rejects.toMatchObject({ status: 500 });
    expect(onEvent).not.toHaveBeenCalled();
  });

  it('401 透出 status 供调用方区分鉴权失败', async () => {
    const { promise } = callSse(
      () => Promise.resolve(new Response('{"code":40101}', { status: 401, headers: { 'Content-Type': 'application/json' } })),
    );

    await expect(promise).rejects.toMatchObject({ status: 401 });
  });

  it('主动 abort 抛 SseAbortError 而非 SseError', async () => {
    const controller = new AbortController();
    const { promise } = callSse(() => {
      controller.abort();
      return Promise.reject(new DOMException('Aborted', 'AbortError'));
    }, controller.signal);

    await expect(promise).rejects.toBeInstanceOf(SseAbortError);
  });

  it('网络故障包装为 SseError', async () => {
    const { promise } = callSse(() => Promise.reject(new TypeError('Failed to fetch')));

    await expect(promise).rejects.toBeInstanceOf(SseError);
  });
});
