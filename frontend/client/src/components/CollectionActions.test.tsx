import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CollectionActions } from './CollectionActions';
import { collectionsApi, useAuthStore } from '@shared';
import type { LoginVO } from '@shared';

afterEach(() => cleanup());

vi.mock('@shared', async (io) => {
  const mod = await io<typeof import('@shared')>();
  return { ...mod, collectionsApi: { ...mod.collectionsApi,
    getCollection: vi.fn().mockResolvedValue(null),
    wishlist: vi.fn().mockResolvedValue({ state: 'ADDED' }),
    save: vi.fn().mockResolvedValue(undefined),
    remove: vi.fn().mockResolvedValue(undefined),
    updateEpStatus: vi.fn().mockResolvedValue(undefined) } };
});
const qc = () => new QueryClient();
test('未收藏时点「想看」调用 wishlist', async () => {
  const login: LoginVO = { token: 't', refreshToken: 'r', user: { id: 1, username: 'u', email: 'e@x.com', role: 'USER', createdAt: '' } };
  useAuthStore.getState().setLogin(login);
  render(<QueryClientProvider client={qc()}><CollectionActions subjectId={'42'} eps={12} /></QueryClientProvider>);
  await userEvent.click(await screen.findByRole('button', { name: /想\s*看/ }));
  expect(collectionsApi.wishlist).toHaveBeenCalledWith('42');
  useAuthStore.getState().logout();
});
test('未登录显示登录提示', async () => {
  useAuthStore.getState().logout();
  render(<QueryClientProvider client={qc()}><CollectionActions subjectId={'42'} eps={12} /></QueryClientProvider>);
  expect(screen.getByText(/登录后可追番/)).toBeTruthy();
});
