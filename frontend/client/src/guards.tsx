import { Navigate, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuthStore } from '@shared';

export function RequireAuth({ children }: { children: ReactNode }) {
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn);
  const location = useLocation();
  if (!isLoggedIn) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <>{children}</>;
}
export function PublicOnly({ children }: { children: ReactNode }) {
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn);
  if (isLoggedIn) return <Navigate to="/" replace />;
  return <>{children}</>;
}
