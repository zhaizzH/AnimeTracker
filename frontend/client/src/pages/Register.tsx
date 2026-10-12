import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { authApi } from '@shared';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AuthShell, Field } from '@/components/auth/auth-shell';

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', email: '', password: '', confirm: '' });
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);
  const set = (key: keyof typeof form) => (event: { target: { value: string } }) =>
    setForm((prev) => ({ ...prev, [key]: event.target.value }));

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!form.username.trim()) return setError('请输入用户名');
    if (!/^\S+@\S+\.\S+$/.test(form.email)) return setError('请输入有效邮箱');
    if (form.password.length < 6) return setError('密码至少 6 位');
    if (form.password !== form.confirm) return setError('两次输入的密码不一致');
    setBusy(true);
    setError(undefined);
    try {
      await authApi.register({ username: form.username, email: form.email, password: form.password });
      toast.success('注册成功，请查收验证码邮件');
      navigate('/verify-email?email=' + encodeURIComponent(form.email));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      title="注册"
      footer={<Link to="/login" className="hover:text-foreground">已有账号？去登录</Link>}
    >
      <form className="grid gap-4" onSubmit={onSubmit} noValidate>
        <Field id="reg-username" label="用户名">
          <Input id="reg-username" aria-label="用户名" autoComplete="username" spellCheck={false} value={form.username} onChange={set('username')} />
        </Field>
        <Field id="reg-email" label="邮箱">
          <Input id="reg-email" type="email" aria-label="邮箱" autoComplete="email" spellCheck={false} inputMode="email" value={form.email} onChange={set('email')} />
        </Field>
        <Field id="reg-password" label="密码">
          <Input id="reg-password" type="password" aria-label="密码" autoComplete="new-password" value={form.password} onChange={set('password')} />
        </Field>
        <Field id="reg-confirm" label="确认密码" error={error}>
          <Input id="reg-confirm" type="password" aria-label="确认密码" autoComplete="new-password" value={form.confirm} onChange={set('confirm')} />
        </Field>
        <Button type="submit" className="w-full" disabled={busy}>
          {busy ? '注册中…' : '注册'}
        </Button>
      </form>
    </AuthShell>
  );
}
