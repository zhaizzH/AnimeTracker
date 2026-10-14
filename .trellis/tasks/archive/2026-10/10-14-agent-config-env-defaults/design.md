# 设计：Agent 模型配置默认值回显

## 背景与问题

`GET /admin/agent/config` 直接返回 Redis 内容（`config_service.py:26-27` `get() or {}`），Redis 空时返回 `{}`，表单全空。默认值实际活在 `Settings`（`.env`），管理员看不到生效值。

**必须避免的陷阱**：把继承的默认值填进表单并保存，会把默认值固化进 Redis（`set()` 是 `SET` 整体替换），此后改 `.env` 失效。故回显必须区分「继承默认」与「显式覆盖」。

## 契约设计

### 新增响应结构（仅 GET）

保留原 6 个字段不变（向后兼容既有消费者），新增 `_sources` 标注来源：

```jsonc
// GET /admin/agent/config  — Redis 空
{
  "model": "qwen3.7-max",
  "modelRoute": "qwen3.7-plus",
  "temperature": 0.3,
  "maxTokens": 4096,
  "thinkingBudget": 2048,
  "reasoningEffort": "high",
  "_sources": { "model": "default", "modelRoute": "default", "temperature": "default",
                "maxTokens": "default", "thinkingBudget": "default", "reasoningEffort": "default" }
}

// 局部覆盖后
{ "model": "custom-x", ..., "_sources": { "model": "override", "temperature": "default", ... } }
```

- `source` 取值只有 `default` | `override`，有限枚举。
- 字段名 `_sources` 用前缀下划线，与 6 个配置字段视觉区分，且不与未来字段冲突。
- 顶层仍是 `ModelConfig` 形状 + 一个额外键，故 `configUpdate` 的请求契约**完全不变**（`_sources` 只出现在 GET 响应）。

> 备选：`{config: {...}, sources: {...}}` 嵌套。否决——会破坏既有 GET 消费者（前端当前按平铺读取），且 `configUpdate` 请求仍是平铺，两个方向形状不一致更易混淆。

### 生效值来源（逐字段，对照 `agent_factory.py` 解析链）

| 字段 | 默认值来源 |
|---|---|
| `model` | `resolve_llm_provider(settings).model` |
| `modelRoute` | `resolve_llm_provider(settings).route_model` |
| `temperature` | `settings.llm_temperature` |
| `maxTokens` | `settings.llm_max_tokens` |
| `thinkingBudget` | `settings.llm_thinking_budget` |
| `reasoningEffort` | `resolve_llm_provider(settings).reasoning_effort` |

有 Redis 值时取 Redis 值（与 `agent_factory.py` 的 `runtime.get(...) or default` 语义一致）。**注意**：`model`/`modelRoute` 用 `or`（空串视为未设置），数值字段用 `runtime.get(k, default)`（0 是合法值，不可当未设置）。此差异必须与 `agent_factory.py` 逐字对齐，否则回显与运行时不一致。

## 后端改动

### 1. `schemas/admin_config.py`

新增来源模型（不塞进 `ModelConfig`，避免污染 `configUpdate` 入参）：

```python
class FieldSource(str, Enum):
    default = "default"
    override = "override"

class ModelConfigSources(BaseModel):
    model: FieldSource
    modelRoute: FieldSource
    temperature: FieldSource
    maxTokens: FieldSource
    thinkingBudget: FieldSource
    reasoningEffort: FieldSource

class ModelConfigView(ModelConfig):
    """GET 响应：生效值 + 逐字段来源。请求仍用 ModelConfig。"""
    sources: ModelConfigSources = Field(alias="_sources", serialization_alias="_sources")
```

> 用 `alias` 让 Python 侧字段名为 `sources`（可读），线上仍序列化为 `_sources`。

### 2. `admin/config_service.py`

```python
def get_effective_config(self) -> dict:
    runtime = self._model_configs.get() or {}
    resolved = resolve_llm_provider(self._settings)
    defaults = {...}          # 上表
    effective, sources = {}, {}
    for k, dv in defaults.items():
        if k in runtime and runtime[k] is not None:
            effective[k], sources[k] = runtime[k], "override"
        else:
            effective[k], sources[k] = dv, "default"
    return {**effective, "_sources": sources}
```

