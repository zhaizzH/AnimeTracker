# Agent 模块测试报告

测试日期：2026-09-12（Asia/Shanghai）。代码基线：main / ba25c7b3。执行范围：现有自动化测试、真实 HTTP/SSE 对话、隔离故障复现、真实浏览器页面。按用户要求，仅测试与报告，未修复业务代码。

**结论：基础聊天可用，尚不满足完整验收。收藏预览被空响应误判阻断，流式错误被代理误报为未登录，完整 Python 测试仍无法通过收集。正常回答保存通过，但兜底与存储失败场景存在缺陷。**

## 1. 本次结果

| 检查 | 本次结果 | 解释 |
|---|---|---|
| 服务 | 用户端 5173、管理端 5174、Business 8080、Agent 8090 均响应 | Business health=UP，Agent health=ok、llm_configured=true |
| Python 全量收集 | 271 项已收集，1 个文件导入错误 | 不是全量通过 |
| Python 隔离诊断 | 271 passed，1.62 秒 | 显式排除 test_capability_route.py 后执行 |
| 前端现有测试 | 15 passed | shared 6、client 6、admin 3 |
| 前端类型检查 | 3 个 workspace 通过 | shared、client、admin |
| Business Maven | 37 tests，0 failures/errors，BUILD SUCCESS | 11 个测试类，包含代理配置、授权、Evidence；不等于完整在线集成覆盖 |
| 真实 API 对话 | 18/18 正常结束且回答与历史一致 | ADMIN 8、USER 8、USER 推荐/预览对照 2；内容正确性另列 |
| 页面 | 登录、新建、发送、刷新后正文恢复通过，无 pageerror | 1 轮真实对话；生成中无停止入口 |
| 权限 | USER 管理员接口 403；跨用户历史 404 | 跨用户流式被拒绝，但代理错误码错误 |
| RAG 证据 | 用户调用 rag_search_subjects、rag_recommend_subjects；词法接口返回 v1 / subject-profile-v1 | 没有采集在线向量召回日志，不能断言本轮走了向量混合召回 |

真实角色来自登录结果：test1=ADMIN，test2=USER。同一客户端 API 会按角色选择不同 Agent；管理员结果不能算作普通用户能力验证。

## 2. 优先处理的缺陷

### F01 · P1 · 未收藏条目无法加入待确认队列

**真实复现：** test2 输入“请推荐《无职转生 第三季》（站内ID 84），并调用预览加入想看工具，等待确认，禁止执行写入。”实际调用了 `preview_add_to_wishlist`，却返回 `pendingItems=[]`，并将 84 放入 `skippedItems`，`existingType=null`。

权威接口 `GET /api/client/collections/84` 返回 `200 {code:200,message:success}`，没有收藏数据。隔离复现同样将该响应解释为 `collected=true`，没有生成 pending action。

**原因：** [Result.java](../../backend/business/common/src/main/java/top/zhaizz/common/result/Result.java) 使用 NON_NULL 省略空 data；[business_http.py](../../backend/agent/app/adapters/business_http.py) 第 60 行 `body.get("data", body)` 将完整 envelope 当作业务记录；[wishlist.py](../../backend/agent/app/agent/client/actions/wishlist.py) 使用 `data is not None` 判断已收藏。

**建议：** 统一空 data 的解包契约，覆盖“字段缺失 / 显式 null / 已收藏记录 / 404 / 其他错误”；修复后再验证预览、确认、幂等。证据：[empty-collection-results.json](./empty-collection-results.json)、[live-action-results.json](./live-action-results.json)。

### F02 · P1 · 合法登录下的输入错误被代理变成 401

同一个有效令牌、同一个请求体的对照结果：

| 输入 | 直连 Agent 8090 | Business 8080 |
|---|---|---|
| 空 content | 422 | 401 未认证 |
| 4097 字符 | 422 | 401 未认证 |
| 其他账号的测试会话 | 404 | 401 未认证 |
| 不存在的会话 | 404 | 401 未认证 |

