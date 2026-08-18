import { beforeEach, expect, test } from 'vitest';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { http, get, post } from './http';
import { useAuthStore } from '../store/auth';
import type { LoginVO } from '../types';

// http 是独立 axios 实例：主请求 mock 在 http 上；refreshOnce 用裸 axios，故 refresh 单独 mock 在 axios 上。
const mock = new MockAdapter(http);
const mockRefresh = new MockAdapter(axios, { onNoMatch: 'passthrough' });
beforeEach(() => { mock.reset(); mockRefresh.reset(); useAuthStore.getState().logout(); });

test('成功响应返回 data 字段', async () => {
  mock.onGet('/api/client/tags').reply(200, { code: 0, message: 'ok', data: [{ id: 1, name: '科幻', count: 3 }] });
  const data = await get<Array<{ id: number; name: string; count: number }>>('/client/tags');
  expect(data[0].name).toBe('科幻');
});
test('code!=0 时 reject 后端 message', async () => {
  mock.onPost('/api/client/auth/login').reply(200, { code: 4001, message: '账号或密码错误', data: null });
  await expect(post('/client/auth/login', {})).rejects.toThrow('账号或密码错误');
});
test('401 时用 refreshToken 刷新并重试原请求', async () => {
  const login: LoginVO = { token: 'stale', refreshToken: 'rt', user: { id: 1, username: 'u', email: 'e@x.com', role: 'ADMIN', createdAt: '' } };
  useAuthStore.getState().setLogin(login);
  mock.onGet('/api/client/me').replyOnce(401).onGet('/api/client/me').reply(200, { code: 0, message: 'ok', data: login.user });
  mockRefresh.onPost('/api/client/auth/refresh').reply(200, { code: 0, message: 'ok', data: { ...login, token: 'fresh' } });
  const user = await get<{ username: string }>('/client/me');
  expect(user.username).toBe('u');
  expect(useAuthStore.getState().token).toBe('fresh');
});