`AdminConfigService.__init__` 增加 `settings` 参数（main.py:261 注入 `settings` 单例）。

**`model`/`modelRoute` 的空串语义**：`agent_factory.py` 用 `or`，空串应视为未设置。故判定改为：`k in runtime and runtime[k] not in (None, "")` 针对字符串字段；数值字段仅判 `is not None`。抽成一个小函数避免散落。

### 3. `api/admin_config.py`

`get_config` 返回 `ModelConfigView(**service.get_effective_config())`。`update_config` 不变。

> `update_config` 返回体保持现状（`ModelConfig`）。前端保存后 invalidate 重取 GET 即可拿到新来源。

## 前端改动（`AgentConfig.tsx`）

### 回显规则

- `_sources[k] === 'override'` → 输入框填生效值
- `_sources[k] === 'default'` → 输入框**留空**，用 placeholder 显示 `继承默认 {值}（.env）`

placeholder 是原生属性，无需额外 DOM，也不会被误当作可提交值。每个默认字段下方补一行说明文字（`text-xs text-muted-foreground`），placeholder 空间有限。

### 保存：只提交覆盖集

提交时**只发送非空字段**。这同时解决两件事：

- R2 不固化默认：默认字段留空 → 不进入提交体 → 不写入 Redis。
- AC6 清除覆盖：把已覆盖字段清空 → 该字段不进入提交体 → 后端整体替换后该键消失 → 回退继承。

**推论（必须处理）**：整体替换语义下，"清空全部字段"会提交 `{}`，后端 `set({})` 写入空对象，GET 时 `{} or {}` 仍得 `{}`，效果等价于全部回退继承——**这是可接受的**，因为空对象与未设置在本解析链中行为一致（`runtime.get() or {}`）。但需在测试中钉住，避免将来有人把「空对象」当成一种第三态。

### temperature 提示

因 D1 后 5 个 slot 统一解析，placeholder 显示 `继承默认 0.3（.env）` 即为真实值，无需再注明 slot 差异（该差异已随 D1 移除）。

## 权衡

- **为什么不把默认值直接填进 value？** 会让用户在无感知下把默认固化进 Redis，且此后 `.env` 变更静默失效——正是本任务要消除的陷阱。
- **为什么 sources 放在响应里而不是单独端点？** 两个字段来自同一份 Redis 读取与同一份 Settings，拆两个端点会产生不一致窗口（两次读之间配置变更）。
- **为什么不改 `set()` 为合并？** 见前序任务 `10-14-agent-config-contract-fix` 的权衡：读-改-写引入并发写覆盖窗口。前端保全 + 稀疏提交无并发面。
- **`_sources` 为何不参与 `configUpdate`？** 它是只读的派生信息，不是配置。放进入参会让调用方以为可以设置来源。

## 兼容性

- `configUpdate` 请求体与 `ModelConfig` 一字未改，Java 网关是 `Map<String,Object>` 透传，无需改动。
- GET 响应新增一个键，对按字段名读取的既有消费者无影响（前端当前读 `d.model` 等）。
- `AdminConfigService` 构造签名新增 `settings`，唯一构造点在 `main.py:261`。

## 回滚

- 后端三文件 + 前端一文件，`git checkout` 即可。
- 无数据迁移：Redis 键格式未变，已存的覆盖值继续有效。

## 测试计划

**后端**（新增 `tests/api/test_admin_config.py` 或 `tests/adapters/`）：
- Redis 空 → 6 字段均为 Settings 值且 `_sources` 全 `default`
- 局部覆盖 → 该字段 `override` 且值来自 Redis，其余 `default` 且值来自 Settings
- 空串 `model` 视为未设置（回退默认并标 `default`）
- `temperature: 0` 是合法值，不得被当成未设置
- 改 Settings 后 GET 反映新值（AC3）
- `update_config` 只写传入字段，Redis 中无默认字段（AC4）

**前端**：
- `override` 字段填 value，`default` 字段留空且 placeholder 含默认值
- 提交只含非空字段
- 清空已覆盖字段后再提交，该键不在请求体中
