# 技术设计：Agent 健康检查深度

对应 `prd.md` 的 R1–R7。本文只记技术决策与取舍；需求与验收标准在 PRD。
事实来源：`research/health-endpoint-facts.md`（含全部 file:line）。

## 1. 影响面

| 文件 | 改动 |
|---|---|
| `backend/agent/app/api/health.py` | **新增**：探测编排 + 报告构造 |
| `backend/agent/app/api/chat.py` | health handler 改为调用 `build_health_report`（保留注册位与路径） |
| `backend/agent/main.py` | lifespan 暴露 `app.state.business_gateway` / `app.state.rag_redis` |
| `backend/agent/app/adapters/redis/command_info.py` | **新增**：`_command_info_present` 唯一实现（消除重复） |
| `backend/agent/app/adapters/redis/vector_set.py` | 复用 `command_info`；新增不依赖版本的 `probe_vector_set_commands` |
| `backend/agent/app/adapters/redis/subject_index.py` | 删除本地 `_command_info_present`，改为导入 |
| `backend/agent/app/adapters/business_http.py` | `request()` 支持单次调用级 `timeout_seconds` 覆盖 |
| `backend/agent/tests/api/test_health.py` | **新增**（含 `conftest.py` 脚手架） |
| `backend/agent/tests/rag/test_lexical_contract.py` | 更新 `_command_info_present` 导入路径 |
| `backend/agent/README.md`、`docs/spec/openapi.yaml` | 端点表与响应 schema 同步 |

**不动**：`error-handling.md:89` 的「恒 200」例外已在 PRD 显式登记；无 schema/迁移变更。

## 2. 响应契约（R2 / R6）

```json
{
  "status": "ok" | "degraded",
  "llm_configured": true,
  "checks": {
    "llm": "ok" | "down",
    "redis": "ok" | "down",
    "business": "ok" | "down",
    "rag": "ok" | "down" | "disabled"
  }
}
```

- **`status` 必须保留**：前端有真实消费方 `frontend/packages/shared/src/api/agent.ts:2` 的 `health()`（`get<string>`），聊天 hook 读 `E?.status` 显示。改名会静默破坏前端。
- **`llm_configured` 保留**：虽当前无消费方，但它是既有对外字段，删除属破坏性变更、无收益。语义不变（LLM 配置是否可解析）。
- **新增 `checks`**：分项明细。取值为有限枚举（R2），禁止异常文本。
- 顶层 `status`：全部 `ok`/`disabled` → `"ok"`；任一 `down` → `"degraded"`。
- HTTP **恒 200**（PRD 已定决策 2），理由与 `error-handling.md:89` 的例外登记见 PRD。

## 3. 分项探测形态（R1 / R3）

### 3.1 llm — 纯配置判定（维持现状）

复用 `resolve_llm_provider(settings)`（`config.py:113-139`）：成功 → `ok`，抛 `ValueError` → `down`。
**不触网**（AC7）。这是唯一「配置即事实」的分项，无网络端点可探。

### 3.2 redis — 真实 PING

`await store.init_db()`（`chat_store.py:49-50` 实现即 `await self._r.ping()`）。
- 必须**每次真实执行**：`RedisChatStore.__init__` 只 `from_url` 不连接（`chat_store.py:35`），构造成功不代表可用。
- 异常（含 `redis.ConnectionError`）→ `down`。
- `store` 为 `None`（lifespan 未挂载）→ `down`，不得静默 `ok`。

### 3.3 business — 真实 HTTP 探针

**探针路径选 `/actuator/health/liveness`**，不探默认 `/actuator/health`。

理由：`application.yml:119-125` 中默认 group 聚合 `db,redis`（`readiness.include: db,redis`），探它会级联探测 Business 的 MySQL/Redis —— 那属于 **Business 自身的就绪度**，不是「Agent 能否连通 Business」。把 Business 的 DB 抖动报告成 Agent 的 Business 依赖故障是错误归因；且会让 health 变成对外部数据库的间接依赖。`liveness` 只回答本任务要回答的问题：**Business HTTP 进程可达且可响应**。

- 路径 `/actuator/health/liveness` 由 `SecurityConfig.java:62` 的 `/actuator/health/**` permitAll 放行 → Agent 无需 token（与 PRD R5「匿名探针」自洽）。
- 成功判定：非 `{"error": true}`（`business_http.py:44-59` 的归一错误信封）即 `ok`。
- 任何异常 / error 信封 / 超时 → `down`。

### 3.4 rag — 条件分项，能力探测

