import { expect, test, vi } from 'vitest';
import { streamSse } from './sse';

test('逐行解析 data: 前缀并回调', async () => {
  const chunks: string[] = [];
  const enc = new TextEncoder();
  const body = new ReadableStream({ start(c) { c.enqueue(enc.encode('data: 你好\n\ndata: [DONE]\n')); c.close(); } });
  vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, body })));
  await streamSse({ url: '/x', body: {}, token: null, onEvent: (d) => chunks.push(d) });
  expect(chunks).toEqual(['你好', '[DONE]']);
  vi.unstubAllGlobals();
});
