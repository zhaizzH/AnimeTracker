import { afterEach, expect, it, vi } from 'vitest';
import { createPublicApi } from './public-client';

afterEach(() => vi.unstubAllGlobals());

it('returns unwrapped backend data', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
    code: 200, message: 'success', data: { content: [], total: 0, page: 1, size: 20 },
  }), { status: 200, headers: { 'content-type': 'application/json' } })));
  const api = createPublicApi('http://business:8080');
  await expect(api.listSubjects({ page: 1, size: 20 })).resolves.toMatchObject({ total: 0 });
});

it('preserves the backend message and request id', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
    code: 400, message: '季度参数无效', data: null,
  }), { status: 400, headers: { 'x-request-id': 'req-42' } })));
  const api = createPublicApi('http://business:8080');
  await expect(api.listSubjects({ page: 1, size: 20 })).rejects.toMatchObject({
    status: 400, message: '季度参数无效', requestId: 'req-42',
  });
});

it('replaces unsafe stack-trace messages with the fallback text', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
    code: 500, message: 'java.lang.NullPointerException', data: null,
  }), { status: 500, headers: { 'x-request-id': 'req-7' } })));
  const api = createPublicApi('http://business:8080');
  await expect(api.listSubjects({ page: 1, size: 20 })).rejects.toMatchObject({
    status: 500, message: '服务暂时不可用，请稍后重试', requestId: 'req-7',
  });
});
