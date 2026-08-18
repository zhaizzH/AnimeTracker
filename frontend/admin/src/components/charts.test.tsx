import { expect, test, vi, afterEach } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { BarChart } from './charts';

afterEach(() => cleanup());

vi.mock('echarts-for-react', () => ({ default: ({ option }: { option: unknown }) => <div data-testid="chart" data-option={JSON.stringify(option)} /> }));

test('BarChart 渲染并透传 option 数据', () => {
  render(<BarChart title="收藏类型" data={[{ label: '想看', value: 3 }]} />);
  expect(screen.getByTestId('chart').dataset.option).toContain('想看');
});
