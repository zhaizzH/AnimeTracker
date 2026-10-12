import { useState, type FormEvent } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import {
  ArrowLeftIcon,
  AtSignIcon,
  BookmarkIcon,
  CalendarDaysIcon,
  LayoutGridIcon,
  LockIcon,
  UserIcon,
} from 'lucide-react';
import { authApi, publishSessionAvailable, useAuthStore } from '@shared';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { InputGroup, InputGroupAddon, InputGroupInput } from '@/components/ui/input-group';
import { Label } from '@/components/ui/label';
import { Logo, LogoIcon } from '@/components/logo';
import { AuthDivider } from '@/components/auth-divider';
import { FloatingPaths } from '@/components/floating-paths';

type Mode = 'login' | 'register';

/** 左侧品牌面板介绍站点能力；文案对齐产品定位（番剧索引 / 追番进度 / 更新日程）。 */
const HIGHLIGHTS = [
  { icon: LayoutGridIcon, title: '番剧索引', desc: '按标签、年份与评分筛选想看的作品' },
  { icon: BookmarkIcon, title: '追番进度', desc: '收藏、评分与看到第几集，一处记录' },
  { icon: CalendarDaysIcon, title: '更新日程', desc: '每周放送表，追的新番更新不再错过' },
];

// 表单字段：label + （可选的输入框前缀图标）+ 控件，统一间距与 a11y 关联。
function AuthField({
  id,
  label,
  icon,
  children,
}: {
  id: string;
  label: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="grid gap-2">
      <Label htmlFor={id}>{label}</Label>
      {icon ? (
        <InputGroup>
          <InputGroupAddon align="inline-start">{icon}</InputGroupAddon>
          {children}
        </InputGroup>
      ) : (
        children
      )}
    </div>
  );
}

/**
 * 登录 / 注册面板。
 *
 * 基于 `@efferd/auth-5`，按本项目契约改造：同一个面板内切换登录与注册；
 * 不提供第三方登录（后端只有用户名/邮箱 + 密码的本地账号）；左侧品牌区改为站点能力简介。
 */
