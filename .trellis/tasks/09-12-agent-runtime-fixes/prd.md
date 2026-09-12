# 修复 Agent 运行时测试问题

## Goal

根据 2026-09-12 Agent 模块测试报告，修复已复现的运行时缺陷和失效的测试门禁，使 Python Agent、Business 代理层与两个前端的行为契约一致。

## Confirmed Problems

- 收藏预览收到 Business 成功信封但缺少 data 时，被 Python 适配器误判为“已收藏”，不会生成待确认动作。
- 直接访问 Python Agent 的合法令牌错误是 404/422；经 Business /api/client/agent/stream 时同类请求被错误改成 401。
- SSE 没有流式答案时的 fallback 没有写入最终聚合答案；答案或会话保存异常被静默吞掉。
- 运行时能力测试仍导入已经不存在的 _capability_agent 等符号；reasoning 分片逐段 strip() 会吞掉词间空格。
- “没问题”被否定词规则误判；推荐工具无法保留年份、季度、评分、播出状态等结构化约束；紧凑证据缺少 airDate 且把未来剧集标记为已完结。
- RAG 不可用时返回空列表，调用方无法区分“无结果”和“解析服务不可用”；主程序没有注入实体名称查询器；流式页面没有使用已有的停止接口。

## Requirements

1. 修复 Business envelope 解包和收藏状态判断：缺少 data 的成功信封必须按“未收集”处理，并覆盖回归测试。
2. 让 Business SSE 在上游 401/403/404/429 和参数校验错误时保留正确 HTTP 语义；正常 SSE 数据格式与现有客户端兼容。
3. 保证 fallback 答案参与聚合和持久化；保存失败必须可观测并返回失败状态，仍安全结束流。
4. 更新失效测试到当前 graph/runtime 契约，保留 reasoning 空格，并修复显式确认和“搜索后执行”意图的确定性路由。
5. 为推荐用例增加可选结构化过滤条件；证据 compact 输出 airDate 和明确的播出状态，日期不足时为 UNKNOWN；RAG 不可用返回带原因的结构化结果。
6. 前端在流式状态显示停止操作，并为上述跨层行为补充最小回归测试；实体名称查询器仅在 Business 提供权威接口后接入，本任务保留不可用原因，避免伪造“无记录”结论。

## Constraints

- 不修改模型训练或外部数据源，不执行真实收藏写入、发布或压力测试。
- 兼容现有 API 字段和 SSE 事件名；只扩大可选请求字段，不破坏旧调用方。
- 测试账号只用于本地验证，不写入源码、任务工件或报告。

## Acceptance Criteria

- [x] Python Agent 全量 pytest 通过，包含修复后的能力路由/运行时测试。
- [x] Business mvn -B test 通过，并有上游错误映射的回归覆盖。
- [x] shared/client/admin 的 typecheck、Vitest 通过；前端停止按钮在流式中可用。
- [x] 空 data 信封生成待确认收藏动作；直接 Python 与 Business 代理返回一致的 4xx 类别。
- [x] fallback 文本被保存；保存异常有日志/失败事件；推荐过滤、airDate/UNKNOWN、RAG 不可用原因均有测试。

实体名称查询器因当前 Business 没有可调用的权威名称搜索接口而暂缓；上线前需补齐接口并复跑名称解析链路。