- `settings.rag_enabled` 为 `False`（`config.py:48` 默认）→ `disabled`，**不发起任何 Vector Set 探测**（AC5）。这是「功能开关关闭」的表达，**不是故障**（R2）。
- 为 `True` 时 → `await asyncio.to_thread(probe_vector_set_commands, rag_redis)`：
  - 对 `VADD/VSIM/VREM` 逐个 `COMMAND INFO`；三条都在 → `ok`，缺任一 → `down`。
  - **不依赖 `index_version`**（R4）：现行 `ensure_version` 强制 `validate_version`（`vector_set.py:128`），而 health 无从得知 active 版本（在线版本由 Business lexical 响应逐请求决定）。故新增独立入口，见 §5。
- `rag_redis` 为 `None` 而 `rag_enabled=True` → `down`（配置声明开启却无客户端，属真实不一致）。

## 4. 编排：并发 + 总预算（R3 / AC10）

### 4.1 决策：并发探测，总预算 3s

串行最坏耗时 = Redis(2s `socket_connect_timeout`) + Business(10s `business_http.py:18`) + RAG(3 次往返) ≈ 12s+，不可接受。

```python
async def build_health_report(*, settings_obj, store, business, rag_redis) -> dict:
    llm = _probe_llm(settings_obj)                       # 纯同步、无 IO
    redis_r, business_r, rag_r = await asyncio.gather(
        _safe(_probe_redis(store)),
        _safe(_probe_business(business)),
        _safe(_probe_rag(settings_obj, rag_redis)),
    )
    ...
```

- `asyncio.gather` **不短路**：某一项失败不影响其余（R2「探测不得短路」、AC3）。
- 每项经 `_safe()` 包裹：任何异常 → `down`，绝不外泄（R3 fail-closed）。`_safe` 内部**只记录类型化结果**，不透出异常文本（R6）。
- **总预算**：整体 `asyncio.wait_for(..., timeout=3.0)`；超时的分项由各自的 `_safe` 兜底为 `down`。3s 取值依据：Redis 2s + 余量，且远小于 Business 默认 10s。

### 4.2 各项的超时来源

| 分项 | 超时 | 来源 |
|---|---|---|
| redis | 2s | 复用 `chat_store.py:35` 的 `socket_connect_timeout=2` |
| business | 2s（单次调用级收窄） | 见 §4.3 |
| rag | 2s | 由 `asyncio.wait_for` 总预算兜底 |

### 4.3 Business 探针收窄超时（唯一需改的适配器）

`HttpBusinessGateway.request()` 当前超时固定 `self._timeout`（`business_http.py:18` = 10.0）。为 health 收窄，给 `request` 增加**可选**参数：

```python
def request(self, method, path, *, params=None, token=None, json_body=None,
            timeout_seconds: float | None = None):
    ...
    timeout=timeout_seconds if timeout_seconds is not None else self._timeout,
```

- 可选参数、默认 `None` → 既有调用方**零行为变更**（其余 7 个业务方法不传即维持 10s）。
- health 探针传 `2.0`。
- 同步 `httpx.request` 在 health 中经 `asyncio.to_thread` 包装，避免阻塞事件循环。

## 5. R4：不依赖版本的能力探测入口 + 消除重复实现

### 5.1 重复实现的消除（AC11）

`_command_info_present` 现有两份：`vector_set.py:236-244` 与 `subject_index.py:295-303`，已被 `tests/rag/test_lexical_contract.py:97-101` 同时覆盖。

**不能**让其中一方直接导入另一方：`vector_set.py:15` 已有 `from app.adapters.redis.subject_index import VECTOR_DIMENSIONS, vector_bytes`，反向导入会成环。

→ 新建 `app/adapters/redis/command_info.py`，存放唯一实现；两方均从它导入。该模块无内部依赖，无环风险。

### 5.2 新增不依赖版本的探测入口

在 `vector_set.py` 新增模块级函数（与 `validate_version` 同层，不进 `RedisVectorSet` 实例方法——health 未必有实例）：

```python
def probe_vector_set_commands(redis_client: Any, commands: Sequence[str] = ("VADD", "VSIM", "VREM")) -> None:
    """探测 Vector Set 命令能力；不创建 key、不写数据、幂等。

    与 ensure_version 的区别：不要求 index_version（health 无从得知当前
    active 版本）。缺任一命令即抛 VectorSetUnavailable。
    """
```

- 复用 §5.1 的唯一 `command_info_present`。
- 异常类型沿用 `VectorSetUnavailable`（`vector_set.py:26`），health 侧统一判 `down`。
- `subject_index.ensure_version`（抛 `RuntimeError`）**保持不动**：在线检索链不经过它，改异常类型属计划外扩大范围。

## 6. 授权（R5，AC8）

**维持 Python 侧匿名，并补授权测试钉住。** PRD 已定（理由：浏览器只访问 `/api/**`；经 Spring 代理的公开路径由 `ClientAgentController` 必填 `Authorization` + `SecurityConfig.java:74` `.authenticated()` 强制登录）。