export function AuthPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated);
  const [mode, setMode] = useState<Mode>('login');
  const [form, setForm] = useState({ username: '', email: '', password: '', confirm: '' });
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);

  const isLogin = mode === 'login';
  const set = (key: keyof typeof form) => (event: { target: { value: string } }) =>
    setForm((prev) => ({ ...prev, [key]: event.target.value }));

  const switchMode = (next: Mode) => {
    setMode(next);
    setError(undefined);
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!isLogin && !form.username.trim()) return setError('请输入用户名');
    if (!isLogin && !/^\S+@\S+\.\S+$/.test(form.email)) return setError('请输入有效邮箱');
    if (isLogin && !form.username.trim()) return setError('请输入用户名/邮箱');
    if (form.password.length < 6) return setError('密码至少 6 位');
    if (!isLogin && form.password !== form.confirm) return setError('两次输入的密码不一致');
    setBusy(true);
    setError(undefined);
    try {
      if (isLogin) {
        const data = await authApi.login({ username: form.username, password: form.password });
        setAuthenticated(data);
        publishSessionAvailable();
        const from = (location.state as { from?: string } | null)?.from ?? '/';
        navigate(from, { replace: true });
      } else {
        await authApi.register({ username: form.username, email: form.email, password: form.password });
        toast.success('注册成功，请查收验证码邮件');
        navigate('/verify-email?email=' + encodeURIComponent(form.email));
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="relative md:h-screen md:overflow-hidden lg:grid lg:grid-cols-2">
      <div className="relative hidden h-full flex-col border-r bg-secondary p-10 lg:flex dark:bg-secondary/20">
        <div className="absolute inset-0 bg-linear-to-b from-transparent via-transparent to-background" />
        <Logo className="mr-auto h-4.5" />

        <div className="z-10 mt-auto space-y-6">
          <div className="space-y-2">
            <h2 className="font-semibold text-lg">把追番这件事，交给 AnimeTracker</h2>
            <p className="text-muted-foreground text-sm">
              整理在追、想看与看过的作品，记录每一集的进度与心情。
            </p>
          </div>
          <ul className="space-y-4">
            {HIGHLIGHTS.map(({ icon: Icon, title, desc }) => (
              <li key={title} className="flex items-start gap-3">
                <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-md border bg-background/60">
                  <Icon className="size-4" />
                </span>
                <span className="space-y-0.5">
                  <span className="block font-medium text-sm">{title}</span>
                  <span className="block text-muted-foreground text-xs">{desc}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
        <div className="absolute inset-0">
          <FloatingPaths position={1} />
          <FloatingPaths position={-1} />
        </div>
      </div>

      <div className="relative flex min-h-screen flex-col justify-center px-8 py-12">
        {/* Top Shades */}
        <div aria-hidden className="absolute inset-0 isolate -z-10 opacity-60 contain-strict">
          <div className="absolute top-0 right-0 h-320 w-140 -translate-y-87.5 rounded-full bg-[radial-gradient(68.54%_68.72%_at_55.02%_31.46%,--theme(--color-foreground/.06)_0,hsla(0,0%,55%,.02)_50%,--theme(--color-foreground/.01)_80%)]" />
          <div className="absolute top-0 right-0 h-320 w-60 rounded-full bg-[radial-gradient(50%_50%_at_50%_50%,--theme(--color-foreground/.04)_0,--theme(--color-foreground/.01)_80%,transparent_100%)] [translate:5%_-50%]" />
          <div className="absolute top-0 right-0 h-320 w-60 -translate-y-87.5 rounded-full bg-[radial-gradient(50%_50%_at_50%_50%,--theme(--color-foreground/.04)_0,--theme(--color-foreground/.01)_80%,transparent_100%)]" />
        </div>

        <Button asChild className="absolute top-7 left-5" variant="ghost">
          <Link to="/">
            <ArrowLeftIcon />
            返回首页
          </Link>
        </Button>

        <div className="mx-auto w-full space-y-6 sm:w-sm">
          <Link to="/" aria-label="AnimeTracker 首页" className="inline-flex items-center gap-2 lg:hidden">
            <LogoIcon className="h-5" />
            <span className="font-medium">AnimeTracker</span>
          </Link>

          <div className="flex flex-col space-y-1">
            <h1 className="font-bold font-heading text-2xl tracking-wide">
              {isLogin ? '登录 AnimeTracker' : '创建 AnimeTracker 账号'}
            </h1>
            <p className="text-base text-muted-foreground">
              {isLogin ? '登录后继续你的追番进度。' : '注册后即可收藏番剧并记录进度。'}
            </p>
          </div>

          <form className="space-y-5" onSubmit={onSubmit} noValidate>
            <div className="space-y-4">
              <AuthField
                id="auth-username"
                label={isLogin ? '用户名/邮箱' : '用户名'}
                icon={<UserIcon />}
              >
                <InputGroupInput
                  id="auth-username"
                  aria-label={isLogin ? '用户名/邮箱' : '用户名'}
                  autoComplete="username"
                  spellCheck={false}
                  placeholder={isLogin ? '输入用户名或邮箱' : '设置一个用户名'}
                  value={form.username}
                  onChange={set('username')}
                />
              </AuthField>

              {!isLogin && (
                <AuthField id="auth-email" label="邮箱" icon={<AtSignIcon />}>
                  <InputGroupInput
                    id="auth-email"
                    type="email"
                    aria-label="邮箱"
                    autoComplete="email"
                    spellCheck={false}
                    inputMode="email"
                    placeholder="your.email@example.com"
                    value={form.email}
                    onChange={set('email')}
                  />
                </AuthField>
              )}

              <AuthField id="auth-password" label="密码" icon={<LockIcon />}>
                <InputGroupInput
                  id="auth-password"
                  type="password"
                  aria-label="密码"
                  autoComplete={isLogin ? 'current-password' : 'new-password'}
                  placeholder="至少 6 位"
                  value={form.password}
                  onChange={set('password')}
                />
              </AuthField>

              {!isLogin && (
                <AuthField id="auth-confirm" label="确认密码" icon={<LockIcon />}>
                  <InputGroupInput
                    id="auth-confirm"
                    type="password"
                    aria-label="确认密码"
                    autoComplete="new-password"
                    placeholder="再次输入密码"
                    value={form.confirm}
                    onChange={set('confirm')}
                  />
                </AuthField>
              )}
            </div>

            {error && (
              <p className="text-sm text-destructive" role="alert">
                {error}
              </p>
            )}

            <Button className="w-full" type="submit" disabled={busy}>
              {busy ? (isLogin ? '登录中…' : '注册中…') : isLogin ? '登录' : '注册'}
            </Button>
          </form>

          {isLogin && (
            <div className="text-right text-sm">
              <Link to="/forgot-password" className="text-muted-foreground hover:text-foreground">
                忘记密码？
              </Link>
            </div>
          )}

          <AuthDivider>{isLogin ? '还没有账号' : '已有账号'}</AuthDivider>

          <Button className="w-full" variant="outline" type="button" onClick={() => switchMode(isLogin ? 'register' : 'login')}>
            {isLogin ? '创建新账号' : '返回登录'}
          </Button>

          <p className="text-muted-foreground text-xs">
            继续即表示你同意本站的
            <a className="underline underline-offset-4 hover:text-primary" href="#">
              服务条款
            </a>
            与
            <a className="underline underline-offset-4 hover:text-primary" href="#">
              隐私政策
            </a>
            。
          </p>
        </div>
      </div>
    </main>
  );
}
