/** 后端 409「同一会话已有 run 在跑」的结构化判据；调用方不需要解析文案。 */
export interface RunConflict {
  /** 后端 data.active_run_id；缺失时只能等待或取消。 */
  activeRunId: string | null;
  status: string | null;
}

/** 后端信封是 `{code, message, data}`；不管 body 还是已摊平的 data 都能识别。 */
export function asRunConflict(err: unknown): RunConflict | null {
  const error = err as { status?: unknown; data?: unknown; body?: unknown } | null;
  if (!error || typeof error !== 'object' || error.status !== 409) return null;
  const raw = (error.data ?? error.body) as { active_run_id?: unknown; data?: unknown } | null | undefined;
  // 先认顶层 active_run_id；摊平后的 data 本身也可能带 data 键，只信信封才再剥一层。
  const data = (raw && typeof raw === 'object' && !('active_run_id' in raw) && 'data' in raw ? raw.data : raw) as
    | { active_run_id?: unknown; status?: unknown }
    | null
    | undefined;
  return {
    activeRunId: typeof data?.active_run_id === 'string' ? data.active_run_id : null,
    status: typeof data?.status === 'string' ? data.status : null,
  };
}
