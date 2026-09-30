# 执行计划：Agent 健康检查深度

对应 `prd.md`（R1–R7 / AC1–AC13）与 `design.md`（§1–§11）。命令在 `backend/agent` 下执行。

## 前置

- 基线：`uv run pytest` 应为 **494 passed**（T1 合入后的实测值；`.trellis/spec/backend/index.md:50` 记录的 413 为更早基线，以实测为准）。
- `tests/` 下**无 `conftest.py`、无 API 层测试**——本任务须自建脚手架。
- 工作区应干净（仅 `.trellis/tasks/**` 未跟踪项与前端 WIP）。

## 验证命令

```bash
cd backend/agent
uv run pytest tests/api/test_health.py -v          # 本任务主战场
uv run pytest tests/rag/test_lexical_contract.py -v # 去重后回归
uv run pytest                                       # 全量（AC12）
```

## 执行清单

### 阶段 1：消除 `_command_info_present` 重复实现（R4，AC11）

- [ ] **1.1** 新建 `app/adapters/redis/command_info.py`：把 `vector_set.py:236-244` 的实现原样搬迁为 `command_info_present(info)`（公开名），模块 docstring 写明「唯一实现，禁止在消费方内联第二份」。
- [ ] **1.2** `vector_set.py`：删除本地 `_command_info_present`，改为 `from app.adapters.redis.command_info import command_info_present`（注意本模块 `:15` 已导入 `subject_index`，`command_info` 必须**无内部依赖**以免成环）。
- [ ] **1.3** `subject_index.py`：同上，删除本地副本并改为导入。
- [ ] **1.4** `tests/rag/test_lexical_contract.py:97-101`：更新为从新模块导入（该测试直接断言两份实现，现应断言同一份）。**保持断言语义不变**。
- [ ] **1.5** `uv run pytest tests/rag/ -v` 通过；grep 确认全仓仅剩一处 `def command_info_present`。

**回滚点 A**：纯机械搬迁，独立成组；回滚即还原两份副本。

### 阶段 2：不依赖版本的探测入口 + Business 超时收窄（R1/R3/R4）

- [ ] **2.1** `vector_set.py`：新增模块级 `probe_vector_set_commands(redis_client, commands=("VADD","VSIM","VREM"))`，逐条 `COMMAND INFO`，缺任一抛 `VectorSetUnavailable`；**不调用 `validate_version`**（该入口刻意不依赖版本）。复用 `command_info_present`。
- [ ] **2.2** `business_http.py::request`：新增可选参数 `timeout_seconds: float | None = None`，`timeout=` 取 `timeout_seconds if timeout_seconds is not None else self._timeout`。**其余 7 个方法一律不传**，保持 10s 默认。
- [ ] **2.3** `uv run pytest tests/adapters/ tests/rag/ -v` 通过，确认既有适配器行为不回归。

**回滚点 B**：两项均为向后兼容的纯新增；回滚无调用方受影响。

### 阶段 3：health 探测实现（R1/R2/R3/R5/R6，AC2–AC10）

- [ ] **3.1** 新建 `app/api/health.py`：
  - `build_health_report(*, settings_obj, store, business, rag_redis) -> dict`：按 `design.md` §2 返回 `{status, llm_configured, checks}`。
  - 三个探针：`_probe_redis(store)`（`await store.init_db()`）、`_probe_business(business)`（`business.request("GET", "/actuator/health/liveness", timeout_seconds=2.0)` 经 `asyncio.to_thread`）、`_probe_rag(settings_obj, rag_redis)`（`rag_enabled=False` → `disabled` 且**不调用**探测入口；否则 `asyncio.to_thread(probe_vector_set_commands, rag_redis)`）。
  - `_safe()` 包裹每项：异常 → `down`，**只记类型化结果**，不透出异常文本。
  - `asyncio.gather` 并发、**不短路**；整体 `asyncio.wait_for(timeout=3.0)`。
  - `store`/`business`/`rag_redis` 为 `None` → 对应分项 `down`（fail-closed），不得 `AttributeError` 冒泡。
