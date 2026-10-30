# 设计补充：`ui_action` SSE 事件端到端打通

> 承接 `prd.md` / `implement.md`。**D1 修正了 spec §6 的重放过滤方案**——原方案有游标错位 bug。

## D1 重放不跳过，改打 `replayed` 标记（修正 spec §6）

### 原方案的 bug

spec §6 写「`subscribe(after=cursor)` 重放段跳过 `UI_ACTION`」。但前后端的游标语义是：

- 前端 `after` = **已收到的帧数**（`useAgentChat.replayRun` 里 `frames += 1`，见
  `frontend/packages/shared/src/hooks/useAgentChat.ts`）
- 后端 `start = max(after, run.buffer_start)`，切 `run.events[start - buffer_start:]`
  （`app/chat/runs.py::_subscription`）

跳帧之后这两个计数不再对位。具体反例：

```
run.events = [answer#0, ui_action#1, answer#2, answer#3]

重连 after=0 → 后端吐 3 帧（跳过 #1）→ 前端 frames=3
再断开，重连 after=3 → 后端切 events[3:] → answer#3 再吐一次
→ 正文重复
```

反向也会漏：若跳过 2 帧，前端 frames 比真实下标少 2，下次 `after` 偏小 → 重复更多。

### 定案

**重放段照常吐 `ui_action`，但在 `meta` 里补 `replayed=true`。前端见到带 `replayed` 的
`ui_action` 直接忽略（不执行、不提示、不计数以外无副作用）。**

帧数与 `run.events` 下标保持 1:1，游标天然对齐，无需改 `after` 的语义。

```python
# app/chat/runs.py::_subscription 重放段
for event in run.events[start - run.buffer_start:]:
    if event.type is AgentEventType.UI_ACTION:
        yield self._with_run_id(run, self._mark_replayed(event))
        continue
    yield self._with_run_id(run, event)
# 实时订阅段（queue 循环）不动，不打标
```

`_mark_replayed` 复用 `_with_run_id` 的「重建 frozen dataclass + 合并 meta」写法，
**不原地改 `event.meta`**——`AgentEvent` 是 `frozen=True`，且缓冲里那份要保持原样供回溯。

语义表述从「实时=执行，重放=展示」细化为：
**重放帧仍然下发（保留可回溯与游标对齐），但带 `replayed` 标记，执行权在前端。**

### 为什么不是另外两条路

- **加 `meta.seq` 绝对下标**：要对所有帧组装点加序号，改动面比打一个大得多，
  且 `after` 语义变更会影响既有重连逻辑，回归风险高。
- **前端按 `action_id` 去重**：需要跨会话唯一 id，把不变量分散到每个消费者。
  spec design 已否过，本决定不改变那个判断。

## D2 `meta` 的承载与空值行为（实测确认）

`AgentEvent.meta: dict[str, Any] = field(default_factory=dict)`；
`serialize_agent_event` 传 `meta=event.meta or None`，`serialize_sse` 用 `exclude_none=True`。

结论：
- **空 dict 会被剔除**（`{} or None → None`），所以 `ui_action` 的 `meta` **必须非空**，
  否则前端拿不到 action/params。这一点本来就会满足（至少有 `action`），但要写进测试。
- `_with_run_id` 会给每帧补 `meta.run_id`，所以重放/实时帧的 meta 一定非空——
  契约测试里断言「meta 保留」时必须用**带 action/params 的事件**，不能拿空 meta 事件断言。

`ui_action` 的 `meta` 结构（本任务只定契约，不产生真实事件）：

```json
{
  "action": "open_anime_index",
  "params": {"year": 2022},
  "label": "2022 年的番",
  "replayed": true
}
```

`replayed` 仅重放段出现。`run_id` 由 `_with_run_id` 自动补，不在本契约里声明。

`Content` 不新增字段，`content` 对 `ui_action` 帧为全空对象（`{}`）。

## D3 前端 `onUiAction` 的签名与 dispatch 位置

`useAgentChat` 选项新增：

```ts
onUiAction?: (action: string, params: Record<string, unknown>, label?: string) => void
```

`dispatch` 的 switch 加：

```ts
case 'ui_action':
  if (ev.meta?.replayed) break;              // D1：重放不执行
  if (typeof ev.meta?.action === 'string') {
    onUiActionRef.current?.(
      ev.meta.action,
      (ev.meta.params as Record<string, unknown>) ?? {},
      typeof ev.meta.label === 'string' ? ev.meta.label : undefined,
    );
  }
  break;
```

- **不写正文、不进 tools 列表**（与 spec 一致）
- `SsePayload.meta` 类型从 `{ run_id?: string }` 扩为
  `{ run_id?: string; action?: string; params?: Record<string, unknown>; label?: string; replayed?: boolean }`
