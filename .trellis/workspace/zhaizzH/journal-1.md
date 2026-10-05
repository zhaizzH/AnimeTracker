# Journal - zhaizzH (Part 1)

> AI development session journal
> Started: 2026-08-29

---



## Session 1: 完成 Trellis Bootstrap 与前端质量门禁
<!-- trellis-session: v=2 fp=faf2fb78f497e1dd -->

**Date**: 2026-08-31
**Task**: 完成 Trellis Bootstrap 与前端质量门禁
**Branch**: `codex/fix-frontend-quality-gate`

### Summary

完成首次 Trellis Plan→Execute→Check→Commit→Archive 流程；从现有 lockfile 恢复 remark-gfm，新增 RequireAdmin 三分支测试，同步前端质量规范，并归档修复子任务与 Bootstrap 父任务。

### Git Commits

| Hash | Message |
|------|---------|
| `ddc9e96` | test(admin): 补充管理权限守卫测试 |

### Status

[OK] **Completed**


## Session 2: 迁移 Business 配置到 App 装配层
<!-- trellis-session: v=2 fp=cf18a5d74c46282c -->

**Date**: 2026-08-31
**Task**: 迁移 Business 配置到 App 装配层
**Branch**: `codex/move-business-config-to-app`

### Summary

完成 6 个配置类迁移到 app.config，并将 RestTemplateConfig 重命名为 AgentConfig；AgentServiceImpl 与 CookieOriginFilter 改为显式构造，补充 5 类回归/架构测试。backend/business mvn -B clean test 全部通过，已归档 Trellis 任务。

### Git Commits

| Hash | Message |
|------|---------|
| `465a941` | refactor(应用): 集中 Business 配置装配 |

### Status

[OK] **Completed**


## Session 3: 统一 Trellis 提交信息规范
<!-- trellis-session: v=2 fp=b7c017272d545cbc -->

**Date**: 2026-08-31
**Task**: 统一 Trellis 提交信息规范
**Branch**: `codex/move-business-config-to-app`

### Summary

发现本次任务的 Trellis 自动归档与日志提交未遵守 .gitmessage 中文约定；已启用仓库 commit.template，修改自动提交默认文案，并将本任务的 3 个历史提交重写为中文主题。

### Git Commits

| Hash | Message |
|------|---------|
| `763f6d0` | chore(工程): 统一 Trellis 提交信息规范 |

### Status

[OK] **Completed**


## Session 4: 全量完善 README.md 相关文档
<!-- trellis-session: v=2 fp=165592dfa3a61850 -->

**Date**: 2026-09-03
**Task**: 全量完善 README.md 相关文档
**Branch**: `main`

### Summary

全量完善了 README.md 项目说明文档，更新了架构、功能列表、快速启动与开发路线图等内容

### Git Commits

| Hash | Message |
|------|---------|
| `c11b806` | feat: 全量完善 README.md 相关文档与实施计划 |

### Status

[OK] **Completed**


## Session 5: 完成 v1 RAG 发布门禁与激活
<!-- trellis-session: v=2 fp=654c69f2d851b1ce -->

**Date**: 2026-09-07
**Task**: 完成 v1 RAG 发布门禁与激活
**Branch**: `main`

### Summary

完成 v1 candidate 120/120 评测、容量/延迟/人工报告与 gate；激活 MySQL search_index_release v1，真实 lexical API 返回 200；Java/Python/任务校验通过。任务仍保留 in_progress，待 24 小时灰度观察，RAG_ENABLED 未修改。

### Git Commits

| Hash | Message |
|------|---------|
| `f0add0d9` | feat(rag): complete v1 release gate and activation |
| `e256113b` | feat(rag): 完善Bangumi混合检索门禁 |

### Status

[OK] **Completed**


## Session 6: 完成 Bangumi RAG 灰度与回滚确认
<!-- trellis-session: v=2 fp=d8e97cc4b93d5c84 -->

