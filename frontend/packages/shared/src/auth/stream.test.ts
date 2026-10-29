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
    mockedStream.mockRejectedValueOnce(unauthorized());
    mockedRefresh.mockResolvedValue(false);

    await expect(streamSseWithAuth(base)).rejects.toBeInstanceOf(SseError);
    expect(mockedStream).toHaveBeenCalledTimes(1);
    expect(mockedRefresh).toHaveBeenCalledTimes(1);
  });

  it('重放后仍是 401 就停止：最多一条流刷新一次', async () => {
    mockedStream.mockRejectedValue(unauthorized());
    mockedRefresh.mockResolvedValue(true);

    await expect(streamSseWithAuth(base)).rejects.toMatchObject({ status: 401 });
    expect(mockedStream).toHaveBeenCalledTimes(2);
    expect(mockedRefresh).toHaveBeenCalledTimes(1);
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
});
