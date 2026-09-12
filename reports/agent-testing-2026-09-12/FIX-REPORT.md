# Agent 测试报告修复复核

复核日期：2026-09-12（Asia/Shanghai）。基于同目录 `REPORT.md` 的 F01–F12 缺陷清单，未执行真实收藏、进度写入或压力测试。

## 已修复

| 缺陷 | 修复结果 |
|---|---|
| F01 | Business `{code,message}` 空 data 信封归一化为 `None`；收藏预览只把真实收藏对象视为已收藏，生成待确认动作。 |
| F02 | 用户端和管理端 SSE 代理延迟提交响应，只有收到首行成功数据才创建 writer；上游 4xx 继续交给统一错误处理。 |
| F03 | fallback 文本进入统一聚合缓冲区并写入历史。 |
| F04 | 能力路由测试改为当前 entry/gateway/runtime 契约，恢复全量收集。 |
| F05 | 明确“加入想看/收藏”动作保留到推荐节点；否定句不会被强制路由。 |
| F06 | 推荐工具新增年份、季度、评分、评分人数和播出状态字段，Prompt 要求重试时原样保留。 |
| F07 | compact 输出 `airDate`；只有权威显式状态可标记 FINISHED/AIRING，过去首播日期不足时返回 UNKNOWN。 |
| F09 | 答案或待确认动作持久化失败记录异常并发送 `status` 错误事件，随后仍发送 `end`。 |
| F10 | 用户端和管理端流式生成时显示“停止”并调用已有 `stop`。 |
| F11 | reasoning 分片保留词间空格，丢弃空块和完全重复 payload。 |
| F12 | 完整肯定短语先于否定词判断，“没问题”和带问号的确认可正确识别。 |

## 暂缓项

F08 的实体名称解析仍不可用：当前 Business 没有权威名称搜索接口，组合根继续 fail-closed 并返回 `entity_resolution_unavailable`。本次已修复 RAG 工具对“不可用”和“无结果”的区分；补齐 Business 名称接口后再接入 `entity_name_lookup` 并复跑在线链路。

## 验证结果

- Python Agent：`284 passed`。
- Business：`mvn -B test` 全量通过，Agent 模块 3 个 SSE 控制器回归测试通过。
- 前端：shared/client/admin typecheck 与 Vitest 全部通过；client/admin 生产构建通过。
- 本地只读健康检查：Business `/actuator/health`、Agent `/api/client/agent/health`、用户端 `:5173`、管理端 `:5174` 均返回 HTTP 200。

真实模型、Redis/Business 故障注入、确认写入幂等、断线恢复和向量召回仍属于后续集成验证范围。
