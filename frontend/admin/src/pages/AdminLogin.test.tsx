import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import AdminLogin from './AdminLogin';

const authApi = vi.hoisted(() => ({ login: vi.fn() }));
const publishSessionAvailable = vi.hoisted(() => vi.fn());
const setAuthenticated = vi.hoisted(() => vi.fn());
const setUnauthenticated = vi.hoisted(() => vi.fn());
const toastError = vi.hoisted(() => vi.fn());

vi.mock('@shared', () => ({
  authApi,
  publishSessionAvailable,
  useAuthStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ setAuthenticated, setUnauthenticated }),
}));
vi.mock('@/lib/toast', () => ({ toastError, toastSuccess: vi.fn() }));

function Destination() {
  const location = useLocation();
  return <output aria-label="到达">{location.pathname}</output>;
}

function renderLogin(initialEntry = '/admin/login') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route path="/admin/dashboard" element={<Destination />} />
        <Route path="/admin/users" element={<Destination />} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(cleanup);

describe('AdminLogin', () => {
  it('必填校验拦截空提交', async () => {
    const user = userEvent.setup();
    renderLogin();
    await user.click(screen.getByRole('button', { name: '登录' }));
    expect(await screen.findByRole('alert')).toHaveProperty('textContent', '请填写用户名和密码');
    expect(authApi.login).not.toHaveBeenCalled();
  });

  it('非 ADMIN 账号提示无权限、登出且不跳转', async () => {
    authApi.login.mockResolvedValue({ user: { role: 'USER' } });
    const user = userEvent.setup();
    renderLogin();
    await user.type(screen.getByLabelText('用户名/邮箱'), 'u');
    await user.type(screen.getByLabelText('密码'), 'p');
    await user.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() => expect(toastError).toHaveBeenCalledWith('该账号无管理权限'));
    expect(setUnauthenticated).toHaveBeenCalled();
    expect(setAuthenticated).not.toHaveBeenCalled();
    expect(publishSessionAvailable).not.toHaveBeenCalled();
  });

  it('ADMIN 登录成功后按 location.state.from 回跳', async () => {
    authApi.login.mockResolvedValue({ user: { role: 'ADMIN' } });
    const user = userEvent.setup();
    render(
      <MemoryRouter
        initialEntries={[{ pathname: '/admin/login', state: { from: '/admin/users?page=2' } }]}
      >
        <Routes>
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin/users" element={<Destination />} />
        </Routes>
      </MemoryRouter>,
    );
    await user.type(screen.getByLabelText('用户名/邮箱'), 'admin');
    await user.type(screen.getByLabelText('密码'), 'p');
    await user.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() => expect(screen.getByLabelText('到达')).toHaveProperty('textContent', '/admin/users'));
    expect(setAuthenticated).toHaveBeenCalled();
    expect(publishSessionAvailable).toHaveBeenCalled();
  });

  it('无 from 时默认跳转 /admin/dashboard', async () => {
    authApi.login.mockResolvedValue({ user: { role: 'ADMIN' } });
    const user = userEvent.setup();
    renderLogin();
    await user.type(screen.getByLabelText('用户名/邮箱'), 'admin');
    await user.type(screen.getByLabelText('密码'), 'p');
    await user.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() =>
      expect(screen.getByLabelText('到达')).toHaveProperty('textContent', '/admin/dashboard'),
    );
  });
});
