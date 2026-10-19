# Design：ChatTongyi → ChatOpenAI（百炼 OpenAI 兼容端点）

## 结论先行

`langchain-community` 已于 2026-05-26 sunset 并归档，**没有**官方独立维护的通义千问 partner 包可替换：`langchain-tongyi` 在 PyPI 不存在（404），`langchain-dashscope` 最后发布 2024-07（0.1.8，第三方、仅 6 个版本、无 CLI），`langchain-qwq` 虽被 LangChain 文档收录但作者为个人、依赖里塞了 `json-repair`/`langgraph-checkpoint` 等 12 个包。

因此落点按 PRD R1 的**第二分支**：不换第三方包，直接走**百炼官方 OpenAI 兼容端点**，用项目里**已有的** `langchain-openai`（`langchain-deepseek` 的传递依赖，`pyproject.toml` 也已直接声明 `langchain-openai>=1.4.2`）承接。净效果是删依赖、删补丁，不引入任何新包。

## 权威事实（全部实测，2026-10-19）

### 端点与参数

- 兼容端点：`https://dashscope.aliyuncs.com/compatible-mode/v1`（阿里云官方文档给出；区域化部署另有 `https://{WorkspaceId}.<region>.maas.aliyuncs.com/compatible-mode/v1`）。
- `ChatOpenAI(base_url=..., model=..., streaming=True, stream_usage=True, temperature=..., max_tokens=..., extra_body={...})` 实测产出的请求体：
  ```json
  {"model":"qwen3.7-plus","stream":true,
   "extra_body":{"enable_thinking":true,"thinking_budget":2048},
   "temperature":0.3,"max_completion_tokens":4096,"messages":[...]}
  ```
  即 `enable_thinking` / `thinking_budget` 作为非 OpenAI 标准参数被正确透传（阿里云文档明确：Python SDK 用 `extra_body` 传）。
- `bind_tools()` 之后 `_get_request_payload` 仍保留 `extra_body` —— 工具调用路径不会丢思考开关（实测 keys 含 `extra_body`，值为原字典）。
- `llm_model_name()` 读 `model_name` 属性；`ChatOpenAI.model_name == "qwen3.7-plus"`，日志字段不退化。

### `max_tokens` → `max_completion_tokens`

`langchain-openai` 的 `_default_params` 会把 `max_tokens` **改名**为 `max_completion_tokens` 再发出。这**不是**回归：百炼 2026-04-20 起把总输出 token 上限字段更新为 `max_completion_tokens`，旧 `max_tokens` 标记废弃。旧 `ChatTongyi` 走 dashscope SDK 直连用 `max_tokens`，迁移后走新字段名，方向与供应商演进一致。必须在 spec 里登记，避免后来人「修」回 `max_tokens`。

### thinking（`reasoning_content`）通道

- `ChatOpenAI` **丢弃** OpenAI 兼容流里的 `reasoning_content`（源码注释明写 "are **not** extracted"）。
- 项目已有 `_patch_chat_openai_reasoning()`（`agent_factory.py:44`）把 `reasoning_content` 存进 `additional_kwargs`，`runtime._extract_reasoning_content_from_chunk` 会读 `additional_kwargs.reasoning_content`。
- 实测：导入 `agent_factory` 后该补丁对 `_convert_delta_to_message_chunk` 生效，`reasoning_content` 被捕获成功。
- **结论**：迁移后 qwen 的思考流走已有的补丁，不需要新写代码；这条通道从「DeepSeek 专用」变成「两家共用」。

### usage 统计

`stream_usage=True` 让末帧带 `usage`，`ChatOpenAI` 会填 `usage_metadata`；`runtime._extract_usage` 读的正是 `usage_metadata`。旧 `ChatTongyi` 把 `token_usage` 放在 `generation_info`，`usage_metadata` 为 `None`。所以迁移后 `agent.model.completed` 日志的 `inputTokens/outputTokens/totalTokens` 由「恒 None」变为**真实值**——是改善，但属于可观测行为变化，须在 spec 注明。

### 依赖闭包

- 全仓 `langchain_community` 唯一引用点：`app/adapters/llm/agent_factory.py:5`。
- `langchain-classic` **仅**被 `langchain-community 0.4.2` 依赖；两者一起消失。
- `dashscope` SDK 仍被 `app/adapters/llm/embeddings.py:83` 使用，**保留**该依赖。

