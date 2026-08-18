import { expect, test, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import Login from './Login';
import { useAuthStore } from '@shared';

const { loginMock } = vi.hoisted(() => ({
  loginMock: vi.fn().mockResolvedValue({ token: 't', refreshToken: 'r', user: { id: 1, username: 'u', email: 'e@x.com', role: 'USER', createdAt: '' } }),
}));

vi.mock('@shared', async (importOriginal) => {
  const mod = await importOriginal<typeof import('@shared')>();
  return { ...mod, authApi: { ...mod.authApi, login: loginMock } };
});

test('登录表单提交后写入登录态', async () => {
  useAuthStore.getState().logout();
  render(<MemoryRouter initialEntries={['/login']}><Login /></MemoryRouter>);
  await userEvent.type(screen.getByLabelText('用户名/邮箱'), 'u');
  await userEvent.type(screen.getByLabelText('密码'), 'password');
  await userEvent.click(screen.getByRole('button', { name: /登\s*录/ }));
  expect(loginMock).toHaveBeenCalledWith({ username: 'u', password: 'password' });
  expect(useAuthStore.getState().isLoggedIn).toBe(true);
  useAuthStore.getState().logout();
});
