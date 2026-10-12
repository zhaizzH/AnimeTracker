# 0013 — 导入单实例由 Redis 锁 + 本地 PID 文件协调，代价是不可水平扩展

- **状态**：accepted
- **记录日期**：2026-10-12
- **相关规范**：`app/adapters/redis/import_lock.py`、[backend/database-guidelines.md](../backend/database-guidelines.md)

## 背景

导入器会全量拉取并重灌派生数据。两个导入进程同时跑会互相覆盖。需要一种「同一时刻只有一个导入在跑」的保证。

## 决策

用 **Redis 锁**（`animetracker:import:lock`，`SET NX EX` 获取 + 周期续期，compare-and-del 释放）保证单实例。释放与续期**刻意用 `WATCH`+`MULTI` 而非 Lua**：语义与 compare-and-del 等价，但免去 `lupa` 依赖，且在 `fakeredis` 无 Lua 时也能测。同时以**本机 PID 文件**协调同一主机内的进程。导入进度计数存于 Redis，终态一次性回写 `import_record`。

## 备选方案

1. **不做互斥，靠调度错开。** 未采纳——full import 与 recent 增量可能重叠，调度错开无法覆盖手工触发。
2. **用 Lua 脚本做原子 compare-and-del。** 未采纳——多一个原生依赖，且使测试环境要求 Lua。
3. **Redis 锁 + WATCH/MULTI + 本地 PID 文件（采纳）。**

## 后果

**正面**

- 单实例语义明确，误删他人锁可防（compare-and-del 校验持有者）。
- 不引入 Lua 依赖，测试可在 `fakeredis` 下完整覆盖。

**代价（明确接受）**

- **不可水平扩展**：PID 文件是本机协调，部署本质上是单节点。
- 跨机场景下 PID 文件失效，只有 Redis 锁在起作用；若 Redis 被清空，锁保护随之减弱。

**约束**

- 释放/续期不得改用 Lua（会破坏测试能力与依赖最小化）；若未来 Redis 端脚本化，升级点仅在 release/renew 两处。
- 不要把「集群多实例导入」当作支持场景。
