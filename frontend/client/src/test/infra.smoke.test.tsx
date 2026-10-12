import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { cn } from '@/lib/utils';
import { ThemeBridge } from '@/components/theme-bridge';
import { useThemeStore } from '@shared';

// ui-infra 冒烟：验证 Tailwind/shadcn 基础设施（@ 别名、cn、Token 变量、主题桥）可运行。
// 页面级测试由子任务 4（client-pages）补齐。

describe('client 基础设施', () => {
  afterEach(() => {
    document.documentElement.classList.remove('dark');
  });

  it('cn() 合并冲突的 Tailwind 类', () => {
    expect(cn('px-2', 'px-4')).toBe('px-4');
    expect(cn('text-foreground', false && 'hidden', undefined)).toBe('text-foreground');
  });

  it('ThemeBridge 依据 store 切换 html.dark', () => {
    useThemeStore.setState({ mode: 'dark', followSystem: false });
    render(<ThemeBridge />);
    expect(document.documentElement.classList.contains('dark')).toBe(true);

    useThemeStore.setState({ mode: 'light', followSystem: false });
    render(<ThemeBridge />);
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('渲染带 shadcn 令牌类的元素', () => {
    render(<div className="bg-background text-foreground" data-testid="probe" />);
    expect(screen.getByTestId('probe')).toBeInTheDocument();
  });
});
