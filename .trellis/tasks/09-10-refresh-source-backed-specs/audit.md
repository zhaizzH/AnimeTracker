# 规范审计记录

日期：2026-09-10。起始 HEAD：e3db80d8，工作区干净。范围由用户确认：全部 backend/frontend/guides 规范。实际写入仅规范及本任务资料。

## 方法与裁决

用户指定 grill-with-docs，其 domain-modeling 依赖缺失；用户同意以 grilling + trellis-spec-bootstrap 推进。已确认的文档原则：当前源码优先、已知缺陷单独说明、历史运行记录注明日期、实际通过的测试才作为执行证据。没有剩余需要用户裁决的设计分支。

直接读取源码、配置和测试完成审计；本次未使用代码图服务、未连接运行数据库、未改业务行为。

## 覆盖矩阵

| 规范范围 | 核对依据 | 处理 |
|---|---|---|
| backend/index、quality | CI、Agent 测试目录、实际 pytest | 去除“仅导入指标测试”，记录收集失败及隔离测试结果 |
| backend/agent、新增 runtime | graph、admin/tools、client 节点、Prompt repository、runtime、chat streaming | 补角色能力、缓存生效、reasoning 空格和历史保存边界 |
| backend/rag | main、retrieval、use_case、gate、SeasonUtil | 补名称解析缺口、画像版本、季度偏差、状态推断、重复 ID 与 CLI 环境加载 |
| backend/database、directory | importer repository、backfill、application.yml、git ls-files、Schema/迁移路径 | 修正旧 subject_credit 仍写入，补 backfill 目录；保留配置绑定及迁移约束 |
| backend/errors、logging | BusinessGateway、GlobalExceptionHandler、observability、streaming | 明确错误脱敏与状态丢失缺口、哈希边界、日志白名单限制 |
| frontend/index、hooks、types、quality | shared SSE/Hook/types、client/admin 聊天组件、package.json、Vite、CI | 补 thinking 展示、end 与错误事件限制；保留现有 CI 分层 |
| frontend/directory、components、state | workspace manifests、SubjectCard、main、guards、theme、Profile、ProgressPreviewModal、AnimeIndex、Import | 现有归属/鉴权/主题/缓存债务仍符合代码，保留 |
| guides/index、cross-layer、reuse | 全链路、OpenAPI、shared HTTP/coordinator、各层所有者 | 增加运行契约导航和跨层排障；保留复用原则 |

## 验证

- `python .trellis/tasks/09-10-refresh-source-backed-specs/validate_specs.py`：19 份 spec，30 个本地 Markdown 链接，26 个显式仓库根路径引用，0 错误；检查各层 index 覆盖全部主题。
- `git diff --check`：通过。CRLF 转换提示不影响内容校验。
- Agent `.venv` 完整 `python -m pytest -q`：收集失败，test_capability_route.py 导入缺失的 _capability_agent。
- 诊断性 `python -m pytest -q --ignore=tests/agent/test_capability_route.py`：271 passed；不是全量通过。
- 未运行 Maven、前端构建或真实模型回放，本次无产品源码变化。

引用检查仅覆盖静态本地链接及明确的仓库根源码路径，不证明全部运行行为；角色、缓存和错误语义另由源码阅读核对。历史 275 passed 不再作为当前基线。

## 后续产品工作（本任务未修改）

恢复能力测试与源码一致性；按角色审查能力自述；修复 reasoning chunk 空格和日期依赖；接通实体名称解析；统一季度/播出状态；保留模型工具层错误状态。应作为代码任务分别验证，而非把缺陷写成推荐模式。
