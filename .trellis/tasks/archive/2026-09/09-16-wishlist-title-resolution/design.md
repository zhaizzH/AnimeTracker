# 技术设计：按标题安全加入想看

## 1. 边界与目标

本任务只修改 Agent 的单个标题加入想看链路，以及与该链路绑定的 Redis 待处理状态。Business 现有搜索、批量权威回查和收藏写入接口作为事实来源，不新增数据库表、不修改 `/api/client/subjects` 列表接口，也不改变已有多番剧推荐收藏流程。

现有 `preview_add_to_wishlist(subjects)` 继续服务于“把推荐结果中的多部番剧加入想看”；单个标题请求使用独立的确定性解析入口，避免把标题解析顺序和候选来源交给模型自由决定。

## 2. 数据流

```text
用户单标题请求 / 显式 subjectId
  -> gateway 路由 recommend_agent
  -> 单标题确定性解析入口
       -> 显式 subjectId: 跳过名称搜索
       -> 否则 GET /api/client/subjects/search?q=<原始标题>
       -> 成功有结果：安全归一化 + 唯一精确匹配
            -> 唯一精确：进入权威校验
            -> 多个或仅包含候选：保存 SUBJECT_RESOLUTION，不回退 RAG
            -> 成功空结果：复用 rag_search_subjects 对应的 RAG 用例
       -> 候选 subjectId 去重
       -> POST /api/client/subjects/batch(excludeCollected=false)
       -> 过滤 active=true、type=2、nsfw=false
       -> 0 个：明确无匹配，停止
       -> 1 个：进入既有 wishlist preview
       -> 多个：保存 SUBJECT_RESOLUTION，展示候选并停止
  -> 用户明确确认
  -> 既有 ADD_TO_WISHLIST 执行工具
  -> Business 幂等写入
```

Business 搜索返回错误、超时、未解包响应或错误结构时，解析入口直接返回可解释的错误；只有成功响应且候选集合为空时才进入 RAG。RAG 无结果、不可用或返回多个未能唯一确认的候选时，不创建 wishlist 预览。

## 3. 检索与匹配

### 3.1 Business 首查

- 使用现有 `BusinessGateway.search_subjects(query, token, size)`，请求 `GET /api/client/subjects/search`，查询词保留用户原始标题，仅做外围空白清理。
- 结果中的 `id`、`name`、`nameCn` 是标题候选；`/search` 不返回别名，因此别名命中由 RAG 的真实 `aliases` 证据承担。
- 对用户输入和候选标题使用同一安全归一化函数：Unicode NFKC、大小写折叠、连续空白折叠、首尾空白清理和安全标点处理。
- 不把“第二季/第2季/2nd season/II”等语义转换写进归一化；只有真实返回的标题或别名可以命中。
- Business 返回多行时只保留归一化后的唯一精确命中；子串结果不能自动选中。
- Business 成功返回非空但没有唯一精确命中时，保留安全候选并进入 `SUBJECT_RESOLUTION`；不能因为没有精确命中就把非空结果当作空结果回退 RAG。

### 3.2 RAG 回退

- 复用 `rag_search_subjects` 已使用的 `RetrieveSubjectsUseCase`，不复制检索、权威回查或 Evidence 逻辑。
- RAG 查询传原始标题作为 `semantic_query`，不传 `entity_name` 或 `entity_kind`，避免进入当前未接入的实体名称解析器。
- 只读取真实返回中的 `subjectId`、标题字段和 `aliases`；相似度最高但没有唯一标题/别名精确命中的候选不能自动进入预览。
- 已有 RAG 的 Business fallback、`available=false` 和 `reason` 语义保留；外层不能把不可用伪装成正常空结果。

### 3.3 权威校验

- 所有待进入预览的候选先调用 `POST /api/client/subjects/batch`，请求体为 `{subjectIds, excludeCollected:false}`。
- 只接受 `active=true`、`type=2`、`nsfw=false` 的 `items`；`missingIds` 和 `filteredIds` 不进入后续状态。
- 收藏状态不在解析阶段处理，由现有预览逻辑检查；这样不会静默覆盖或改变用户已有收藏。

## 4. 待处理状态与来源绑定

在现有 `PendingAction` 判别联合中新增 `SUBJECT_RESOLUTION`：

- `userId`、`expiresAt`、原始查询；
- 去重后的权威候选列表：`subjectId`、规范显示名、匹配来源/类型；
- 使用现有 Agent Redis 待确认键和 600 秒 TTL，不新增存储系统。

多候选时只保存此状态，不保存 `ADD_TO_WISHLIST`。选择工具只接受注入的 `SUBJECT_RESOLUTION`，按序号或归一化后的唯一名称从服务端候选中选择；模型不能提交任意 `subjectId`。选择后重新做 `/batch` 校验，再调用现有预览逻辑并将状态替换为 `ADD_TO_WISHLIST`。

状态绑定规则：用户不匹配、过期、候选不存在、名称选择不唯一或新查询与原始查询无关时，拒绝复用并清理状态。成功生成 wishlist 预览、取消和无关新查询都清理 `SUBJECT_RESOLUTION`。

## 5. Agent 组合与兼容性

- `recommend_agent` 显式注册单标题解析/选择入口，并保留现有推荐、收藏读取和 wishlist 工具。
- `gateway_router` 对 `SUBJECT_RESOLUTION` 的候选选择请求确定性路由到 `recommend_agent`；明确确认只能对 `ADD_TO_WISHLIST` 生效，不能把候选选择误当成写入确认。
- `run.py` 的待处理上下文增加候选状态展示，但不向模型暴露可自行改写的执行参数。
- `parse_pending_action_json` 继续使用判别联合；现有 `COLLECTION_PROGRESS_UPDATE` 和 `ADD_TO_WISHLIST` JSON 保持兼容。
- 不改 Business API、数据库 Schema、前端 API 或多番剧推荐收藏协议。

## 6. 错误与回滚

- 检索接口基础设施错误：返回错误语义，不回退 RAG，不创建状态。
- 两级检索无唯一有效候选：返回“没有找到匹配项”，不预览、不写入。
- Redis 待处理状态保存失败：不得宣称候选或预览已持久化；沿用现有状态错误事件。
- 无数据库迁移。回滚只需回滚 Agent 代码；已存在的 `SUBJECT_RESOLUTION` 状态在旧版本无法解析时按既有损坏/未知状态安全清理，不会触发写入。

## 7. 可观测性与隐私

记录稳定的检索阶段和结果类别（Business 命中、RAG 回退、无结果、候选歧义、权威过滤、后端错误），不记录完整用户标题、完整模型回答、token 或工具参数。沿用现有 trace id 和工具状态事件。
