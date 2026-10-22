# 0008 — Java 与 Python 共享 `JWT_SECRET`，各自本地验签

- **状态**：accepted
- **记录日期**：2026-10-12
- **相关规范**：[backend/java-modules-auth.md](../backend/java-modules-auth.md)、`backend/agent/app/api/deps.py`

## 背景

Agent 需要从请求中得知「这是哪个用户、什么角色」。凭据是 Java 签发的 JWT。Agent 有两种途径获知：回调 Java 校验，或自己验签。

## 决策

Java 与 Agent **共享同一 `JWT_SECRET`**（逐字节一致），Agent **本地验签**、从 claim 取 userId/role，**不回调** business。因此 Agent 的验签算法必须同时接受 Java 可能签出的全部 HMAC 变体：`Keys.hmacShaKeyFor` 会按密钥字节长度自动在 HS256/HS384/HS512 之间选择，Agent 侧显式声明 `algorithms=["HS256","HS384","HS512"]`。

## 备选方案

1. **Agent 回调 business 校验凭据。** 未采纳——在「Java 已代理 Python」的拓扑下，回调会形成代理回路（配合前面的边界决策），并为每个请求增加一次网络往返与线程占用。
2. **共享密钥 + 本地验签（采纳）。** 用「两处共享一个密钥」换取每请求零往返。

## 后果

**正面**

- Agent 处理请求无需就认证再发起一次网络调用；在代理拓扑下避免了回路。
- 认证在 Agent 侧完全本地化，延迟可预测。

**代价**

- **密钥轮换必须两端同时协调**，否则一侧签发的 token 在另一侧验签失败。
- 认证逻辑在两种语言里各有一份，必须同步维护。算法自动选择是隐性契约：若只声明 `HS256`，Java 用强密钥签出的 HS512 token 全部验签失败（真实踩过）。

**约束**

- 两端 `JWT_SECRET` 必须逐字节一致；轮换需成对发布。
- Agent 侧不得收窄 `algorithms` 列表；改动任一端签发算法时必须端到端验证。