**Date**: 2026-09-09
**Task**: 完成 Bangumi RAG 灰度与回滚确认
**Branch**: `main`

### Summary

用户确认 v1 24 小时灰度观察与 release/功能开关回滚通过；同步灰度证据、任务元数据和运行审计，完成 09-03-bangumi-rag-retrieval 归档。

### Git Commits

| Hash | Message |
|------|---------|
| `23f322b3` | 完成 RAG v1 发布门禁与激活 |
| `eef1561e` | 整理 Bangumi RAG 会话日志 |

### Status

[OK] **Completed**


## Session 7: 完成源码规范审计与归档
<!-- trellis-session: v=2 fp=b03b26b72cf6e189 -->

**Date**: 2026-09-10
**Task**: 完成源码规范审计与归档
**Branch**: `main`

### Summary

审计全部规范，更新14份并新增Agent运行契约；用户验收并提交，任务已归档。

### Main Changes

- 记录角色工具边界、Prompt缓存、RAG与SSE已知限制

### Git Commits

| Hash | Message |
|------|---------|
| `6a5d61e6` | docs(spec): 按当前源码更新项目开发规范 |

### Testing

- [OK] 文档19份、链接30个、显式源码引用26个，检查通过
- [OK] 完整Python测试存在既有收集失败；隔离该文件后271 passed，不代表全量通过

### Status

[OK] **Completed**

### Next Steps

- 后续代码任务处理能力测试与实现不一致问题


## Session 8: 修复 Agent 运行时与测试报告问题
<!-- trellis-session: v=2 fp=307bccde3749ed18 -->

**Date**: 2026-09-12
**Task**: 修复 Agent 运行时与测试报告问题
**Branch**: `main`

### Summary

完成 Agent 报告 F01-F07、F09-F12 修复，新增 Python/Java/前端回归测试与报告；Python 284 passed，Maven clean test、前端 typecheck/Vitest/build 通过。F08 实体名称解析等待 Business 权威接口。

### Git Commits

| Hash | Message |
|------|---------|
| `cdbfa3d4` | fix: 修复 Agent 运行时与测试报告问题 |

### Status

[OK] **Completed**


## Session 9: 完成 Business 规范复核修复
<!-- trellis-session: v=2 fp=b4dd41de9d0ce3bc -->

**Date**: 2026-09-14
**Task**: 完成 Business 规范复核修复
**Branch**: `codex/business-spec-implementation`

### Summary

完成 Javadoc 声明和 doclint 校验工具、架构门禁与专项回归，修复导入日志隐私和误写标点；95 个 Java 测试与 6 个检查器测试通过，255 文件 1658 声明检查通过。

### Git Commits

| Hash | Message |
|------|---------|
| `0a9e69b5` | fix(business): 完成规范复核缺陷修复与文档校验 |

### Status

[OK] **Completed**


## Session 10: 提交 Business 规范任务代码
<!-- trellis-session: v=2 fp=3286b109f374e659 -->

**Date**: 2026-09-14
**Task**: 提交 Business 规范任务代码
**Branch**: `codex/business-spec-implementation`

### Summary

完成 Business 分层、Javadoc、架构门禁与专项测试修复；95 个 Java 测试和 JDK 文档检查通过，任务已归档。

### Git Commits

| Hash | Message |
|------|---------|
| `0a9e69b5` | fix(business): 完成规范复核缺陷修复与文档校验 |
| `2e8ad93c` | chore(trellis): 归档规范复核修复并记录验证 |

### Status

[OK] **Completed**


## Session 11: 精简 Java 后端中文注释规范
<!-- trellis-session: v=2 fp=3faf328f2b971efa -->

**Date**: 2026-09-15
**Task**: 精简 Java 后端中文注释规范
**Branch**: `main`

### Summary

