import { beforeEach, describe, expect, it, vi } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import { http } from './http';
import { useAuthStore } from '../store/auth';

vi.mock('../auth/coordinator', () => ({ refreshWithLock: vi.fn(async () => false) }));

const { refreshWithLock } = await import('../auth/coordinator');
const mock = new MockAdapter(http);

describe('http 错误透出', () => {
  beforeEach(() => {
    mock.reset();
    vi.mocked(refreshWithLock).mockClear();
    useAuthStore.getState().setUnauthenticated();
  });

  it('把后端 Result.message 透出，而不是 axios 的状态码文案', async () => {
    mock.onPost('/client/auth/login').reply(401, { code: 401, message: '用户名或密码错误' });

    await expect(http.post('/client/auth/login', {})).rejects.toThrow('用户名或密码错误');
  });

  it('登录 401 不触发刷新重试', async () => {
    mock.onPost('/client/auth/login').reply(401, { code: 401, message: '用户名或密码错误' });

    await expect(http.post('/client/auth/login', {})).rejects.toThrow();
    expect(refreshWithLock).not.toHaveBeenCalled();
  });

  it('普通接口 401 先刷新再重放', async () => {
    vi.mocked(refreshWithLock).mockResolvedValueOnce(true);
    mock.onGet('/client/me').replyOnce(401, { code: 401, message: '未认证' });
    mock.onGet('/client/me').replyOnce(200, { code: 200, message: 'success', data: { id: 1 } });

    await expect(http.get('/client/me')).resolves.toEqual({ id: 1 });
    expect(refreshWithLock).toHaveBeenCalledTimes(1);
  });

  it('刷新失败时仍抛出原始错误文案', async () => {
    mock.onGet('/client/me').reply(401, { code: 401, message: '未认证' });

    await expect(http.get('/client/me')).rejects.toThrow('未认证');
  });

  it('错误对象携带 status 与结构化 data，供 409 冲突分支读取', async () => {
    mock.onPost('/client/agent/stream').reply(409, {
      code: 409,
      message: '当前会话已有进行中的对话',
      data: { active_run_id: 'abc', status: 'running', capabilities: ['interrupt'] },
    });

    const err = (await http.post('/client/agent/stream', {}).catch((e: unknown) => e)) as {
      message: string;
      status?: number;
      data?: unknown;
    };
    expect(err.status).toBe(409);
    expect(err.data).toEqual({ active_run_id: 'abc', status: 'running', capabilities: ['interrupt'] });
  });
});
