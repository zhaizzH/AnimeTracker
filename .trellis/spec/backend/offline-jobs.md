# Agent 离线任务契约

> 从 [Agent 编排与流式协议](./agent-guidelines.md) 拆出（2026-10-22），因为主文件已达单文件注入上限的 82%。
> 本章覆盖 importer / indexer / backfill / scheduler 等离线链路；在线编排与流式协议仍在主文件。

## 离线任务

- importer、indexer、scheduler 使用 `python -m jobs.<name>...` 运行并返回明确退出码。
- indexer 只有显式 `--activate` 且全部报告通过时才激活 MySQL `search_index_release`。
- scheduler 使用 Asia/Shanghai 规则；仓库没有常驻宿主配置，不得假设已有 cron/systemd/容器部署。

#### Scenario: Person/Character 回填报告

##### 1. Scope / Trigger

- 触发：运行 `jobs.backfill.main --report` 或定时采集回填状态。

##### 2. Signatures

- 文本：`python -m jobs.backfill.main --report`。
- JSON：`python -m jobs.backfill.main --report-json`。
- `EntityDetailJobRepository.generate_report() -> BackfillReport`。

##### 3. Contracts

- 报告字段包含 `totalJobs/completed/pending/failed/abandoned/coveragePct/failureReasons`。
- stale 字段为 `staleEntities/staleByKind`，统计 active Person/Character 且 `detail_status <> COMPLETE` 的实体。
- 报告只读，不认领、暂停、恢复或修改任务；错误正文不得输出到 JSON。

##### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| 无任务 | 覆盖率为 0，报告仍成功生成 |
| 任务失败/放弃 | 按 `last_error_code` 聚合，不输出错误正文 |
| active 实体未完成详情 | 计入 `staleEntities` 与 `staleByKind` |
| 数据库查询失败 | CLI 返回非零退出码，不伪造空报告 |

##### 5. Good/Base/Bad Cases

- Good：调度器采集 `--report-json`，按同一时间窗口记录覆盖率和 stale 数量。
- Base：人工使用 `--report` 查看摘要。
- Bad：报告命令顺便认领任务，或把 API 错误正文写入报告。

##### 6. Tests Required

- Backfill repository 单测断言覆盖率、失败原因、stale 按实体类型聚合及 JSON 字段。
- CLI/编译检查断言 `--report-json` 可导入并返回稳定字段。

##### 7. Wrong vs Correct

```text
Wrong: 只统计 COMPLETED/TOTAL，忽略 active 实体仍处于 SUMMARY_ONLY 的 stale 状态。
Correct: 同时统计任务状态和 person/character 的 detail_status，并通过 --report-json 输出。
```

#### 离线任务最低契约

- importer CLI 的 `--mode` 为 `full|season|recent|since|sample`；`--dry-run` 只扫描，不打开数据库或写对象存储，当前仅支持 full 扫描语义。
- importer 并发 worker 上限为 10；断点由扫描 ID 的 SHA-256、offset 和最后条目共同校验，扫描结果变化时拒绝复用旧断点。
- importer 使用 Redis 锁 `animetracker:import:lock`（`SET NX EX` + 周期续期 + compare-and-del 释放）做跨进程互斥，**Redis 不可达时导入直接失败**（锁是硬依赖）；每个 worker 独立 Session，失败必须 rollback、关闭连接并返回非零结果。运行中进度计数同样在 Redis（`animetracker:import:{record_id}:done`），终态一次性回写 `import_record.subject_count`。
- indexer 报告缺失、版本不一致、契约/指标不达标时必须 fail closed；只有显式 `--activate` 且所有报告通过时才更新 MySQL `search_index_release`，旧版本投影不得先删除。
- scheduler 使用 Asia/Shanghai 的固定时刻（每日 recent、每周 since、季度 full），同一分钟同模式去重；仓库不提供常驻宿主、重叠任务终止或重启托管。
- 运行环境仅提供普通 Redis 而未加载 Vector Set 时，不能执行 `jobs.indexer`；Redis Vector Set 与 MySQL `search_document` 必须使用同一 `indexVersion`，发布指针只在 MySQL 更新。
- 以上契约的参数、退出码、报告字段或阈值发生变化时，必须同时更新本文件和 `quality-guidelines.md` 的验证清单，并补失败路径测试。

#### Scenario: recent 导入日历源失败

##### 1. Scope / Trigger

- 触发：修改 `jobs.importer.main` 的 `recent` 扫描、代理配置或导入断点/状态处理。
- 目的：避免 Bangumi 日历请求失败时把“未扫描到条目”误记为成功，导致断点无法恢复。

##### 2. Signatures

- 命令：`python -m jobs.importer.main --mode recent [--resume]`。
- 扫描源：`BangumiClient.get_calendar() -> list`（`jobs/importer/client.py` 该方法返回注解为裸 `list`，同文件邻居方法的 `list[dict]` 更精确，取值时仍需按实际结构校验）。
- 代理环境变量：`HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY` 由 `requests` 隐式遵循，importer 代码没有显式读取或校验它们；只由进程环境注入，不写入日志或任务记录。（代码中显式的只有 `BANGUMI_IMAGE_PROXY_URL`。）

##### 3. Contracts

- `recent` 必须先成功获取并去重日历 ID，再调用 `_run_batch`。
- 日历获取异常必须抛出 `RuntimeError("日历获取失败")`，由 `main()` 统一将当前 `import_record` 标为 `FAILED`，退出码为 `1`。
- 失败时不得调用 `complete_import_record(..., "COMPLETED")`，不得清除 `checkpoint_json`、累计成功/失败计数或把 `subject_count` 伪造为 0 成功。
- 成功时 checkpoint 的 `offset` 必须到达本次日历 ID 总数；已有条目可返回 `SKIPPED`，这不等于导入失败。

##### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| `get_calendar()` 返回有效列表 | 去重 ID 后执行批处理，完成时记录 `COMPLETED` |
| `get_calendar()` 超时、代理拒绝或响应异常 | 记录 `FAILED`、保留 checkpoint、返回退出码 1 |
| `--resume` 且记录为 `RUNNING/FAILED` | 校验扫描 ID SHA-256、offset 和最后 ID；不匹配则拒绝恢复 |
| 日历条目已存在且 `import_status=1` | 记录 `SKIPPED`，推进 checkpoint，不计入 failure |
| 代理不可用 | 不把空日历当作成功；错误日志只保留归一化错误类型/消息 |

##### 5. Good/Base/Bad Cases

- Good：代理可用，日历 113 条，resume 推进到 `offset=113`，所有条目已存在时状态为 `COMPLETED`、`failure_count=0`。
- Base：日历请求中断，状态为 `FAILED`，下次使用同一 checkpoint 可继续，不重复伪造成功。
- Bad：捕获日历异常后 `return 0`，让主流程把未扫描批次标记为 `COMPLETED`。

##### 6. Tests Required

- `tests/jobs/importer/test_recent_failure.py`：日历客户端抛异常时断言 `run_recent` 抛出 `RuntimeError`，消息为“日历获取失败”。
- `tests/jobs/importer` 全套：断言成功、跳过、失败计数和 checkpoint 行为不回归。
- 运行 `python -m compileall -q jobs/importer` 与 `git diff --check`。

##### 7. Wrong vs Correct

##### Wrong

```python
try:
    calendar = client.get_calendar()
except Exception:
    return 0  # main() 会错误地写入 COMPLETED
```

##### Correct

```python
try:
    calendar = client.get_calendar()
except Exception as error:
    logger.error("日历获取失败: %s", sanitize_import_error(error))
    raise RuntimeError("日历获取失败") from error
```

#### Scenario: search indexer 基础设施错误码

##### 1. Scope / Trigger

- 触发：修改 `jobs.indexer.main.run_search_batch` 的 Embedding、Redis 或任务重试处理。
- 目的：错误码必须能区分 Embedding 与 Redis 故障，避免排障时把 Embedding 网络问题误判为 Redis 故障。

##### 2. Signatures

- `run_search_batch(...) -> IndexBatchResult`：批量消费 `job` 表中 `type='SEARCH_INDEX'` 的任务，失败任务进入可重试状态。
- `SearchIndexJobRepository.mark_failed(job_id, *, error_code, error_message, retry_seconds=0, claimed_at=None) -> bool`：写入错误码并设置 `next_retry_at`。Port 定义（`app/entities/ports.py`）为 `mark_failed(job_id, *, error_code, error_message, retry_seconds) -> None`，无 `claimed_at`；实现（`jobs/indexer/search_repository.py`）更宽，引用时须注明是哪一侧。

##### 3. Contracts

- `EmbeddingUnavailable` 映射为 `EMBEDDING_UNAVAILABLE`。
- `EmbeddingRateLimited` 映射为 `EMBEDDING_RATE_LIMITED`。
- Redis 连接/超时异常映射为 `REDIS_UNAVAILABLE`。
- 上述异常都必须保持失败可重试语义；不能因为错误码分类改变而确认索引成功或激活 release。
- 其他异常保留稳定类型名，不把数据库/配置错误伪装成 Redis 故障。

##### 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| Embedding 服务不可用 | `EMBEDDING_UNAVAILABLE`、`FAILED + next_retry_at` |
| Embedding 限流 | `EMBEDDING_RATE_LIMITED`、`FAILED + next_retry_at` |
| Redis 连接或超时 | `REDIS_UNAVAILABLE`、`FAILED + next_retry_at` |
| 数据库/实体加载异常 | 使用异常类型名，不生成 Redis/Embedding 专属码 |
| 重试次数耗尽 | 由仓储层进入 `ABANDONED`，gate 必须拒绝发布 |

##### 5. Good/Base/Bad Cases

- Good：EmbeddingUnavailable 记录为 `EMBEDDING_UNAVAILABLE`，任务保留 `next_retry_at`。
- Base：Redis 写入连接失败记录为 `REDIS_UNAVAILABLE`，不写入 `search_document` 完成状态。
- Bad：对所有可重试异常统一写 `REDIS_UNAVAILABLE`，导致监控和修复方向错误。

##### 6. Tests Required

- `tests/jobs/indexer/test_main_multi_entity.py`：断言 EmbeddingUnavailable、EmbeddingRateLimited、Redis 连接失败分别产生准确错误码。
- 断言三类故障的 `IndexBatchResult` 均为 `retried=1、failed=0`，且仓储收到 `mark_failed`。
- 运行 `pytest tests/jobs/indexer tests/jobs/scheduler tests/rag` 与 `python -m compileall -q jobs/indexer`。

##### 7. Wrong vs Correct

##### Wrong

```python
code = "REDIS_UNAVAILABLE" if _is_retryable(error) else type(error).__name__
```

##### Correct

```python
if isinstance(error, EmbeddingUnavailable):
    code = "EMBEDDING_UNAVAILABLE"
elif isinstance(error, RedisConnectionError):
    code = "REDIS_UNAVAILABLE"
```
