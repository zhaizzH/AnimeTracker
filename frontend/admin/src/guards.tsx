import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { message } from 'antd';
import { useAuthStore } from '@shared';

export function RequireAdmin({ children }: { children: ReactNode }) {
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn);
  const role = useAuthStore((s) => s.user?.role);
  if (!isLoggedIn) return <Navigate to="/admin/login" replace />;
  if (role !== 'ADMIN') { message.error('无管理权限'); useAuthStore.getState().logout(); return <Navigate to="/admin/login" replace />; }
  return <>{children}</>;
}
