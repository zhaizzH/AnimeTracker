import { render, screen } from '@testing-library/react';
import { SearchForm } from './search-form';

it('keeps search state in a shareable GET URL', async () => {
  render(<SearchForm initialQuery="" />);
  expect(screen.getByRole('search')).toHaveAttribute('action', '/discover');
  expect(screen.getByRole('textbox', { name: '搜索番剧' })).toHaveAttribute('name', 'q');
});
