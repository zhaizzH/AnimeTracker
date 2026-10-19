# Implement：ChatTongyi → ChatOpenAI（百炼兼容端点）

全部改动在 `backend/agent`，逐 step 可独立验证。基线：660 passed / 1 warning（`langchain-community` sunset）。

## Step 0 — 记录基线

```bash
cd backend/agent && uv run pytest -q -p no:randomly 2>&1 | tail -5
# 期望：660 passed, 1 warning（sunset 告警）
```

## Step 1 — Settings 增加 `DASHSCOPE_BASE_URL`

文件：`backend/agent/app/config.py`

在 `dashscope_model_route` 之后加：

```python
dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
```

`_resolve_by_key()` 与 `resolve_llm_provider()` 的 dashscope 分支各补 `base_url=s.dashscope_base_url`（DeepSeek 分支已有同构写法，照抄）。

同步 `backend/agent/.env.example`：

```
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

同步 `backend/agent/README.md` 的 LLM 配置表（`DASHSCOPE_MODEL_ROUTE` 下一行）。

**验证**：`uv run pytest tests/test_env_template_contract.py -q` 全绿（模板键 ⊆ Settings 字段）。

## Step 2 — 重写 `create_llm` 的 dashscope 分支

文件：`backend/agent/app/adapters/llm/agent_factory.py`

1. 顶部 `from langchain_community.chat_models.tongyi import ChatTongyi` → `from langchain_openai import ChatOpenAI`；
2. **删除**整段 `_patch_chat_tongyi()` 定义与它的调用（`_patch_chat_tongyi()` 那行）；
3. 保留 `_patch_chat_openai_reasoning()` 原样（现在两家共用）；
4. dashscope 分支改为：

```python
extra_body: dict = {}
if model.startswith("qwen3"):
    extra_body["enable_thinking"] = True
    if thinking_budget:
        extra_body["thinking_budget"] = thinking_budget
return ChatOpenAI(
    model=model,
    api_key=api_key,
    base_url=base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
    streaming=True,
    stream_usage=True,
    temperature=temperature,
    max_tokens=max_tokens,
    extra_body=extra_body or None,
)
```

5. `create_llm` 的 docstring 里「百炼 qwen3 显式开启 enable_thinking」保留，但「ChatTongyi」字样全部改掉。

**验证**：`uv run python -c "import app.adapters.llm.agent_factory, sys; print('langchain_community' in sys.modules)"` → `False`。

## Step 3 — 移除 `langchain-community` 依赖

文件：`backend/agent/pyproject.toml`

删 `"langchain-community==0.4.2"`。

```bash
cd backend/agent && uv sync
```

**验证**：`uv pip list 2>/dev/null | grep -c "langchain-community\|langchain-classic"` → `0`；`grep -rn "langchain_community" app/ jobs/ tests/ main.py` 无输出。

## Step 4 — 新增契约测试

新文件：`backend/agent/tests/adapters/test_llm_factory.py`（纯构造，不触网）

1. `test_dashscope_creates_openai_compatible_client`：provider=dashscope → `ChatOpenAI` 实例，`openai_api_base` == 传入的 base_url；
2. `test_qwen3_enables_thinking_in_extra_body`：`model="qwen3.7-plus"` → `extra_body == {"enable_thinking": True, "thinking_budget": 2048}`；
3. `test_non_qwen3_has_no_thinking`：`model="qwen-max"` → `extra_body` 为 `None`；
4. `test_zero_thinking_budget_omits_budget`：`thinking_budget=0` → `extra_body == {"enable_thinking": True}`；
5. `test_max_tokens_sent_as_max_completion_tokens`：`_get_request_payload("hi")["max_completion_tokens"] == 4096` 且无 `max_tokens` 键（钉住字段改名，防「修」回旧名）；
6. `test_bind_tools_keeps_extra_body`：`bind_tools([dummy])` 后 `_get_request_payload` 仍含 `extra_body`；
7. `test_stream_usage_enabled`：`stream_usage is True` 且 `streaming is True`；
8. `test_factory_import_does_not_load_community`：`"langchain_community" not in sys.modules`；
9. `test_deepseek_branch_unchanged`：provider=deepseek → `ChatDeepSeek`，`_default_params` 含 `max_tokens`（DeepSeek 官方端点用旧字段名，不是笔误）。

**验证**：`uv run pytest tests/adapters/test_llm_factory.py -q` 全绿。

## Step 5 — 全量门禁 + spec 收尾

1. `uv run pytest -q -p no:randomly 2>&1 | tail -5`：全绿且 **warnings summary 无 sunset 告警**；passed 数 = 660 + 9 = 669（若 Step 4 用例数不同则以实测为准）。
2. 更新 `.trellis/spec/backend/agent-guidelines.md`「认证与配置」段：补 `DASHSCOPE_BASE_URL`、说明 dashscope 走 OpenAI 兼容端点、`max_tokens`→`max_completion_tokens` 的事实、`stream_usage` 带来的 token 日志改善。
3. 更新 `.trellis/spec/backend/quality-guidelines.md` 的测试基线数字 + 日期。
4. `git diff --stat` 核对：只动 `backend/agent/**`，不碰 Business/前端。

## 回滚

`git checkout -- backend/agent/{pyproject.toml,app/adapters/llm/agent_factory.py,app/config.py,.env.example}` + 删测试文件 + `uv sync`。

## 提交计划

1. `refactor(agent): ChatTongyi 迁到 ChatOpenAI 百炼兼容端点`（agent_factory + config + .env.example + README + 测试）
2. `chore(agent): 移除 langchain-community 依赖`（pyproject + uv.lock）
3. `docs(spec): 登记百炼兼容端点与 max_completion_tokens 契约`（两份 spec）
