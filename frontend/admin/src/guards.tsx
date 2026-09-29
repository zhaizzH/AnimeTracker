import { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';
import { toastError } from '@/lib/toast';
import { useAuthStore } from '@shared';

const returnTo = (location: ReturnType<typeof useLocation>) => location.pathname + location.search + location.hash;

export function RequireAdmin({ children }: { children: ReactNode }) {
  const status = useAuthStore((state) => state.status);
  const role = useAuthStore((state) => state.user?.role);
  const location = useLocation();
  const denied = status === 'authenticated' && role !== 'ADMIN';

  // 副作用必须离开 render 阶段：render 中调用通知会在并发渲染下重复触发。
  useEffect(() => {
    if (denied) toastError('无管理权限');
  }, [denied]);

  if (status === 'unauthenticated' || denied) return <Navigate to="/admin/login" replace state={{ from: returnTo(location) }} />;
  return <>{children}</>;
}
