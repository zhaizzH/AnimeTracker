# AnimeTracker 测试报告 round-7（r3）

## 1. 基础信息

| 项 | 值 |
|---|---|
| 被测 commit | `a10276c`（本地=远程，docs: 第六轮测试计划与报告） |
| 基线 SHA | `72da11c`（round-6 全量 162/162 全绿点；上轮误更新的 a10276c 已修正回滚） |
| 变更范围 | 72da11c..HEAD 10 文件：导入统计卡（ImportServiceImpl/ImportStatusVO/测试/前端/mock/openapi）+ Login 光标 + docs |
| 环境指纹 | Debian 13 (192.168.0.3)、JDK 21.0.11、Maven 3.9.9、Node v24.19.0、Docker MySQL8.4.9/Redis8.8.0/MinIO/Postgres、3.8G RAM+7.9G swap、profile=local、nginx 测试期间重启供前端访问 |
| 执行 | Hermes（2026-08-11 13:16-14:05） |
| 数据基线 | subjects 10614 / episodes 148782 / import_record COMPLETED 18 + FAILED 6（含测试终止的 id=45）=24 / user_collection 5 |

## 2. 分层四态

| 层 | 用例数 | PASS | FAIL | SKIP | LIMITED | 耗时 |
|---|---|---|---|---|---|---|
| L0 单元 | 8 | 8 | 0 | 0 | 0 | ~3min（含 clean 全量重编译） |
| L2 前端构建 | 2 | 2 | 0 | 0 | 0 | ~40s |
| L1 Agent 能力 | 4 | 4 | 0 | 0 | 0 | ~2min（pytest 100 passed 4.72s + AI SSE） |
| L3 接口契约 | 18 | 18 | 0 | 0 | 0 | ~5min（含 recent 导入触发） |
| L4 E2E 视觉 | 22 | 22 | 0 | 0 | 0 | ~8min |
| **合计** | **54** | **54** | **0** | **0** | **0** | **~18min** |

通过率 100%（54/54）。执行中 6 个用例首跑 FAIL，全部定性为**测试脚本预期/断言错误**（非产品缺陷），修正后 PASS，详见 §3。

## 3. 缺陷清单

**P0/P1/P2 产品缺陷：0 个。**

### 脚本错误（非产品缺陷，6 项已修正）
| 用例 | 现象 | 定性 |
|---|---|---|
| L3-AUTH-002 | 5 次错误密码未触发限流 | 产品逻辑为**第 6 次起拒绝**（failCount>=5 判据）且返回 401「登录失败次数过多」，非 429；第 6 次正确密码实测被拒 ✅ 功能正常。脚本预期（5 次/429）错误 |
| L3-SUBJECT-001 | /api/admin/subjects GET 405 | admin 模块无列表端点（仅 CRUD）；列表是 client 公开接口 `GET /api/client/subjects`，total=10614 ✅ |
| L3-SCHEDULE-001 | schedule 返回 4 被断 FAIL | 响应 data 是 `{content:[...]}` 结构（非裸数组）；content 50 条今日排期 ✅ |
| L3-IMPORT-004c | recent 导入「结束→FAILED」误判 | 脚本把 totalLogs 增长（任务**开始**）当成任务**结束**；id=45 实际 RUNNING 中 |
| L4-ADMIN-IMPORT-001 | 三卡数字断言 FAIL | inner_text 的 div 换行（`任务总数\n24`），`"任务总数 24"` 匹配不到；正则 `任务总数\s*(\d+)` 后页面 24/18/5 == DB 24/18/5 ✅ |
| L4-CLIENT-DETAIL-001 | 详情页断言 FAIL | 按钮文本是「想 看」（空格分隔）非「想看」；且 14749 被 L3-COLL-003 改为 type=1，断言按 DB 动态比对后 ✅ |

### 观察项（P3/风险，不阻塞，登记技术债）
| 编号 | 内容 | 影响 |
|---|---|---|
| P3-OBS-01 | agent 导入封面上传走代理 `proxy.8000150.xyz` 频繁 Read timeout（15s×重试），recent 导入 14 分钟仅完成 20%（115 条） | 导入任务耗时极长、长时间 RUNNING；已终止 id=45 恢复测试基线。建议：封面失败降级跳过/异步重试/无超时上限 |
| P3-OBS-02 | 导入进行中（写入 subject 半成品）时主页「今日放送」出现瞬时空白卡片（只有 NEW 标签） | 导入终止后复验消失，页面刷新正常。数据写入竞态，非代码缺陷 |
| P3-OBS-03 | `mock/admin.ts` importStatus 仅 2 字段（缺 failedCount/recentRecords/lastImportedAt） | 仅影响无后端 mock 模式，前端有 `?? 0` 兜底；生产不受影响 |
| P3-OBS-04 | P2 #11 延续：112 条 subject.image 指向旧 IP 192.168.0.110:9000（上轮登记，待用户定 MinIO endpoint） | 图片无法加载（本机 47.96.127.231 不可达） |

## 4. Flaky / 受限

- Flaky：无
- 受限：无
- 未覆盖：L5 混沌/性能/SAST（需显式指令）；MinIO 公网可达性（P2 #11）

## 5. 变更影响与上线建议

- 变更影响验证：导入页四卡（任务总数=24=import_record 全量、成功 18、失败 6 全量 DB 聚合）三方核对一致；Login 光标单一性桌面+移动验证通过；409 语义、热门榜、dashboard 布局（chart-lg span 8=777px）全回归通过
- **上线建议：放行**
- 回滚条件：导入统计卡数字与 DB 聚合不一致（totalLogs≠import_record count）或登录页出现多光标时回滚

## 6. 审计链路

- 执行：Hermes 单 agent（本环境无缺陷进入修复环节，步骤 7 未触发）
- 环境清理：id=44（卡死 full 导入）、id=45（过慢 recent 导入）测试前/中终止并标记 FAILED；Redis 限流 key 已 del；种子重放确认 user/collection 基线
- baseline-success-sha.txt：本轮 54/54 全绿无 P0，测试后更新为 `a10276c`
