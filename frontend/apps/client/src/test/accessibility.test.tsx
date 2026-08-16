import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { axe } from 'vitest-axe';
import { TestPublicShell } from './public-shell';

describe('公开应用外壳无障碍', () => {
  it('has no automated accessibility violations in the public shell', async () => {
    const { container } = render(<TestPublicShell />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