- [ ] **3.2** `app/api/chat.py`：`include_health` 分支改为调用 `build_health_report`，从 `request.app.state` 取依赖（用 `getattr(..., None)`）；保留路径 `/health`、`GET`、**无 `auth_dep`**。
- [ ] **3.3** `main.py`：lifespan 中新增 `app.state.business_gateway`；`settings.rag_enabled` 时新增 `app.state.rag_redis`（与 `_build_agent_dependencies` 同一 `effective_rag_redis_url`）。
- [ ] **3.4** 新建 `tests/api/__init__.py` 与 `tests/api/conftest.py`：构造带假 `app.state` 的 FastAPI app 并挂 client chat router（`include_health=True`），提供 `TestClient` fixture。**不启动真实 lifespan**（避免连真 Redis/MySQL）。
- [ ] **3.5** 新建 `tests/api/test_health.py`：覆盖 AC2–AC10 全部用例（清单见 `design.md` §9）。
- [ ] **3.6** `uv run pytest tests/api/test_health.py -v` 通过。

**回滚点 C**：health 报告为纯新增只读逻辑；回滚即回到「恒 200 + 仅 `status`/`llm_configured`」。

### 阶段 4：文档与 spec 同步（R7）

- [ ] **4.1** `backend/agent/README.md:434`：端点表补响应字段说明（`status`/`llm_configured`/`checks`），保留角色列现状。
- [ ] **4.2** `.trellis/spec/backend/agent-guidelines.md:351`：把「只反映 LLM 配置」的缺口描述更新为已实现；按 `:353` 五要素记录本任务的检查项/状态码/降级响应/公开字段/匿名决策。
- [ ] **4.3** `.trellis/spec/backend/error-handling.md:89` 附近：登记「健康检查恒 200 + body 表达降级」为**有意例外**及理由（PRD 已定），避免文档与实现再次背离。
- [ ] **4.4** `docs/spec/openapi.yaml:2887-2913`：响应 schema 由通用 `{code,message,data:string}` 改为与实现一致的 `{status,llm_configured,checks}`；**保留** `Authorization` 必填声明（Spring 代理层事实）并在 description 注明 Python 侧匿名的双层差异。
- [ ] **4.5** `backend/agent/README.md` 或 spec 中登记「Python 匿名 / Java 必填」为有意设计（PRD R5）。

### 阶段 5：交付验证

- [ ] **5.1** `uv run pytest` 全量通过（AC12），对照基线 494 记录实际数字。
- [ ] **5.2** 逐条核对 AC1–AC13，把实际证据（命令 + 结果）写入完成说明；不得只标「已完成」。
- [ ] **5.3** `git diff` 自查：确认未改 Spring/Business Java 侧、未新增 MinIO 导入/字段、未动检索与重排算法、未放宽 `extra="forbid"`。

## 审查门禁

- 阶段 1 完成后：核对 AC11，重点确认搬迁未改变 `command_info_present` 的判定语义（`[None]`/`{"VADD": None}` 仍判不支持）。
- 阶段 3 完成后：核对 AC2–AC10，重点确认「不短路」（AC3 断言其余探针被调用）、「RAG 关闭不探测」（AC5）、「LLM down 不触网」（AC7）、「耗时上界」（AC10）。
- 全部完成后：`trellis-check` 复核，再按 Phase 3.4 提交。

## 已知不做（防范围蔓延）

- **不含 MinIO 探测**（PRD 已定决策 1；`app/` 零网络调用）。
- **不修改 Spring/Business Java 侧**（`ClientAgentController`、`SecurityConfig`、`AgentServiceImpl` 的错误映射）；health 不返回 503，故不触发 Spring 的 5xx→503 映射。
- **不新增 k8s/容器探针配置**（仓库无常驻宿主部署假设）。
- **不探 Embedding(DashScope) 与 MySQL**（PRD Out of Scope）。
- **不改 `subject_index.ensure_version` 的异常类型**（仍抛 `RuntimeError`；在线检索链不经过它）。
- **不改 `error-handling.md` 的既有错误清单条目本身**，只登记例外。
- **不把 `{code,message,data}` 内联响应重构为 `components.schemas` 复用**（全文 68 路径规模，独立工程）。
