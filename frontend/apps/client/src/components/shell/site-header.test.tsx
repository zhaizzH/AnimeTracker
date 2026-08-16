import { render, screen, within } from '@testing-library/react';
import { SiteHeader } from './site-header';

it('contains only the approved primary destinations', () => {
  render(<SiteHeader />);
  const navigation = screen.getByRole('navigation', { name: '主导航' });
  expect(within(navigation).getByRole('link', { name: '首页' })).toHaveAttribute('href', '/');
  expect(within(navigation).getByRole('link', { name: '放送时间表' })).toHaveAttribute('href', '/schedule');
  expect(within(navigation).queryByText('我的追番')).not.toBeInTheDocument();
});
