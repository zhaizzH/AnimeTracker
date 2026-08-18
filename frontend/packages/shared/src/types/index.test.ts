import { expect, test } from 'vitest';
import type { ApiResult, Paged, LoginVO, SubjectListItem, CollectionVO, LogsPage, ExecuteResultVO } from './index';

test('类型与 openapi 字段逐字对齐（编译期契约）', () => {
  const login: LoginVO = { token: 't', refreshToken: 'r', user: { id: 1, username: 'u', email: 'e@x.com', role: 'USER', createdAt: '2026-01-01' } };
  expect(login.user.username).toBe('u');

  const item: SubjectListItem = { id: 1, name: 'n', score: 7.5, rank: 3, eps: 12, type: 2, airWeekday: 1, collectionTotal: 9 };
  expect(item.score).toBe(7.5);

  const res: ApiResult<Paged<CollectionVO>> = { code: 0, message: 'ok', data: { content: [], total: 0, page: 1, size: 20 } };
  expect(res.data.total).toBe(0);

  const logs: LogsPage = { content: { content: [], total: 0, page: 1, size: 20, stats: { total: 0, failedCount: 0, successCount: 0, avgDurationMs: 0 } }, total: 0, page: 1, size: 20 };
  expect(logs.content.stats.total).toBe(0);

  const exec: ExecuteResultVO = { state: 'COMPLETED', replayed: false, preview: null, succeeded: [], skipped: [], failed: [] };
  expect(exec.state).toBe('COMPLETED');
});
