# 实施计划：按标题安全加入想看

## 1. 实现顺序

1. **补齐测试契约与纯函数**
   - 增加安全标题归一化、唯一精确匹配、候选去重和候选选择的单元测试。
   - 明确区分 Business 成功空结果、Business 错误、RAG 不可用、RAG 无结果和多候选。

2. **实现确定性单标题解析入口**
   - 复用 `BusinessGateway.search_subjects` 和 `batch_subjects`。
   - 实现 Business 首查、仅成功空结果回退 RAG、标题/真实别名匹配和 `/batch` 校验。
   - 保证显式 `subjectId` 路径跳过搜索但仍执行 `/batch`。

3. **扩展待处理状态联合**
   - 在 `app/chat/pending_action.py` 增加 `SUBJECT_RESOLUTION` 类型及候选字段。
   - 更新待处理上下文、判别解析、路由和取消/替换语义；保持旧类型 JSON 兼容。
   - 加入用户、TTL、候选来源和选择唯一性校验。

4. **接入 recommend_agent**
   - 注册单标题解析和候选选择入口；复用 RAG 搜索用例，不复制 RAG 逻辑。
   - 唯一候选调用既有 wishlist preview；多候选保存解析状态并等待选择。
   - 保留现有推荐结果多项加入想看的调用路径和行为。

5. **更新提示词与回归测试**
   - 在推荐 Agent Prompt 中说明单标题请求必须使用确定性解析入口、候选选择和两段式确认。
   - 增加工具注册、路由、状态序列化、选择、过期、错误回退和写入边界测试。

6. **执行质量门禁**
   - 运行受影响的 Agent 测试，再运行完整 Python Agent 测试。
   - 检查跨层契约：Business 路径、batch 字段、Agent 状态、RAG fallback 和现有 wishlist 行为。
   - 若提示词或 OpenAPI 事实发生变化，同步检查对应文档；本设计预期不修改 OpenAPI。

## 2. 重点文件与回滚点

### 重点文件

- `backend/agent/app/agent/client/recommend.py`
- `backend/agent/app/agent/client/actions/wishlist.py`
- `backend/agent/app/agent/client/gateway.py`
- `backend/agent/app/agent/run.py`
- `backend/agent/app/chat/pending_action.py`
- `backend/agent/app/chat/pending_events.py`
- `backend/agent/app/adapters/business_http.py`
- `backend/agent/resources/prompt/client/recommend_agent_prompt.md`
- `backend/agent/tests/agent/` 与必要的 `backend/agent/tests/rag/`

### 回滚点

- 纯函数和解析服务完成后可单独回退，不影响现有收藏写入。
- `SUBJECT_RESOLUTION` 状态接入前后分别运行旧 wishlist 回归测试。
- Agent 组合与 Prompt 接入若导致推荐收藏回归，可先撤回新入口注册；不得绕过预览确认来修复失败。

## 3. 验证命令

```powershell
Set-Location backend/agent
uv run pytest tests/agent -q
uv run pytest -q
```

如环境没有 `uv`，使用项目已配置的 Python 测试入口执行同等测试；不因工具替换而跳过完整 Agent 测试。

## 4. 必测场景

- Business 搜索唯一标题命中：不调用 RAG，完成 `/batch` 后只生成预览。
- Business 搜索成功空结果：调用 RAG；RAG 标题/真实别名唯一命中后生成预览。
- Business 搜索超时/5xx/401/坏响应：不调用 RAG、不生成预览。
- RAG 不可用、无结果或多个候选：不生成预览、不写入。
- “第二季”和“第2季”没有真实别名关系时不自动视为相同。
- `/batch` 过滤候选后分别剩余 0、1、多个条目。
- 显式 `subjectId`：跳过搜索，仍执行 `/batch` 和确认。
- 多候选按序号、唯一名称、歧义名称、非法选择、用户不匹配、过期和新查询清理。
- 预览后只有明确确认才执行；已有收藏不覆盖；基础设施写入不确定时保留动作。
- 既有推荐结果多项加入想看、进度更新及现有状态解析测试继续通过。

## 5. 启动前门禁

- `prd.md`、`design.md`、`implement.md` 已完成并通过最终规划摘要审核。
- 用户在最新规划摘要后明确批准实现。
- 执行 `python ./.trellis/scripts/task.py validate .trellis/tasks/09-16-wishlist-title-resolution` 通过。
- 通过门禁后才执行 `task.py start`，再读取 `trellis-before-dev` 并进入代码修改阶段。
