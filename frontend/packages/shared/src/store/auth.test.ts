import { beforeEach, expect, test } from 'vitest';
import { useAuthStore } from './auth';
import type { LoginVO } from '../types';

const login: LoginVO = { token: 'at', refreshToken: 'rt', user: { id: 1, username: 'u', email: 'e@x.com', role: 'USER', createdAt: '2026-01-01' } };
beforeEach(() => useAuthStore.getState().logout());
test('setLogin 写入 token 与用户并置 isLoggedIn', () => {
  useAuthStore.getState().setLogin(login);
  const s = useAuthStore.getState();
  expect(s.token).toBe('at'); expect(s.refreshToken).toBe('rt'); expect(s.user?.role).toBe('USER'); expect(s.isLoggedIn).toBe(true);
});
test('logout 清空全部', () => {
  useAuthStore.getState().setLogin(login);
  useAuthStore.getState().logout();
  expect(useAuthStore.getState().isLoggedIn).toBe(false);
});
