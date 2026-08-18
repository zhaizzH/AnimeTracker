import { beforeEach, expect, test } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import * as authApi from './auth';
import * as subjectsApi from './subjects';
import * as collectionsApi from './collections';
import { run } from './admin/import';
import { list as logsList } from './admin/logs';
import { http } from './http';

// 各 API 模块走共享 http 实例（baseURL=/api），mock 须挂在该实例上。
const mock = new MockAdapter(http);
beforeEach(() => mock.reset());

test('auth.login 发送 username+password', async () => {
  mock.onPost('/api/client/auth/login').reply((cfg) => {
    const body = JSON.parse(cfg.data);
    expect(body).toEqual({ username: 'u', password: 'p' });
    return [200, { code: 0, message: 'ok', data: null }];
  });
  await authApi.login({ username: 'u', password: 'p' });
});
test('collections.save 带 path id 与 body', async () => {
  mock.onPost('/api/client/collections/42/save').reply((cfg) => {
    expect(JSON.parse(cfg.data)).toEqual({ type: 2, rate: 8 });
    return [200, { code: 0, message: 'ok', data: null }];
  });
  await collectionsApi.save(42, { type: 2, rate: 8 });
});
test('search 数组参数无 [] 后缀（tag=a&tag=b）', async () => {
  mock.onGet('/api/client/subjects/search').reply((cfg) => {
    expect(cfg.params.tag).toEqual(['a', 'b']);
    expect(cfg.params.page).toBe(1);
    return [200, { code: 0, message: 'ok', data: null }];
  });
  await subjectsApi.search({ q: '', tag: ['a', 'b'], page: 1, size: 20 });
});
test('import.run 拼装查询参数', async () => {
  mock.onPost('/api/admin/import/run?mode=season&key=2026-summer').reply((cfg) => {
    expect(cfg.url).toContain('mode=season');
    expect(cfg.url).toContain('key=2026-summer');
    return [200, { code: 0, message: 'ok', data: null }];
  });
  await run({ mode: 'season', key: '2026-summer' });
});
test('logs.list 透传筛选字段', async () => {
  mock.onGet('/api/admin/logs').reply((cfg) => {
    expect(cfg.params).toMatchObject({ action: 'LOGIN', page: 1, size: 20 });
    return [200, { code: 0, message: 'ok', data: null }];
  });
  await logsList({ action: 'LOGIN', page: 1, size: 20 });
});
