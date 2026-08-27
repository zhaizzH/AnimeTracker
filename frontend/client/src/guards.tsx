import { Navigate, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuthStore } from '@shared';

const returnTo = (location: ReturnType<typeof useLocation>) => location.pathname + location.search + location.hash;

export function RequireAuth({ children }: { children: ReactNode }) {
  const status = useAuthStore((state) => state.status);
  const location = useLocation();
  if (status === 'unauthenticated') return <Navigate to="/login" replace state={{ from: returnTo(location) }} />;
  return <>{children}</>;
}

export function PublicOnly({ children }: { children: ReactNode }) {
  const status = useAuthStore((state) => state.status);
  if (status === 'authenticated') return <Navigate to="/" replace />;
  return <>{children}</>;
}