- 回调用 **ref 持有**（`onUiActionRef`），与既有 `apiRef`/`tokenRef` 同一理由：
  调用方传内联函数，直接进 `useCallback` 依赖会让 `makeOnEvent` 每次渲染重建。
- **实时与回放共用同一个 `dispatch`**，所以 `replayed` 判断放在 `dispatch` 内，
  两条路径自动都受保护，不必在 `replayRun` 里再判一次。
- `action` 非字符串或缺失时静默丢弃：服务端是唯一生产者，非法帧属于契约破坏，
  前端不做补救性跳转。

### 与 child 1 的接缝

本任务**只**在 `AgentChat.tsx` 提供 `onUiAction` 实现，调用 child 1 的两个 setter：

```ts
onUiAction={(action, params, label) => {
  markAgentNavigation();
  navigate(buildPath(action, params));   // 见 D4
  if (label) showNavHint(label);
}}
```

不改 `AIAssistantFloat.tsx` 内部。

## D4 前端 path 构造：直接用服务端给的 path，不重复实现映射

`navigation_emitter` 已经在服务端构造好 path+query（spec §5「服务端独占 URL 知识」）。
因此 `meta` 里**再带一个 `path` 字段**，前端 `navigate(meta.path)` 即可：

```json
{"action": "open_anime_index", "params": {"year": 2022}, "path": "/anime?year=2022&page=1", "label": "2022 年的番"}
```

理由：若前端再实现一次 action→path 映射，白名单知识就复制成两份，键名漂移时两端各自背锅。
`action`/`params` 仍保留在 meta 里供日志、测试与未来的非导航类 action 使用。

**安全约束**：前端只接受以 `/` 开头且不以 `//` 开头的 `path`，其余一律丢弃。
这是防「服务端被污染后下发 `javascript:` / 外链」的廉价兜底，不替代服务端白名单。

D2 的 meta 结构以此为准（`path` 为必填，`label` 可选）。

## D5 改动清单（在原 7 处基础上修订）

| # | 文件 | 改动 |
|---|---|---|
| 1 | `app/chat/events.py` | `AgentEventType` 加 `UI_ACTION = "ui_action"`；`AgentEvent` 字段不动 |
| 2 | `app/api/schemas/sse.py` | `MessageType` 加 `UI_ACTION`；`Content` 不动 |
| 3 | `app/api/sse.py` | 无需改逻辑（`MessageType(event.type.value)` 自动覆盖）；**补测试**锁 `meta` 非空保留 |
| 4 | `app/chat/runs.py` | 重放段 `_mark_replayed`，**不是跳过**（D1）；新增 `_mark_replayed` 静态方法 |
| 5 | `frontend/packages/shared/src/hooks/useAgentChat.ts` | `SsePayload.meta` 扩字段；switch 加 case；选项加 `onUiAction` + ref |
| 6 | `docs/spec/openapi.yaml` | `SSEFrame` type 枚举加 `ui_action`；`meta` 描述补 action/params/path/label/replayed |
| 7 | `backend/agent/tests/contracts/test_sse_contract.py` | 契约 enum 加值；`_sample_events()` 补一个带完整 meta 的 `UI_ACTION` 事件 |

第 7 处的 `_sample_events()` 必须补样本——契约测试的传递断言只对**被采样的类型**生效，
只加枚举不加样本会漏掉序列化路径的覆盖。

## D6 Java 透传：已实测，无需改动

`backend/business/agent/src/main/java/top/zhaizz/agent/controller/AgentSseResponseWriter.java`
是**逐行原样转发**（`writerRef[0].write(line + "\n")`），不解析 JSON、无类型白名单、
无 `MessageType` 枚举。

结论：`ui_action` 不需要任何 Java 改动。spec 里「疑似原样转发，需实测确认」的待办关闭。

仍需跑一次 `mvn -B clean test` 确认基线不回归，但那是常规验证，不是改动项。

## TDD 切片（修订）

- **A 契约**：先加内部枚举 → 契约测试红（wire 未覆盖）→ 加 wire 枚举 + openapi + 样本 → 绿
- **B 重放**：写「缓冲含 `ui_action`，after 重连时**帧数与缓冲一致**且该帧带 `replayed=true`」
  的失败测试 → 实现 `_mark_replayed` → 绿。
  另加一条回归：连续两次重连，`after` 用前端口径（已收帧数）不会重复或遗漏任何帧。
- **C 前端**：收到 `ui_action` 正文不变、tools 不变、`onUiAction` 被调且参数正确；
  带 `replayed` 时回调**不被调用**。
- **D path 兜底**：`path` 为 `javascript:alert(1)` / `https://evil` 时 `navigate` 不被调用。

## 不做

- 不产生真实 `ui_action`（`navigation-graph` 的事）
- 不改 `AgentEvent` 字段结构
- 不在 `_drive()` 写入侧过滤或打标
- 不改 Java 透传
- 不改 `AIAssistantFloat.tsx`（child 1）
