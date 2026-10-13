# Design — 全量文档刷新

## 1. Scope / Trigger

- Trigger：用户请求「全量更新文档」，覆盖 spec + README 全套，属跨层/基础设施文档一致性维护。`grill-with-docs` 访谈已产出决议（见下「决议台账」）。
- 本质：**文档与代码事实对齐** + 补齐缺失契约段 + 补齐缺失子模块 README。不改代码、不改 schema、不改接口契约本身。

## 2. 事实来源与校验口径

| 断言类别 | 权威来源 | 校验命令 |
|---|---|---|
| 表数量 | `docs/database/db-schema.sql` | `grep -cE '^CREATE TABLE' docs/database/db-schema.sql` → 20 |
| OpenAPI 路径数 | `docs/spec/openapi.yaml` | `grep -cE '^  /' docs/spec/openapi.yaml` → 68 |
| OpenAPI 前缀分布 | 同上 | `grep -oE '^  /api/[^/]+(/[^/]+)?' docs/spec/openapi.yaml \| sort \| uniq -c` |
| Maven 模块数 | `backend/business/pom.xml` | `grep -cE '<module>' backend/business/pom.xml` → 9 |
| Java 测试类数 | `backend/**/src/test` | `find backend -name '*Test.java' \| wc -l` → 30 |
| Python 测试用例数 | `backend/agent/tests` | `grep -rcE '^\s*def test_' backend/agent/tests \| awk -F: '{s+=$2} END{print s}'` → 525 |
| 前端测试文件数 | `frontend/**/*.test.*` | `find frontend -name '*.test.*' -not -path '*/node_modules/*' \| wc -l` → 21 |
| 前端图表库 | `frontend/admin/package.json` | `grep -E 'recharts\|echarts' frontend/admin/package.json` → recharts ^3.8.0 |
| 依赖版本 | 各 `pom.xml` / `package.json` / `pyproject.toml` | 直接读取 |
| 端口 | `application.yml` / `vite.config.mts` / README | 5173/5174/8080/8090 |

**口径规则**：易腐数字一律写作「`值`（命令 → 结果，2026-10-13）」。测试运行结果类数字（`220 passed` / `650 passed` / `525 def test_`）标注「未复核（最后实测：<提交号>）」，本任务不重跑。

## 3. 契约（本轮要加固的文档契约）

### 3.1 图表契约（admin 看板）

- **Signatures**：`frontend/admin/src/components/ui/chart.tsx` 暴露 shadcn chart 原语（`ChartContainer` 等）；`dashboard/visitors-chart.tsx` 消费 `recharts`。
- **Contracts**：admin 图表依赖 = `recharts ^3.8.0`；不存在 `echarts` / `echarts-for-react`。
- **Validation**：`grep -E 'echarts' frontend/admin/package.json` 必须为空。
- **Wrong vs Correct**：Wrong = 文档写「ECharts 6 + echarts-for-react 3」；Correct = 文档写「Recharts 3（经 shadcn chart 原语）」。

### 3.2 前端外壳契约（shared vs app-local）

- **契约**：不存在可安装的 `@efferd/app-shell-*` 包；`@efferd` 是 `components.json` 的 shadcn registry 源。外壳是本地代码：client `client/src/components/app-shell.tsx` 的 `AppShell`；admin `admin/src/layouts/AdminLayout.tsx`。
- **Validation**：`frontend/README.md` 不得出现「`@efferd/app-shell-2/-5`」作为依赖的说法，须与 `.trellis/spec/frontend/index.md` 一致。

### 3.3 admin 部署契约（替代对未跟踪文件的引用）

- **协议/契约**：admin 与 client 同域不同端口/路径，由反向代理承载；前端 `baseURL` 固定 `/api`，前端不直连 Agent。
- **Env keys**：`AT_AUTH_COOKIE_SECURE`（HTTP 本地开发须为 `false`）；`MINIO_PUBLIC_BASE_URL`（图片公开前缀）。
- **Validation**：`.trellis/spec/frontend/directory-structure.md` 不再把 `docs/deploy/nginx/animetracker.conf` 当唯一权威，改为描述契约 + 注明本地产物示例（未入库）。
- **Wrong vs Correct**：Wrong = 「admin 部署权威见 `docs/deploy/nginx/...`」（未跟踪文件）；Correct = 描述契约 + 「本地产物示例见 `docs/deploy/`（未入库）」。

