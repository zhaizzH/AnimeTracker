# 实体名称解析接线(跨层)

## Goal

当前 entity_name_lookup=None，任何按人物/角色/声优名称的检索都返回 entity_resolution_unavailable；RedisEntityNameLookup 为死代码。按 spec 目标经 Business typed resolver 把名称解析为本地实体ID再接 /resolve 关系扩展。需 Business 侧支持，跨层任务。

## Requirements

- TBD

## Acceptance Criteria

- [ ] TBD

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
