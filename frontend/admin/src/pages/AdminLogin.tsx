import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { authApi, publishSessionAvailable, useAuthStore } from '@shared';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toastError } from '@/lib/toast';

export default function AdminLogin() {
  const navigate = useNavigate();
  const location = useLocation();
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated);
  const setUnauthenticated = useAuthStore((s) => s.setUnauthenticated);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError('请填写用户名和密码');
      return;
    }
    setError('');
    setPending(true);
    try {
      const data = await authApi.login({ username, password });
      if (data.user.role !== 'ADMIN') {
        toastError('该账号无管理权限');
        setUnauthenticated();
        return;
      }
      setAuthenticated(data);
      publishSessionAvailable();
      const from = (location.state as { from?: string } | null)?.from ?? '/admin/dashboard';
      navigate(from, { replace: true });
    } catch (err) {
      toastError((err as Error).message);
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="mx-auto mt-20 w-full max-w-[360px]">
      <Card>
        <CardHeader>
          <CardTitle>AnimeTracker 管理后台</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-4" onSubmit={onSubmit}>
            <div className="flex flex-col gap-2">
              <Label htmlFor="admin-username">用户名/邮箱</Label>
              <Input
                id="admin-username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                aria-label="用户名/邮箱"
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="admin-password">密码</Label>
              <Input
                id="admin-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-label="密码"
              />
            </div>
            {error && (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            )}
            <Button type="submit" className="w-full" disabled={pending}>
              {pending ? '登录中…' : '登录'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
