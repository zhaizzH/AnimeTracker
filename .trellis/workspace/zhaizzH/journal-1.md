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
| `59d5a88` | feat: 全量完善 README.md 相关文档与实施计划 |

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
| `c1e1453a` | feat(rag): 完善Bangumi混合检索门禁 |

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
| `2eceefbc` | 完成 RAG v1 发布门禁与激活 |
| `5ee0072b` | 整理 Bangumi RAG 会话日志 |

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
| `4f02607c` | docs(spec): 按当前源码更新项目开发规范 |

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
| `f8c915b3` | fix: 修复 Agent 运行时与测试报告问题 |

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
| `9a732b22` | fix(business): 完成规范复核缺陷修复与文档校验 |

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
| `9a732b22` | fix(business): 完成规范复核缺陷修复与文档校验 |
| `937bdcff` | chore(trellis): 归档规范复核修复并记录验证 |

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
| `3861752b` | docs(java): 规范自然中文注释 |
| `67b4ed8f` | docs(java): 补齐注释规范示例 |

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
| `ef8775b` | style(java): 统一后端中文注释标点 |

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
| `62c7086a` | feat(agent): 按标题设置收藏类型(1-5)与写入意图路由 |

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
| `01095e23` | feat(agent): 写入硬确认门禁(write_confirmed)与动作版本绑定 |

### Testing

- [OK] uv run pytest 全量 351 通过；execute 工具对模型零可见参数；图状态传播实证三场景(写入意图非确认→False、确认+pending→True、重发非确认+pending→False)。完整 LLM E2E 因 DeepSeek 402 余额不足未能跑，待充值补做

### Status

[OK] **Completed**

### Next Steps

- 分支 feat/write-confirmation-hard-gate 未合并；DeepSeek 充值后补一次真实 LLM E2E(标记为看过→确认写入→重发非确认不写)；后续按序做 T1 季度对齐→T2 RAG正确性→T4 测试补齐
