import { describe, expect, it } from 'vitest';
import type { components } from '@animetracker/api-contract';
import { toSubjectCardModel } from './model';

// 真实生成类型：OpenAPI schema 中“条目列表视图（摘要信息）”。
// 字段均为可选，因此测试可用局部字段断言映射逻辑。
type SubjectList = components['schemas']['条目列表视图（摘要信息）'];

describe('toSubjectCardModel', () => {
  it('prefers the Chinese title and preserves the original title', () => {
    expect(toSubjectCardModel({ id: 7, name: 'Sousou no Frieren', nameCn: '葬送的芙莉莲', image: '', score: 9.1, eps: 28, airDate: '2023-09-29' } as SubjectList)).toMatchObject({
      title: '葬送的芙莉莲', originalTitle: 'Sousou no Frieren', href: '/subjects/7',
    });
  });

  it('formats score, season and episode as text labels', () => {
    expect(toSubjectCardModel({ id: 7, name: 'Sousou no Frieren', nameCn: '葬送的芙莉莲', score: 9.1, eps: 28, airDate: '2023-09-29' } as SubjectList)).toMatchObject({
      scoreLabel: '9.1 分',
      seasonLabel: '2023 秋',
      episodeLabel: '全 28 集',
    });
  });
});
