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