更新自然中文无句号的 Java 注释规范，新增检查器回归；Business clean test、Javadoc 声明检查和 JDK doclint 全部通过；复核后补齐类型示例、修正方法体示例标点与归档状态记录

### Git Commits

| Hash | Message |
|------|---------|
| `65f265f5` | docs(java): 规范自然中文注释 |
| `41751ca9` | docs(java): 补齐注释规范示例 |

### Status

[OK] **Completed**


## Session 12: 统一后端 Java 中文注释标点
<!-- trellis-session: v=2 fp=70b487b395cc1af1 -->

**Date**: 2026-09-15
**Task**: 统一后端 Java 中文注释标点
**Branch**: `main`

### Summary

扫描并修复 backend/business 全部 255 个 Java 文件的 1635 处中文注释末尾句号；Javadoc 检查器、doclint、Maven clean test 全部通过

### Git Commits

| Hash | Message |
|------|---------|
| `0347bc4` | style(java): 统一后端中文注释标点 |

### Status

[OK] **Completed**


## Session 13: 刷新 Backend Trellis 规范
<!-- trellis-session: v=2 fp=d0e0a7f5be65cac3 -->

**Date**: 2026-09-16
**Task**: 刷新 Backend Trellis 规范
**Branch**: `main`

### Summary

按当前 Java 后端源码、POM、ArchitectureBoundaryTest、资源配置和 CI 更新 Backend 规范，合并同主题文档并保留历史记录

### Main Changes

- 更新模块矩阵、common/app 异常边界、资源清单与 CORS 配置债务说明
- 补充 2026-09-16 Java 测试、Javadoc 和检查器回归基线

### Git Commits

| Hash | Message |
|------|---------|
| `d8bb08b` | docs(trellis): refresh backend specifications |

### Testing

- [OK] mvn -B test -f backend/business/pom.xml：95 passed
- [OK] check_javadoc.py：255 files、1658 declarations、0 violations
- [OK] test_check_javadoc.py：7 passed；Trellis、链接、占位文本和 git diff --check 通过

### Status

[OK] **Completed**

### Next Steps

- 后续修改模块边界或配置时同步更新对应主题文档并重跑质量门禁


## Session 14: 实现 09-16 按标题安全加入想看（Business 优先 + RAG 回退 + SUBJECT_RESOLUTION）
<!-- trellis-session: v=2 fp=568b57c1639a508d -->

**Date**: 2026-09-20
**Task**: 实现 09-16 按标题安全加入想看（Business 优先 + RAG 回退 + SUBJECT_RESOLUTION）
**Branch**: `main`

### Summary

为单标题加入想看补齐确定性解析链路：显式 subjectId 跳搜索仍 /batch；否则 Business /search 首查，仅成功空结果回退 RAG(复用 RetrieveSubjectsUseCase)；/batch(excludeCollected=false) 只留 active/type2/nsfw；唯一精确候选复用 build_wishlist_preview 走预览→确认，多个/歧义进入新增 SUBJECT_RESOLUTION(600s TTL, 绑定 user/query/候选)。gateway 对该状态确定性路由 recommend_agent，确认词只对 ADD_TO_WISHLIST 生效。归一化仅字符层面(第二季≠第2季)。

### Main Changes

- 新增 app/agent/client/actions/subject_resolution.py 与 tests/agent/test_subject_resolution.py；改 pending_action.py(联合新增 SUBJECT_RESOLUTION)、wishlist.py(抽出 build_wishlist_preview)、recommend.py(注册工具)、gateway.py(路由)、run.py(候选上下文)、recommend_agent_prompt.md

### Git Commits

(No commits - planning session)

### Testing

- [OK] uv run pytest tests/agent 42 通过；uv run pytest 全量 313 通过；compileall 与 git diff --check 干净

### Status

[OK] **Completed**

### Next Steps

- 代码尚未提交：需切特性分支→提交→set-branch→按需 archive；并已新建 09-20-watchlist-title-resolution 处理追番(在看)写入与路由缺口


