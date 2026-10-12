import { useState, type FormEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import { authApi, publishSessionAvailable, useAuthStore } from '@shared';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AuthShell, Field } from '@/components/auth/auth-shell';

export default function VerifyEmail() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const email = params.get('email') ?? '';
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated);
  const [code, setCode] = useState('');
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (code.length !== 6) return setError('请输入 6 位验证码');
    setBusy(true);
    setError(undefined);
    try {
      const data = await authApi.verifyEmail({ email, code });
      setAuthenticated(data);
      publishSessionAvailable();
      toast.success('邮箱验证成功');
      navigate('/', { replace: true });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title="验证邮箱">
      <p className="mt-0 mb-4 text-sm text-muted-foreground">验证码已发送至：{email || '（未提供邮箱）'}</p>
      <form className="grid gap-4" onSubmit={onSubmit} noValidate>
        <Field id="verify-code" label="验证码" error={error}>
          <Input
            id="verify-code"
            aria-label="验证码"
            maxLength={6}
            placeholder="6 位验证码"
            value={code}
            onChange={(e) => setCode(e.target.value)}
          />
        </Field>
        <Button type="submit" className="w-full" disabled={busy}>
          {busy ? '验证中…' : '验证'}
        </Button>
      </form>
    </AuthShell>
  );
}