**影响：** 用户收到错误的登录提示，客户端无法正确区分输入不合法和会话不可访问。没有发生越权读取。

**定位：** [ClientAgentController.java](../../backend/business/agent/src/main/java/top/zhaizz/agent/controller/ClientAgentController.java) 提前设置 SSE 响应并取得 writer；[AgentServiceImpl.java](../../backend/business/agent/src/main/java/top/zhaizz/agent/service/impl/AgentServiceImpl.java) 会将上游错误抛出；[SecurityConfig.java](../../backend/business/app/src/main/java/top/zhaizz/app/config/SecurityConfig.java) 默认拒绝其他路径。错误派发被安全层覆盖是待进一步日志确认的原因，当前已确定的是端到端错误码不一致。

**建议：** 覆盖真实 Controller/SSE 错误响应，保留 400/422、404 等语义；不要将所有失败引导为重新登录。证据：[error-mapping-results.json](./error-mapping-results.json)。

### F03 · P1 · 兜底回答显示正常，保存内容为空

隔离 workflow 只返回 `result="fallback answer"`，不发正文增量。`stream_agent_events` 输出 answer/end，但保存回调收到空字符串。

**定位：** [streaming.py](../../backend/agent/app/chat/streaming.py) 第 139–149 行，兜底文本未追加至 `aggregated_answer`。

**建议：** 所有显示给用户的最终正文采用一致的聚合与保存路径。此次 18 轮在线正常回答未触发此问题；本项是确定性的隔离复现，不是线上历史丢失统计。证据：[isolated-results.json](./isolated-results.json)。

### F04 · P1（测试门禁）· 完整 pytest 无法收集

[test_capability_route.py](../../backend/agent/tests/agent/test_capability_route.py) 第 3 行导入不存在的 `_capability_agent`；同文件还引用不存在的 `_is_rag_capability_question`、`_NON_CHINESE_THINKING_FALLBACK`。本次实际首先失败于 `_capability_agent`。

**复现：** 在 `backend/agent` 运行 `.venv/Scripts/python.exe -m pytest --collect-only -q`。

**建议：** 先明确能力路由的目标契约，再使实现与测试一致。排除文件仅用于诊断，不能作为修复或 CI 通过依据。

## 3. 其他已复现问题

| ID / 等级 | 复现与影响 | 定位与建议 |
|---|---|---|
| F05 / P2 | “先搜索…然后预览加入想看”只调用搜索、详情、收藏读取；回答自述无写入工具，未调用预览工具 | gateway Prompt 只将“推荐番剧”列为推荐节点职责。复合意图应保留后续动作并选择能处理该动作的节点。见 live-user-results 的 preview |
| F06 / P2 | 请求推荐 2026 年高评分动画，4 次检索中从带年份逐步退化为“高评分热门动画”“动画”，最终承认无法核验年份 | 推荐重试丢失条件；`_compact` 也不输出 airDate。建议固定结构化条件，并向回答层保留年份证据。见 live-user-results 的 recommend |
| F07 / P2 | 搜索回答把 ID 84 称为 FINISHED；剧集接口仍含 2026-09-13、09-20、09-27 的计划日期 | `use_case.py::_infer_air_status` 把任何已过首播日都标记 FINISHED，且使用本机日期。建议使用权威播出状态，未知时保留 UNKNOWN；不能由首播日期推导完结 |
| F08 / P2 | “宫崎骏参与制作”按实体名检索后，回答断言数据库没有记录；但线上组合根未接名称解析器 | main.py 两分支注入 entity_name_lookup=None；rag_tools.py::_items 将 unavailable 和正常空结果都变成 []。应将“名称解析不可用”和“无结果”传递给模型，避免不成立的不存在断言 |
| F09 / P2 | 模拟回答或 pending 存储异常，仍发正常 end，客户端无法辨别保存失败 | streaming.py 捕获回调异常后 pass。建议可观测地报告持久化失败，并明确定义部分成功；未对真实 Redis 注入故障 |
| F10 / P2（交互缺口） | 页面生成过程中只有加载中的发送按钮，没有停止入口 | AgentConversation 未消费 Hook 暴露的 stop。页面截图与按钮清单已保存；真实页面停止生成未能执行 |
| F11 / P3 | reasoning chunks `I `、`will `、`search` 拼接成 `Iwillsearch` | runtime.py 第 54–55 行对每块 strip。建议保留块边界空格，仅用 trim 判断是否为空 |
| F12 / P3 | `_is_explicit_confirmation("没问题")=false`，但该词在白名单；`确认？=true`，问号检查失效 | gateway.py 先移除问号再判断否定标记，且“没”拦截白名单。仅证明解析分支不一致，未验证导致真实误写 |

