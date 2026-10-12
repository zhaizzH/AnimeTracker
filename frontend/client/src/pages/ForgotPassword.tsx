import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { authApi } from '@shared';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AuthShell, Field } from '@/components/auth/auth-shell';

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!/^\S+@\S+\.\S+$/.test(email)) return setError('请输入有效邮箱');
    setBusy(true);
    setError(undefined);
    try {
      await authApi.forgotPassword({ email });
      toast.success('验证码已发送（邮箱不存在时也提示成功）');
      navigate('/reset-password?email=' + encodeURIComponent(email));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      title="找回密码"
      footer={<Link to="/login" className="hover:text-foreground">回到登录</Link>}
    >
      <form className="grid gap-4" onSubmit={onSubmit} noValidate>
        <Field id="forgot-email" label="邮箱" error={error}>
          <Input
            id="forgot-email"
            type="email"
            aria-label="邮箱"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>
        <Button type="submit" className="w-full" disabled={busy}>
          {busy ? '发送中…' : '发送验证码'}
        </Button>
      </form>
    </AuthShell>
  );
}
