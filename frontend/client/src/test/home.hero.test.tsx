import { describe, it, expect, vi } from 'vitest';
import { render, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Home from '../pages/Home';
import './matchMedia';

vi.mock('@shared', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@shared')>();
  return {
    ...actual,
    subjectsApi: {
      ...actual.subjectsApi,
      list: vi.fn().mockResolvedValue({ content: [], total: 0 }),
      schedule: vi.fn().mockResolvedValue({
        content: [1, 2, 3].map((i) => ({
          id: i, name: `anime${i}`, nameCn: null, image: '',
          score: 8, eps: 12, airWeekday: 4, collectionTotal: 100,
        })),
        total: 3, page: 1, size: 50,
      }),
    },
    useBootstrapAuth: () => {},
    useThemeStore: () => 'light',
    resolveMode: () => 'light',
  };
});

const renderHome = async () => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={qc}><MemoryRouter><Home /></MemoryRouter></QueryClientProvider>);
  for (let i = 0; i < 30 && !document.querySelector('.od-hero__slide'); i++) {
    await act(async () => { await new Promise((r) => setTimeout(r, 20)); });
  }
};

const activeTitle = () =>
  document.querySelector('.od-hero__slide.is-active .od-hero__title')?.textContent;

describe('Home hero 自动轮播', () => {
  it('真实计时下按 1→2→3 连续切换', async () => {
    await renderHome();
    expect(activeTitle()).toBe('anime1');
    await new Promise((r) => setTimeout(r, 5500));
    await act(async () => {});
    expect(activeTitle()).toBe('anime2');
    await new Promise((r) => setTimeout(r, 5000));
    await act(async () => {});
    expect(activeTitle()).toBe('anime3');
  }, 20000);
});
