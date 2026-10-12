import { useState, type FormEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  BotIcon,
  ClapperboardIcon,
  LockIcon,
  ScrollTextIcon,
  UserIcon,
} from 'lucide-react';
import { authApi, publishSessionAvailable, useAuthStore } from '@shared';
import { Button } from '@/components/ui/button';
import { InputGroup, InputGroupAddon, InputGroupInput } from '@/components/ui/input-group';
import { Label } from '@/components/ui/label';
import { toastError } from '@/lib/toast';
import { AuthDivider } from '@/components/auth-divider';
import { FloatingPaths } from '@/components/floating-paths';

/** 左侧品牌面板介绍后台能力；文案对齐管理端职责。 */
const HIGHLIGHTS = [
  { icon: ClapperboardIcon, title: '番剧管理', desc: '维护条目、剧集与放送状态' },
  { icon: ScrollTextIcon, title: '日志审计', desc: '追踪导入任务与管理操作记录' },
  { icon: BotIcon, title: 'Agent 配置', desc: '调整角色提示词与工具能力' },
];

// 表单字段：label + 带前缀图标的输入框，统一间距与 a11y 关联。
function AuthField({
  id,
  label,
  icon,
  children,
}: {
  id: string;
  label: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="grid gap-2">
      <Label htmlFor={id}>{label}</Label>
      <InputGroup>
        <InputGroupAddon align="inline-start">{icon}</InputGroupAddon>
        {children}
      </InputGroup>
    </div>
  );
}

/**
 * 管理后台登录面板。
 *
 * 基于 `@efferd/auth-5`，与用户端登录页同一设计：独占整屏、左侧品牌简介、右侧登录表单。
 * 不提供注册/找回密码（后台账号由管理员开通），并保留 ADMIN 角色校验。
 */
export default function AdminLogin() {
  const navigate = useNavigate();
  const location = useLocation();
  const setAuthenticated = useAuthStore((s) => s.setAuthenticated);
  const setUnauthenticated = useAuthStore((s) => s.setUnauthenticated);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);

  const onSubmit = async (e: FormEvent) => {
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
    <main className="relative md:h-screen md:overflow-hidden lg:grid lg:grid-cols-2">
      <div className="relative hidden h-full flex-col border-r bg-secondary p-10 lg:flex dark:bg-secondary/20">
        <div className="absolute inset-0 bg-linear-to-b from-transparent via-transparent to-background" />

        <div className="relative mr-auto flex items-center gap-2 text-sm font-semibold">
          <span className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-foreground">A</span>
          <span>AnimeTracker 后台</span>
        </div>

        <div className="z-10 mt-auto space-y-6">
          <div className="space-y-2">
            <h2 className="font-semibold text-lg">AnimeTracker 管理后台</h2>
            <p className="text-muted-foreground text-sm">
              维护番剧库、用户与内容导入，让站点数据保持准确。
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

        <div className="mx-auto w-full space-y-6 sm:w-sm">
          <div className="inline-flex items-center gap-2 lg:hidden">
            <span className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-foreground text-sm font-semibold">
              A
            </span>
            <span className="font-medium">AnimeTracker 后台</span>
          </div>

          <div className="flex flex-col space-y-1">
            <h1 className="font-bold font-heading text-2xl tracking-wide">登录管理后台</h1>
            <p className="text-base text-muted-foreground">仅限管理员账号访问。</p>
          </div>

          <form className="space-y-5" onSubmit={onSubmit} noValidate>
            <div className="space-y-4">
              <AuthField id="admin-username" label="用户名/邮箱" icon={<UserIcon />}>
                <InputGroupInput
                  id="admin-username"
                  aria-label="用户名/邮箱"
                  autoComplete="username"
                  spellCheck={false}
                  placeholder="输入用户名或邮箱"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </AuthField>

              <AuthField id="admin-password" label="密码" icon={<LockIcon />}>
                <InputGroupInput
                  id="admin-password"
                  type="password"
                  aria-label="密码"
                  autoComplete="current-password"
                  placeholder="输入密码"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </AuthField>
            </div>

            {error && (
              <p className="text-sm text-destructive" role="alert">
                {error}
              </p>
            )}

            <Button className="w-full" type="submit" disabled={pending}>
              {pending ? '登录中…' : '登录'}
            </Button>
          </form>

          <AuthDivider>管理端</AuthDivider>

          <p className="text-muted-foreground text-xs">
            后台账号由管理员统一开通，如需访问请联系站点管理员。
          </p>
        </div>
      </div>
    </main>
  );
}
