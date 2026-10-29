import { refreshWithLock } from './coordinator';
import { useAuthStore } from '../store/auth';
import { SseError, streamSse, type StreamOptions } from '../sse';

/**
 * 给 SSE 通道补上 Axios 那套「刷新一次 → 重放」闭环。
 *
 * 只对 401 生效：403 刷新救不了；网络/协议故障也重试无益，交给调用方分类。
 * 最多重放一次，禁止无限重试。
 *
 * 重放安全的前提（后端契约）：鉴权依赖在创建 run 之前抛 401，所以被杀掉的
 * `POST /stream` 没有产生 run，重放不会凭空多开一条。
 */
export async function streamSseWithAuth(options: StreamOptions): Promise<void> {
  try {
    return await streamSse(options);
  } catch (err) {
    if (!(err instanceof SseError) || err.status !== 401) throw err;
    const refreshed = await refreshWithLock();
    if (!refreshed) throw err;
    // 重放必须用刷新后的令牌：原 token 已过期，照抄会再得一次 401。
    return streamSse({ ...options, token: useAuthStore.getState().token });
  }
}
