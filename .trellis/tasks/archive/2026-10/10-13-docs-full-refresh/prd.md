# 全量文档刷新：spec 漂移修正 + README 全套订正与补建

## Goal

让项目全部人读文档（`.trellis/spec/**` 与 README 全套）与当前代码事实一致：修正已确认漂移、补齐存在缺口但缺失的契约段、补齐缺失的子模块 README，并把易腐数字改用「验证命令 + 核对日期」承载，避免再次无声腐化。

## Requirements

### 范围（R1）

- R1.1 更新 README 全套：`README.md`(root)、`docs/README.md`、`frontend/README.md`、`backend/README.md`、`backend/business/README.md`、`backend/agent/README.md`、`backend/agent/jobs/importer/README.md`。
- R1.2 新建三份子包 README：`frontend/client/README.md`、`frontend/admin/README.md`、`frontend/packages/shared/README.md`。
- R1.3 修正 `.trellis/spec/**`：`backend/*`、`frontend/*`、`guides/*`、`GLOSSARY.md`；仅在访谈/审计产出新术语或符合三条准入的决策时才新增 `GLOSSARY.md` 条目或 ADR，**不重写**已有 21 篇 ADR。
- R1.4 `docs/retrospective/项目复盘.md` 仅做事实复核（引用路径/命令是否仍存在），不改写观点与叙事。

### 契约深度（R2）

- R2.1 spec 的「7 段契约深度」（Scope/Trigger、Signatures、Contracts、Validation & Error Matrix、Good/Base/Bad、Tests Required、Wrong vs Correct）**只施加于存在契约缺口或漂移的主题**；契约已完整的主题只修正事实，不硬凑签名。
- R2.2 主题定位：后端 `agent-guidelines.md`、`rag-retrieval-contract.md`、`database-guidelines.md`、`error-handling.md`；前端 `component-guidelines.md`、`hook-guidelines.md`；`guides/cross-layer-thinking-guide.md`。逐一判定是否存在缺口后决定是否补 7 段。

### 易腐数字（R3）

- R3.1 每个易腐事实（表数、OpenAPI 路径数、Maven 模块数、测试类/用例数、端口、依赖版本）就地附**验证命令 + 核对日期**（本任务核对日期 `2026-10-13`）。
- R3.2 测试基线数字本任务**不重跑**测试：统一标注为「未复核（最后实测：<提交号>）」并给出验证命令，避免叠加过期数字。

### 本地产物处理（R4）

- R4.1 `docs/deploy/` 记为「local-only 部署套件」（含 nginx / systemd / 部署方案.md），修正 root README 与 `backend/README.md` 中「仓库中不存在 `deploy/` 目录」的过期陈述；**不解除 gitignore**。
- R4.2 `.trellis/spec/frontend/directory-structure.md` 中对 `docs/deploy/nginx/animetracker.conf` 的引用改为**描述契约本身**（admin 由反代按路径/端口承载、`baseURL` 固定 `/api`），并注明「本地产物示例见 `docs/deploy/`（未入库）」，不让已跟踪 spec 依赖未跟踪文件。

### 已确认漂移清单（R5，逐条修正）

- R5.1 图表库：root README + `frontend/README.md` 的「ECharts 6 + echarts-for-react 3」→ 实际为 **recharts 3.8**（经 shadcn `ui/chart.tsx` 原语消费）；以代码为准订正。
- R5.2 root README + `backend/agent/README.md` + `jobs/importer/README.md` 称 `importer.pid` / `indexer-remaining.json` 未被 gitignore 覆盖 → 实际 `.gitignore` 已忽略（并含 `import.log`）；删除该过期「待补充」项。
- R5.3 root README / `backend/business/README.md`：`docs/conventions/backend-conventions.md` 已不存在 → 移除死链，改指向 `.trellis/spec/backend/`。
- R5.4 `frontend/README.md` 称 client/admin 使用 `@efferd/app-shell-2/-5` 安装包 → 与 spec 矛盾（不存在可安装包，外壳是本地代码）；订正为本地文件路径。
- R5.5 `backend/README.md` 称数据库脚本「含两份迁移」→ 已无迁移脚本；订正为仅 `db-schema.sql`。
- R5.6 `docs/README.md` OpenAPI 前缀计数表订正：subjects 7→9、collections 8→10、me 4→5、admin 10→26、admin/agent 6→10（总 68 不变，附验证命令）。
- R5.7 `docs/README.md` 「迁移脚本使用 INFORMATION_SCHEMA 条件 DDL」过期措辞删除。
- R5.8 测试类数 31→30（root/business README）；前端测试文件 20→21（spec `frontend/quality-guidelines.md`，新增 `client/src/test/subject.info-cards.test.tsx`）。
- R5.9 `database-guidelines.md` `source_active` 出现次数 17→18（附验证命令）。
- R5.10 `agent-guidelines.md` 路径 `collection_state.py:24` 补全为 `app/agent/client/actions/collection_state.py`。
- R5.11 pytest 用例数 468→525（`backend/README.md`、`backend/agent/README.md`），按 R3.2 保留但标注核对方式与日期。
- R5.12 `backend/agent/README.md` 「待补充」列表编号 `1,3,4,5` 缺 2 → 重排。

### 一致性（R6）

- R6.1 重写并复核 root README 与 `docs/README.md` 的「待补充」清单：已解决项（deploy、迁移脚本、前端子包 README、pid/json gitignore）删除或更新；仍成立项保留并修措辞。
- R6.2 校验全部跨文档链接目标存在；新增子包 README 后更新 `frontend/README.md` 与 root README 的导航。
- R6.3 术语一致：以 `.trellis/spec/GLOSSARY.md` 为单一来源，README 用词与之对齐（Subject/Collection/CollectionType 等）。

## Constraints

- C1 文档任务：不改业务代码、不改 schema、不改接口契约本身（仅让文档与代码一致）。
- C2 不重跑测试套件；不解除任何 gitignore。
- C3 遵守 Trellis 工作流：规划产物落盘 → review gate → `task.py start` 后才实施。
- C4 前端 spec 文件存在混合 CRLF/LF，`Edit` 会重写为 LF 放大 diff——如需编辑，改动面控制在必要行。

## Acceptance Criteria

- [ ] AC1 R5.1–R5.12 全部漂移项已修正，且每条数值类改动附验证命令 + `2026-10-13` 日期。
- [ ] AC2 `frontend/client`、`frontend/admin`、`frontend/packages/shared` 三份子包 README 已创建，并被 `frontend/README.md` 与 root README 导航引用。
- [ ] AC3 契约缺口主题已按 7 段补齐（未缺口的主题在 design/implement 中说明「无缺口，仅修事实」）。
- [ ] AC4 `docs/deploy/` 在两份 README 中记为 local-only 部署套件；「不存在 deploy 目录」的过期陈述已清除；spec 不再直接依赖未跟踪路径。
- [ ] AC5 全仓文档内链无死链接（含 `docs/conventions/` 消除）。
- [ ] AC6 「待补充」清单已逐条复核重写，无自相矛盾项。
- [ ] AC7 可验证：`grep` 类计数命令与文档记载一致（openapi=68、db-schema=20、模块=9）。
- [ ] AC8 提交分为 `docs(spec): ...` 与 `docs(readme): ...` 两次。
