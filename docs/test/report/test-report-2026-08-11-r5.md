# AnimeTracker 测试报告 round-9（r5）

## 1. 基础信息

| 项 | 值 |
|---|---|
| 被测 commit | `fa2e442`（本地=远端，与 origin/main 同步） |
| 基线 SHA | `f9e8701`（round-8 全量 49PASS/3LIMITED 全绿点） |
| 变更范围 | f9e8701..fa2e442 共 3 commit：`b709c0e` fix（faint 对比度 #5c6c7a，**唯一代码变更**）+ `44715b7` docs + `fa2e442` chore |
| 环境指纹 | Debian 13 (192.168.0.3)、JDK 21.0.11、Maven 3.9.9、Node v24.19.0、Python 3.13.5、MySQL8.4.9/Redis8.8.0/MinIO/Postgres、3.8G RAM+swap、profile=local、nginx 启用 |
| 执行 | Hermes（2026-08-11 20:35-21:20，单 agent，无缺陷进入修复环节） |
| 数据基线 | subjects=10614 / episodes=148782 / import_record 26→27（id=48 COMPLETED 115 条）/ user_collection 5（在看4/想看1） |

## 2. 分层四态

| 层 | 用例数 | PASS | FAIL | SKIP | LIMITED | 通过率 | 耗时 |
|---|---|---|---|---|---|---|---|
| L0 单元 | 6 | 6 | 0 | 0 | 0 | 100% | ~2min（mvn test 35/35 + 静态检查） |
| L2 前端构建 | 2 | 2 | 0 | 0 | 0 | 100% | ~1min（双端 tsc 0 error + build） |
| L1 Agent 能力 | 4 | 4 | 0 | 0 | 0 | 100% | ~3min（pytest 100 passed + AI SSE 四方核对） |
| L3 接口契约 | 19 | 19 | 0 | 0 | 0 | 100% | ~6min（含 recent 导入触发闭环） |
| L4 E2E 视觉 | 21 | 18 | 0 | 0 | 3 | 100%* | ~30min |
| **合计** | **52** | **49** | **0** | **0** | **3** | **100%** | **~42min** |

*L4 通过率按 PASS/(PASS+FAIL)；3 个 LIMITED 为 390 移动视口环境限制（同 r4），不阻塞。

## 3. 缺陷清单

**P0/P1/P2 产品缺陷：0 个。**

### 观察项（P3/风险）
| 编号 | 内容 | 影响 |
|---|---|---|
| P3-OBS-01（强化） | LLM 分组表达不稳定：同问题两次回答风格不同（一次把无进度条目拆为「在看(1部,待观看)」，一次平铺列表），**数据/状态标签始终正确**（5 部全对、无「看过」误报、计数正确） | 建议 prompt 固定分组口径或由工具提供分组数据；当前不影响正确性 |
| P3-OBS-02（延续） | 导入 recent 受封面代理拖慢：id=48 抓 115 条耗时 17 分钟（代理波动，本次自然完成） | 导入耗时长，建议封面失败降级跳过 |

### 环境观察（非产品缺陷，记录教训）
| 项目 | 现象 | 定性 |
|---|---|---|
| L4-CLIENT-DETAIL-001 首查 | 详情页显示未收藏（无取消收藏/进度 0/评分 0），但接口与 DB 均为已收藏（type=3/rate=1/ep=6） | **Browserbase 云浏览器会话中途重置**：localStorage 被清空（出现 about:blank、storage SecurityError、登录态丢失）→ authStore 状态不一致产生假象。**重新登录后复验 PASS**（评分 1 星/进度 6/取消收藏按钮均在）。教训：L4 遇登录态异常先重新登录复验，勿直接定产品缺陷 |

## 4. Flaky / 受限 / 未覆盖

- Flaky：无
- 受限（LIMITED，3 个）：L4-ADMIN-LOGIN-002 / L4-ADMIN-DASH-003 / L4-MOBILE-001——390×844 移动视口无法模拟（Browserbase 视口固定 + playwright 不可装），补测条件：真机/390 视口
- 未覆盖：L5 混沌/性能/SAST（需显式指令）；MinIO 外网可达性（P2 #11 延续）；admin 移动端视口

## 5. 结论

- **变更影响验证**：
  - **L4-READ-001 对比度断言首次实战通过**：浅色主题实测 `--text-soft` #4c5c6a=**6.13:1**、`--text-faint` #5c6c7a=**4.81:1**（均 ≥4.5 达标，faint 修复生效）；深色源码确认 soft #b7c6d0=9.93、faint #8496a2=5.68（≥4.0 未回归）
  - faint 颜色变更无布局副作用：admin 登录/仪表盘/导入/日志/番剧管理全页面无溢出、无裁切、三级文字层次保持
  - 全量回归：L0 35 单测、L2 双端构建、L1 100 pytest + AI 四方核对、L3 19 契约（含导入 recent 触发→RUNNING→COMPLETED 闭环）、L4 18 视觉全过（登录光标 1 个/chart-lg span 8/导入四卡 27-20-6/收藏 5 行/详情页收藏态/console 0 error）
- **上线建议：放行**（无 P0/P1/P2；3 个 LIMITED 为环境限制；P3 观察项不阻塞）
- 回滚条件：faint 对比度再次低于 4.5 或 15px 字号引发布局溢出时回滚
- 审计链路：Hermes 单 agent 执行，修复环节未触发；产物 test-plan-2026-08-11-r5.md + 本报告；基线更新建议：全绿无 P0 → 用户确认后 baseline-success-sha.txt 更新为 `fa2e442`
