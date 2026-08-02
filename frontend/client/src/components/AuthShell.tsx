import type { ReactNode } from 'react';

interface AuthShellProps {
  title: string;
  en: string;
  subtitle?: string;
  children: ReactNode;
}

export default function AuthShell({ title, en, subtitle, children }: AuthShellProps) {
  return (
    <div className="auth-page">
      <div className="auth-brand">
        <div className="auth-brand-cn">番组手账</div>
        <div className="auth-brand-en">ANIMETRACKER</div>
      </div>
      <div className="auth-sheet">
        <div className="auth-sheet-head">
          <h1>{title}</h1>
          <div className="auth-en">{en}</div>
          {subtitle && <p className="auth-note">{subtitle}</p>}
        </div>
        {children}
      </div>
    </div>
  );
}
