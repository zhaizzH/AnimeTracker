# Agent↔Business 契约测试规范

本文件是 **agent ↔ `docs/spec/openapi.yaml`** 这条边界上「哪些行为被测试钉住、怎么钉、钉不住什么」的单一来源。

> 与其他规范的关系：SSE **帧格式细节**与**待确认动作的时序/门禁**仍以 [Agent 编排与流式协议](./agent-guidelines.md#scenario-agent-sse-事件契约) 和 [Agent 安全写操作契约](./write-operations.md) 为准；本文件不复制那两处正文，只补充「这两者由哪些测试钉住、钉到什么程度」。

> **规范唯一来源（2026-10-22 起）**：本文件是契约测试规范的**唯一执行来源**。
> 此前的 OpenSpec 副本（`openspec/specs/` 下 `agent-business-contract` /
> `agent-stream-wire-contract` / `pending-action-protocol` 三份，及其 `2026-10-22` 归档变更）
> 已**整体移除**，不再与本文件共存。引用契约测试规范时只指本文件。

## 测试套件的位置与运行

```bash
cd backend/agent
uv run pytest tests/contracts -q      # 契约子集，CI 单独成步
uv run pytest -q                      # 全量（契约子集 + 其余）
```

| 文件 | 职责 | 规模 |
|---|---|---|
| `tests/contracts/_contract.py` | 契约加载器（`lru_cache` 单次解析）、路径模板匹配器（字面优先，其次唯一通配）、`$ref` 解析 | — |
| `tests/contracts/test_http_contract.py` | AST 遍历调用点 → 方法/路径/请求字段比对；契约结构完整性 | 87 |
| `tests/contracts/test_sse_contract.py` | SSE 帧 wire 形态与契约 `SSEFrame` 双向对齐 | 29 |
| `tests/contracts/test_preview_contract.py` | pending-action 持久化协议（键、TTL、判别联合、字段大小写、版本绑定） | 30 |
| `tests/contracts/test_run_route_contract.py` | Java 对外六条 run 路由、`after` 查询、GET SSE 与 run 响应、POST `/stream` 的 409 信封 | 8 |
| `tests/api/test_run_api.py` | run 路由契约：`meta.run_id` 注入、409 冲突体、归属 404、回放唯一 `is_end`、stop 幂等 | 7 |

CI 步骤位于 `.github/workflows/ci.yml` 的 `backend-python` job，名为 `contract drift (agent <-> openapi)`，在 `uv run pytest` 之前单独执行——失败时日志标题直接说明是契约漂移，而不是混在全量用例里的一条匿名 FAILED。

## 1. Scope / Trigger

- 触发：修改 `backend/agent/app/**` 下任何出站 HTTP 调用（method/path/请求字段）、`docs/spec/openapi.yaml`、SSE 序列化（`app/api/sse.py`、`app/api/schemas/sse.py`）、或 `app/chat/pending_action.py` 及其持久化路径。
- 目标：让「agent 与契约文件不一致」在 CI 变红，而不是在线上暴露。
- 不适用：契约与 Java 源码的一致性（见第 8 节边界声明，无自动校验）。

## 2. Signatures

### 契约文件与加载

- 契约事实源：`docs/spec/openapi.yaml`，**手工维护**，不是从 Java 注解自动导出。
- `tests/contracts/_contract.py::load_contract()`：`lru_cache` 保证整轮只解析一次。
- `match_operation(method, path) -> Match`：**字面命中优先**，其次唯一通配匹配；两义或零匹配均失败。

### HTTP 调用点

- 遍历 `app/**/*.py` 的 AST，识别两种形态：`<obj>.request(...)` 与 `asyncio.to_thread(<obj>.request, ...)`。
- 当前构成：**25 个调用点 = 24 个属性调用 + 1 个 `asyncio.to_thread` 健康探针**（`GET /actuator/health/liveness`，常量来自 `app.api.health`）。
- 适配器内部的 `httpx.request` 排除在外，不重复计数。

### 请求字段

- 只对**静态可判定**的载荷做字段断言：直接传入的 dict 字面量、先绑定到局部变量再传入的 dict 字面量、以及对该局部变量的字符串下标追加。
- 运行时构造的载荷（当前仅 `lexical_search` 转发调用方构造的 query dict）进显式豁免表，每条带 file、line、reason，且断言「豁免项仍对应活跃调用点」。

### PendingAction 字段大小写（易误解，单列）

| 字段类别 | wire 形态 | 例子 |
|---|---|---|
| business DTO 原样带过来的 | **camelCase** | `subjectId`、`subjectName`、`summary`、`actionId` |
| agent 自定义的信封字段 | **snake_case** | `preview_id`、`user_id`、`expires_at` |

信封必须保持蛇形，因为 Redis 里已存的就是这个形态；改成驼峰会 strand 掉现有载荷。
解析侧因 `populate_by_name=True` 对两种写法都宽容——这是刻意的，历史载荷不能读失败。

### PendingAction 持久化

- 键：`agent:pending-action:{session_id}`，**不含 user 标识**（用户绑定靠存储值，不靠键隔离）。
- TTL：默认 600 秒；值内另带 `expires_at`，使反序列化后仍可判定过期。
- 判别联合 4 个变体：`COLLECTION_PROGRESS_UPDATE`、`ADD_TO_WISHLIST`、`SUBJECT_RESOLUTION`、`SET_COLLECTION_TYPE`。
- 单一入口：`serialize_agent_event`（SSE 序列化）与 `parse_pending_action_json`（待确认动作解析）。

## 3. Contracts

- 契约文件自身必须内部自洽：`$ref` 全部可解析、**无孤儿 schema**、不含只存在于 Java 测试类的夹具路径（`/api/client/subjects/1`、`/api/client/private`、`/api/admin/private`、`/actuator/health`）。
- 每个 agent 出站调用的 method+path 必须解析到唯一 operation。
- 静态可判定的请求字段必须出现在该 operation 的 request schema properties 或 `parameters` 中。
- SSE：`type` 枚举**四值**（`answer`/`thinking`/`function_call`/`status`），**不存在 `end`**；每帧含 `type`、`content`、`is_end`、整数 `timestamp`；`content` 子字段限定为 `text`/`node`/`parent_node`/`state`/`message`/`result`/`name`/`arguments`。
- SSE 分帧：单行 `data: ` + JSON + 空行，不使用 `event:` 行。
- 错误语义分离：**工具失败** = `function_call` + `state=end` + `result=error`；**持久化失败** = `status` + `state=error` + 非空 `message`。两者不得混用。
- 恰好一个 `is_end=true` 帧收尾，且其后无任何帧（异常路径同样要产生）。

### Run 生命周期契约（2026-10-22 新增）

语义细节见 [Agent 编排与流式协议](./agent-guidelines.md#scenario-chat-run-生命周期与重连)，这里只列可测的接口事实：

| 路由 | 契约事实 |
|---|---|
| `POST /stream` | 首帧 `meta.run_id` 非空；同会话已有 `status=running` 的 run → **409**，body 为 `{"detail": {"active_run_id": str, "status": str, "capabilities": ["interrupt"]}}`；`cancelled` 不算 active |
| `GET /runs/{run_id}/stream?after=N` | 回放缓冲后继续推送；`after` 越过截断点时先发一条 `status`/`warning` 帧；整体仍只有一条 `is_end` 且位于末尾；他人 `run_id` → **404** |
| `GET /sessions/{session_id}/run` | 返回 `{run_id, status}`；会话不属当前用户 → **404**；无 run → **404** |
| `POST /runs/{run_id}/stop` | 幂等，200；只标状态不 cancel 底层 task；响应体含 `{run_id, status: "cancelled"}` |

不属于契约（故意不钉）：跨进程重连。进程重启后重跑不可恢复，`agent:run:*` 投影的 `running` 会被懒收敛为 `failed`；客户端必须能从「历史里没有这条回答」推出失败。

**`docs/spec/openapi.yaml` 已收录 Java 对外层的六条 run 路由**（client/admin 各三条，见任务 `10-27-agent-run-proxy-java`）。
其中 `GET /runs/{runId}/stream` 声明 `after` 查询参数与 `text/event-stream` 响应；会话 run 查询和 stop 声明统一响应信封。
两条 `POST /stream` 的 409 也已收录：Java 代理将 Python 的 `detail` 对象映射到统一信封的 `data`，因此浏览器看到的是 `{code: 409, message, data: {active_run_id, status, capabilities}}`，不是裸 `{detail: ...}`。
Python 直连 `:8090` 的 409 仍是 `{"detail": ...}`；两种形状由 Java 代理层明确转换。
- 确认绑定：执行时使用的 `preview_id` 必须来自已持久化的 pending action，**不受模型传入参数影响**。

## 4. Validation & Error Matrix

| 条件 | 必须行为 |
|---|---|
| `$ref` 指向不存在的 schema | 测试失败并指名悬空引用 |
| `components.schemas` 中存在无引用 schema | 测试失败并指名孤儿 |
| 契约声明了夹具路径 | 测试失败并指名该路径 |
| 调用点 method/path 无匹配 operation | 失败并报 method、path、`file:line` |
| 路径只能通配匹配但调用点不含运行时 ID | 失败（疑似拼写错误），除非显式进白名单 |
| 请求字段契约未声明 | 失败并指名 operation、字段、调用点 |
| 事件 `type` 超出四值枚举 | 失败并指名越界值 |
| 帧出现未声明的 `content` 子字段 | 失败并指名该键 |
| 工具失败被写成 `state=error` | 失败（约定是 `state=end` + `result=error`） |
| pending action 键模板/TTL 变动 | 失败并报期望值与实际值 |
| 未知 `type` 变体或损坏 JSON | 抛 `ValidationError`，不得降级为可用动作 |

## 5. Good/Base/Bad Cases

- **Good**：新增出站调用时，同时更新契约并在 `tests/contracts` 里让新调用点被自动发现；改信封字段名之前先确认 Redis 存量。
- **Base**：只改内部实现，不动 wire 形态与调用边界——契约套件保持全绿，无需改动。
- **Bad**：
  - 为了让孤儿 schema 检查通过，把 schema 加个 `$ref` 只为「消除告警」，而不真正使用它。
  - 把 `//` 之外的路径拼写错误当作「通配能匹配上」而放过（`/collections/count` 会静默落到 `/collections/{subjectId}`）。
  - 把信封字段改成驼峰以「看起来更统一」，忽略 Redis 存量兼容。

## 6. Tests Required

- **HTTP 侧**：新增/修改任何出站调用必须跑 `uv run pytest tests/contracts -q`；调用点数量变化时同步更新期望构成（当前 25 = 24 + 1 探针）。
- **SSE 侧**：改 `app/api/sse.py` 或 `app/api/schemas/sse.py` 时，除了契约套件，还要跑 `tests/api/test_sse_serialization.py`（帧形态与响应头的第一道回归）。
- **PendingAction 侧**：改 `app/chat/pending_action.py` 时同时跑 `tests/contracts/test_preview_contract.py` 与既有的 `tests/agent/test_collection_type.py`、`test_subject_resolution.py`（后两者用 `by_alias=True` 做往返）。
- **契约侧**：改 `docs/spec/openapi.yaml` 后必须跑契约套件；孤儿 schema 与悬空 `$ref` 都会被打成红灯。run 路由的收录由 `tests/contracts/test_run_route_contract.py` 额外钉住，删除六条 operation、`after` 查询或 409 声明会变红。

## 7. Wrong vs Correct

### 信封字段被改成驼峰（会 strand 存量数据）

#### Wrong

```python
class CollectionProgressPendingAction(_AliasCompatModel):
    preview_id: str = Field(alias="previewId")   # 存量 Redis JSON 是 preview_id
    user_id: int = Field(alias="userId")
    expires_at: datetime = Field(alias="expiresAt")
```

#### Correct

```python
class CollectionProgressPendingAction(_AliasCompatModel):
    # 信封保持蛇形：Redis 里已存的载荷就是这个形态
    preview_id: str
    user_id: int
    expires_at: datetime
    # 只有 business DTO 带过来的字段用驼峰
    items: list[CollectionProgressPendingItem] = Field(default_factory=list, alias="summary")
```

### 路径拼写错误只靠「能解析」放行

#### Wrong

```python
business.request("GET", "/api/client/collections/count", token=user.token)
# 通配匹配到了 /api/client/collections/{subjectId}，测试若只看「能解析」就静默通过
```

#### Correct

```python
business.request("GET", "/api/client/collections/counts", token=user.token)
# 字面命中；通配匹配必须显式进白名单，否则即视为拼写错误
```

## 8. 边界声明（不要高估这套测试）

2026-10-22 两次漂移演练（演练记录原在 OpenSpec 归档侧，该目录已整体移除；结论保留于此）证明了：

- **契约侧漂移会变红**：把 save 操作的 `epStatus` 改名为 `ep_status`，失败信息点名 operation、字段与调用点 `business_http.py:92`。
- **agent 侧漂移会变红**：把 `/collections/counts` 手误成 `/collections/count`，失败信息点名 `collections.py:60`。

同样重要的是它**不**证明什么：

- 两次演练都只在 **agent ↔ 契约文件** 这条边上制造漂移，**完全没有触及** `backend/business/**` 的 Java 源码。
- 若 Java DTO 字段改名而 `openapi.yaml` 没跟着改，本套件**依然全绿**——它信任 `openapi.yaml` 是事实源。
- `docs/spec/openapi.yaml` 是手工维护的导出产物，因此「契约 ↔ Java 源码」这条边**目前没有任何自动校验**，仍需人工逐项对照，并记录未同步项为已知债务。
- 套件只断言 agent **实际发送**的字段，不覆盖无人调用的响应字段。演练中曾把一个响应体里的 `epStatus` 改名而全绿，即是此边界的体现。

关闭该缺口需要 springdoc 自动导出或解析 Java 源码，均未纳入当前范围。