## Session 15: 实现 09-20 按标题设置收藏类型(1-5)与写入意图路由
<!-- trellis-session: v=2 fp=40721320b23a8164 -->

**Date**: 2026-09-21
**Task**: 实现 09-20 按标题设置收藏类型(1-5)与写入意图路由
**Branch**: `feat/collection-type-resolution`

### Summary

新增 set_subject_collection/execute_set_collection_type/cancel：复用 09-16 解析链路，预览三态 ADD/NOOP/CHANGE，确认后经 /collections/{id}/save 写目标类型，CHANGE 预览可见不静默覆盖。pending_action 增 SET_COLLECTION_TYPE，SUBJECT_RESOLUTION 增可选 collection_type(默认None向后兼容)并按其分派。gateway 写入意图改为动词+填充词+类型名正则(覆盖'添加到我的追番'插词)并保留否定守卫，纯查询不误触发。抽出共享 check_collection_state，新增 save_collection 网关方法。

### Main Changes

- 新增 collection_type.py/collection_state.py + test_collection_type.py/test_write_intent_routing.py；改 subject_resolution.py(抽 resolve_candidates/finalize_resolution)、wishlist.py、pending_action.py、gateway.py、recommend.py、run.py、ports.py、business_http.py、gateway_prompt.md、recommend_agent_prompt.md

### Git Commits

| Hash | Message |
|------|---------|
| `344f534d` | feat(agent): 按标题设置收藏类型(1-5)与写入意图路由 |

### Testing

- [OK] uv run pytest 全量 339 通过；真实服务端到端(test2/userId5,subject110)验证 路由→ADD预览→确认写type2→CHANGE预览→确认写type4→NOOP不写，测试数据已 /remove 清理

### Status

[OK] **Completed**

### Next Steps

- 代码在分支 feat/collection-type-resolution 未合并；如需硬门禁(写入必须匹配确认词而非依赖模型判断)可另开任务


## Session 16: 实现 T3 写入硬确认门禁(write_confirmed)与 action_id 版本绑定
<!-- trellis-session: v=2 fp=b62e34c58a67e8b7 -->

**Date**: 2026-09-21
**Task**: 实现 T3 写入硬确认门禁(write_confirmed)与 action_id 版本绑定
**Branch**: `feat/write-confirmation-hard-gate`

### Summary

把三条写链路(wishlist/progress/collection_type)的'明确确认'从提示词级升级为代码级硬门禁：AgentState.write_confirmed 仅由 gateway_router 依当前回合确定性设置(模型不可篡改)，共享守卫 require_confirmed_write 统一校验 用户→类型→用户绑定→TTL→确认标志；非确认回合即使模型调用 execute 也拒写、Business 零调用。Wishlist/SetCollectionType 动作加服务端 action_id(版本失效/trace，非模型回传令牌，默认空兼容旧JSON)。根治 09-20 E2E 观察到的'重发加入请求即被当确认写入'。

### Main Changes

- 新增 write_guard.py + test_write_guard.py；改 state.py/service.py(write_confirmed)、gateway.py(各分支注入标志)、pending_action.py(action_id)、wishlist.py/collection_progress.py/collection_type.py(execute 接守卫)；更新 test_collection_type.py execute 用例传 write_confirmed 并补非确认拒写/他人动作/action_id 用例

### Git Commits

| Hash | Message |
|------|---------|
| `0562df8d` | feat(agent): 写入硬确认门禁(write_confirmed)与动作版本绑定 |

### Testing

- [OK] uv run pytest 全量 351 通过；execute 工具对模型零可见参数；图状态传播实证三场景(写入意图非确认→False、确认+pending→True、重发非确认+pending→False)。完整 LLM E2E 因 DeepSeek 402 余额不足未能跑，待充值补做

### Status

[OK] **Completed**

### Next Steps

