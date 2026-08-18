import { afterEach, expect, test, vi } from 'vitest';
import { render, screen, waitFor, cleanup, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProgressPreviewModal } from './ProgressPreviewModal';
import { collectionsApi } from '@shared';

vi.mock('@shared', async (io) => {
  const mod = await io<typeof import('@shared')>();
  return { ...mod, collectionsApi: { ...mod.collectionsApi,
    progressPreview: vi.fn().mockResolvedValue({ previewId: 'p1', state: 'PENDING', expiresAt: {}, weekStart: '2026-08-17', cutoffDate: '2026-08-17', items: [{ subjectId: 1, subjectName: 'A', currentEpStatus: 1, targetEpStatus: 2, completedAfterUpdate: false, suggestMarkAsWatched: false }] }),
    executePreview: vi.fn().mockResolvedValue({ state: 'COMPLETED', replayed: false, preview: null, succeeded: [], skipped: [], failed: [] }) } };
});
afterEach(() => cleanup());
test('确认执行成功后关闭并展示结果', async () => {
  render(<QueryClientProvider client={new QueryClient()}><ProgressPreviewModal open onClose={() => {}} /></QueryClientProvider>);
  expect(await screen.findByText(/A：1 → 2 集/)).toBeTruthy();
  await fireEvent.click(screen.getByRole('button', { name: /确认\s*更新/ }));
  await waitFor(() => expect(collectionsApi.executePreview).toHaveBeenCalledWith('p1'));
});
