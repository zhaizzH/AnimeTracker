/// <reference types="@testing-library/jest-dom/vitest" />
import { expect, test } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SHARED_SENTINEL } from '@shared';
test('client 可引用 shared 源码', () => {
  render(<span data-testid="x">{SHARED_SENTINEL}</span>);
  expect(screen.getByTestId('x')).toHaveTextContent('shared-ok');
});