- 分支 feat/write-confirmation-hard-gate 未合并；DeepSeek 充值后补一次真实 LLM E2E(标记为看过→确认写入→重发非确认不写)；后续按序做 T1 季度对齐→T2 RAG正确性→T4 测试补齐


## Session 17: T1 季度/档期映射跨层对齐 + .git 损毁恢复
<!-- trellis-session: v=2 fp=9661e4493be803a3 -->

**Date**: 2026-09-21
**Task**: T1 季度/档期映射跨层对齐 + .git 损毁恢复
**Branch**: `feat/quarter-season-alignment`

### Summary

统一 season 词表到 app/rag/seasons.py(winter=1..autumn=4)，5 处消费方改引用，新增 test_season_alignment.py 跨层回归(62 条)，更新 3 处钉错测试，413 passed 全绿；会话中遭遇 .git 被外部进程(Codex)两轮删除，从回收站按原路径恢复全部 refs/objects 并用 packed-refs 固化分支引用。

### Git Commits

| Hash | Message |
|------|---------|
| `007c4a06` | fix(agent): 季度映射对齐权威动漫季约定(winter=1..autumn=4) |

### Status

[OK] **Completed**


## Session 18: admin 地基：Tailwind+shadcn 接入与 shared 去 antd
<!-- trellis-session: v=2 fp=a6b546d962d22e44 -->

**Date**: 2026-09-22
**Task**: admin 地基：Tailwind+shadcn 接入与 shared 去 antd
**Branch**: `feat/admin-shadcn-migration`

### Summary

完成 admin-ui-foundation 子任务（父任务 09-21-admin-tailwind-shadcn-dashboard 的阶段 A+B）：admin 接入 Tailwind v4 + shadcn/ui 地基与 @efferd 命名空间，shared 拆分 AuthGate 消除 antd 运行时依赖，并完成 preflight 破坏的就地补偿。

### Main Changes

- admin 接入 Tailwind v4 CSS-first + @tailwindcss/vite，新增 @/ → ./src 别名（vite+tsconfig 双侧，保留 @shared），components.json 注册 @efferd registry，落地 24 个 shadcn 组件与 cn()/toast 封装
- shared 新增 useAuthStatus() headless 登录态，AuthGate 改为 UI 无关实现（保留全部 auth-gate*/od-* 类名与 ARIA 语义），SubjectCard 弃用 theme.useToken() 改引 --od-* 变量修复暗色回归
- 实测证伪「调整 Tailwind 引入顺序可避免 preflight 覆盖」：antd reset.css 仅 3.6KB 且不含 h1-h6/ul/ol 规则；改为就地补偿（charts.tsx h3 补 text-[1.17em]、Dashboard ol 补 list-decimal pl-10）

### Git Commits

| Hash | Message |
|------|---------|
| `08ef7948` | feat(admin): 接入 Tailwind v4 与 shadcn/ui 地基，注册 @efferd 命名空间 |
| `3fc9fe67` | fix(shared): 拆分 AuthGate 逻辑，去除 antd 运行时依赖 |
| `59348271` | fix(admin): Tailwind preflight 破坏处就地补偿 |
| `f73e0174` | docs(trellis): admin UI 迁移父任务与 4 个子任务的规划产物 |

### Testing

- [OK] npm run typecheck：shared/client/admin 三 workspace 通过
- [OK] npm test -w @animetracker/shared 6/6；npm test -w client 7/7
- [OK] npm run build：三 workspace 成功（admin 2367 modules）
- [OK] Playwright 实测 client 登录态三态（checking / retryable-error / 正常）无回归；SubjectCard light/dark 逐值对齐

### Status

[OK] **Completed**

### Next Steps

- 09-21-admin-app-shell（阶段 C）需先补 design.md + implement.md 再 start


## Session 19: 完成 Admin app-shell 外壳迁移
<!-- trellis-session: v=2 fp=74115f932ddbaa92 -->

