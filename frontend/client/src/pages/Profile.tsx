import { useRef, useState, type FormEvent } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { UploadIcon } from 'lucide-react';
import { authApi, filesApi, useAuthStore, formatDate, publishSignedOut } from '@shared';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Field } from '@/components/auth/auth-shell';

export default function Profile() {
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const { data } = useQuery({ queryKey: ['me'], queryFn: () => authApi.me() });
  const u = data ?? user;

  const [pwdOpen, setPwdOpen] = useState(false);
  const [pwd, setPwd] = useState({ oldPassword: '', newPassword: '' });
  const [emailOpen, setEmailOpen] = useState(false);
  const [emailStep, setEmailStep] = useState<'send' | 'verify'>('send');
  const [emailForm, setEmailForm] = useState({ newEmail: '', code: '' });
  const [editOpen, setEditOpen] = useState(false);
  const [editForm, setEditForm] = useState({ nickname: '', avatar: '' });
  const fileRef = useRef<HTMLInputElement>(null);

  const onPwd = async (event: FormEvent) => {
    event.preventDefault();
    if (pwd.newPassword.length < 6) return toast.error('密码至少 6 位');
    try {
      await authApi.updatePassword(pwd);
      useAuthStore.getState().setUnauthenticated();
      publishSignedOut();
      toast.success('密码已修改，请重新登录');
      setPwdOpen(false);
      setPwd({ oldPassword: '', newPassword: '' });
      navigate('/login');
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const onSendCode = async () => {
    if (!/^\S+@\S+\.\S+$/.test(emailForm.newEmail)) return toast.error('请输入有效邮箱');
    try {
      await authApi.sendEmailCode({ newEmail: emailForm.newEmail });
      toast.success('验证码已发送至新邮箱');
      setEmailStep('verify');
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const onVerifyEmail = async () => {
    if (emailForm.code.length !== 6) return toast.error('请输入 6 位验证码');
    try {
      await authApi.verifyEmailCode(emailForm);
      toast.success('邮箱已更新');
      setEmailOpen(false);
      setEmailForm({ newEmail: '', code: '' });
      setEmailStep('send');
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const onEdit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      const next = await authApi.updateProfile({ nickname: editForm.nickname, avatar: editForm.avatar });
      useAuthStore.setState({ user: next });
      setEditOpen(false);
      toast.success('资料已更新');
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const onAvatarFile = async (file: File | undefined) => {
    if (!file) return;
    try {
      const url = await filesApi.uploadAvatar(file);
      setEditForm((f) => ({ ...f, avatar: url }));
      toast.success('已上传');
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const initial = (u?.nickname ?? u?.username ?? '用').slice(0, 1);

  return (
    <div className="mx-auto w-full max-w-[720px] p-6">
      <div className="rounded-xl border bg-card p-6">
        <div className="flex flex-col items-start gap-6 sm:flex-row sm:items-center">
          <Avatar className="size-20">
            <AvatarImage src={u?.avatar ?? undefined} alt="" />
            <AvatarFallback>{initial}</AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <h2 className="mb-1 text-xl font-semibold">{u?.nickname ?? u?.username}</h2>
            <dl className="grid gap-1 text-sm">
              <div className="flex gap-2"><dt className="w-20 text-muted-foreground">用户名</dt><dd>{u?.username}</dd></div>
              <div className="flex gap-2"><dt className="w-20 text-muted-foreground">邮箱</dt><dd className="truncate">{u?.email}</dd></div>
              <div className="flex gap-2"><dt className="w-20 text-muted-foreground">角色</dt><dd>{u?.role}</dd></div>
              <div className="flex gap-2"><dt className="w-20 text-muted-foreground">注册时间</dt><dd>{formatDate(u?.createdAt)}</dd></div>
            </dl>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => { setEditForm({ nickname: u?.nickname ?? '', avatar: u?.avatar ?? '' }); setEditOpen(true); }}>编辑资料</Button>
              <Button variant="outline" onClick={() => setPwdOpen(true)}>修改密码</Button>
              <Button variant="outline" onClick={() => setEmailOpen(true)}>修改邮箱</Button>
            </div>
          </div>
        </div>
      </div>

      {/* 修改密码 */}
      <Dialog open={pwdOpen} onOpenChange={setPwdOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>修改密码</DialogTitle></DialogHeader>
          <form id="pwd-form" className="grid gap-4" onSubmit={onPwd}>
            <Field id="pwd-old" label="旧密码">
              <Input id="pwd-old" type="password" aria-label="旧密码" autoComplete="current-password"
                value={pwd.oldPassword} onChange={(e) => setPwd((p) => ({ ...p, oldPassword: e.target.value }))} />
            </Field>
            <Field id="pwd-new" label="新密码">
              <Input id="pwd-new" type="password" aria-label="新密码" autoComplete="new-password"
                value={pwd.newPassword} onChange={(e) => setPwd((p) => ({ ...p, newPassword: e.target.value }))} />
            </Field>
          </form>
          <DialogFooter>
            <Button type="submit" form="pwd-form">确认</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 修改邮箱 */}
      <Dialog open={emailOpen} onOpenChange={(next) => { setEmailOpen(next); if (!next) setEmailStep('send'); }}>
        <DialogContent>
          <DialogHeader><DialogTitle>修改邮箱</DialogTitle></DialogHeader>
          <div className="grid gap-4">
            <Field id="email-new" label="新邮箱">
              <Input id="email-new" type="email" aria-label="新邮箱" autoComplete="email" spellCheck={false} inputMode="email"
                value={emailForm.newEmail} onChange={(e) => setEmailForm((f) => ({ ...f, newEmail: e.target.value }))} />
            </Field>
            {emailStep === 'verify' && (
              <Field id="email-code" label="验证码">
                <Input id="email-code" aria-label="验证码" maxLength={6} inputMode="numeric" spellCheck={false}
                  value={emailForm.code} onChange={(e) => setEmailForm((f) => ({ ...f, code: e.target.value }))} />
              </Field>
            )}
          </div>
          <DialogFooter>
            <Button onClick={emailStep === 'send' ? onSendCode : onVerifyEmail}>确认</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 编辑资料 */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>编辑资料</DialogTitle></DialogHeader>
          <form id="edit-form" className="grid gap-4" onSubmit={onEdit}>
            <Field id="edit-nickname" label="昵称">
              <Input id="edit-nickname" aria-label="昵称" autoComplete="off"
                value={editForm.nickname} onChange={(e) => setEditForm((f) => ({ ...f, nickname: e.target.value }))} />
            </Field>
            <Field id="edit-avatar" label="头像">
              <Input id="edit-avatar" aria-label="头像" autoComplete="off"
                value={editForm.avatar} onChange={(e) => setEditForm((f) => ({ ...f, avatar: e.target.value }))} />
            </Field>
            <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden"
              onChange={(e) => { void onAvatarFile(e.target.files?.[0]); e.target.value = ''; }} />
            <Button type="button" variant="outline" onClick={() => fileRef.current?.click()}>
              <UploadIcon />上传头像
            </Button>
          </form>
          <DialogFooter>
            <Button type="submit" form="edit-form">确认</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
