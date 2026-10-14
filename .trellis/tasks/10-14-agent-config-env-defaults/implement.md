# 执行计划：Agent 模型配置默认值回显

## 状态

**实现已完成，运行态复验通过；未提交。**

- D1（移除 temperature 的 slot 特例）已完成并提交（`d3f0af18`），650 tests passed。
- 回显主线（步骤 1–5）已全部实现，步骤 6 运行态复验已执行（见「复验实录」）。
- 实测数字：后端 `uv run pytest` **663 passed, 6 xfailed**；前端 shared 15 / client 38 / admin 71（合计 124 passed）。

## 步骤

### 1. 后端契约

- [x] `schemas/admin_config.py`：加 `FieldSource` 枚举、`ModelConfigSources`、`ModelConfigView(ModelConfig)`
      用 `Field(alias="_sources")`，Python 侧名 `sources`、线上序列化为 `_sources`
- [x] `admin/config_service.py`：
  - `__init__` 增 `settings` 参数
  - 新增 `get_effective_config()`：逐字段按 `agent_factory.py` 语义取默认/覆盖
  - 字符串字段（model/modelRoute）空串视为未设置；数值字段仅判 `is not None`
- [x] `api/admin_config.py`：`get_config` 返回 `ModelConfigView`；`update_config` 返回值也改为 View 以保持一致
- [x] `main.py:261`：注入 `settings`

### 2. 后端测试

- [x] 新增 `tests/admin/test_config_service.py`，13 例
- [x] 关键边界：空串 model、temperature=0、局部覆盖
- [x] `uv run pytest`：663 passed, 6 xfailed

### 3. 前端类型与回显

- [x] `shared/src/types/index.ts`：新增 `ModelConfigViewVO` / `ModelConfigFieldSource` / `ModelConfigFields`（未改 `ModelConfigVO`，保持请求类型纯净）
- [x] `shared/src/api/admin/agent.ts`：`config` 返回 `ModelConfigViewVO`，`configUpdate` 入参仍是 `ModelConfigVO`
- [x] `AgentConfig.tsx`：抽 `ConfigInput` 组件；`default` 字段留空 + placeholder；`override` 填 value；已移除 `serverCfg` 与 `toNumber`/`toText`/`NUMERIC_FIELDS` 死代码

### 4. 前端保存语义

- [x] 提交体只含非空字段（`toSparseBody`，逐字段显式赋值以避开 TS union-key 写入收窄）
- [x] 验证：默认字段不进请求体；清空已覆盖字段则该键消失（前端 3 例 + 后端 2 例）

### 5. 前端测试

- [x] 更新 `AgentConfig.test.tsx` 的 mock 为带 `_sources` 的新形状（`cfgView` helper）
- [x] 新增「默认值回显」3 例：default 留空 + placeholder、override 填值、override 的 0 值
- [x] 新增「稀疏提交」5 例：只提交填写字段、全空提交 `{}`、清空撤销、数值类型、越界拦截
- [x] `npm run typecheck` 通过；`npm test` 124 passed（shared 15 / client 38 / admin 71）

### 6. 运行态复验（可选）

- [x] 用 test1 登录复验：GET 返回全 default + 生效值
- [x] 稀疏提交复验：只写该字段，其余保持 default
- [x] Redis 已还原（删除测试残留键，复验全 default）

## 关键陷阱（实现时必须遵守）

1. **`serverCfg` 基线合并要移除**。前序任务用「GET 原始对象打底 + 表单字段覆盖」保全未呈现字段；本任务新契约下，GET 返回的是**生效值**（含默认），若继续用它打底会把默认值固化。改为「只提交非空字段」。
2. **空串 ≠ 未设置**。`model`/`modelRoute` 在 `agent_factory.py` 走 `or`，空串应回退默认；但 `temperature=0` 是合法值，不可误判为未设置。两类字段判定逻辑不同，抽函数（`_TRUTHY_FIELDS` + 键存在判断）隔离。
3. **`_sources` 不进 `configUpdate` 入参**。它是只读派生信息；入参仍是 `ModelConfig` / `ModelConfigVO`。
4. **空对象 `{}` 提交等价于"没有修改"**（**已按用户决定实现，取代初稿**）。
   初稿曾写「空对象等价于全部回退继承」，实测与用户要求相反，已修正：
   service 在 `config` 为空时**直接返回现值、不写存储**。故清空全部字段后提交不会撤销任何覆盖——
   要撤销须逐个清空字段提交。此点在 `test_empty_body_is_a_noop` 与
   `test_clearing_field_by_field_does_eventually_remove_all_overrides` 中钉住。
5. **Redis 开发实例是 db 1 且带密码**（`.env` 的 `REDIS_URL=redis://:…@localhost:6379/1`）。
   清理测试数据时必须用该 URL；用默认 db 0 无密码会"删除成功但没删到"，
   再叠加 `model_config_repository.py:7` 的 5 秒本地缓存，会看到"Redis 已空但接口仍报 override"的假象。

## 验证命令

```bash
cd backend/agent && uv run pytest -q
cd frontend && npm run typecheck && npm test
```

## 复验实录（运行中的服务，账号 test1）

Python 服务自动重载后实测（经 `:5174` 代理）：

| # | 操作 | 结果 | 对应 AC |
|---|---|---|---|
| 1 | GET /config（Redis 空） | 6 字段均为 .env 值 + `_sources` 全 `default` | AC1 |
| 2 | POST `{"temperature":0.9}` | 该字段 `override`，其余仍 `default` | AC2 / AC4 |
| 3 | POST `{"temperature":0}` | `temperature=0` 且标 `override`（0 未被当成未设置） | 边界 |
| 4 | POST `{}` | 无变化，`temperature` 仍为 `0`/`override` | D2 |
| 5 | POST `{"model":"qwen3.7-max"}` | `temperature` 回退 `0.3`/`default`（撤销生效） | AC6 |
| 6 | 清理残留键后复验 | 全 `default`，`model=qwen3.7-max`、`temperature=0.3` | 环境还原 |

生效值与 `.env` 一致：`qwen3.7-max` / `qwen3.7-plus` / `0.3` / `4096` / `2048` / `high`。

**复验中发现并已处理的坑**：清理测试残留时误用 db 0 + 无密码，Redis 实际是 db 1 + 密码，
导致"删了但没删到"；叠加 5 秒缓存，出现"Redis 已空但接口仍报 override"的假象。
用正确 URL 删除后复验正常。详见「关键陷阱 5」。

## 未决事项

- `docs/spec/openapi.yaml:2671-2720` 的 `/api/admin/agent/config` 文档漂移（`data` 写作 `type: string`、
  请求体虚构 `key: object` 属性）为**预先存在**，前序任务已列入 Non-Goals，本任务未扩大范围修改。
  本任务新增的 `_sources` 字段亦未同步进该文档——若将来修文档需一并覆盖。
- 本任务改动**尚未提交**（用户要求暂停）。

## 回顾门

- AC1–AC4 与 AC9 是行为契约，必须有断言，不能只靠代码审阅。
- AC3（改 Settings 后 GET 反映新值）是"回显确实来自 Settings"的反证，不可用常量 mock 绕过。
- 若发现 `_sources` 形状会导致前端出现第三态分支，回到 `design.md` 修订契约。


## 回滚点

- `git checkout -- backend/agent/app/{api/admin_config.py,admin/config_service.py,api/schemas/admin_config.py,main.py} frontend/admin/src/pages/AgentConfig.tsx frontend/packages/shared/src/{types/index.ts,api/admin/agent.ts}`
- Redis 键格式未变，回滚无数据影响。
