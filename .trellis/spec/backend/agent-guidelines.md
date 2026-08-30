# Agent 编排与流式协议

## 组合与路由

- `backend/agent/main.py` 是组合根，创建 store、配置仓库、Business Gateway、RAG 用例和 LangGraph。
- 领域节点只依赖 `AgentDependencies` 或端口，不读取环境变量、不创建基础设施客户端。
- `app/agent/graph.py` 先按角色分流；普通用户只允许 `search_agent / discover_agent / recommend_agent`。
- 每个节点只注册完成职责所需的工具；新增工具先确定最小可见节点。
- RAG 关闭时使用显式不可用适配器与 Business fallback，不能把检索失败静默伪装为空结果。

## SSE 契约

- 运行时只产生 `AgentEvent`，事件类型为 `answer / thinking / function_call / status / end`。
- `app/api/sse.py` 是序列化单一入口；结束事件必须设置 `is_end=true`。
- 保持 `text/event-stream`、`Cache-Control: no-cache`、`X-Accel-Buffering: no`。
- 改事件字段时同步 `schemas/sse.py`、前端 `useAgentChat.ts` 与 `docs/spec/openapi.yaml`。
- 浏览器只请求 Spring 代理路径，不配置或直连 Agent 的 `:8090`。

## 安全写操作

1. 预览工具查询权威 Business 数据并生成强类型 `PendingAction`。
2. `ChatService` 按用户与会话把动作写入 Redis。
3. 用户明确确认后，执行工具只读取 `InjectedState` 中的 action 或 preview ID。
4. 基础设施错误导致结果不确定时保留动作；`PREVIEW_CHANGED` 必须重新确认。
5. 取消只清理待确认状态，不修改业务数据。

参考：`app/agent/client/actions/wishlist.py`、`collection_progress.py`、`app/chat/pending_action.py`。

## 认证与配置

- Agent 使用共享 `JWT_SECRET` 本地 HS256 验签，避免回调 Spring 形成代理环路。
- 管理路由必须使用 `require_admin`，不能只靠提示词限制。
- `Settings` 使用 `extra="forbid"`；新增环境变量同步 `app/config.py` 与 `.env.example`。
- `LLM_PROVIDER` 显式选择 deepseek 或 dashscope；缺 Key 时启动失败。
- 日志只记录供应商和模型名，绝不记录 Key、JWT、用户输入或完整回答。

## 离线任务

- importer、indexer、scheduler 使用 `python -m jobs.<name>...` 运行并返回明确退出码。
- indexer 只有显式 `--activate` 且全部报告通过时才执行 `FT.ALIASUPDATE`。
- scheduler 使用 Asia/Shanghai 规则；仓库没有常驻宿主配置，不得假设已有 cron/systemd/容器部署。
