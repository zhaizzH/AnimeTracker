import { afterEach, describe, expect, it } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import NotFound from './NotFound';

// admin 的 vitest.setup.ts 不注册自动 cleanup（无 globals），须在本文件显式清理，
// 否则第二个用例会命中前一个用例遗留的 DOM，role 查询出现重复匹配。
afterEach(cleanup);

// 路由表里 `*` 指向本页（admin/src/router.tsx）；这里固定该叶子路由，
// 断言页面自身渲染与两个跳转目标的 href（均为绝对路径，避免嵌套路由下解析歧义）。
function renderNotFound() {
  return render(
    <MemoryRouter initialEntries={['/definitely-not-a-page']}>
      <Routes>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('管理端 404 页面', () => {
  it('渲染 404 标识与说明文案', () => {
    renderNotFound();
    expect(screen.getByText('404')).toBeInTheDocument();
    expect(screen.getByText(/页面可能已被移动或不存在/)).toBeInTheDocument();
  });

  it('跳转目标指向面板内的可用页面，而非回登录页或跨应用前台', () => {
    renderNotFound();
    expect(screen.getByRole('link', { name: /返回面板/ })).toHaveAttribute('href', '/dashboard');
    expect(screen.getByRole('link', { name: /番剧管理/ })).toHaveAttribute('href', '/subjects');
  });
});
