import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { RequireAdmin } from './guards';

type AuthState = {
  status: 'checking' | 'authenticated' | 'unauthenticated' | 'retryable-error';
  user?: { role: 'USER' | 'ADMIN' };
};

const authState = vi.hoisted(() => ({
  current: { status: 'unauthenticated' } as AuthState,
}));
const messageError = vi.hoisted(() => vi.fn());

vi.mock('@shared', () => ({
  useAuthStore: (selector: (state: AuthState) => unknown) => selector(authState.current),
}));

vi.mock('antd', () => ({
  message: { error: messageError },
}));

function LoginPage() {
  const location = useLocation();
  const state = location.state as { from?: string } | null;
  return (
    <>
      <h1>管理端登录</h1>
      <output aria-label="登录后返回地址">{state?.from}</output>
    </>
  );
}

function TestApp() {
  return (
    <MemoryRouter initialEntries={['/admin/users?page=2#selected']}>
      <Routes>
        <Route path="/admin/login" element={<LoginPage />} />
        <Route
          path="/admin/users"
          element={<RequireAdmin><main>受保护内容</main></RequireAdmin>}
        />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  authState.current = { status: 'unauthenticated' };
  messageError.mockReset();
});

afterEach(cleanup);

describe('RequireAdmin', () => {
  it('未登录时跳转登录页并保留完整返回地址', () => {
    render(<TestApp />);

    expect(screen.getByRole('heading', { name: '管理端登录' })).not.toBeNull();
    expect(screen.getByRole('status', { name: '登录后返回地址' }).textContent)
      .toBe('/admin/users?page=2#selected');
    expect(screen.queryByText('受保护内容')).toBeNull();
  });

  it('非管理员登录后提示无权限并跳转登录页', () => {
    authState.current = { status: 'authenticated', user: { role: 'USER' } };

    render(<TestApp />);

    expect(messageError).toHaveBeenCalledWith('无管理权限');
    expect(screen.getByRole('heading', { name: '管理端登录' })).not.toBeNull();
    expect(screen.queryByText('受保护内容')).toBeNull();
  });

  it('管理员可以看到受保护内容', () => {
    authState.current = { status: 'authenticated', user: { role: 'ADMIN' } };

    render(<TestApp />);

    expect(screen.getByText('受保护内容')).not.toBeNull();
    expect(screen.queryByRole('heading', { name: '管理端登录' })).toBeNull();
    expect(messageError).not.toHaveBeenCalled();
  });
});
