# v1 灰度与回滚确认

确认日期：2026-09-09（UTC+8）

## 结果

- 24 小时小流量灰度观察：通过。
- 异常回切 release 与功能开关确认：通过。
- 当前 v1 `search_index_release` 保持 `ACTIVE`；未执行旧索引、旧 Vector Set 或旧表清理。

## 证据边界

本记录依据本次会话中用户对已完成 24 小时灰度观察与回滚确认的明确反馈；不补写未提供的请求量、错误率、P95 或告警数值。运行态详细数据仍以 [phase8-live-runtime-audit.md](../phase8-live-runtime-audit.md) 和 v1 五份 gate 报告为准。

