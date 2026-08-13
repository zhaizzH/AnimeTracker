# AnimeTracker 开发指南

个人动漫追番平台「番组手账」：管理番剧条目、追番进度、评分标签，内置 AI 对话 Agent（搜索/发现/推荐）。前后端分离，AI Agent 独立 Python 服务。

## 技术架构

| 模块 | 技术 | 端口 / 说明 |
| ---- | ---- | ---- |
| `backend/business` | Spring Boot 3.2 + MyBatis-Plus + Java 21（Maven 多模块） | 8080，业务后端 |
| `backend/agent` | FastAPI + LangGraph | 8090，AI 对话 Agent（Python venv） |
| `backend/data/importer` | Python 3.10+ + SQLAlchemy | 数据导入（Bangumi） |
| `frontend/client` | React 18 + TS + Vite 6 + Ant Design 5 + Zustand + React Query | 5173（开发），80（生产，nginx） |
| `frontend/admin` | 同上技术栈 | 5174（开发），81（生产，nginx） |
| 依赖 | MySQL 8 / Redis / MinIO | 3306 / 6379 / 9000 |

`backend/business` 多模块：`app`（启动）、`common`、`pojo`（entity/vo/dto）、`admin`、`client`、`agent`（Java 转发层，转发到 Python 8090）。

## 关键命令

```bash
# 后端构建（产物在 app/target/）
cd backend/business && mvn clean package -DskipTests

# AI Agent（Python）
cd backend/agent && source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8090

# 前端
cd frontend/client && npm install && npm run dev   # admin 同理
```

## 代码规范

### 错误拦截（backend/business）

- 错误码 = HTTP 状态码，统一 `ErrorType` 枚举 + `BizException`，禁止裸 int
- Service 层：`throw new BizException(ErrorType.X, "中文消息")`；带数据用三参构造
- 安全层 401/403 走 `SecurityConfig.writeJson`；业务异常/参数校验走 `GlobalExceptionHandler`
- 日志：业务异常 `log.warn`，未知异常 `log.error`（全栈），校验失败 `log.warn`
- 禁止向客户端透传内部细节（resourcePath、SQL、堆栈 → 通用中文消息）
- 兜底：DB 约束冲突 → 409，AccessDenied → 403，未知 → 500
- 响应体统一 `{code, message, data}`，code = HTTP 状态码

### 注释规范

- 注释用**中文**，解释 why 不解释 what
- public 类/方法加 Javadoc 一句话概述；controller 端点 doc 补触发条件
- `@param`/`@return` 非显然才写，不机械堆
- pojo 模块所有字段必须加注释：entity 按 `docs/db-schema.sql`，vo/dto 按业务含义
- 反例：`int total = a + b; // 计算总数` ✗

### pojo 分包（backend/business）

- `pojo.entity` 扁平不动；`pojo.dto` / `pojo.vo` 下按 8 领域子包分包：auth / user / subject / collection / log / dashboard / imprt / tag（`import` 是 Java 关键字不可作包名，导入领域包名取 `imprt`）
- 归类按业务领域语义（番剧统计归 subject、收藏统计归 collection、纯运营聚合指标归 dashboard），不按类名首业务词、不按产出模块；评分/类型分布仅在独立聚合 VO（RatingCountVO/TypeCountVO）时归 dashboard，嵌在领域统计 VO 内时随宿主归领域
- 命名后缀：入参/请求体 `XxxDTO`、列表/查询筛选（含分页）`XxxQueryDTO`、出参 `XxxVO`；每个类文件单 public 类，禁止 controller 内嵌请求类
- DTO 约束注解一律带中文 `message`，逐条写在注解上，不引入 zh ValidationMessages 资源束

### controller 参数/返回（backend/business）

- 单参 / `@PathVariable` / `@RequestHeader` / multipart / 仅 page/size 薄参 → 不折叠 DTO，校验留在方法签名，由类级 `@Validated` 触发
- 两个及以上 query/body 字段收进一个 DTO，形参名固定 `request`；query 一律 model-attribute 绑定（QueryDTO 不加 `@RequestBody`），`@RequestBody` 仅 POST/PUT JSON body DTO
- 返回一律 `Result<T>`，分页用 `PageResult<T>`；分页默认 page=1、size=20、上限 `@Max(100)`（导入记录例外：默认 10、上限 1000）
- 折叠后原 required 参数必须补 `@NotBlank` 类兜底约束，避免缺参静默退化为 null 透传

### 分层边界与 converter（backend/business）

- controller 只做参数绑定 + `SecurityUtil` 取身份 + 调 service，无业务逻辑无 SQL；默认值/哨兵/trim 逻辑在 service
- entity↔vo/dto 转换一律走 converter 包，禁止在 service/controller 手写转换
- service 层抛业务异常用 `BizException`；service 变量命名：组装单个返回 VO 用 `vo`，多 VO 用角色名（`detailVO`/`statsVO`），service 层没有 `result`（`Result` 是 controller 层概念）

### mapper XML（backend/business）

- 位置 `<module>/src/main/resources/mapper/XxxMapper.xml`，`namespace` = mapper 接口全限定名
- 简单 CRUD 用 MyBatis-Plus 内置方法，复杂 SQL 写 XML
- pojo 类搬迁/改名必须同步 mapper XML 的 `resultType`（编译抓不到，靠全量 grep 核对）

### agent 转发层豁免

- agent 模块（Java 转发层）body 透传 `Map<String,Object>`，不建 DTO、不强制分包；仅统一 `Result<?>` 返回

## 提交规范

- 格式：`类型(范围): 中文描述`，如 `feat(数据): 添加 Bangumi 数据导入器`
- 类型：`feat | fix | docs | style | refactor | perf | test | chore | ci`
- 模板见 `.gitmessage`

## 部署

- 生产环境 systemd 服务：`animetracker-business`（8080）、`animetracker-agent`（8090）
- 一键更新：`sudo ./update.sh`（git pull → 后端构建重启 → Agent 重启 → 前端构建 → 验证）
- 生产配置在 `/etc/animetracker/application-local.yml`（jar 以 `--spring.config.additional-location=file:/etc/animetracker/` 加载）
- 生产 nginx：80 = client dist，81 = admin dist，`/api` 反代 8080

## 注意事项

- 本仓库 public：**数据库/中间件密码、密钥等敏感信息一律不入库**，需要时向维护者索取
- 改 `backend/business` 的 entity/表结构时，同步检查 `docs/db-schema.sql` 和 pojo 注释
- AI Agent 模块的 API 经 Java `agent` 模块转发（`/api/agent/**`），不要直接暴露 8090
- 两个前端（client/admin）开发态都通过 Vite 代理把 `/api` 转发到 `http://localhost:8080`
