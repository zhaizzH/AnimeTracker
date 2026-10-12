# 0014 — Agent 配置 `extra="forbid"`，却把 jobs 专用 env 键声明为 `str` 直通

- **状态**：accepted
- **记录日期**：2026-10-12
- **相关规范**：`backend/agent/app/config.py`

## 背景

Agent（FastAPI 服务）与离线 jobs（importer/indexer/backfill）**共享同一份 `.env`**，但各自只需要其中一部分键。配置模型设了 `extra="forbid"`——多出一个未声明的键就拒绝启动。

于是出现一个矛盾：jobs 专用的键如果不在 Agent 的 `Settings` 里声明，Agent 会因为它们「多余」而启动失败。

## 决策

把 jobs 专用键在 Agent 的 `Settings` 里**声明为 `str` 直通**，仅为容身共享 `.env`，业务读取仍走 `os.getenv`。**类型刻意用 `str` 而非 `int`**：若声明为 `int`，一个只有 scheduler 会用的坏值（如 `BACKFILL_BATCH_SIZE=abc`）会变成 **Agent 启动失败**——一个与 Agent 无关的键拖垮在线服务。

同时明确：`BACKEND_BASE_URL` 与 `BUSINESS_BASE_URL` **语义不同、禁止合并**（前者是 Agent 调用 business 的地址，后者是 indexer shadow eval 的 `--business-url` 默认值）。

## 备选方案

1. **`extra="ignore"`，不声明 jobs 键。** 未采纳——放弃「拼错 env 键名立刻报错」这一保护。
2. **声明 jobs 键为真实类型（`int` 等）。** 未采纳——把无关键的校验失败提升为 Agent 启动失败。
3. **`extra="forbid"` + jobs 键声明为 `str` 直通（采纳）。** 保留拼写保护，同时不让 jobs 键的值参与在线服务的启动校验。

## 后果

**正面**

- 在线服务对自身配置的拼写错误 fail-loud；对 jobs 专用键则容忍其取值。
- 共享一份 `.env` 不需要拆分或重复维护。

**代价与陷阱**

- `Settings` 里存在一些「声明了但 Agent 不读」的键，看起来冗余——改动时容易误删，删除会导致 Agent 启动失败。
- `BACKEND_BASE_URL` 与 `BUSINESS_BASE_URL` 名字近似、用途不同，**极易被「统一」成一个**。

**约束**

- 不得删除 `Settings` 中的 jobs 直通键；不得把它们的类型收窄为 `int` 等校验型。
- 不得合并 `BACKEND_BASE_URL` 与 `BUSINESS_BASE_URL`。
