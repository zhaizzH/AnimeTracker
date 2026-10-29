import { beforeEach, describe, expect, it, vi } from 'vitest';
import { streamSse, SseError } from '../sse';
import { refreshWithLock } from './coordinator';
import { useAuthStore } from '../store/auth';
import { streamSseWithAuth } from './stream';

vi.mock('../sse', async () => {
  const actual = await vi.importActual<typeof import('../sse')>('../sse');
  return { ...actual, streamSse: vi.fn() };
});
vi.mock('./coordinator', () => ({ refreshWithLock: vi.fn() }));

const mockedStream = vi.mocked(streamSse);
const mockedRefresh = vi.mocked(refreshWithLock);

const unauthorized = () => new SseError('401', { status: 401 });
const base = { url: '/agent/stream', body: {}, token: 'old-token', onEvent: vi.fn() };

beforeEach(() => {
  mockedStream.mockReset();
  mockedRefresh.mockReset();
  useAuthStore.getState().setUnauthenticated();
});

describe('streamSseWithAuth', () => {
  it('401 时刷新一次并用新令牌重放，且只重放一次', async () => {
    mockedStream.mockRejectedValueOnce(unauthorized()).mockResolvedValueOnce(undefined);
    mockedRefresh.mockImplementation(async () => {
      // 真实刷新会写回 store；这里模拟后端换发的新令牌
      useAuthStore.getState().setAuthenticated({ token: 'new-token' } as never);
      return true;
    });

    await streamSseWithAuth(base);

    expect(mockedRefresh).toHaveBeenCalledTimes(1);
    expect(mockedStream).toHaveBeenCalledTimes(2);
    expect(mockedStream.mock.calls[1][0].token).toBe('new-token');
  });

  it('刷新失败时把原 401 抛出，不重放，也不再刷新', async () => {
    // beforeEach 把 store 复位成未认证，这里先置回已登录，才能验证「刷新失败不会额外踢人」
    useAuthStore.getState().setAuthenticated({ token: 'old-token' } as never);
    mockedStream.mockRejectedValueOnce(unauthorized());
    mockedRefresh.mockResolvedValue(false);

    await expect(streamSseWithAuth(base)).rejects.toBeInstanceOf(SseError);
    expect(mockedStream).toHaveBeenCalledTimes(1);
    expect(mockedRefresh).toHaveBeenCalledTimes(1);
    // 刷新失败常见原因是网络抖动：不能因此把用户踢到登录页
    expect(useAuthStore.getState().status).toBe('authenticated');
  });

  it('403 不触发刷新（刷新救不了权限）', async () => {
    mockedStream.mockRejectedValueOnce(new SseError('403', { status: 403 }));

    await expect(streamSseWithAuth(base)).rejects.toMatchObject({ status: 403 });
    expect(mockedRefresh).not.toHaveBeenCalled();
    expect(mockedStream).toHaveBeenCalledTimes(1);
  });

  it('非鉴权故障原样抛出，不刷新', async () => {
    mockedStream.mockRejectedValueOnce(new SseError('502', { status: 502 }));

    await expect(streamSseWithAuth(base)).rejects.toMatchObject({ status: 502 });
    expect(mockedRefresh).not.toHaveBeenCalled();
  });

  it('刷新成功但重放仍 401：置为未认证让 guard 跳登录页，而不是停在带着死令牌的 authenticated', async () => {
    mockedStream.mockRejectedValue(unauthorized());
    mockedRefresh.mockResolvedValue(true);
    useAuthStore.getState().setAuthenticated({ token: 'new-token' } as never);

    await expect(streamSseWithAuth(base)).rejects.toMatchObject({ status: 401 });

    // 最多重放一次：刷新一次、两条流，不递归
    expect(mockedRefresh).toHaveBeenCalledTimes(1);
    expect(mockedStream).toHaveBeenCalledTimes(2);
    expect(useAuthStore.getState().status).toBe('unauthenticated');
    expect(useAuthStore.getState().token).toBeNull();
  });

  it('刷新救回来的那次 401 不会把状态置成未认证', async () => {
    mockedStream.mockRejectedValueOnce(unauthorized()).mockResolvedValueOnce(undefined);
    mockedRefresh.mockImplementation(async () => {
      useAuthStore.getState().setAuthenticated({ token: 'new-token' } as never);
      return true;
    });

    await streamSseWithAuth(base);

    expect(useAuthStore.getState().status).toBe('authenticated');
  });

  it('刷新成功后重放遇到 502 不置未认证：不是鉴权问题就别把人踢走', async () => {
    mockedStream.mockRejectedValueOnce(unauthorized()).mockRejectedValueOnce(new SseError('502', { status: 502 }));
    mockedRefresh.mockResolvedValue(true);
    useAuthStore.getState().setAuthenticated({ token: 'new-token' } as never);

    await expect(streamSseWithAuth(base)).rejects.toMatchObject({ status: 502 });

    expect(useAuthStore.getState().status).toBe('authenticated');
  });
});
