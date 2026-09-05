# Phase 4 人物/角色回填报告

日期：2026-09-05

## 报告契约

`jobs.backfill.repository.EntityDetailJobRepository.generate_report()` 现在同时输出：

- 任务覆盖率：总任务、完成、待处理、失败、放弃和 `coveragePct`。
- 失败原因：按 `last_error_code` 聚合，错误正文不进入报告。
- stale 数据：按 `person`/`character` 统计 `source_active=1 AND detail_status <> 'COMPLETE'` 的实体，分别输出 `staleEntities` 与 `staleByKind`。

CLI 保留 `--report` 文本输出，并新增 `--report-json`，便于定时任务采集；两者均为只读查询，不会认领、暂停或修改任务。

## 验证

```text
cd backend/agent
\.venv\Scripts\python.exe -m pytest tests/jobs/backfill/test_backfill.py -q --basetemp pytest-tmp-phase4-final
15 passed
python -m compileall -q app jobs
git diff --check
```

真实数据库回填尚未执行；报告只补齐观测契约，Person/Character 详情仍按既定限速和 checkpoint 流程渐进处理。
