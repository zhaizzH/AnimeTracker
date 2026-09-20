# 按标题安全加入想看

## Goal

让用户通过单个番剧标题请求“加入想看”时，系统能够安全解析到正确条目，并始终经过预览和明确确认，避免因 RAG 名称解析不可用而错误地要求用户提供 ID，或把相似作品误加入收藏。

## Background

- 当前客户端推荐 Agent 只有 `rag_recommend_subjects`，单个标题请求没有确定性的 Business 优先解析链路。
- `GET /api/client/subjects/search` 支持 `q` 参数并返回标题摘要；`GET /api/client/subjects` 本身不承担名称搜索。
- `POST /api/client/subjects/batch` 能返回权威有效条目、缺失 ID 和被过滤 ID；有效候选必须是动画、非 NSFW 且 active。
- 现有加入想看动作已经采用“预览 → 明确确认 → 幂等写入”，本任务不改变该写入边界。

## Requirements

1. 用户明确提供 `subjectId` 时，跳过名称搜索，但仍必须经过 `/api/client/subjects/batch` 权威校验后才能生成预览。
2. 用户只提供标题时，代码必须按以下顺序执行：
   1. 调用 `GET /api/client/subjects/search?q=<原始标题>`。
   2. 对标题和可信别名做安全字符归一化后进行唯一精确匹配。
   3. 只有 Business 搜索成功且没有候选时，才调用 `rag_search_subjects` 进行模糊回退；不得把接口异常伪装成无结果。
   4. RAG 回退不得自行进行“第二季”与“第 2 季”等语义转换；只使用真实标题或工具证据中的别名。
   5. 对候选调用 `/api/client/subjects/batch`，要求 `active=true`、`type=2`、`nsfw=false`，且传 `excludeCollected=false`。
3. 只有权威校验后剩余一个候选时，才进入现有加入想看预览逻辑。
4. 多个有效候选必须进入短期 `SUBJECT_RESOLUTION` 状态，展示候选并暂停；支持按序号或唯一名称选择，选择后再进入预览。
5. `SUBJECT_RESOLUTION` 绑定用户、原始查询和候选 ID，TTL 为 600 秒；成功生成预览、取消、无关新查询或过期时清理。
6. 没有唯一有效候选时，明确回复“没有找到匹配项”，不生成预览、不写入。
7. 现有“把推荐结果中的多部番剧加入想看”流程保持不变。

## Acceptance Criteria

- [ ] 标题请求首先调用 `/api/client/subjects/search`；成功空结果后才调用 RAG，且 Business 异常不会触发 RAG 回退。
- [ ] 标题/别名归一化只包含安全字符处理；非唯一精确匹配不会自动选中。
- [ ] RAG 候选必须来自 `rag_search_subjects` 的真实返回；名称解析失败、无结果或多个候选均不会产生错误预览。
- [ ] `/api/client/subjects/batch` 校验后只保留 `active=true`、`type=2`、`nsfw=false` 的候选，并使用 `excludeCollected=false`。
- [ ] 唯一有效候选进入现有预览；预览仍需用户明确确认后才写入，且不覆盖已有收藏。
- [ ] 多候选状态能按序号或唯一名称选择，并验证用户、TTL 和候选来源；无关新查询不会复用旧候选。
- [ ] 直接提供 `subjectId` 时跳过名称搜索但保留 `/batch` 校验和确认流程。
- [ ] 现有推荐结果批量加入想看及其回归测试保持通过。

## Out of Scope

- 不修改 Business `/api/client/subjects` 列表接口使其支持名称搜索。
- 不改变现有收藏状态枚举、幂等写入接口或“预览后确认”的安全边界。
- 不重写通用 RAG 检索算法，也不为本任务启用当前未接入的实体名称解析器。
- 不扩展现有多番剧推荐收藏流程的候选来源或交互协议。

## Open Questions

无。产品范围、匹配规则、异常策略、候选状态和确认边界已确认。

## Notes

- 本任务涉及 Agent 路由、Business 适配、Redis 待确认状态和回归测试，是复杂任务；开始实现前必须补齐 `design.md` 与 `implement.md`。
