import { expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { RequireAdmin } from './guards';
import { useAuthStore } from '@shared';
import type { LoginVO } from '@shared';

test('非 ADMIN 重定向到登录页', () => {
  const login: LoginVO = { token: 't', refreshToken: 'r', user: { id: 1, username: 'u', email: 'e@x.com', role: 'USER', createdAt: '' } };
  useAuthStore.getState().setLogin(login);
  render(
    <MemoryRouter initialEntries={['/admin/dashboard']}>
      <Routes>
        <Route path="/admin/login" element={<div>管理登录</div>} />
        <Route path="/admin/dashboard" element={<RequireAdmin><div>看板</div></RequireAdmin>} />
      </Routes>
    </MemoryRouter>,
  );
  expect(screen.getByText('管理登录')).toBeTruthy();
  useAuthStore.getState().logout();
});
test('ADMIN 放行', () => {
  const login: LoginVO = { token: 't', refreshToken: 'r', user: { id: 1, username: 'a', email: 'a@x.com', role: 'ADMIN', createdAt: '' } };
  useAuthStore.getState().setLogin(login);
  render(
    <MemoryRouter initialEntries={['/admin/dashboard']}>
      <Routes>
        <Route path="/admin/login" element={<div>管理登录</div>} />
        <Route path="/admin/dashboard" element={<RequireAdmin><div>看板</div></RequireAdmin>} />
      </Routes>
    </MemoryRouter>,
  );
  expect(screen.getByText('看板')).toBeTruthy();
  useAuthStore.getState().logout();
});
