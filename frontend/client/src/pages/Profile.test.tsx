import { expect, test, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Profile from './Profile';
import { useAuthStore } from '@shared';

const { meMock, updateProfileMock, updatePasswordMock } = vi.hoisted(() => ({
  meMock: vi.fn().mockResolvedValue({ id: 1, username: 'u', email: 'e@x.com', role: 'USER', createdAt: '' }),
  updateProfileMock: vi.fn().mockResolvedValue({}),
  updatePasswordMock: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('@shared', async (io) => {
  const mod = await io<typeof import('@shared')>();
  return {
    ...mod,
    authApi: { ...mod.authApi, me: meMock, updateProfile: updateProfileMock, updatePassword: updatePasswordMock },
  };
});
test('修改密码提交 old/new', async () => {
  const login = { token: 't', refreshToken: 'r', user: { id: 1, username: 'u', email: 'e@x.com', role: 'USER', createdAt: '' } };
  useAuthStore.getState().setLogin(login as never);
  render(<QueryClientProvider client={new QueryClient()}><Profile /></QueryClientProvider>);
  await userEvent.click(await screen.findByRole('button', { name: '修改密码' }));
  await userEvent.type(screen.getByLabelText('旧密码'), 'old');
  await userEvent.type(screen.getByLabelText('新密码'), 'new123');
  await userEvent.click(screen.getByRole('button', { name: /确\s*认/ }));
  await waitFor(() => expect(updatePasswordMock).toHaveBeenCalledWith({ oldPassword: 'old', newPassword: 'new123' }));
  useAuthStore.getState().logout();
});
