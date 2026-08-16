// @vitest-environment node
// 回归测试：Client 组件会被服务端预渲染，惰性初始值读取 document 时必须安全回退。
import { renderToString } from 'react-dom/server';
import { ThemeToggle } from './theme-toggle';

it('renders on the server without a document global', () => {
  const html = renderToString(<ThemeToggle initialMode="system" />);
  expect(html).toContain('跟随系统');
});
