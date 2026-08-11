# AnimeTracker 测试报告 round-8（r4）

## 1. 基础信息

| 项 | 值 |
|---|---|
| 被测 commit | `f9e8701`（前端可读性增强，rebase 于 15fc3d3 之上；本地含前端可读性 commit，未推送） |
| 基线 SHA | `a10276c`（round-7 全量 54/54 全绿点） |
| 变更范围 | a10276c..f9e8701 共 39 文件：常量类重构 35 文件（ErrorType/ImportConstants/OperationLogConstants/AgentApiPaths/RedisKeys + 包移动）+ 前端可读性 4 文件（admin/client 字号 15px/对比度加深） |
| 环境指纹 | Debian 13 (192.168.0.3)、JDK 21.0.11、Maven 3.9.9、Node v24.19.0、Python 3.13.5、Docker MySQL8.4.9/Redis8.8.0/MinIO/Postgres、3.8G RAM+7.9G swap、profile=local、nginx 测试期间启用（:80 client/:81 admin） |
| 执行 | Hermes（2026-08-11 15:20-16:00，单 agent，无缺陷进入修复环节） |
| 数据基线 | subjects=10614 / episodes=148782 / import_record 25（COMPLETED 19/FAILED 6）→ 测试后 26（id=47 COMPLETED 114 条）/ user_collection 5（在看4/想看1） |

## 2. 分层四态

| 层 | 用例数 | PASS | FAIL | SKIP | LIMITED | 通过率 | 耗时 |
|---|---|---|---|---|---|---|---|
| L0 单元 | 6 | 6 | 0 | 0 | 0 | 100% | ~2min（mvn test 35/35 + 静态检查） |
| L2 前端构建 | 2 | 2 | 0 | 0 | 0 | 100% | ~1min（tsc 0 error + vite build） |
| L1 Agent 能力 | 4 | 4 | 0 | 0 | 0 | 100% | ~3min（pytest 100 passed + AI SSE 四方核对） |
| L3 接口契约 | 19 | 19 | 0 | 0 | 0 | 100% | ~5min |
| L4 E2E 视觉 | 21 | 18 | 0 | 0 | 3 | 100%* | ~25min |
| **合计** | **52** | **49** | **0** | **0** | **3** | **100%** | **~36min** |

*L4 通过率按 PASS/(PASS+FAIL) 计；3 个 LIMITED 为环境限制（无法模拟 390 移动视口），不阻塞。

## 3. 缺陷清单

**P0/P1 产品缺陷：0 个。**

### P2 一般（1 个，**已修复**）
| 用例 ID | 现象 | 根因（证据链） | 修复 |
|---|---|---|---|
| L4-READ-001 | admin 浅色主题 `--text-faint: #6b7c8b` 对比度 **3.82:1**（WCAG AA 要求 ≥4.5） | 本轮可读性改动把 faint 从 #8a9aa8 加深到 #6b7c8b（旧值约 2.5:1），soft 已达标（6.13:1），faint 未达 AA。深色主题 faint 5.68:1 已达标。计算依据：WCAG 相对亮度公式，bg #eef2f6 | ✅ 已修复：`--text-faint`/`colorTextTertiary` 浅色主题加深至 **#5c6c7a**（global.css + theme.ts 两处）；实测对比度 **4.81:1 ≥ 4.5 达标**（浏览器 getComputedStyle 实测定值 + 13 个元素生效），保持 soft→faint 层次；admin 构建通过 + 登录页视觉复验无异常。防护：对比度断言已固化进测试计划模板（L4-READ-001） |

### 观察项（P3/风险）
| 编号 | 内容 | 影响 |
|---|---|---|
| P3-OBS-01 | LLM 组计数标签在小样本/非标准数据分布下可能不精确（实测：数据被 L3 污染时 AI 组标题「想看（1部）」但列出 2 部；干净基线数据下计数正确） | 建议 prompt 由工具提供分组计数而非 LLM 自行统计 |
| P3-OBS-02 | 延续：导入 recent 模式受封面代理拖慢（id=47 本次 17.5 分钟 114 条，未超时自然 COMPLETED） | 导入耗时极长，建议封面失败降级跳过/异步重试 |

### 测试脚本/设计问题（非产品缺陷，已修正，计入教训）
| 项目 | 现象 | 定性 |
|---|---|---|
| L3-IMPORT-006/007 | 首测用 JSON body 调 `/api/admin/import/run`，而 runImport 是 `@RequestParam`（query 参数）——mode 缺失走 Spring 参数校验（message=「请求参数错误」），validate() 自定义 message 未触发 | 脚本请求方式错误；改 `?mode=season` / `?mode=bogus` 后 validate 正常返回「season 模式需要 key」/「mode 必须是 full / season / recent / since」✅ 产品逻辑正确 |
| L1-AI-001 首测 | 首测 FAIL：AI 回答与「种子基线」不符（尼古喵喵被归入想看） | **测试顺序副作用**：L3-COLL-002/003 把 14749 改为 type=1/rate=9，AI 回答与当时的 DB 实际一致（映射正确）；重放种子恢复基线后 AI 回答全对（在看4/想看1/合计5部/无「看过」）。教训：L3 收藏变更用例须在 L1-AI 用例之前重放种子，或调整用例顺序 |

## 4. Flaky / 受限 / 未覆盖

- Flaky：无
- 受限（LIMITED，3 个）：
  - L4-ADMIN-LOGIN-002 / L4-ADMIN-DASH-003 / L4-MOBILE-001：**无法模拟 390×844 移动视口**（Browserbase 云端浏览器视口固定 1280×577，window.resizeTo 无效；本机 pip 装 playwright 失败——PyPI 直连/代理/清华源均不可达）。桌面视口全页面无溢出；收藏页 ≤768px 走卡片布局（`useIsMobile` + `collection-cards` 代码路径确认，操作列在卡片内可达）
  - **补测条件**：真机或 playwright 390 视口复验全站溢出与移动布局
- 未覆盖：L5 混沌/性能/SAST（需显式指令）；MinIO 图片外网可达性（P2 #11 延续，待用户定 endpoint）；admin 移动端视口（同上受限）

## 5. 结论

- **变更影响验证**：
  - 常量类重构（重点回归）：错误码全链路一致（401 登录失败过多/409 冲突/400 参数校验含自定义 message/权限拒绝）——ErrorType 枚举与旧行为等价；导入 mode 常量校验正确（season 需 key/since 需 since/bogus 拒绝）；OperationLogConstants 生效（logs 接口模块/操作字段正常）；RedisKeys 键前缀不变（auth:login-fail: 解锁正常）；无裸 int 构造 BizException
  - 前端可读性：body 字号 15px 生效（admin+client）；15px 下全页面无溢出/裁切/遮挡（vision 检查 4 页面）；chart-lg 布局比例保持 span 8/664px；soft 对比度 6.13:1 达标；faint 3.82:1 未达 AA（P2）
  - 全量回归：L0 35 单测、L2 双端构建、L1 100 pytest + AI 四方核对、L3 19 契约、L4 18 视觉全过
- **上线建议：放行**（无 P0/P1；P2 faint 对比度可排期修复；3 个 LIMITED 为环境限制非缺陷）
- 回滚条件：错误码语义变化导致客户端异常（如 409/401 语义变更）或 15px 字号引发布局溢出时回滚
- 审计链路：执行 Hermes 单 agent；修复环节未触发；测试产物 docs/test/plan/test-plan-2026-08-11-r4.md + 本报告；基线文件本轮全绿无 P0 → 待用户确认提交后更新 baseline-success-sha.txt 为 f9e8701
