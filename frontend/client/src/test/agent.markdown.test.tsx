import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import AgentMarkdown from '../components/AgentMarkdown';

describe('AgentMarkdown', () => {
  it('将 GFM 表格渲染为可横向滚动的语义表格', () => {
    render(
      <AgentMarkdown>{`| 番剧 | 状态 |
| --- | --- |
| 尼古喵喵 | 在看 |`}</AgentMarkdown>,
    );

    const table = screen.getByRole('table');
    const scrollRegion = screen.getByRole('region', { name: '表格，可横向滚动' });

    expect(table).not.toBeNull();
    expect(scrollRegion.querySelector('table')).toBe(table);
  });
});

