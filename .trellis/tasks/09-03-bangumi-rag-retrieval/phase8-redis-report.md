# Phase 8 Redis/RediSearch 验证报告

日期：2026-09-05（继续验证）

## 验证范围

- 使用 `backend/agent/.env` 中的 Redis 配置连接本机服务；密码未写入报告。
- 未写入业务键，也未修改现有索引或别名。
- 验证 RAG 索引器所依赖的 RediSearch 命令，而不是仅验证 Redis TCP 可达。

## 结果

| 检查项 | 结果 |
|---|---|
| Redis PING | 通过 |
| Redis 版本 | `8.8.0` |
| 已加载模块 | 仅 `vectorset` |
| `FT._LIST` | 失败：`unknown command` |
| `FT.SEARCH` | 失败：`unknown command` |
| `FT.CREATE` | 失败：`unknown command` |

## 本机运行时复核

- Windows 环境未发现 Docker、Redis Stack、Redis Enterprise 或 `redis-server`/`redis-cli` 可执行入口，无法在当前工作区直接启动带 RediSearch 的替代实例。
- 运行 `jobs.indexer.gate` 读取当前任务报告目录时，五份报告均缺失，gate 明确返回 `gate=FAIL`；未执行 `--activate`，因此没有写入 alias 或索引。

## 结论

当前服务是可用的普通 Redis，但不是现有 RAG 索引器所需的 RediSearch/Redis Stack 实例。`jobs.indexer`、`RedisEntityNameLookup` 和版本化索引别名均使用 `FT.CREATE`、`FT.SEARCH`、`FT.ALIASUPDATE` 等命令；在当前实例上不能构建或发布 RAG 索引。

这不是应用代码故障，也不应通过引入 Neo4j、Elasticsearch 或 Milvus 绕过。应先提供启用 RediSearch 的 Redis Stack/Redis Enterprise 实例，或明确批准改写索引适配器；在此之前保持 `RAG_ENABLED=false`。提供实例后，先运行 `FT.CREATE`/`FT.SEARCH`/`FT.ALIASUPDATE` 探针，再生成五份同一 `indexVersion` 的 gate 报告，最后才允许人工确认 alias 激活。

## 未覆盖

- RediSearch 实例上的真实 subject/entity 索引写入、BM25+KNN 查询和 alias 灰度。
- DashScope embedding、MinIO 原始快照、Business/Evidence 端到端链路。
- 生产 Redis 备份、恢复与容量压测。
