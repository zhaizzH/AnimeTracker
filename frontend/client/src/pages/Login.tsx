import { useState, type FormEvent } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { authApi, publishSessionAvailable, useAuthStore } from '@shared';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AuthShell, Field } from '@/components/auth/auth-shell';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!username.trim()) return setError('请输入用户名/邮箱');
    if (password.length < 6) return setError('密码至少 6 位');
    setBusy(true);
    setError(undefined);
    try {
      const data = await authApi.login({ username, password });
      setAuthenticated(data);
      publishSessionAvailable();
      const from = (location.state as { from?: string } | null)?.from ?? '/';
      navigate(from, { replace: true });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      title="登录"
      footer={
        <>
          <Link to="/register" className="hover:text-foreground">没有账号？去注册</Link>
          <Link to="/forgot-password" className="hover:text-foreground">忘记密码</Link>
        </>
      }
    >
      <form className="grid gap-4" onSubmit={onSubmit} noValidate>
        <Field id="login-username" label="用户名/邮箱">
          <Input
            id="login-username"
            aria-label="用户名/邮箱"
            autoComplete="username"
            spellCheck={false}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </Field>
        <Field id="login-password" label="密码" error={error}>
          <Input
            id="login-password"
            type="password"
            aria-label="密码"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        <Button type="submit" className="w-full" disabled={busy}>
          {busy ? '登录中…' : '登录'}
        </Button>
      </form>
    </AuthShell>
  );
}