**Date**: 2026-09-22
**Task**: 完成 Admin app-shell 外壳迁移
**Branch**: `feat/admin-shadcn-migration`

### Summary

完成 AdminLayout app-shell 迁移：接入 7 路由侧栏、共享认证用户菜单与登出、共享主题切换；移除 Admin 入口的 AntD ConfigProvider 与 reset.css；补回归测试并通过 admin tests、typecheck、build。已归档 09-21-admin-app-shell。

### Git Commits

| Hash | Message |
|------|---------|
| `4ba7302` | feat(admin): 迁移 AdminLayout 到 app-shell |

### Status

[OK] **Completed**


## Session 20: 完成 admin app-shell 布局迁移
<!-- trellis-session: v=2 fp=5d0918ac9eded7fa -->

**Date**: 2026-09-22
**Task**: 完成 admin app-shell 布局迁移
**Branch**: `feat/admin-shadcn-migration`

### Summary

完成 AdminLayout app-shell 迁移：新增侧栏导航、用户菜单、主题切换和退出流程；移除 AdminLayout 入口的 AntD ConfigProvider/reset.css；补充 6 项布局回归测试。typecheck、admin 测试与 client/admin 构建均通过。

### Git Commits

| Hash | Message |
|------|---------|
| `4ba73029` | feat(admin): 迁移 AdminLayout 到 app-shell |

### Status

[OK] **Completed**


## Session 21: 完成后端 Lombok 移除：9 模块手写化并移除依赖
<!-- trellis-session: v=2 fp=45963754c4ada0d2 -->

**Date**: 2026-09-28
**Task**: 完成后端 Lombok 移除：9 模块手写化并移除依赖
**Branch**: `feat/admin-dashboard-block`

### Summary

将 backend/business 全部 9 个 Java 模块的 Lombok 注解替换为手写等价 Java，并移除父 POM、9 个子 POM 与 README 的 Lombok 依赖。本会话清理 common 残留注解、迁移 pojo/vo(35)、pojo/entity(20)、client(30)、admin(11) 及 agent/app/auth/log/infrastructure 残余 12 个文件，共 108 个文件。验证：mvn clean test 110/0/0（基线 95）、9 模块签名零漂移（224 类）、2149 个生成方法体中仅 4 处纯格式化差异、check_javadoc 3717 声明 0 违规、backend/business 零 Lombok 引用、OpenAPI 与 DB schema 未改动。

### Git Commits

| Hash | Message |
|------|---------|
| `690de064` | refactor(common): 清除残留 @Getter/@Setter 注解 |
| `ef248cf0` | refactor(pojo): 移除 Lombok 并显式声明访问器与构建器 |
| `a392c93f` | refactor(client): 移除 Lombok 并显式声明构造器与访问器 |
| `313f46cd` | refactor(admin): 用显式构造器替换 @RequiredArgsConstructor |
| `667bd8a2` | refactor(agent): 移除 Lombok 并显式声明构造器 |
| `a09b11d9` | refactor(app): 移除 @Data 并显式声明配置属性访问器 |
| `9429a0b0` | refactor(auth): 移除 Lombok 并显式声明访问器与构造器 |
| `b02431af` | refactor(log): 用显式构造器替换 @RequiredArgsConstructor |
| `256d2630` | refactor(infrastructure): 移除 Lombok 并显式声明访问器 |
| `f2642b76` | test(后端): 补充 Lombok 迁移后的 JSON 往返回归测试 |
| `522f6ad2` | chore(构建): 从父 POM 与 README 移除 Lombok 依赖 |
| `e2fb74a8` | docs(规范): 移除已失效的 Lombok 生成成员 Javadoc 豁免 |
| `d983bfc6` | docs(任务): 记录 Lombok 移除完成状态与验证证据 |

### Status

[OK] **Completed**


## Session 22: admin 全页面迁移到 shadcn 并移除 Ant Design
<!-- trellis-session: v=2 fp=7598ac2ff429c596 -->

