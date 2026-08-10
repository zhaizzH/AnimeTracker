# AnimeTracker「番组手账」测试计划

> 版本：v1.2（2026-08-10）
> 制定方：Hermes Agent 主导，融合 Claude Code 与 OpenAI Codex 双 AI 评审意见（三方协作产出）
> 适用：测试专用笔记本（16GB 内存），源码方式运行全部服务（local profile）
> 执行方式：本文件交给 **Codex CLI** 作为任务规格读取执行

---

## 0. 执行说明（Codex 指令）

> 执行者（Codex）按以下规则执行本测试计划，不要自行发挥范围。

1. **读代码核对端点**：执行 L3 前先 `rg -n "Mapping\(" backend/business --type java | head -50` 核对冒烟脚本端点路径，与实际 controller 不一致时以代码为准，并在报告注明。
2. **顺序执行**：L0 → L1 → L2 → L3 → L4，逐层串行；每层完成即记录结果。
3. **失败分类**：
   - 环境问题（DB/Redis 未起、端口占用、缺 DASHSCOPE_API_KEY）→ 记「环境受限」于报告 §四，继续后续层，不阻塞。
   - 代码问题 → 记缺陷（复现步骤、实际/期望响应、严重度）于报告 §三，并在**本地修复**（改代码 + 复测通过）；**修复后不提交**，改动留在工作区。
4. **测试账号**：client 用 `test1/123456`，admin 用 `admin/123456`；登录失败先查库确认账号存在且邮箱已验证，**不要注册新账号**（避免撞限流）。
5. **安全**：报告/输出中不得出现 token、密钥；测试账号密码仅在登录命令中使用，不写入报告。
6. **产出**：执行完按 §7 模板写报告，保存为 `docs/test-report-<YYYYMMDD>.md`。**禁止 git commit / push**——修复代码与报告均留在本地工作区，待人工 review 后自行提交。

---

## 1. 测试目标

1. 验证用户侧核心闭环可用：**看番 → 收藏 → 对话**。
2. 验证错误处理规范落地：响应体统一 `{code, message, data}`，`code` = HTTP 状态码；401/403/409/500 映射正确，不透传内部细节（见 docs/backend-conventions.md）。
3. 回归安全修复：验证码防爆破（5 次锁 5 分钟）、认证接口限流（邮箱+IP）、JWT 登出即失效（Redis 白名单）。
4. 确认管理端边界：**仅测已接入真实 API 的部分（登录 + 仪表盘 + 导入）**，其余预览页骨架只测不报错。
5. 确认 AI Agent 链路：Java(:8080) 转发 → Python(:8090) SSE 流式，工具调用回查 business API。

## 2. 测试范围

| 范围 | 含 | 不含 |
|---|---|---|
| 后端 Java | app/src/test 11 个测试类回归 | 不新增集成测试框架 |
| Agent Python | tests/ 20 个 pytest 文件 | 真实 LLM 长对话回归（视 DASHSCOPE_API_KEY 而定） |
| 前端 | tsc 类型检查 + 生产构建；手动冒烟 | 组件/单元测试（前端零测试，本次不补脚手架） |
| API | curl 冒烟全链路 | 压测、性能基准 |
| E2E | 关键链路浏览器实测 | 多用户并发、全量数据导入 |

## 3. 环境与前置条件

**测试机**：另一台笔记本（16GB 内存），**源码方式**运行服务（非 jar），local profile。

| 依赖 | 端口 | 启动方式 | 检查命令 |
|---|---|---|---|
| MySQL 8 (Docker) | 3306 | Docker | `docker ps \| grep mysql` |
| Redis (Docker) | 6379 | Docker | `redis-cli ping` |
| MinIO (Docker) | 9000 | Docker | `docker ps \| grep minio` |
| business 后端 | 8080 | `mvn -pl app spring-boot:run -Dspring-boot.run.profiles.active=local` | `curl -s http://localhost:8080/doc.html` |
| agent 服务 | 8090 | `venv/bin/uvicorn main:app --host 0.0.0.0 --port 8090`（backend/agent 下） | `curl -s http://localhost:8090/docs` |
| client 前端 | 5173 | `cd frontend/client && npm run dev` | 浏览器访问 |
| admin 前端 | 5174 | `cd frontend/admin && npm run dev` | 浏览器访问 |

**测试账号（已提供，测试专用）**

| 端 | 账号 | 密码 | 角色 |
|---|---|---|---|
| client | test1 | 123456 | 普通用户 |
| admin | admin | 123456 | 管理员（role=ADMIN） |

**准备清单**

- [ ] 测试账号：test1 / admin 已就绪（如上表；如登录失败，先查库确认账号存在且邮箱已验证）
- [ ] 测试数据：至少 1 部带剧集的番剧（subject + episode）
- [ ] 端口预检：`ss -ltn | grep -E ':(8080|8090)'` 确认服务可用
- [ ] Agent 侧配置：`backend/agent/.env`（DASHSCOPE_API_KEY、REDIS_URL）存在性确认
- [ ] 数据库已按 `docs/db-schema.sql` 建表

