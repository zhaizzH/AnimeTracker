# 实施计划：按标题设置收藏类型与写入意图路由

## 1. 实现顺序

1. **共享收藏状态检查 + 网关写方法（行为保持）**
   - 抽 `wishlist.py::_check_collection_state` 到 `app/agent/client/actions/collection_state.py::check_collection_state`，wishlist 改为引用；先跑既有 wishlist/subject_resolution 回归证明零行为变化。
   - `ports.py` + `business_http.py` 新增 `save_collection(subject_id, *, collection_type, token, rate=None, ep_status=None)`；加适配器单测断言方法、路径、JSON body、Authorization。

2. **扩展待处理状态联合**
   - `pending_action.py` 新增 `SetCollectionTypePendingAction`（SET_COLLECTION_TYPE），并给 `SubjectResolutionPendingAction` 加可选 `collection_type`（alias collectionType，默认 None，旧 JSON 兼容）。
   - 补判别解析、序列化往返、旧类型兼容测试。

3. **泛化解析与选择分派**
   - `subject_resolution.py` 抽出 `_resolve_candidates(...)`；`resolve_subject_by_title` 改为调用它（想看行为不变，回归证明）。
   - `select_resolved_subject` 依据 `pending.collection_type` 分派到想看预览或 SET_COLLECTION_TYPE 预览；None 分支必须与 09-16 完全一致。

4. **实现设类型预览与写入**
   - `collection_type.py`：`build_collection_type_preview(...)`（ADD/NOOP/CHANGE 三态）+ 工具 `set_subject_collection(title, collection_type: Literal[1,2,3,4,5], subject_id?)`、`execute_set_collection_type`、`cancel_set_collection_type`。
   - `/save` 结果解释：None=成功、409=已收藏无变化、404=条目不存在、code None=基础设施错误保留动作。

5. **路由与提示词**
   - `gateway.py`：扩写入词表（复合动词短语，保留否定守卫，不加裸名词）；`RECOMMEND_PENDING_ACTION_TYPES` 增加 SET_COLLECTION_TYPE；SUBJECT_RESOLUTION 路由沿用。
   - `gateway_prompt.md` 补 recommend_agent 写入职责并显式把纯查询留给 search/discover。
   - `recommend_agent_prompt.md` 补单标题写入流程、类型映射(1..5)、“加入想看”仍走 `resolve_subject_by_title`、类型变更须在预览可见、两段式确认。
   - `run.py::_build_pending_context` 增加 SET_COLLECTION_TYPE 分支与 SUBJECT_RESOLUTION 的目标类型提示。
   - `recommend.py` 注册三个新工具。

6. **执行质量门禁**
   - 先跑受影响测试（collection_type、subject_resolution、wishlist、gateway/routing、pending_action），再跑 `uv run pytest tests/agent` 与全量 `uv run pytest`。
   - 跨层核对：`/save` body 字段与 DTO 一致、type 枚举与前后端一致、SET_COLLECTION_TYPE 写入边界与确认、SUBJECT_RESOLUTION 向后兼容、想看链路零回归。
   - 未改 OpenAPI（endpoint 已存在）；如后续触及 Business 再同步文档。

## 2. 重点文件与回滚点

### 重点文件

- `backend/agent/app/agent/client/actions/collection_type.py`（新增）
- `backend/agent/app/agent/client/actions/collection_state.py`（新增）
- `backend/agent/app/agent/client/actions/subject_resolution.py`
- `backend/agent/app/agent/client/actions/wishlist.py`
- `backend/agent/app/chat/pending_action.py`
- `backend/agent/app/agent/client/gateway.py`
- `backend/agent/app/agent/client/recommend.py`
- `backend/agent/app/agent/run.py`
- `backend/agent/app/agent/ports.py`、`backend/agent/app/adapters/business_http.py`
- `backend/agent/resources/prompt/client/gateway_prompt.md`、`recommend_agent_prompt.md`
- `backend/agent/tests/agent/`

### 回滚点

- 步骤 1（共享检查 + 网关方法）纯增量/行为保持，可独立回退。
- 步骤 2-3 接入前后各跑一次 09-16 想看回归；`select_resolved_subject` 的 None 分支若回归，先撤回 collection_type 分派。
- 步骤 4-5 若导致推荐/想看回归，可先撤回 `set_subject_collection` 注册与路由词表新增；不得绕过预览确认或静默覆盖来“修复”失败。

## 3. 验证命令

```powershell
Set-Location backend/agent
uv run pytest tests/agent -q
uv run pytest -q
```

无 `uv` 时用项目既有 Python 测试入口跑同等测试，不跳过全量 Agent 测试。

## 4. 必测场景

- 路由：加入/添加到/标记为 + 追番/在看/看过/搁置/抛弃/想看 → recommend_agent；“不要/别/取消”不误触发；“我的追番进度/追番日程/我收藏了什么/番剧详情”不被写入词表误触发。
- 解析复用：Business 唯一精确 → 不进 SUBJECT_RESOLUTION；成功空 → 回退 RAG；Business 异常 → 不回退不预览；`/batch` 只留 active/type2/nsfw，excludeCollected=false。
- 多候选：SUBJECT_RESOLUTION 携带 collection_type；按序号/唯一名选择后进入该类型预览；歧义名/越界/用户不匹配/过期/候选失效的处理与 09-16 一致。
- 预览三态：未收藏→ADD；已在目标类型→NOOP 不建动作不写入；他类型→CHANGE 展示 当前→目标。
- 写入：确认→/save 成功 clear 并汇报；409→告知已收藏不算失败；404→报错 clear；基础设施错误(code None)→保留动作不宣称成功；未确认/取消→不写入。
- 类型安全：collection_type 越界/非整数被 schema 拒绝；模型不能提交任意 subjectId（只走解析/选择）。
- 兼容与回归：SET_COLLECTION_TYPE 判别解析与序列化往返；带/不带 collectionType 的 SUBJECT_RESOLUTION 都能解析；09-16 想看链路、多番剧推荐批量加入想看、进度更新全部通过。
- 适配器：save_collection 断言 POST 路径、`{type,rate,epStatus}` body、Bearer 透传。

## 5. 启动前门禁

- `prd.md`、`design.md`、`implement.md` 已完成并通过规划摘要审核。
- 三个 Open Questions 已由用户确认（已收藏按意图变更并预览可见、全部类型 1..5、路由词表+提示词双保险）。
- 用户在最新规划摘要后明确批准实现。
- `python ./.trellis/scripts/task.py validate .trellis/tasks/09-20-watchlist-title-resolution` 通过。
- 过门禁后 `task.py start`，再读 `trellis-before-dev` 进入编码。