**Date**: 2026-09-29
**Task**: admin 全页面迁移到 shadcn 并移除 Ant Design
**Branch**: `feat/backend-lombok-removal`

### Summary

完成 09-21-admin-pages-migration 阶段 E–G：Import/Logs/Subjects/AgentConfig/AgentChat 五个页面从 Ant Design 迁移到 shadcn/ui + Tailwind，逐页测试验证并保留全部既有契约（Import 3000ms 轮询与失效 effect、Logs 4 卡口径与 action 回填 setPage(1)、Subjects 6 个筛选维度、AgentConfig staleTime Infinity、AgentChat 流式交互与思考折叠）。顺带修三个真实 bug：ui/button.tsx 缺 forwardRef 导致 AlertDialogTrigger asChild 传入 ref 失败；AgentConfig 配置刷新会覆盖用户正在编辑的表单值；react-markdown 被 client/admin import 却未在任何 package.json 声明，npm install 修剪后构建直接失败。阶段 F 删除 admin 的 antd/echarts/echarts-for-react，vite manualChunks 改为 vendor-react/vendor-data/vendor-ui，产物无 antd chunk。阶段 G 更新 4 份前端 spec。typecheck/test/build 全绿：client 6 + shared 7 + admin 55 = 68 passed。父链任务 09-21-admin-tailwind-shadcn-dashboard 4/4 完成并归档。

### Git Commits

| Hash | Message |
|------|---------|
| `2faddc55` | refactor(admin): Import 迁移到 shadcn，保留轮询与失效 effect |
| `056acfa3` | refactor(admin): Logs 迁移到 shadcn，保留筛选与分页语义 |
| `40003f1f` | refactor(admin): Subjects 迁移到 shadcn，保留 6 个筛选维度与表单校验 |
| `7d3c878a` | refactor(admin): AgentConfig 迁移到 shadcn，修正配置刷新覆盖用户编辑 |
| `78378fa9` | refactor(admin): AgentChat 迁移到 shadcn，保留流式交互 |
| `1b909fda` | chore(admin): 移除 antd/echarts 依赖，声明 react-markdown |
| `80b3c4d8` | docs(spec): 更新前端规范以反映 admin 已脱离 Ant Design |

### Status

[OK] **Completed**

## Session — 09-21-agent-test-coverage-backfill 测试盲区补齐

### Summary

补 3 处此前零测试覆盖的 Agent 盲区，`uv run pytest` 由 516 → **585 passed**（+69，6 xfailed）。

先复核代码发现原任务 6 类盲区中 health / Evidence 重复 ID / streaming 持久化失败已被其它任务落地，范围收窄为 3 类真盲区：

- `tests/api/test_sse_serialization.py`（16 passed）：五类事件 → wire `type` 映射、`end` 以 `is_end=true` 表达（`MessageType` 枚举不含 `end`，默认 `type="answer"`）、`exclude_none` 剔除空字段、`data: ` 前缀 + `\n\n` 分帧、`ensure_ascii=False`、响应头（`text/event-stream`/`no-cache`/`keep-alive`/`X-Accel-Buffering`）、逐帧消费。
- `tests/agent/test_gateway_routing_result.py`（29 passed, 4 xfailed）：`_resolve_routing_result` 全部 5 个 `raise` 点与合法路径；含 `extract_text` 的 content 块列表形态。
- `tests/agent/test_collection_progress.py`（24 passed, 2 xfailed）：13 个分支点，含写入门禁拒绝矩阵（5 例，断言 Business 零调用）、404/409 清理与 409 非「重新生成」保留、COMPLETED/PREVIEW_CHANGED/无 previewId 三分支、既有动作不被误清。

**补测暴露 2 处真实缺陷**，按任务「纯补测不改生产代码」约束未修复，以 `xfail(strict=True)` 钉住并转新任务：

