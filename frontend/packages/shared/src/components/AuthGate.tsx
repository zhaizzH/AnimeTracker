import type { ReactNode } from 'react';
import { useAuthStore } from '../store/auth';
import { retryBootstrapAuth } from '../auth/coordinator';

export function AuthGate({ children }: { children: ReactNode }) {
  const status = useAuthStore((state) => state.status);
  if (status === 'checking') return <div role="status">正在恢复登录状态…</div>;
  if (status === 'retryable-error') {
    return <div role="alert"><p>暂时无法确认登录状态</p><button type="button" onClick={() => void retryBootstrapAuth()}>重试</button></div>;
  }
  return <>{children}</>;
}