- handler **不加** `auth_dep`（现状不变，`chat.py:99-107` 分支本就绕过 router 级 `auth_dep`）。
- 测试：无 `Authorization` 头的 GET → 断言 200（钉住匿名现状）。若未来改策略，该测试即失败点。
- 两层不一致（Python 匿名 / Java 必填）在 spec 与 README 登记为**有意设计**（PRD R5）。

## 7. app.state 暴露（最小侵入）

health 需要三样东西，当前只有 `store` 已挂（`main.py:247`）：

- `store` — 已有。
- `business_gateway` — **新增** `app.state.business_gateway = HttpBusinessGateway(settings.backend_base_url)`。注意 `_build_agent_dependencies` 内已有一个实例但未返回；health 另建一个轻量实例（构造只存字符串与超时，无 IO），避免改动图组装签名。
- `rag_redis` — **新增**，仅在 `settings.rag_enabled` 时构造（与 `_build_agent_dependencies` 用同一 `effective_rag_redis_url`）。

handler 用 `getattr(request.app.state, name, None)` 读取，缺失即判 `down`（fail-closed），不用 `AttributeError` 冒泡。

## 8. 日志与信息泄露（R6）

- **不新增 `log_event` 事件**：health 是高频诊断端点，逐次记结构化事件会污染日志且需扩 `_ALLOWED_FIELDS` 白名单（`observability.py:37-43`）。探测失败对调用方已由 `checks` 字段表达。
- 响应体禁含：上游错误正文、堆栈、文件路径、连接串、桶名、JWT、密钥（`error-handling.md:80-83`）。Business 的 `{"error": true, "message": ...}` 原文**绝不透出**——`checks` 只给枚举值（AC9）。

## 9. 测试设计（AC1–AC13）

新增 `tests/api/` 包（含 `__init__.py` 与 `conftest.py`，当前 `tests/` 无 API 层测试脚手架、无 `conftest.py`）。

| 用例 | 覆盖 | 方式 |
|---|---|---|
| 全绿 | AC2 | 三探针替身均成功 → 各分项 `ok`/`disabled`，`status="ok"`，HTTP 200 |
| Redis 故障不短路 | AC3 | `store.init_db` 抛 `redis.ConnectionError` → `redis=down`，**其余分项仍被探测**（断言替身被调用） |
| Business 故障 | AC4 | `httpx.request` 抛 `httpx.ConnectError`（模板 `tests/adapters/test_business_http.py:57-65`）→ `business=down`；返回 `{"error":true,...}` 同判 |
| RAG 关闭 | AC5 | `rag_enabled=False` → `rag=disabled`，且断言 Vector Set 探测入口**未被调用** |
| RAG 能力 | AC6 | `COMMAND INFO VADD` 返回 `[None]`（桩法复用 `test_lexical_contract.py:97-101`）→ `down`；三条存在 → `ok`；断言探测入口**不需要** `index_version` |
| LLM 不可解析 | AC7 | 无 Key → `llm=down`，且断言未触发网络/Redis 调用 |
| 授权 | AC8 | 无 `Authorization` 的 GET → 200 |
| 无敏感信息 | AC9 | 序列化后不匹配 `redis://`、`Bearer `、`minioadmin`、`Traceback`、`.py", line` |
| 耗时上界 | AC10 | 注入「永不返回」的 Redis/Business 替身 → 请求在总预算内返回，不挂死 |
| 去重 | AC11 | `test_lexical_contract.py:97-101` 更新导入后仍绿；断言全仓仅一处定义 |
| 回归 | AC12 | `uv run pytest` 全绿 |
| 无 MinIO | AC13 | grep 断言：`app/` 无新增 MinIO 导入，响应无 MinIO 字段 |

## 10. 回滚

单组提交、单组回滚：health 报告为**纯新增只读逻辑**，回滚即回到「恒 200 + 仅 `status`/`llm_configured`」。
`request()` 的 `timeout_seconds` 为可选默认 `None`，回滚无调用方受影响。
`_command_info_present` 的搬迁若不回滚会影响两处导入——回滚时须连同 `command_info.py` 一起还原。

无数据库、无 schema、无迁移。

## 11. 风险

| 风险 | 缓解 |
|---|---|
| 探 `/actuator/health/liveness` 不覆盖 Business 的下游（DB/Redis）就绪度 | 有意为之（§3.3）：那是 Business 自身 readiness 的职责，Agent health 只回答连通性；避免错误归因与级联 |
| 并发探测让替身测试变脆 | 测试用 `asyncio.gather` 语义下各探针独立替身，不依赖执行顺序；断言用「是否被调用」而非调用序 |
| 前端 `health()` 实际不解析 `checks`，新字段对前端无用 | 新增 `checks` 面向运维/诊断与测试；前端契约由保留 `status` 保证不破坏 |
| 总预算 3s 在极慢环境误判 `down` | 3s 已含 Redis 2s 预算 + 余量；超时判 `down` 是 fail-closed 的既定语义（R3），不是误报 |