1. `gateway.py:129` — JSON 为标量/数组（`"x"`/`123`/`true`/`["a"]`）时 `(data or {}).get` 抛 `AttributeError` 而非 `ValueError`；调用方 `:157` 无本地捕获，异常穿透图执行层，与其余 4 条判定语义不一致。→ `09-29-gateway-scalar-json-attributeerror`
2. `collection_progress.py:44,65` — 裸调 `data.get`；`HttpBusinessGateway.request` 在 Java 成功但 `data` 为 null 时显式 `return None`（`business_http.py:68`）。**同目录其它 5 个模块均用 `isinstance(data, dict) and data.get(...)` 守卫**，仅此处遗漏。→ `09-29-collection-progress-none-guard`

选用 `xfail(strict=True)` 而非普通 `xfail`：缺陷被修复后用例会变红，强制清理标记，避免「已修但标记留存」或「标记被忽略后无人回归」。

spec 同步：`agent-guidelines.md` 新增「Gateway 路由结果解析」与「Business 响应守卫」两节（含两处已知缺陷条、守卫写法对照表、SSE 帧格式与 `end` 语义澄清）；`quality-guidelines.md` 更新测试基线至 585 并登记 `xfail(strict)` 的登记约定。

`app/`、`business/`、`frontend/` 零改动，仅新增 3 个测试文件。

### Git Commits

| Hash | Message |
|------|---------|
| `4c70abbf` | chore(trellis): 重设计任务板并归档三个已完成任务 |
| `4c9a65ba` | test(agent): 补齐 SSE 序列化、gateway 路由解析与 collection_progress 测试 |

### Status

[OK] **Completed** — 任务已归档；2 处缺陷转 `09-29-*` 新任务待修


## Session — 10-04-db-schema-slim 收尾（R7 执行 + 归档）

### 完成
- R7 生产重建全部落地：备份实测可还原 → 20 表重建 → 用户三表恢复 → season 2026-autumn 136 条验证 → 索引重建 5368 SEARCH + 136 RAG 全 COMPLETED → backfill 4080 ENTITY_DETAIL 清零 → recent 增量 101 条 + 增量 backfill 清零
- 终态对账全绿（AC1/2/6/7）；person 3086 / character 994 全 COMPLETE；credit 未解析 0
- 验证：pytest 629 passed / mvn EXIT=0

### 教训（已写入 implement.md / runbook）
1. Clash fake-IP 轮流劫持 `dashscope.aliyuncs.com` 与 `api.bgm.tv`，同一时刻只放行一个；Python/OpenSSL 直连 TLS 被截而 curl/schannel 通。解法：Python 显式 `HTTPS_PROXY=http://127.0.0.1:7897`；但 embedding 仍间歇断 → 索引增量（SEARCH 8937 PENDING）用户决定跳过，网络稳定后 `jobs.indexer.main --index-version v1` 可接上（attempts<5 可重试，任务不丢）
2. 多进程 backfill：`claim_batch` 同事务 lease 回收 UPDATE + `FOR UPDATE SKIP LOCKED` → 1213 死锁。临时并行 worker（跳过 lease UPDATE，8 进程）10 分钟跑完 4080 条；长期：lease 回收拆独立低频任务
3. `mysqldump/mysql` 还原必须 `--default-character-set=utf8mb4`（客户端侧），否则 GBK 错位误报「备份损坏」
4. AC2 credit 比对必须按 `bangumi_id`（subject.id 自增重灌后重排）

### Git Commits
| Hash | Message |
|------|---------|
| `8d48e2cc` | docs(task): R7 全部完成——索引重建+backfill 清零，终态对账全绿 |
| `b4328ebe` | docs(task): recent 增量导入完成，索引增量跳过（fake-IP 网络受限） |

### Status
[OK] **Completed** — 任务归档；索引增量遗留已记录于 implement.md（非缺陷，网络恢复后可续）
