import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeToggle } from './theme-toggle';

it('stores the selected dark theme and updates the document', async () => {
  const user = userEvent.setup();
  render(<ThemeToggle initialMode="system" />);
  await user.selectOptions(screen.getByLabelText('主题'), 'dark');
  expect(document.documentElement.dataset.theme).toBe('dark');
  expect(document.cookie).toContain('at-theme=dark');
});

it('keeps a saved theme cookie untouched on mount and reflects it in the select', () => {
  document.cookie = 'at-theme=; Max-Age=0';
  document.cookie = 'at-theme=dark; Path=/; SameSite=Lax';
  render(<ThemeToggle initialMode="system" />);
  expect(screen.getByLabelText('主题')).toHaveValue('dark');
  expect(document.documentElement.dataset.theme).toBe('dark');
  expect(document.cookie).toContain('at-theme=dark');
  expect(document.cookie).not.toContain('at-theme=system');
});
