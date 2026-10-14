import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthGate } from './AuthGate';
import { useAuthStatus } from '../hooks/useAuthStatus';

vi.mock('../hooks/useAuthStatus');

const retry = vi.fn();

function mockStatus(status: 'checking' | 'retryable-error' | 'ready') {
  vi.mocked(useAuthStatus).mockReturnValue({ status, retry } as never);
}

// AuthGate 被 client 与 admin 共用，且 shared 无 Tailwind 依赖，
// 样式只能走 shadcn 令牌的内联 CSS 变量；此处锁住「不残留旧暖纸色值」与令牌引用。
describe('AuthGate 视觉对齐 shadcn 令牌', () => {
  beforeEach(() => vi.clearAllMocks());

  it('恢复中：渲染标题与 spinner，且以 role=status 播报', () => {
    mockStatus('checking');
    render(<AuthGate><div>正文</div></AuthGate>);

    expect(screen.getByText('正在恢复登录状态')).toBeTruthy();
    expect(screen.queryByText('正文')).toBeNull();

    const panel = screen.getByRole('status');
    expect(panel.getAttribute('aria-busy')).toBe('true');
  });

  it('恢复中：底色与文字改用 background/foreground 令牌，不再硬编码暖纸色', () => {
    mockStatus('checking');
    render(<AuthGate><div /></AuthGate>);

    const shell = screen.getByRole('status').closest('main')!;
    expect(shell.style.background).toContain('var(--background');
    expect(shell.style.color).toContain('var(--foreground');

    // 旧实现的 '#F7F5F0' / '#23261F' 与 antd 青色 '#2DD4BF' 必须彻底消失
    const html = document.body.innerHTML;
    for (const legacy of ['#F7F5F0', '#23261F', '#2DD4BF', '#B58A3C', '#6E7266']) {
      expect(html).not.toContain(legacy);
    }
  });

  it('恢复中：spinner 取 primary 令牌，沿用共用关键帧名', () => {
    mockStatus('checking');
    const { container } = render(<AuthGate><div /></AuthGate>);

    const spinner = container.querySelector<HTMLElement>('.auth-gate__spinner')!;
    expect(spinner.style.borderTopColor).toContain('var(--primary');
    // 动画名不能改：client/admin 的 index.css 按此名定义 keyframes
    expect(spinner.style.animation).toContain('auth-gate-spin');
  });

  it('可重试错误：告警图标走 destructive 令牌，重试按钮可点', () => {
    mockStatus('retryable-error');
    const { container } = render(<AuthGate><div /></AuthGate>);

    const alert = screen.getByRole('alert');
    expect(alert.getAttribute('aria-live')).toBe('assertive');

    const icon = container.querySelector<HTMLElement>('.auth-gate__icon')!;
    expect(icon.style.color).toContain('var(--destructive');

    const btn = screen.getByRole('button', { name: '重新连接' });
    expect(btn.style.background).toContain('var(--primary');
    btn.click();
    expect(retry).toHaveBeenCalledTimes(1);
  });

  it('就绪：直接放行子树，不渲染任何外壳', () => {
    mockStatus('ready');
    render(<AuthGate><div>正文</div></AuthGate>);

    expect(screen.getByText('正文')).toBeTruthy();
    expect(screen.queryByRole('status')).toBeNull();
  });
});
