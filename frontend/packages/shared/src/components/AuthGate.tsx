import type { ReactNode } from 'react';
import { useAuthStatus } from '../hooks/useAuthStatus';

// 本组件为 UI 无关外壳：不依赖 antd 主题上下文，也不假设消费应用自带 .auth-gate 样式。
// 以下字面量取自 client `index.css` 的「暖纸玻璃」令牌，作为两个 app 的共同兜底；
// client 侧仍由 .od-auth-gate 规则覆盖，admin 则可直接使用这套默认视觉。
const SHELL = {
  background: '#F7F5F0',
  color: '#23261F',
} as const;
const PANEL = {
  background: 'rgba(255, 255, 255, 0.62)',
  border: '1px solid rgba(255, 255, 255, 0.7)',
  borderRadius: 14,
  boxShadow: '0 10px 30px rgba(35, 38, 31, 0.08)',
} as const;
const BRAND = {
  marginBottom: 24,
  fontFamily: "'Noto Serif SC', 'Songti SC', SimSun, serif",
  fontSize: 26,
  fontWeight: 700,
  letterSpacing: '0.02em',
} as const;
const TITLE = {
  margin: '0 0 12px',
  fontSize: 24,
  fontWeight: 500,
  lineHeight: 1.15,
} as const;
const SUBTITLE = {
  margin: 0,
  color: '#6E7266',
} as const;
// 原为 antd <Result status="warning">，其图标为 fontSizeHeading3 * 3 = 72px、
// 取色 colorWarning；antd 的警告图标本身是「实心圆 + 感叹号」。
const ICON = {
  width: 72,
  height: 72,
  color: '#B58A3C',
} as const;
// 原为 antd <Button type="primary">：controlHeight 38 / borderRadius 10 / 青色底白字。
const RETRY = {
  marginTop: 20,
  height: 38,
  padding: '0 22px',
  border: '1px solid #2DD4BF',
  borderRadius: 10,
  background: '#2DD4BF',
  color: '#FFFFFF',
  fontFamily: 'inherit',
  fontSize: 14,
  cursor: 'pointer',
} as const;

export function AuthGate({ children, className }: { children: ReactNode; className?: string }) {
  const { status, retry } = useAuthStatus();
  const shellStyle = {
    minHeight: '100vh',
    display: 'grid',
    placeItems: 'center',
    padding: 24,
    background: SHELL.background,
    color: SHELL.color,
  } as const;
  const panelStyle = {
    width: 'min(100%, 480px)',
    padding: '40px 32px',
    textAlign: 'center',
    background: PANEL.background,
    border: PANEL.border,
    borderRadius: PANEL.borderRadius,
    boxShadow: PANEL.boxShadow,
  } as const;
  // checking 态的自绘 spinner：client 侧由 .od-auth-gate 的动画规则接管。
  const spinnerStyle = {
    width: 32,
    height: 32,
    margin: '8px auto 20px',
    border: '3px solid #E3E0D7',
    borderTopColor: '#2DD4BF',
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