## 4. 分层测试策略

### L0 Java 单测（约 5–15 分钟）

```bash
cd /home/zhaizz/projects/AnimeTracker/backend/business
export MAVEN_OPTS="-Xmx1g"          # 限堆，避免与 Docker 依赖争内存
mvn test                             # 全模块单测，产物 target/surefire-reports/
```

**通过标准**
- `BUILD SUCCESS`，0 failure / 0 error
- 11 个测试类全部执行（surefire-reports 核对）：log / ratelimit / exception / client service+controller / admin mapper+service
- 首轮失败区分「环境问题」（DB 未起、端口占用）与「代码问题」，前者修复重跑，后者记为缺陷

### L1 Agent pytest（约 3–5 分钟）

```bash
cd /home/zhaizz/projects/AnimeTracker/backend/agent
venv/bin/python -m pytest tests/ -v --tb=short
```

**通过标准**
- 20 个 pytest 文件全部 collected，通过率 100%
- 重点核对：SSE/流式、create_agent InjectedState（用户上下文注入，LLM 不可见 token）、HTTP 助手 401 统一映射、收藏工具全只读
- 失败的若为真实 LLM 调用（无 DASHSCOPE_API_KEY），记录为「环境跳过」而非用例失败

### L2 前端 tsc + 构建（每端约 5–10 分钟）

```bash
cd /home/zhaizz/projects/AnimeTracker/frontend/client && npm run build   # 含 tsc 检查
cd /home/zhaizz/projects/AnimeTracker/frontend/admin  && npm run build
```

**通过标准**
- 退出码 0，无 TS 类型错误；`dist/` 生成且含 index.html + assets
- admin 构建可过即达标（预览版不追业务正确性）

### L3 API 冒烟（curl，约 15–30 分钟）

服务已在运行，直接打真实端点（路径以实际 controller 为准，见 docs/openapi.yaml 核对）：

```bash
BASE=http://localhost:8080

# 1 未授权访问 → 期望 code=401
curl -s $BASE/api/client/subjects | jq '.code'

# 2 登录成功（测试账号 test1/123456）→ 200 且 data 含 token
TOKEN=$(curl -s -X POST $BASE/api/client/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"test1","password":"123456"}' | jq -r '.data.token')

# 3 带 token 访问列表 → 200，data 含 records
curl -s $BASE/api/client/subjects -H "Authorization: Bearer $TOKEN" | jq '.code'

# 4 收藏链路（新增/列表/计数）
curl -s -X POST $BASE/api/client/collections -H "Authorization: Bearer $TOKEN" \
  -d '{"subjectId":1,"status":"watching"}' | jq '.code'    # 期望 200 或 409(已存在)

# 5 无效 token → 401
curl -s $BASE/api/client/subjects -H "Authorization: Bearer invalid-token" | jq '.code'

# 6 Agent SSE：Java 转发层流式
curl -sN $BASE/api/client/agent/stream -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"message":"推荐一部四月新番"}' | head -20

# 7 登出后原 token 再访问 → 401（Redis 白名单失效）
```

**通过标准**
- 未带/无效 token → 401；错误响应 body 恰为 `{code, message, data}`
- 业务异常 message 为中文，**不含** resourcePath/SQL/堆栈
- 不存在资源 → 404；DB 冲突（重复收藏）→ 409
- SSE：`Content-Type: text/event-stream`，依次收到 thinking / tool_status / answer 事件，结束后正常断开
- 注意：auth 端点控制请求频率，避免触发限流误伤

### L4 端到端（浏览器手动，约 1 小时）

1. 服务已运行；如前端需 dev server：`cd frontend/client && npm run dev`（:5173）、admin（:5174）
2. 按 §5 关键链路逐条走查，记录实际结果
3. 按链路分批走（先用户端 → Agent → 管理端），**不要同时全开**（内存风险）

## 5. 关键链路清单

### 链路 A：登录/认证（安全重点）

| # | 步骤 | 期望 |
|---|---|---|
| A1 | 未登录访问受保护页 | 跳转登录或接口 401 |
| A2 | 正常用户登录 | 成功，JWT 下发，Redis 白名单有记录 |
| A3 | 密码错误 ×5 | 第 6 次起锁定（防爆破，5 分钟） |
| A4 | 同一邮箱+IP 快速多次发验证码 | 触发限流，429 或 200+限流提示 |
| A5 | 登出 | 原 token 失效，再访问 401 |

### 链路 B：番剧列表/详情

| # | 步骤 | 期望 |
|---|---|---|
| B1 | 列表分页 | 200，`{code:200, data:{records,total}}` |
| B2 | 关键词搜索 | 命中结果正确 |
| B3 | 季度筛选 | 仅返回该季度 |
| B4 | 标签筛选 | 标签聚合正确 |
| B5 | 详情 + 剧集列表 | 条目字段完整、episode 有序 |