## 设计决策

### D1 用 `ChatOpenAI`，不引入新包

理由：`langchain-openai` 已是直接依赖；兼容端点由阿里云官方保证；`ChatOpenAI` 覆盖 Chat Completions + 流式 + tool calling + `extra_body`，`ChatTongyi` 的能力在此场景是子集（项目不用多模态、不用 `partial`、不用 dashscope 原生 `incremental_output`）。

### D2 新增 `DASHSCOPE_BASE_URL`，默认指向兼容端点

`ResolvedLlmProviderConfig.base_url` 字段已存在（DeepSeek 在用），dashscope 分支复用同一字段即可，不新增类型。默认值 `https://dashscope.aliyuncs.com/compatible-mode/v1`。

不硬编码在 Python 里的理由：区域化 workspace 端点必须可覆盖；且与 `DEEPSEEK_BASE_URL` 保持对称（同一份 `ResolvedLlmProviderConfig` 的两个 provider 都从 Settings 取 base_url）。按 ADR-0014，新增 env 键必须同步 `app/config.py` + `.env.example`，并有 `test_env_template_contract` 兜底。

### D3 思考开关维持 `model.startswith("qwen3")` 判据

现状逻辑照搬，只是从 `model_kwargs` 挪到 `extra_body`（`model_kwargs` 会把值摊平到请求顶层，`extra_body` 才是嵌套透传的官方入口）。`thinking_budget` 仅在非 0 时附加——现状行为保持。

### D4 删掉 `_patch_chat_tongyi()`（42 行）

它修的是 `ChatTongyi.subtract_client_response` 在 `incremental_output=False` 时手工做 delta 相减的缺陷。`ChatOpenAI` 走标准 OpenAI 流式增量（`delta.content` 本身就是增量），**不存在**相减环节，补丁无对象可打。删除，不做「留着备用」。

### D5 `stream_usage=True` 显式打开

`ChatOpenAI` 只在「默认 base_url + 默认 client」时自动开 `stream_usage`；我们显式设了 `base_url`，自动开启条件不满足，必须显式传，否则 `usage_metadata` 恒 `None`、token 日志退回全 None。

### D6 只改 LLM 工厂，不动 runtime / graph / prompt

`create_llm` 的签名（`provider/model/temperature/api_key/max_tokens/base_url/thinking_budget/reasoning_effort`）与返回契约（`BaseChatModel`）不变，`AgentLlmFactory.create` 的解析链不变，`admin/config_service.py` 的回显逻辑不变。

## 不做的

- 不引入 `langchain-qwq` / `langchain-dashscope` / 自写 dashscope `BaseChatModel` 封装。
- 不删 `dashscope` SDK 依赖（embeddings 仍在用）。
- 不改 `LLM_PROVIDER` 语义、模型默认值、Prompt、Redis 运行时配置键名。
- 不做真实百炼调用验证（本机到 `dashscope.aliyuncs.com` TLS 握手失败，无法连通）。改为**契约级测试**：断言构造出的请求体字段与 `extra_body` 内容，而非断言网络返回。

## 测试策略

新增 `tests/adapters/test_llm_factory.py`（纯构造，不触网）：

1. dashscope provider 产出 `ChatOpenAI`，`openai_api_base` 指向配置的 base_url；
2. qwen3 模型带 `extra_body.enable_thinking=True` + `thinking_budget`；非 qwen3 模型不带；
3. `max_tokens` 经 `_get_request_payload` 后以 `max_completion_tokens` 出现（钉住 D-`max_tokens` 事实，防止有人「修」回旧字段名）；
4. `bind_tools` 后 `extra_body` 仍在 payload 里（思考 + 工具共存）；
5. `stream_usage is True`、`streaming is True`；
6. `agent_factory` 模块可导入且 `langchain_community` 不在 `sys.modules`（对 R4/AC1 的可执行断言）；
7. deepseek 分支回归：仍是 `ChatDeepSeek`，参数不变。

## 回滚

改动集中在 `pyproject.toml` + `agent_factory.py` + `config.py` + 两个配置文件 + 一个新测试文件。回滚 = 恢复 `langchain-community==0.4.2` 与 `ChatTongyi` 分支，`uv sync` 即可。
