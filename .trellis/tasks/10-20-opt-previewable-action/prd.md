# 优化项 3: PreviewableAction 抽象 + 三业务对齐矩阵

## Goal

先做三业务对齐矩阵：列出 wishlist/collection_type/collection_progress 在预览上限、TTL、跳过逻辑、错误处理、幂等保证上的差异，逐字段决策保留/统一。然后抽象 PreviewableAction 模板方法基类，把『预览→确认→取消』流程骨架下沉到一处。完成信号：9 个工具收敛到 3 个；新增写业务（评分/列表/删除）从改 3 文件降到改 1 文件声明 1 个子类；585 个测试全绿（不改测试，除非测试本身在测三件套复制粘贴）。

## Requirements

- TBD

## Acceptance Criteria

- [ ] TBD

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
