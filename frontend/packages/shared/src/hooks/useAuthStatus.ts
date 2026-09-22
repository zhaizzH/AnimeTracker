import { useAuthStore, type AuthStatus } from '../store/auth';
import { retryBootstrapAuth } from '../auth/coordinator';

export type { AuthStatus };

/**
 * 无 UI 依赖的登录态读取：各 app 用同一份状态自行渲染外壳。
 * 逻辑与 AuthGate 原实现一致（含 retryable-error 分支的重试）。
 */
export function useAuthStatus(): { status: AuthStatus; retry: () => void } {
  const status = useAuthStore((state) => state.status);
  return { status, retry: () => void retryBootstrapAuth() };
}