### 链路 C：收藏/进度

| # | 步骤 | 期望 |
|---|---|---|
| C1 | 新增收藏（watching/planned/completed） | 200 |
| C2 | 重复收藏 | 409 |
| C3 | 更新观看进度（集数） | 200，计数接口反映 |
| C4 | MyCollections 页 | 收藏项正确展示 |
| C5 | Agent 侧 | 收藏被工具只读读取、推荐排除已收藏 |

### 链路 D：Agent SSE 对话（重点验证）

| # | 步骤 | 期望 |
|---|---|---|
| D1 | POST agent stream 带 token | 200，`text/event-stream` |
| D2 | 流式事件类型 | 依次收到 thinking / tool_status / answer，不中断 |
| D3 | 自然语言「搜索 XX」 | 触发 search 工具，回查 business API 后给结果 |
| D4 | 「我的收藏」类问题 | InjectedState 注入用户身份，只读读取该用户收藏 |
| D5 | 首段输出时间 | Java 转发生效，长思考不首段断流 |
| D6 | 会话持久化 | Redis 有 session，可列出会话 |
| D7 | 断点/中断 | SSE 关闭不拖垮 8090，日志无堆栈 |
| D8 | 无 DASHSCOPE_API_KEY | 降级验证：建连 + 错误兜底返回（记录为环境受限） |

### 链路 E：管理端

| # | 步骤 | 期望 |
|---|---|---|
| E1 | admin 登录 | 走真实 login 接口，非 ADMIN 角色被拒（403） |
| E2 | 仪表盘 | 统计数据渲染 |
| E3 | 导入任务（小批量 since 模式） | 创建导入 → importer 跑通 → import_record 落库 → 新 subject 出现在用户端列表 |
| E4 | 其余骨架页 | 仅验证页面可渲染、无 console 报错；不验证未接入功能 |

## 6. 风险与注意事项

| 风险 | 影响 | 对策 |
|---|---|---|
| 内存 16GB | MySQL+Redis+MinIO + Java + Python + 双 Node dev server 同时跑仍可能吃紧 | 分层串行执行；`MAVEN_OPTS=-Xmx1g`；Node dev server 用完即关 |
| Resend 外部邮件依赖 | 无 api-key → 注册/验证码全链路不可测 | 用预置已验证账号绕开发码；发码用例标记「可选」 |
| 测试账号 | 中途注册会撞限流（邮箱+IP 计数） | 已提供 test1 / admin 预置账号，避免注册；登录失败先查库确认账号状态 |
| DASHSCOPE_API_KEY | 无 Key → SSE 真实回答不可用 | 降级为「建连+会话+错误兜底」验证 |
| Redis 不可用 | 登录（JWT 白名单）与 Agent 会话全挂 | 冒烟前 `redis-cli ping`；Redis 挂视为环境失败 |
| 认证接口限流误伤 | 测试脚本高频请求被限流 | auth 端点控制频率 |
| 管理端是预览版 | 过度测试未接入页面得出假失败 | 范围锁定：登录+仪表盘+导入+页面可渲染 |
| 公共仓库 | 测试中不得出现真实密码/密钥 | 账号与配置走环境变量；报告不贴 token |
| SSE 转发 | 长连接被代理缓冲截断 | 冒烟直连 8080；nginx 生产需 `proxy_buffering off` |

## 7. 测试报告模板

```markdown
# AnimeTracker 测试报告

- 日期 / 执行人 / 分支 / commit：
- 环境：内存峰值、依赖服务清单（MySQL/Redis/MinIO/Key 就绪状态）

## 一、总览
| 分层 | 用例数 | 通过 | 失败 | 跳过 | 通过率 |
|---|---|---|---|---|---|
| L0 Java 单测 | | | | | |
| L1 Agent pytest | | | | | |
| L2 前端 tsc+build | | | | | |
| L3 API 冒烟 | | | | | |
| L4 E2E 关键链路 | | | | | |
| **合计** | | | | | |

## 二、关键链路结果
| 链路 | A 登录 | B 番剧 | C 收藏 | D Agent SSE | E 管理端 |
|---|---|---|---|---|---|
| 结论 | ✅/❌ | | | | |
| 失败步骤 | | | | | |

## 三、失败明细（P0 阻断 → P1 → P2）
| 编号 | 分层 | 链路 | 期望 | 实际 | 严重度 |
|---|---|---|---|---|---|
| 1 | | | | | P0 |

## 四、环境受限项（跳过原因）
| 项 | 原因 | 能否补测 |
|---|---|---|

## 五、风险遗留
## 六、上线建议（P0 清零前不建议发布）
```

---

**执行顺序建议**：L0 → L1 → L2 → L3 → L4，逐层串行；每层完成即填报告模板对应行。
