import { describe, expect, it } from 'vitest';
import { SseError } from '../sse';
import { asRunConflict } from './conflict';

/** 后端 409 统一信封（Java 代理层）。 */
const ENVELOPE = {
  code: 409,
  message: '当前会话已有进行中的对话',
  data: { active_run_id: 'run-active', status: 'running', capabilities: ['interrupt'] },
};

describe('asRunConflict', () => {
  it('识别 SSE 通路：SseError.body 里的统一信封', () => {
    const err = new SseError('Agent 流式请求失败（409）', { status: 409, body: ENVELOPE });

    expect(asRunConflict(err)).toEqual({ activeRunId: 'run-active', status: 'running', capabilities: ['interrupt'] });
  });

  it('识别 JSON 通路：toError 已把 data 摊平到 error.data', () => {
    const err = Object.assign(new Error('当前会话已有进行中的对话'), { status: 409, data: ENVELOPE.data });

    expect(asRunConflict(err)).toEqual({ activeRunId: 'run-active', status: 'running', capabilities: ['interrupt'] });
  });

  it('非 409 不是冲突', () => {
    expect(asRunConflict(new SseError('boom', { status: 500, body: ENVELOPE }))).toBeNull();
    expect(asRunConflict(new Error('当前会话已有进行中的对话'))).toBeNull();
    expect(asRunConflict(null)).toBeNull();
    expect(asRunConflict('409')).toBeNull();
  });

  it('409 但 data 缺失时仍进冲突分支，只是没有可停的 run 标识', () => {
    const err = new SseError('Agent 流式请求失败（409）', { status: 409 });

    expect(asRunConflict(err)).toEqual({ activeRunId: null, status: null, capabilities: null });
  });

  it('显式空 capabilities 是「不允许」：原样透出空数组', () => {
    const err = Object.assign(new Error('409'), {
      status: 409,
      data: { active_run_id: 'run-active', status: 'running', capabilities: [] },
    });

    expect(asRunConflict(err)?.capabilities).toEqual([]);
  });

  it('缺 capabilities 字段是「不知道」，不是「不允许」', () => {
    const err = Object.assign(new Error('409'), {
      status: 409,
      data: { active_run_id: 'run-active', status: 'running' },
    });

    expect(asRunConflict(err)?.capabilities).toBeNull();
  });

  it('capabilities 里的非字符串元素被过滤掉', () => {
    const err = Object.assign(new Error('409'), {
      status: 409,
      data: { active_run_id: 'run-active', status: 'running', capabilities: ['interrupt', 42, null] },
    });

    expect(asRunConflict(err)?.capabilities).toEqual(['interrupt']);
  });
});
