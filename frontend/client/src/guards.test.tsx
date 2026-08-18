import { expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { RequireAuth } from './guards';
import { useAuthStore } from '@shared';
import type { LoginVO } from '@shared';
const login: LoginVO = { token: 't', refreshToken: 'r', user: { id: 1, username: 'u', email: 'e@x.com', role: 'USER', createdAt: '' } };
test('未登录访问受保护页重定向到 /login', () => {
  useAuthStore.getState().logout();
  render(
    <MemoryRouter initialEntries={['/private']}>
      <Routes>
        <Route path="/login" element={<div>登录页</div>} />
        <Route path="/private" element={<RequireAuth><div>受保护</div></RequireAuth>} />
      </Routes>
    </MemoryRouter>,
  );
  expect(screen.getByText('登录页')).toBeTruthy();
});
test('已登录放行', () => {
  useAuthStore.getState().setLogin(login);
  render(
    <MemoryRouter initialEntries={['/private']}>
      <Routes>
        <Route path="/login" element={<div>登录页</div>} />
        <Route path="/private" element={<RequireAuth><div>受保护</div></RequireAuth>} />
      </Routes>
    </MemoryRouter>,
  );
  expect(screen.getByText('受保护')).toBeTruthy();
  useAuthStore.getState().logout();
});
