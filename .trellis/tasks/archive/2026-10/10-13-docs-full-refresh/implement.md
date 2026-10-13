# Implement — 全量文档刷新

> 提交 A = `docs(spec): ...`（阶段 1）；提交 B = `docs(readme): ...`（阶段 2）。两阶段各自可回滚。

## 阶段 0 — 复测事实（只读，落盘证据）

- [ ] 0.1 跑 design §2 全部校验命令，记录结果与日期 `2026-10-13`。
- [ ] 0.2 复核审计漂移清单逐条为真（R5.1–R5.12）；任一条不成立则从清单剔除并在 implement 记录。
- [ ] 0.3 校验点：命令输出与预期值一致后，才进入阶段 1。

## 阶段 1 — `.trellis/spec/**`（提交 A）

- [ ] 1.1 `backend/database-guidelines.md`：`source_active` 17→18（R5.9）并附命令。
- [ ] 1.2 `backend/agent-guidelines.md`：补全 `collection_state.py` 路径为 `app/agent/client/actions/collection_state.py`（R5.10）；判定是否存在契约缺口，若是则按 7 段补。
- [ ] 1.3 `backend/rag-retrieval-contract.md` / `backend/error-handling.md` / `backend/directory-structure.md`：判定缺口，缺则补 7 段，否则仅修事实。
- [ ] 1.4 `backend/index.md` + `quality-guidelines.md`：测试基线改「未复核（最后实测：<提交号>）」+ 命令（R3.2）。
- [ ] 1.5 `frontend/quality-guidelines.md`：测试文件 20→21（R5.8）并附命令。
- [ ] 1.6 `frontend/directory-structure.md`：移除对 `docs/deploy/nginx/animetracker.conf` 的权威引用，改为描述契约 + 注明本地产物（R4.2/Q13）。
- [ ] 1.7 `frontend/component-guidelines.md` / `hook-guidelines.md`：判定缺口，缺则补 7 段。
- [ ] 1.8 `guides/cross-layer-thinking-guide.md` / `guides/index.md`：校验链接与易腐数字口径。
- [ ] 1.9 `GLOSSARY.md`：仅当访谈产出新术语时新增条目（预计无；如无则不动）。
- [ ] 1.10 **Review gate**：`grep -rn "docs/deploy\|17 处\|20 个" .trellis/spec` 应无过期命中。
- [ ] 1.11 **提交 A**：`git add .trellis/spec && git commit -m "docs(spec): 修正漂移并补齐契约缺口"`。

## 阶段 2 — README 全套（提交 B）

- [ ] 2.1 root `README.md`：
  - [ ] 2.1.1 图表库 ECharts→Recharts 3（:62/:136）（R5.1）。
  - [ ] 2.1.2 移除死链 `docs/conventions/backend-conventions.md`（:178/:424）（R5.3）。
  - [ ] 2.1.3 `docs/deploy/` 记为 local-only 部署套件，删「不存在 deploy 目录」（:36/:441）（R4.1）。
  - [ ] 2.1.4 重写「待补充」清单（删 deploy、pid/json gitignore、前端子包 README 等已解决项）（R6.1）。
  - [ ] 2.1.5 新增子包 README 导航链接（R6.2）。
  - [ ] 2.1.6 易腐数字附命令 + 日期。
- [ ] 2.2 `docs/README.md`：OpenAPI 前缀计数订正（R5.6）、删 INFORMATION_SCHEMA 迁移措辞（R5.7）、deploy 说明（R4.1）、重写「待补充」（R6.1）。
- [ ] 2.3 `frontend/README.md`：图表库订正（R5.1）、去除 `@efferd/app-shell-*` 依赖表述（R5.4）、补三份子包 README 链接。
- [ ] 2.4 新建 `frontend/client/README.md`（页面结构 / 路由 / 状态管理约定 / 组件规范）。
- [ ] 2.5 新建 `frontend/admin/README.md`（页面结构 / 布局 / 图表原语 / 鉴权）。
- [ ] 2.6 新建 `frontend/packages/shared/README.md`（API 命名空间 / auth 协调 / SSE / 类型 / 公共组件）。
- [ ] 2.7 `backend/README.md`：删「含两份迁移」（R5.5）、测试类 31→30（R5.8）、pytest 468→525 标注（R5.11）、deploy 措辞（:230）。
- [ ] 2.8 `backend/business/README.md`：死链 `docs/conventions/` 改指 `.trellis/spec/backend/`（R5.3）、测试类 31→30（R5.8）。
- [ ] 2.9 `backend/agent/README.md`：pytest 468→525（R5.11）、pid/json gitignore 项删除、待补充编号重排（R5.12）。
- [ ] 2.10 `backend/agent/jobs/importer/README.md`：pid/json gitignore 项（R5.2）。
- [ ] 2.11 `docs/retrospective/项目复盘.md`：仅事实复核（R1.4）。
- [ ] 2.12 **Review gate**：跑 design §6 的 AT1–AT8，全部通过。
- [ ] 2.13 **提交 B**：`git add README.md docs frontend backend && git commit -m "docs(readme): 全量订正 README 并补建子包文档"`。

## 阶段 3 — 收尾

- [ ] 3.1 全仓死链脚本复扫（含根、docs、frontend、backend、.trellis/spec）。
- [ ] 3.2 更新 task.json 完成后归档：`python ./.trellis/scripts/task.py archive 10-13-docs-full-refresh`。
- [ ] 3.3 按需记录 journal。

## 回滚点

- RP1 阶段 1 提交后：`git revert <A>`。
- RP2 阶段 2 提交后：`git revert <B>`。

## 验证命令速查

```bash
grep -cE '^CREATE TABLE' docs/database/db-schema.sql          # 20
grep -cE '^  /' docs/spec/openapi.yaml                        # 68
grep -cE '<module>' backend/business/pom.xml                  # 9
find backend -name '*Test.java' | wc -l                       # 30
grep -rcE '^\s*def test_' backend/agent/tests | awk -F: '{s+=$2} END{print s}'   # 525
find frontend -name '*.test.*' -not -path '*/node_modules/*' | wc -l              # 21
grep -E 'echarts' frontend/admin/package.json                 # 空
grep -rn 'docs/conventions' --include='*.md' . | grep -v node_modules             # 空
```
