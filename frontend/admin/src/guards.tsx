import { Navigate, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';
import { message } from 'antd';
import { useAuthStore } from '@shared';

const returnTo = (location: ReturnType<typeof useLocation>) => location.pathname + location.search + location.hash;

export function RequireAdmin({ children }: { children: ReactNode }) {
  const status = useAuthStore((state) => state.status);
  const role = useAuthStore((state) => state.user?.role);
  const location = useLocation();
  if (status === 'unauthenticated') return <Navigate to="/admin/login" replace state={{ from: returnTo(location) }} />;
  if (status === 'authenticated' && role !== 'ADMIN') {
    message.error('无管理权限');
    return <Navigate to="/admin/login" replace state={{ from: returnTo(location) }} />;
  }
  return <>{children}</>;
}