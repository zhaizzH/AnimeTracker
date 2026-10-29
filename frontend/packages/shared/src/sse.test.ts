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

describe('streamSse 请求方法', () => {
  const captured = () => (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0] as [string, RequestInit];

  it('默认走 POST：JSON body + JSON Content-Type', async () => {
    const { promise } = callSse(sseResponse(['data: {}\n\n']));
    await promise;

    const [, init] = captured();
    expect(init.method).toBe('POST');
    expect(init.body).toBe('{}');
    expect((init.headers as Record<string, string>)['Content-Type']).toBe('application/json');
  });

  it('GET 不带 body、不带 JSON Content-Type，query 由调用方拼进 url', async () => {
    const onEvent = vi.fn();
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(sseResponse(['data: {}\n\n']))));
    await streamSse({ url: '/agent/runs/r1/stream?after=0', method: 'GET', token: 't', onEvent });

    const [url, init] = captured();
    expect(url).toBe('/agent/runs/r1/stream?after=0');
    expect(init.method).toBe('GET');
    expect(init.body).toBeUndefined();
    expect((init.headers as Record<string, string>)['Content-Type']).toBeUndefined();
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer t');
  });

  it('GET 重连中被主动 abort 同样抛 SseAbortError', async () => {
    const controller = new AbortController();
    const onEvent = vi.fn();
    vi.stubGlobal(
      'fetch',
      vi.fn(() => {
        controller.abort();
        return Promise.reject(new DOMException('Aborted', 'AbortError'));
      }),
    );

    await expect(
      streamSse({ url: '/agent/runs/r1/stream?after=0', method: 'GET', token: 't', signal: controller.signal, onEvent }),
    ).rejects.toBeInstanceOf(SseAbortError);
  });
});

describe('SseError 携带解析后的 body', () => {
  it('409 的 JSON 体能被读出来，message 只保留截断后的原文', async () => {
    const payload = { detail: { active_run_id: 'abc', status: 'running', message: 'x'.repeat(400) } };
    const { promise } = callSse(
      () =>
        Promise.resolve(
          new Response(JSON.stringify(payload), {
            status: 409,
            headers: { 'Content-Type': 'application/json' },
          }),
        ),
    );

    const err = (await promise.catch((e: unknown) => e)) as SseError;
    expect(err.status).toBe(409);
    expect(err.body).toEqual(payload);
    // message 里的原文按 200 字截断：结构化字段只能从 body 读，不能指望 message 里有完整载荷。
    expect(err.message.length).toBeLessThan(JSON.stringify(payload).length);
  });

  it('非 JSON 错误体时 body 为 undefined，message 仍带截断后的原文便于定位', async () => {
    const raw = '<html>boom</html>';
    const { promise } = callSse(
      () => Promise.resolve(new Response(raw, { status: 502, headers: { 'Content-Type': 'text/html' } })),
    );

    const err = (await promise.catch((e: unknown) => e)) as SseError;
    expect(err.status).toBe(502);
    expect(err.body).toBeUndefined();
    expect(err.message).toContain(raw);
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
