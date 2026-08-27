import type { ReactNode } from 'react';
import { Button, Result, Spin, Typography, theme } from 'antd';
import { useAuthStore } from '../store/auth';
import { retryBootstrapAuth } from '../auth/coordinator';

export function AuthGate({ children, className }: { children: ReactNode; className?: string }) {
  const status = useAuthStore((state) => state.status);
  const { token } = theme.useToken();
  const shellStyle = {
    minHeight: '100vh',
    display: 'grid',
    placeItems: 'center',
    padding: 24,
    background: token.colorBgLayout,
    color: token.colorText,
  } as const;
  const panelStyle = {
    width: 'min(100%, 480px)',
    padding: '40px 32px',
    textAlign: 'center',
    background: token.colorBgContainer,
    border: `1px solid ${token.colorBorderSecondary}`,
    borderRadius: token.borderRadiusLG,
    boxShadow: token.boxShadowSecondary,
  } as const;

  if (status === 'checking') {
    return (
      <main className={`auth-gate auth-gate--checking ${className ?? ''}`.trim()} style={shellStyle}>
        <section className="auth-gate__panel" role="status" aria-live="polite" aria-busy="true" style={panelStyle}>
          <div className="auth-gate__brand">AnimeTracker</div>
          <Spin size="large" />
          <Typography.Title level={2}>正在恢复登录状态</Typography.Title>
          <Typography.Paragraph type="secondary">正在安全地恢复你的会话，请稍候。</Typography.Paragraph>
        </section>
      </main>
    );
  }

  if (status === 'retryable-error') {
    return (
      <main className={`auth-gate auth-gate--error ${className ?? ''}`.trim()} style={shellStyle}>
        <section className="auth-gate__panel" role="alert" aria-live="assertive" style={panelStyle}>
          <div className="auth-gate__brand">AnimeTracker</div>
          <Result
            className="auth-gate__result"
            status="warning"
            title={<Typography.Title level={2} style={{ margin: 0 }}>暂时无法确认登录状态</Typography.Title>}
            subTitle="网络连接可能不稳定，请重新连接后继续。"
            extra={<Button type="primary" onClick={() => void retryBootstrapAuth()}>重新连接</Button>}
          />
        </section>
      </main>
    );
  }

  return <>{children}</>;
}
