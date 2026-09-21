# Agent 配置与 env 漂移修复

## Goal

.env.example 仍含已删除的 RAG_INDEX_ALIAS(extra=forbid 会致启动失败)与过时 RediSearch 说明、缺 MODEL_ROUTE 项；画像向量 _subject_vector_lookup 用配置版本而非 active release，版本漂移时个性化静默失效。对齐 Settings 与模板，画像链改用 active release 版本。

## Requirements

- TBD

## Acceptance Criteria

- [ ] TBD

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
