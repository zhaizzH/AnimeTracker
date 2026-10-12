import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import NotFound from '@/pages/NotFound';

// 路由表里 `*` 指向本页（client/src/router.tsx）；这里固定该叶子路由，
// 断言页面自身渲染与两个跳转目标的 href，不重复覆盖已在 typecheck/构建期生效的懒加载接线。
function renderNotFound() {
  return render(
    <MemoryRouter initialEntries={['/definitely-not-a-page']}>
      <Routes>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('404 页面', () => {
  it('渲染 404 标识与说明文案', () => {
    renderNotFound();
    expect(screen.getByText('404')).toBeInTheDocument();
    expect(screen.getByText(/页面可能已被移动或不存在/)).toBeInTheDocument();
  });

  it('提供指向首页与番剧列表的导航链接', () => {
    renderNotFound();
    expect(screen.getByRole('link', { name: /返回首页/ })).toHaveAttribute('href', '/');
    expect(screen.getByRole('link', { name: /浏览番剧/ })).toHaveAttribute('href', '/anime');
  });
});
