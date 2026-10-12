# AnimeTracker 领域术语表

本文件是 AnimeTracker 的**领域语言**单一来源：只定义本项目特有的概念（番剧、收藏、检索、Agent 写操作），一行一个规范词，给出它**是**什么，以及应避免的竞争词。这里不放签名、字段、路径、阈值或决策理由——那些属于 `.trellis/spec/` 下的各层规范。

**工程约定类词汇不在此表**（如「基线数字」「flaky」「move-only 重构」「xfail(strict=True)」）；它们不是领域概念，留在 [guides/cross-layer-thinking-guide.md](./guides/cross-layer-thinking-guide.md#项目术语表)。

## 番剧目录域（catalog）

**Subject**：
一部番剧条目，整个目录的聚合根；只收录 Bangumi 动画类条目。
_Avoid_: 番剧、条目、anime、title、entry

**Episode**：
Subject 下的一集；集号为可排序小数，以容纳特别篇。
_Avoid_: 剧集

**SubjectAlias**：
Subject 的多语言替代表题。
_Avoid_: 别名

**SubjectMetaTag**：
挂在 Subject 上的**官方**元标签。
_Avoid_: 标签、tag——与 SubjectTag 是两张不同的表，勿混用

**SubjectTag**：
来源于 Bangumi 的**社区/用户**标签，带被使用次数。
_Avoid_: 标签——与 SubjectMetaTag 区分

**SubjectRelation**：
两个 Subject 之间的有向关系（前传/续集/外传等）。
_Avoid_: 关联条目、relation

> **`relation` 在本库有四种互不相同的含义**：作品↔作品关系、主创在作品内的主次、角色在作品内的主次、以及角色↔演员的配音/出演属性。引用 `relation` 时必须连带指明所属表，绝不能只说「relation」。

**Person**：
现实中的个人、公司或组合（监督、制作公司等）。
_Avoid_: 人物、staff、creator

**Character**：
作品内的虚构角色或作品内组织。
_Avoid_: 角色

**SubjectPersonCredit**：
Subject 与 Person 之间的主创职责关系；Person 未解析时以占位名记录。
_Avoid_: 主创、credit、staff

**CharacterActor**：
**限定在某一 Subject 内**的角色↔Person 映射（声优或演员）。
_Avoid_: 声优、VA、cast

## 用户收藏域（collection）

**Collection**：
用户对一个 Subject 的追踪记录，每个 (用户, Subject) 至多一条，携带状态、评分与观看进度。
_Avoid_: favorite、收藏、bookmark、watchlist——「收藏」指 Collection 整体，不只是「想看」

**CollectionType**：
Collection 的五态之一：想看 / 看过 / 在看 / 搁置 / 抛弃。
_Avoid_: status、state

**Wishlist**：
把 Subject 标记为「想看」而不覆盖既有 Collection 的**动作**，幂等。
_Avoid_: 想看——「Wishlist」是动作，「想看」是 CollectionType 的一个状态，二者不是同义词

**ep_status / epStatus**：
用户在一个 Collection 上已看到的集数。
_Avoid_: 看到第几集、progress——与「进度预览」区分

**Rate**：
用户对 Collection 的评分，取一个「未评分」值加 0~满分区间。
_Avoid_: 评分——与 Subject 上的 Bangumi 社区评分数值区分

**Watch profile**：
由用户收藏派生的偏好向量，用于推荐。
_Avoid_: 观看画像、preference

## 导入与任务域（import / jobs）

**ImportRecord**：
一次导入器运行的审计记录（模式、计数、断点、心跳）。
_Avoid_: 导入记录、import job——与 Job 区分

**ImportMode**：
导入器的运行模式：全量 / 季度 / 近期 / 增量 / 抽样。
_Avoid_: sync mode

**Season key**：
季度标识，形如 `{年}-{春|夏|秋|冬}`。
_Avoid_: 季度、quarter——对外接口用 `quarter` 措辞，实体/投影用 season key

**Job**：
统一任务队列中的一项；三类任务（实体详情补全、检索索引、RAG 索引）共用一张表、靠类型区分。
_Avoid_: 任务、task、queue item

**EntityKind**：
可被索引的实体类别：Subject / Episode / Person / Character 四类。
_Avoid_: entity type——与五值的 Evidence 实体类型不是同一枚举，勿互相套用

**Backfill**：
对 Person / Character 详情字段的渐进式补全。
_Avoid_: 回填、enrichment——「enrichment」也用于 Evidence，注意语境

**Index version**：
双搜索投影（词法 + 语义）的版本标识；同一时刻只有一个版本处于激活态。
_Avoid_: 索引版本、release——release 指激活指针记录本身

## 检索与 RAG 域（retrieval）

**Evidence**：
在候选 Subject 送入模型前，附在其上的、经权威回查的结构化事实（摘要、命中标签/主创/角色/关系、评分类分等）。
_Avoid_: 证据、provenance、citation、context

**Authority（回查）**：
Business 数据库是候选有效性的唯一裁决者；检索命中在经回查前一律不可信。
_Avoid_: 权威回查、verify、hydrate

**Lexical search**：
基于 MySQL 全文索引（ngram 分词）的词法召回。
_Avoid_: 词法召回、keyword search

**Semantic search / Vector Set**：
基于 Redis 8 Vector Set 的语义召回。
_Avoid_: vector search——不要写 RediSearch / Redis Stack，本项目刻意不用它们

**RRF**：
把词法与语义两路召回结果做 reciprocal rank fusion 的融合算法。
_Avoid_: 融合、merge、blend

**Profile**：
按实体类型构建并嵌入的确定性规范文本，带版本与内容哈希。
_Avoid_: 档案、document、chunk

**gate / 发布门禁**：
索引激活前的强制检查：校验同版本的多份评估报告与阈值，任一缺失/不一致/不达标即 fail-closed；通过并经人工确认后才允许激活。
_Avoid_: 部署、promote

**Shadow index / shadow eval**：
激活前对候选索引的评估。
_Avoid_: canary、staging

## Agent 与写安全域（agent / write safety）

**PendingAction**：
以类型判别的、暂存的待确认写意图（改收藏进度、加想看、解析 Subject、设收藏类型）。
_Avoid_: 待确认动作、draft、cart、intent

**Preview → confirm → execute**：
所有 Agent 写操作的两阶段协议：预览不写任何东西，确认才执行；确认参数由系统注入，模型不能自行构造。
_Avoid_: HITL、approval flow

**Domain agent**：
面向用户的三个图节点：检索 / 发现 / 推荐，另有管理端节点。
_Avoid_: 域节点、route、skill、worker

**Gateway router**：
选择 Domain agent 的结构化意图路由节点；检测到待确认动作加明确确认时，确定性强制走「推荐」。
_Avoid_: 意图路由、classifier、dispatcher

**AgentEvent**：
SSE 事件信封，四类：answer / thinking / function_call / status；**没有 end 类型**，结束由结束标志表达。
_Avoid_: stream event、chunk

**Session**：
一次持久化的聊天会话。
_Avoid_: 会话、conversation、thread、chat

**Managed prompt**：
以 Redis 为准、本地文件为兜底的提示词。
_Avoid_: 托管提示词、system prompt

## 认证域（auth）

**Access token**：
短寿命、仅存前端内存的 Bearer 凭据；绝不持久化到 cookie 或 localStorage。
_Avoid_: JWT、id token

**Refresh token / `at_refresh`**：
放在 HttpOnly cookie 中的轮换凭据，带空闲与绝对寿命上限。
_Avoid_: refresh cookie、session token

**AuthSessionStore**：
服务端保存的刷新会话，用于密码/角色变更时即时失效。
_Avoid_: token store、whitelist

**Superadmin**：
靠固定用户 id 识别的粗粒度管理员；角色枚举本身只有普通用户与管理员两级。
_Avoid_: 超管、root、owner

**OperationLog**：
用户/管理员操作的审计记录，由注解加切面采集。
_Avoid_: 操作日志、audit log、event log
