import { beforeEach, describe, expect, it, vi } from 'vitest';
import { get, post } from './http';
import { runStreamUrl, sessionRun, stopRun } from './agent';
import { chatRunStreamUrl, chatSessionRun, chatStopRun } from './admin/agent';

vi.mock('./http', () => ({ get: vi.fn(), post: vi.fn() }));

const mockedGet = vi.mocked(get);
const mockedPost = vi.mocked(post);

describe('run api 路径', () => {
  beforeEach(() => {
    mockedGet.mockReset();
    mockedPost.mockReset();
    mockedGet.mockResolvedValue({ run_id: 'r1', status: 'running' } as never);
    mockedPost.mockResolvedValue(undefined as never);
  });

  it('client sessionRun 走 GET，且 session id 被编码', async () => {
    await sessionRun('s/1');

    expect(mockedGet).toHaveBeenCalledWith('/client/agent/sessions/s%2F1/run');
  });

  it('client stopRun 走 POST，run id 被编码', async () => {
    await stopRun('r/1');

    expect(mockedPost).toHaveBeenCalledWith('/client/agent/runs/r%2F1/stop');
  });

  it('client runStreamUrl 带 after 查询参数', () => {
    expect(runStreamUrl('r1', 0)).toBe('/api/client/agent/runs/r1/stream?after=0');
    expect(runStreamUrl('r1', 7)).toBe('/api/client/agent/runs/r1/stream?after=7');
    expect(runStreamUrl('r/1', 0)).toBe('/api/client/agent/runs/r%2F1/stream?after=0');
  });

  it('admin 三方法走 /admin/agent/chat 前缀', async () => {
    await chatSessionRun('s1');
    await chatStopRun('r1');

    expect(mockedGet).toHaveBeenCalledWith('/admin/agent/chat/sessions/s1/run');
    expect(mockedPost).toHaveBeenCalledWith('/admin/agent/chat/runs/r1/stop');
    expect(chatRunStreamUrl('r1', 3)).toBe('/api/admin/agent/chat/runs/r1/stream?after=3');
  });
});
