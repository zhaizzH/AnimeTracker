# 优化项 2: PendingAction 生命周期管理器

## Goal

把 ContextVar/Redis/LangGraph state 三层同步显性化为 PendingActionLifecycle 类，提供 set/replace/clear/get 四个方法。工具代码不再直接调 emit_pending_action_* 或 InjectedState("pending_action")，统一走 lifecycle 入口。pending_action.py 顶部补 docstring 讲清三层设计。完成信号：3 个写业务工具不再出现 emit_pending_action_*；新增 PendingAction 子类只需改 2 个文件（子类定义 + union 注册）。

## Requirements

- TBD

## Acceptance Criteria

- [ ] TBD

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