### 3.4 本地产物边界契约

- **契约**：`docs/deploy/`、`docs/superpowers/`、`docs/api/` 为 local-only，未入库（`.gitignore:140-150`）。README 必须如实表达「本地产物」而非「不存在」。
- **Validation**：`git ls-files docs/deploy` 为空；`.gitignore` 含 `docs/deploy`。

## 4. Validation & Error Matrix（文档校验）

| 条件 | 判定 | 处置 |
|---|---|---|
| 文档内链目标不存在 | FAIL | 修链或删链（如 `docs/conventions/`） |
| 数值与校验命令不符 | FAIL | 改文档 + 附命令与日期 |
| spec 引用被 gitignore 的文件作为权威 | FAIL | 改为描述契约 + 注明本地产物 |
| 测试数无实测依据 | WARN | 标「未复核 + 最后实测提交号」 |
| 术语与 GLOSSARY 不一致 | FAIL | 对齐 GLOSSARY |
| 「待补充」条目已被解决 | FAIL | 删除或更新 |

## 5. Good / Base / Bad

- **Good**：文档每处易腐断言都带可复现命令与日期；死链清零；子包 README 齐备；spec 不依赖未跟踪文件。
- **Base**：漂移修完、链接可用、数字正确，但部分易腐数字未附命令（低于目标但不阻塞）。
- **Bad**：引入新断言却无出处；把「未复核」测试数写成当前通过数；spec 继续引用 `docs/deploy/`。

## 6. Tests Required（校验断言点）

本任务为文档任务，「测试」= 可复现的校验命令，逐条断言：

- AT1 `grep -cE '^CREATE TABLE' docs/database/db-schema.sql` == 20。
- AT2 `grep -cE '^  /' docs/spec/openapi.yaml` == 68；前缀分布与 `docs/README.md` 表一致。
- AT3 `grep -E 'echarts' frontend/admin/package.json` 无输出；文档图表库表述与之一致。
- AT4 `frontend/README.md` 无 `@efferd/app-shell` 依赖表述。
- AT5 `docs/conventions` 在全部文档中零命中。
- AT6 全仓文档内链脚本检查无死链（相对路径目标存在）。
- AT7 三份子包 README 存在且被 `frontend/README.md` / root README 引用。
- AT8 `.trellis/spec/frontend/directory-structure.md` 不含对 `docs/deploy/nginx/animetracker.conf` 的权威引用。

## 7. 决议台账（grill 产出）

| # | 决议 |
|---|---|
| Q1 | README 全套 + spec 漂移修正；glossary/ADR 仅在产出新条目时新增 |
| Q2/Q5 | 7 段契约深度，仅施加于存在契约缺口/漂移的主题 |
| Q3 | `docs/deploy/` 记为 local-only 部署套件；不解除 gitignore |
| Q4 | 建 Trellis 任务 + 轻量验证（不重跑测试） |
| Q6 | 易腐数字附验证命令 + 日期 |
| Q7 | 单任务 + 两次提交 |
| Q8 | 重写并复核「待补充」清单 |
| Q9 | 新建 frontend client/admin/shared 三份子包 README |
| Q10 | 测试数标「未复核 + 最后实测提交号」 |
| Q11 | `项目复盘.md` 仅事实复核 |
| Q12 | 图表库以代码为准 = Recharts 3 |
| Q13 | spec 引用改为描述契约 + 注明本地产物 |

## 8. 风险与回滚

- 风险：`Edit` 对混合换行 spec 文件放大 diff（C4）→ 优先整体重写语义一致段落，必要时控制改动行数并在提交信息注明。
- 风险：审计结论有误 → 每条改动前用第 2 节命令自查，不盲信。
- 回滚：两次独立提交，任一提交可单独 `git revert`。
