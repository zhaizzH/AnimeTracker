import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TagChip, tagChipClass } from '@/components/TagChip';

// 索引页与详情页共用这一份样式；此处锁住胶囊的语义，防止单侧改样式后两页漂移
describe('TagChip 样式契约', () => {
  it('未选中：胶囊外形 + 悬浮态', () => {
    const cls = tagChipClass(false);
    for (const token of ['rounded-full', 'border', 'px-3', 'py-1', 'text-xs', 'hover:bg-accent']) {
      expect(cls).toContain(token);
    }
    expect(cls).not.toContain('bg-primary');
  });

  it('选中：用主题 token 反白，而非硬编码颜色', () => {
    const cls = tagChipClass(true);
    for (const token of ['border-primary', 'bg-primary', 'text-primary-foreground']) {
      expect(cls).toContain(token);
    }
  });

  it('外部 className 可追加且不覆盖基础胶囊样式', () => {
    const cls = tagChipClass(false, 'mt-2');
    expect(cls).toContain('mt-2');
    expect(cls).toContain('rounded-full');
  });
});

describe('TagChip 交互', () => {
  it('aria-pressed 反映选中态，点击回传事件', async () => {
    const onClick = vi.fn();
    const user = userEvent.setup();
    render(<TagChip selected onClick={onClick}>恐怖 (12)</TagChip>);

    const chip = screen.getByRole('button', { name: '恐怖 (12)' });
    expect(chip).toHaveAttribute('aria-pressed', 'true');

    await user.click(chip);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('默认 type=button，不会误触发表单提交', () => {
    render(<TagChip>科幻</TagChip>);
    expect(screen.getByRole('button', { name: '科幻' })).toHaveAttribute('type', 'button');
  });
});
