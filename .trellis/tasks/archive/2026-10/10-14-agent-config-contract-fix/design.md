# 设计：Admin Agent 配置页契约修复

## 边界

**改动范围**：`frontend/admin/src/pages/AgentConfig.tsx`（主）、`AgentConfig.test.tsx`（契约对齐）。

**不动**：后端 `admin_config.py` / `schemas/admin_config.py` / `config_service.py` / `model_config_repository.py`。后端"整体替换"语义保持原样——保全未呈现字段是前端职责（见"权衡"）。

## 契约（唯一真源：Python schema）

```
GET  /admin/agent/prompts        -> [{promptKey: string, promptContent: string}]
GET  /admin/agent/prompts/{key}  -> {promptKey, promptContent}
POST /admin/agent/prompts/{key}/update   body {promptContent} -> {promptKey, promptContent}
POST /admin/agent/prompts/{key}/reset    (no body)            -> {promptKey, promptContent}
GET  /admin/agent/config         -> {model?, modelRoute?, temperature?, maxTokens?, thinkingBudget?, reasoningEffort?}
POST /admin/agent/config/update  body 同 GET（exclude_none），整体替换
```

前端已由 `http.ts:29` 解包 `body.data`，故 UI 直接拿到上表右值。

## R1 列表解析

删掉双分支猜测，只留一条：

```ts
const ks = Array.isArray(raw) ? raw.map((x) => x.promptKey) : [];
```

`adminAgentApi.prompts` 在 shared 里声明的返回类型是 `Record<string, unknown>`，与真实"数组"不符，故此处仍需 `Array.isArray` 收窄。**不改 shared 的类型声明**（会波及 admin 其它调用点），在页面内注释说明偏差来源。

## R2 保存防覆盖（关键安全行为）

现状：`loadDetail` 用 `.catch(() => ({}))` 吞掉 404，`content` 变空串，而按钮 `disabled={!selected || isPending}` —— `selected` 仍有值，于是**空内容可提交**，直接覆盖线上提示词。

修法：新增 `loaded` 状态，仅在详情**成功**返回后置真；切换条目时先置假。保存按钮条件加 `!loaded`。

```
loadDetail(k):
  setSelected(k); setContent(''); setLoaded(false)
  try  -> d = await promptDetail(k); setContent(d.promptContent ?? ''); setLoaded(true)
  catch -> setLoaded(false); toastError(...)
```

按钮：`disabled={!selected || !loaded || savePrompt.isPending}`。

这会顺带让 R6 的部分场景变安全：切到新条目、响应未到期间按钮不可点。

## R3+R4 字段保全与补齐

两种策略：

- **A（合并）**：保留一个 `serverCfg`（GET 的原始对象），提交时 `{...serverCfg, model, temperature, maxTokens, thinkingBudget}`。
- **B（补字段）**：把 `modelRoute`、`reasoningEffort` 做进表单，提交全部 6 个字段。

**采用 A+B**：B 解决"无法在页面编辑这两个字段"（PRD R4），A 兜住未来后端再加字段时的同类丢失。仅 A 会留下字段不可编辑；仅 B 在新增第 7 个字段时复发。

实现要点：`serverCfg` 存 GET 原始对象，随 `modelCfg.data` 更新；提交时以它为底。注意 `exclude_none` 语义——值为 `undefined` 的键前端不发送，不会把 `null` 写进去。

## R5 错误态

```
promptsData.isLoading -> 加载中…
promptsData.isError   -> 加载失败 + 重试按钮（refetch）
!isLoading && keys.length === 0 -> 暂无提示词
```

三分支互斥，顺序即优先级。

## R6 竞态

用请求序号守卫：

```ts
const seq = useRef(0);
const loadDetail = async (k: string) => {
  const my = ++seq.current;
  ...
  const d = await promptDetail(k).catch(() => null);
  if (my !== seq.current) return;   // 已被更新的请求取代，丢弃
  ...
};
```

`useRef` 而非 state：序号参与渲染无意义，只需跨 await 保持。

## R7 重置错误

`resetPrompt` 补 `onError: (e) => toastError((e as Error).message)`，与 `savePrompt` 一致。

## 权衡与取舍

- **为什么不让后端做合并？** 后端 `set()` 是 `SET`，改成读-改-写会引入并发写覆盖窗口（两个管理员同时保存）。前端保全更简单且无并发面。后端 `ModelConfig` 全字段可选 + `exclude_none` 本就支持稀疏更新，A 方案正好利用这一点。
- **为什么保留 `serverCfg` 而不是提交前重新 GET？** 重新 GET 有 5s 缓存（`model_config_repository.py:7` `_REFRESH_SECONDS`），且多一次往返；`serverCfg` 与表单同源，语义更明确。
- **`loaded` 与 `content` 空串的区别**：合法的空提示词（真的把内容清空）与"没加载到"必须区分，故用独立布尔量而非 `content !== ''`。

## 兼容性 / 回归面

- 后端无改动，契约不变，其它调用 `adminAgentApi` 的页面（`AgentChat` 用 chat* 系列）不受影响。
- 测试文件 `AgentConfig.test.tsx` 的 mock 形状必须同步改，否则新代码在旧 mock 下会渲染空列表（这正是本次要修的类问题）。
- 现有 7 条用例中，依赖 `{keys: [...]}` 的两条需改 mock 形状，其余断言保持。

## 回滚

改动仅限两个前端文件，`git checkout` 该二文件即可；无数据迁移、无接口变更。
