import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import RouteError from './error';

describe('根路由错误边界（安全错误渲染）', () => {
  it('shows the backend message when it is safe', () => {
    render(<RouteError error={new Error('接口限流')} reset={() => {}} />);
    expect(screen.getByRole('alert')).toHaveTextContent('接口限流');
  });

  it('filters diagnostic leakage from stack-trace style messages', () => {
    render(<RouteError error={new Error('java.lang.NullPointerException at top.')} reset={() => {}} />);
    expect(screen.getByRole('alert')).toHaveTextContent('服务暂时不可用');
  });
});
