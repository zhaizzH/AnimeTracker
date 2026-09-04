# Phase 5 indexer 接线报告

## 已完成

- `backend/agent/jobs/indexer/main.py` 新增 `run_search_batch`，生产 CLI 默认同时消费旧 `rag_index_job` 与通用 `search_index_job`；可用 `--queue legacy|search|both` 显式选择。
- 通用队列支持 `SUBJECT`、`EPISODE`、`PERSON`、`CHARACTER`，通过 `MultiEntityLoader` 加载事实、通过多实体 profile 构建文本，并在 profile hash 漂移时重新入队，不把新文本写入旧 hash。
- 新增 `backend/agent/jobs/indexer/entity_index.py`，按版本写入通用 Redis/RediSearch shadow HASH；失效实体通过 tombstone 删除后才完成任务。
- `search_index_job` 完成/失败写回增加 `claimed_at` lease 校验；tombstone 认领会更新时间、尝试次数和 claim 时间。
- 保留旧 Subject indexer 的 Redis alias 与任务状态流程；新通用 Subject 任务写入实体 shadow index，二者不互相标记状态。
- importer 在 Subject 事实事务中同时写入旧 `rag_index_job` 与通用 `search_index_job` outbox；Subject、Episode、Person、Character 均使用现有多实体 profile builder 生成 `profile_version/content_hash`。
- importer 的 `write_bundle` 行为测试已覆盖完整 Subject 导入：旧 `rag_index_job` 与 Subject、Episode、Person、Character 五类通用任务均在同一写入流程中发布；实体响应不完整时不发布对应人物/角色任务。
- Person/Character profile 的职业、别名、代表作品、登场作品和声优关系从同一事务已写入的权威表读取；persons/characters/episodes 上游响应不完整时不发布对应实体任务。
- 通用 outbox 使用 `(entity_kind, entity_id, index_version)` 幂等键；同 hash 的已完成/进行中任务不重置，失败、失效或 hash 变化任务重置为 `PENDING`。

## 验证

```text
cd backend/agent
pytest tests/jobs/indexer tests/rag/test_multi_profile.py -q --basetemp .pytest-tmp-phase5-final
59 passed
python -m compileall -q app jobs
git diff --check
```

测试覆盖四种实体成功写入、tombstone 删除、profile hash 漂移重入队和 embedding 暂时不可用时的失败/重试状态。未连接真实 MySQL、Redis 或 Embedding 服务；Phase 8 的真实基础设施门禁仍待执行。

importer outbox 补充测试：

```text
cd backend/agent
pytest tests/jobs/importer/test_search_outbox.py -q --basetemp .pytest-tmp-outbox
5 passed
```

该测试验证通用任务 SQL 写入、完成任务幂等、失败任务重试、不完整实体响应的 fail-closed 行为，以及 `write_bundle` 对五类实体任务的接线。
