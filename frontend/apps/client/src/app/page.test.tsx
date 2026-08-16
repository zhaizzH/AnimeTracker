import { render, screen } from '@testing-library/react';
import HomePage from './page';

it('renders the AnimeTracker product name', async () => {
  render(await HomePage());
  expect(screen.getByRole('heading', { name: '番组手账' })).toBeInTheDocument();
});
