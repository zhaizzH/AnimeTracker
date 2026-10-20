# 优化项 4: agent ↔ business 契约测试

## Goal

基于 business 的 OpenAPI 导出建立契约测试。在 backend/agent/tests/contracts/ 下新增三类：(1) HTTP 契约：断言 business_http.py 所有 request() 调用的路径和字段在 OpenAPI 里有定义；(2) SSE 帧契约：state 字段取值域、result=error vs state=error、is_end 帧序；(3) previewId 写协议契约：Redis key 格式、TTL、确认时 payload 与 preview 版本绑定。CI 必跑。完成信号：business 改字段名 agent 测试红；agent 改路径拼写测试红。

## Requirements

- TBD

## Acceptance Criteria

- [ ] TBD

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
