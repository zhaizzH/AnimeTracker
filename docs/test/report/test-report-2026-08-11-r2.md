# AnimeTracker「番组手账」测试报告（第六轮 · 全量回归）

> 报告版本：v1.0（2026-08-11 第二轮）
> 被测 commit：72da11c（c789319 feat(导入): 状态改直查库并新增分页历史接口, agent加孤儿进程PID门禁, 收藏同类型无变化才409）
> 基线 commit：afc235f（上轮 6015eca 全绿 158/158 + P1 修复复验）
> 计划文件：docs/test/plan/test-plan-2026-08-11-r2.md
> 执行人：Hermes Agent（project-test-pipeline skill v1.1.0）
> 执行时间：2026-08-11 11:00 ~ 11:25

---

## 一、基础信息（环境指纹）

| 项 | 值 |
|---|---|
| OS | Debian 13 (linux 6.12.101+deb13-amd64) |
| 机器 | 本机 192.168.0.3（DHCP） |
| JDK | OpenJDK 21.0.11 |
| Maven | 3.9.9 |
| Node | v24.19.0 |
| MySQL | 8.4.9（Docker 1Panel-mysql-aeEP） |
| Redis | 8.8.0（Docker 1Panel-redis-HGyc，应用数据 db=1） |
| MinIO | minio RELEASE.2025-04-22（Docker） |
| swap | 7.9G |
| profile | local（application-local.yml + /etc/animetracker/ 覆盖层） |
| 被测 SHA | 72da11ce4a712d08cf70b2f6a9250dff35230745 |
| 基线 SHA | afc235f（本地 baseline-success-sha.txt） |
| 数据基线 | user_collection 5 条（type=3 ×4 + type=1 ×1），user 3 条（admin/test1/test2），subject 10614，episode 148782 |

## 二、分层结果汇总

| 层 | 用例数 | PASS | FAIL | SKIP | LIMITED | 通过率 | 耗时 |
|---|---|---|---|---|---|---|---|
| L0 Java 单测 | 35 | 35 | 0 | 0 | 0 | 100% | ~3min |
| L1 pytest + AI 文本 | 101 | 101 | 0 | 0 | 0 | 100% | ~5s + AI对话~60s |
| L2 前端构建 | 4 | 4 | 0 | 0 | 0 | 100% | ~22s |
| L3 API 冒烟 | 12 | 12 | 0 | 0 | 0 | 100% | ~15s |
| L4 E2E 浏览器 | 10 | 10 | 0 | 0 | 0 | 100% | ~3min |
| **合计** | **162** | **162** | **0** | **0** | **0** | **100%** | |

注：L0 从 34 增至 35（新 updatesRatingWhenSameTypeResubmitted）；L3 从 10 增至 12（409 新语义 ×2 + records 分页）；L4 从 9 增至 10（导入状态面板 + 登录页光标回归 + 导入任务页）。

## 三、缺陷清单

**本轮无 P0/P1/P2/P3 代码缺陷。**

执行过程中的 2 个测试脚本断言问题（非产品缺陷，已修正）：
1. L4-ADMIN-003 导入状态面板断言：原断言查找「FAILED/成功/失败」文本，但新实现用 BarList 渲染（颜色区分状态，不显示状态文本）。修正为断言「共 N 条记录」+ 内容条存在 → PASS（共 21 条记录，105 内容条，console 0 错误）。
2. L1-AI-001 检测脚本字符串处理 bug（replace 逻辑误报）——人工核对全文「看过」0 次 → 确认 PASS。

**遗留记录（非本轮引入）**：
- P2 #11（上轮）：112 条 subject.image 硬编码旧 IP 192.168.0.110 → 封面加载失败，待确认 MinIO 可达地址后修数据，排期。
- 观察项：import_record 中 10:33 有一条 FAILED 导入记录（导入进程提前结束，errorMessage 截断），为 agent 重启时自动触发的 recent 导入；非测试用例触发，不判定缺陷，列入观察。

## 四、Flaky / 受限 / 未覆盖

| 项 | 说明 |
|---|---|
| Flaky | 无（162 例无间歇性失败） |
| 受限 | 无 |
| 未覆盖 | L5 可选层未启用；真实 LLM 长对话未覆盖；压测未做；导入任务实际执行（启动真实抓取）未覆盖（避免污染数据） |

## 五、变更影响摘要

基线 afc235f → 被测 72da11c 变更（c789319 feat(导入)，14 文件）：
1. **导入状态直查库**：agent 移除 import_api 状态接口（-39 行），business ImportServiceImpl 改查 import_record 表 → L3 records 分页接口 + L4 导入状态面板验证 ✅ 通过
2. **新增 /api/admin/import/records 分页历史**（page/size/status 参数，@Min/@Max 校验）→ L3-IMP-001 ✅
3. **agent 孤儿进程 PID 门禁**（import_runner +43 行）→ L1 pytest 100 通过（含 test_import_api 改造）✅
4. **收藏 409 新语义**：同类型且评分/进度均无变化才 409；改评分/进度/换类型合法更新 → L3-COL-002/003/004 三条全过 ✅ + L0 新单测 ✅
5. **admin 前端**：Dashboard 导入区域改 records（Promise.all 6 接口仍正常）、ImportTasks 分页历史 → L4-ADMIN-003/004 ✅

上轮修复回归：热门榜 collectionCount（L4 显示 1/1/1）✅、登录页光标唯一（L4-ADMIN-005）✅、AI 收藏类型四方一致（L1-AI-001）✅、移动端卡片布局（L4-MOBILE-001）✅。

## 六、上线建议

- **结论：放行**（162/162 全绿，无 P0，无 P1）
- 本轮无代码修复，仅测试文档新增：`docs/test/plan/test-plan-2026-08-11-r2.md` + `docs/test/report/test-report-2026-08-11-r2.md`
- 待提交内容（工作区已有）：
  1. `frontend/admin/src/pages/Login.tsx` — 登录页光标修复（上轮用户确认并入本轮，已复验 PASS）
  2. `docs/test/plan/test-plan-2026-08-11-r2.md` — 本轮计划
  3. `docs/test/report/test-report-2026-08-11-r2.md` — 本轮报告
  4. `baseline-success-sha.txt` — 本地基线更新（不提交仓库）
- 回滚触发条件：导入状态/分页接口异常 → 回滚 c789319；收藏重复提交行为异常 → 检查 CollectionServiceImpl 409 判断逻辑
- 边界约定：本流水线仅预合并门禁；生产灰度冒烟为后置补充；测试通过 ≠ 自动上线，合并/上线决策权保留给用户

## 七、审计链路

| 轮次 | Agent | 动作 | 结果 |
|---|---|---|---|
| — | hermes | 全流程执行（本次无代码修复，无 agent 派发） | 162/162 ✅ |
| 备注 | 上轮修复 | Login.tsx 光标修复（用户确认并入本轮提交） | L4-ADMIN-005 复验 PASS |

## 八、附：关键证据

- AI 文本四方核对：AI 回答「4 部在看、1 部想看」，「看过」0 次 = DB（type=3×4+type=1×1）= 接口 = 前端 ✅
- 409 新语义：无变化重复 → 409「该条目已收藏」；同 type 改评分 → 200；换 type → 200 ✅
- chart-lg 布局：gridColumn=span 8，2/3 宽 ✅
- 导入状态面板：共 21 条记录，105 内容条，console 0 错误 ✅
- 移动端 390px：docSW=390=winW 无溢出，5 卡片，取消按钮可见 ✅
- 登录页光标：1 个且在最后一行（上轮修复回归）✅
- 截图存证：/tmp/l4_20260811_r2-*.png
