import { describe, expect, it } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { SubjectInfoCards } from '@/components/subject-info-cards';

const base = { rank: 12, eps: 24, airDate: '2024-01-07T00:00:00.000Z', type: 2, collectionTotal: 3456 };

function cardValue(label: string) {
  const term = screen.getByText(label);
  return within(term.closest('div')!).getByRole('definition').textContent;
}

describe('SubjectInfoCards', () => {
  it('以 <dl> 承载 5 项信息，标题为 <dt>、值为 <dd>', () => {
    render(<SubjectInfoCards {...base} />);
    expect(document.querySelector('dl')).not.toBeNull();
    for (const label of ['排名', '集数', '放送', '类型', '收藏']) {
      expect(screen.getByText(label).tagName).toBe('DT');
    }
    expect(screen.getAllByRole('definition')).toHaveLength(5);
  });

  it('值与改动前一致：放送按本地化日期、类型走映射', () => {
    render(<SubjectInfoCards {...base} />);
    expect(cardValue('排名')).toBe('12');
    expect(cardValue('集数')).toBe('24');
    expect(cardValue('类型')).toBe('动画');
    expect(cardValue('收藏')).toBe('3456');
    // formatDate 输出随运行环境时区变化，不锁具体串，只锁非占位
    expect(cardValue('放送')).not.toBe('—');
  });

  it('缺值显示 —：rank 0 与无放送日期', () => {
    render(<SubjectInfoCards {...base} rank={0} airDate={null} />);
    expect(cardValue('排名')).toBe('—');
    expect(cardValue('放送')).toBe('—');
  });

  it('未映射枚举保留原始码 未知(n)，不与缺值的 — 混淆', () => {
    render(<SubjectInfoCards {...base} type={9} />);
    expect(cardValue('类型')).toBe('未知(9)');
    expect(cardValue('类型')).not.toBe('—');
  });

  it('统计值 0 原样显示 0，不被吞成 —', () => {
    render(<SubjectInfoCards {...base} eps={0} collectionTotal={0} />);
    expect(cardValue('集数')).toBe('0');
    expect(cardValue('收藏')).toBe('0');
  });
});
