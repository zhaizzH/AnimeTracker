import { useState, type FormEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import { authApi } from '@shared';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AuthShell, Field } from '@/components/auth/auth-shell';

export default function ResetPassword() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [form, setForm] = useState({ email: params.get('email') ?? '', code: '', newPassword: '', confirm: '' });
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);
  const set = (key: keyof typeof form) => (event: { target: { value: string } }) =>
    setForm((prev) => ({ ...prev, [key]: event.target.value }));

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!/^\S+@\S+\.\S+$/.test(form.email)) return setError('请输入有效邮箱');
    if (form.code.length !== 6) return setError('请输入 6 位验证码');
    if (form.newPassword.length < 6) return setError('密码至少 6 位');
    if (form.newPassword !== form.confirm) return setError('两次输入的密码不一致');
    setBusy(true);
    setError(undefined);
    try {
      await authApi.resetPassword({ email: form.email, code: form.code, newPassword: form.newPassword });
      toast.success('密码已重置，请重新登录');
      navigate('/login');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title="重置密码">
      <form className="grid gap-4" onSubmit={onSubmit} noValidate>
        <Field id="reset-email" label="邮箱">
          <Input id="reset-email" type="email" aria-label="邮箱" autoComplete="email" value={form.email} onChange={set('email')} />
        </Field>
        <Field id="reset-code" label="验证码">
          <Input id="reset-code" aria-label="验证码" maxLength={6} placeholder="6 位验证码" value={form.code} onChange={set('code')} />
        </Field>
        <Field id="reset-password" label="新密码">
          <Input id="reset-password" type="password" aria-label="新密码" autoComplete="new-password" value={form.newPassword} onChange={set('newPassword')} />
        </Field>
        <Field id="reset-confirm" label="确认新密码" error={error}>
          <Input id="reset-confirm" type="password" aria-label="确认新密码" autoComplete="new-password" value={form.confirm} onChange={set('confirm')} />
        </Field>
        <Button type="submit" className="w-full" disabled={busy}>
          {busy ? '重置中…' : '重置密码'}
        </Button>
      </form>
    </AuthShell>
  );
}
