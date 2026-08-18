import { useEffect } from 'react';
import { useAuthStore } from '../store/auth';
import { me } from '../api/auth';

export function useBootstrapAuth() {
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const logout = useAuthStore((s) => s.logout);
  useEffect(() => {
    if (!token || user) return;
    me().then(setUser).catch(() => logout());
  }, [token, user, setUser, logout]);
}
