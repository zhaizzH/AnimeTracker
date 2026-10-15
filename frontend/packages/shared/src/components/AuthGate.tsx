import type { ReactNode } from 'react';
import { useAuthStatus } from '../hooks/useAuthStatus';

// 本组件为 UI 无关外壳：不依赖主题上下文，也不假设消费应用自带 .auth-gate 样式。
// 视觉一律走 shadcn 令牌的 CSS 变量（与 SubjectCard 同款约定）：内联样式里的 var() 会正常
// 参与级联，故 .dark 翻转时自动跟随；逗号后的字面量是兜底，取值与亮色主题一致，
// 仅在消费应用未定义令牌时生效。shared 无 Tailwind 依赖，两端也未 @source 本包，
// 故此处不能用 utility class。
const TOKEN = {
  background: 'var(--background, oklch(1 0 0))',
  foreground: 'var(--foreground, oklch(0.145 0 0))',
  card: 'var(--card, oklch(1 0 0))',
  border: 'var(--border, oklch(0.922 0 0))',
  mutedForeground: 'var(--muted-foreground, oklch(0.556 0 0))',
  primary: 'var(--primary, oklch(0.205 0 0))',
  primaryForeground: 'var(--primary-foreground, oklch(0.985 0 0))',
  // 原为 antd colorWarning 的赭黄；告警语义在 shadcn 里由 destructive 承担。
  destructive: 'var(--destructive, oklch(0.577 0.245 27.325))',
  fontSans: 'var(--font-sans, system-ui, sans-serif)',
} as const;

// 面板对齐 auth-shell（AuthShell 卡片为 rounded-xl border bg-card shadow-sm），
// rounded-xl = radius-lg + 4px，故此处照抄该偏移，使恢复态与验证邮箱/找回密码等页面观感一致。
const PANEL = {
  background: TOKEN.card,
  border: `1px solid ${TOKEN.border}`,
  borderRadius: 'calc(var(--radius, 0.625rem) + 4px)',
  boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
} as const;
const BRAND = {
  marginBottom: 20,
  fontFamily: TOKEN.fontSans,
  fontSize: 20,
  fontWeight: 600,
  letterSpacing: '-0.025em',
} as const;
const TITLE = {
  margin: '0 0 8px',
  fontSize: 20,
  fontWeight: 500,
  lineHeight: 1.3,
} as const;
const SUBTITLE = {
  margin: 0,
  fontSize: 14,
  lineHeight: 1.6,
  color: TOKEN.mutedForeground,
} as const;
// 原为 antd <Result status="warning">，其图标为 fontSizeHeading3 * 3 = 72px、
// 取色 colorWarning；antd 的警告图标本身是「实心圆 + 感叹号」。尺寸收到 56 以贴近
// shadcn 空状态的比例。
const ICON = {
  display: 'block',
  width: 56,
  height: 56,
  margin: '0 auto',
  color: TOKEN.destructive,
} as const;
// 对齐 shadcn Button 默认档：h-9 / rounded-md / px-4 / text-sm / font-medium，
// 底色改用 primary 令牌（原为 antd 青色 #2DD4BF）。
const RETRY = {
  marginTop: 20,
  height: 36,
  padding: '0 16px',
  border: `1px solid ${TOKEN.primary}`,
  borderRadius: 'calc(var(--radius, 0.625rem) - 2px)',
  background: TOKEN.primary,
  color: TOKEN.primaryForeground,
  fontFamily: TOKEN.fontSans,
  fontSize: 14,
  fontWeight: 500,
  cursor: 'pointer',
} as const;

export function AuthGate({ children, className }: { children: ReactNode; className?: string }) {
  const { status, retry } = useAuthStatus();
  const shellStyle = {
    minHeight: '100vh',
    display: 'grid',
    placeItems: 'center',
    padding: 24,
    background: TOKEN.background,
    color: TOKEN.foreground,
    fontFamily: TOKEN.fontSans,
  } as const;
  const panelStyle = {
    width: 'min(100%, 420px)',
    padding: '40px 32px',
    textAlign: 'center',
    ...PANEL,
  } as const;
  // checking 态的自绘 spinner：自包含实现，不依赖消费应用的外部动画规则。
  const spinnerStyle = {
    width: 32,
    height: 32,
    margin: '8px auto 20px',
    border: `3px solid ${TOKEN.border}`,
    borderTopColor: TOKEN.primary,
    borderRadius: '50%',
    animation: 'auth-gate-spin 0.8s linear infinite',
  } as const;

  if (status === 'checking') {
    return (
      <main className={`auth-gate auth-gate--checking ${className ?? ''}`.trim()} style={shellStyle}>
        <section className="auth-gate__panel" role="status" aria-live="polite" aria-busy="true" style={panelStyle}>
          <div className="auth-gate__brand" style={BRAND}>AnimeTracker</div>
          <div className="auth-gate__spinner" style={spinnerStyle} aria-hidden="true" />
          <h2 className="auth-gate__title" style={TITLE}>正在恢复登录状态</h2>
          <p className="auth-gate__subtitle" style={SUBTITLE}>正在安全地恢复你的会话，请稍候。</p>
        </section>
      </main>
    );
  }

  if (status === 'retryable-error') {
    return (
      <main className={`auth-gate auth-gate--error ${className ?? ''}`.trim()} style={shellStyle}>
        <section className="auth-gate__panel" role="alert" aria-live="assertive" style={panelStyle}>
          <div className="auth-gate__brand" style={BRAND}>AnimeTracker</div>
          <div className="auth-gate__result">
            <svg className="auth-gate__icon" style={ICON} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
              <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm-1 4h2v8h-2V6Zm0 10h2v2h-2v-2Z" />
            </svg>
            <h2 className="auth-gate__title" style={TITLE}>暂时无法确认登录状态</h2>
            <p className="auth-gate__subtitle" style={SUBTITLE}>网络连接可能不稳定，请重新连接后继续。</p>
            <button type="button" className="auth-gate__retry" style={RETRY} onClick={retry}>重新连接</button>
          </div>
        </section>
      </main>
    );
  }

  return <>{children}</>;
}