附加观察：管理员首轮出现英文开头 `I'll search for that title.`；后续轮次声称上一轮未调用工具，但 SSE 已记录上一轮 4 次搜索。语言与自述一致性仍需要多次回放，不能以这一次样本估计发生率。

## 4. 页面与证据解释

[ui-results.json](./ui-results.json) 记录了页面结果。最初的 `history_text_matches=false` 比较了含“思考过程”的整块文本；按当前契约思考过程不恢复到历史。单独对比回答正文 `answer_body_matches=true`，因此**不将该 false 误报为正文丢失**。

[生成中截图](./ui-streaming.png) · [回答完成截图](./ui-complete.png)。截图由实际浏览器测试保存；本次图片查看工具受沙箱错误影响，页面结论依据 Playwright DOM、交互与错误监听。

浏览器连接工具两次初始化失败，随后使用已有 Playwright 隔离浏览器完成页面操作。首次页面探针因 Ant Design 的“登 录”空格匹配失败，修正定位器后通过；这是测试脚本问题，未列为产品缺陷。

## 5. 复跑与未覆盖范围

| 证据 / 入口 | 用途 |
|---|---|
| [pytest-diagnostic.xml](./pytest-diagnostic.xml) | 排除失效文件后的 271 项明细 |
| [java-summary.json](./java-summary.json) | 本次 Maven 37 项结果汇总 |
| [live-admin-results.json](./live-admin-results.json)、[live-user-results.json](./live-user-results.json)、[live-action-results.json](./live-action-results.json) | 输入、工具事件、回答、时延和历史一致性 |
| [boundary-results.json](./boundary-results.json)、[error-mapping-results.json](./error-mapping-results.json) | 权限、输入、目录/剧集、索引版本与错误码对照 |
| [isolated_probe.py](./isolated_probe.py)、[empty_collection_probe.py](./empty_collection_probe.py) | 无真实存储写入的缺陷复现 |

在线探针从标准输入接收登录 JSON，文件不包含密码或令牌。运行前确认使用测试账号。`live_probe.py`、`action_probe.py` 会创建测试会话并消耗模型调用；不要把输出文件覆盖为新一轮结果后仍沿用本报告统计。RAG 状态/空结果的额外函数级复现记录在 isolated-results.json。

本次共完成 18 轮 API 对话与 1 轮页面对话；创建的测试会话保留供复查。未执行真实收藏/进度写入、数据导入、索引发布、配置变更或删除。工作区只新增 reports 下的报告与探针；没有修复或提交业务代码。

**未覆盖：** 实际确认写入及幂等、进度批量更新、真实网络断线恢复、并发/负载、管理员页面交互、Prompt/模型配置热更新、真实向量召回路径和长时间灰度。预览被 F01 阻断；上述未覆盖项不能计为通过。停止生成因缺少页面入口记录为 F10。

**建议下一步：** 优先修复 F01 空收藏解包，再修复 F02 错误码与 F03 保存路径；恢复 F04 门禁后，用相同测试账号复跑预览→确认→历史一致性。
