# 契约基准修复记录

本文件记录 `docs/spec/openapi.yaml` 的修复证据，对应 `tasks.md` 任务 1.1–1.5。
修复理由见 `proposal.md` — Why 的「执行本提案前发现的阻断事实」。

## 1. 前置条件核验（任务 1.1）

```bash
git status --porcelain docs/spec/openapi.yaml
# （无输出 → 工作区干净）

git log --oneline 00993ff3..HEAD -- docs/spec/openapi.yaml
# 22d7cb63 chore(task): 归档 10-20-opt-previewable-action（3/4 完成）
```

结果：工作区干净，且 `00993ff3..HEAD` 之间只有 `22d7cb63` 触碰过该文件。
该提交 message 自述「归档任务」，不含任何有意为之的契约变更，故整体回退属误操作。

## 2. 修复前后对照

修复方式：`git show 00993ff3:docs/spec/openapi.yaml > docs/spec/openapi.yaml`，
再叠加两处有意 delta（删除夹具路径、声明 liveness 探针）与两处字段级补齐。

| 指标 | `22d7cb63`/HEAD（已损坏） | 修复后 |
|---|---:|---:|
| 行数 | 5823 | 4910 |
| `paths` 数 | 72 | 69 |
| operation 数 | 74 | 71 |
| `components.schemas` 数 | 38 | 5 |
| `$ref` 出现次数 | 0 | 8 |
| `components.securitySchemes` 存在 | 否 | 是 |
| `info.description` 字符数 | 0 | 1527 |
| `text/event-stream` 出现次数 | 0 | 4 |

> 关于 `components.schemas` 从 38 降到 5：恢复 `00993ff3` 后先得到 37 个 schema，
> 其中 **32 个完全没有任何引用**（既不被 `paths` 引用，也不被其它 schema 引用），
> 且命名是 Spring 导出的占位串（`java.time.OffsetDateTime`、整句中文描述当键名）。
> 其中 30 个在 `paths` 里有一份**逐字节相同**的内联副本（共 55 处），另 2 个
> （`批量权威回查中可返回的条目字段。`、`批量权威回查分类结果。`）是漂移过的近似副本。
> 任务 3.5 要求「无孤儿 schema」，按既定决策**直接删掉这 32 个死 schema**，
> `paths` 内的内联定义原样保留——语义零变化，仅减少重复。
> 因此最终只剩 5 个被真正引用的 schema：`ChatRequest`、`SSEFrame`、
> `LexicalSearchResult`、`LexicalSearchCandidate`、`EvidenceCandidate`。

复现命令（在仓库根执行）：

```bash
python - <<'PY'
import yaml, subprocess
def stats(raw, d):
    ops = sum(len([m for m in v if m in ('get','post','put','delete','patch')]) for v in d['paths'].values())
    return dict(lines=len(raw.splitlines()), paths=len(d['paths']), ops=ops,
        schemas=len(d['components']['schemas']), refs=raw.count('$ref:'),
        securitySchemes='securitySchemes' in d['components'],
        info_desc_len=len(d['info'].get('description','') or ''),
        event_stream=raw.count('text/event-stream'))
old_raw = subprocess.run(['git','show','HEAD:docs/spec/openapi.yaml'],capture_output=True,text=True,encoding='utf-8').stdout
new_raw = open('docs/spec/openapi.yaml',encoding='utf-8').read()
for name, raw in (('HEAD', old_raw), ('now', new_raw)):
    print(name, stats(raw, yaml.safe_load(raw)))
PY
```

## 3. 有意 delta 清单

### 3.1 删除夹具路径（任务 1.2）

`22d7cb63` 混入的 4 条路径全部来自 `SecurityConfigAuthorizationTest.java`
（MockMvc 安全测试在测试类内部声明的 `@GetMapping`），不是真实对外接口：

- `/api/client/subjects/1`
- `/api/client/private`
- `/api/admin/private`
- `/actuator/health`

核验：`00993ff3` 副本本身**不含**这 4 条路径，故回退到该版本即已达成删除目标，
无需额外编辑。修复后复核：

```bash
python -c "import yaml;d=yaml.safe_load(open('docs/spec/openapi.yaml',encoding='utf-8'));print([p for p in ['/api/client/subjects/1','/api/client/private','/api/admin/private','/actuator/health'] if p in d['paths']])"
# []
```

### 3.2 新增 liveness 探针声明（任务 1.3）

`GET /actuator/health/liveness` 是 agent 侧真实跨层依赖
（`backend/agent/app/api/health.py` 的 `BUSINESS_LIVENESS_PATH`），
而 `backend/business/app/src/main/resources/application.yml` 已通过
`management.endpoint.health.probes.enabled: true` 暴露该分组。回退后的契约缺此路径，
故新增，并在 `info.description` 的「运维探针（非业务 API）」小节说明其非业务属性。

注意区分：被删除的 `/actuator/health` 是测试夹具产物；新增的
`/actuator/health/liveness` 是真实探针。两者不是同一路径。

### 3.3 补齐 evidence 接口校验约束（任务 1.4）

回退后的契约对这两个接口已有字段级定义，但两处约束与 Java 校验注解不一致，
已补齐（未新增字段，只补约束）：

| 位置 | Java 事实 | 修复前 | 修复后 |
|---|---|---|---|
| `evidence/batch` → `subjectIds` | `@NotEmpty` | 仅 `maxItems: 50` | 增 `minItems: 1` |
| `evidence/resolve` → `ids[]` | `@Positive` | 仅 `minItems/maxItems` | 增 `items.minimum: 1` |

其余已一致，核验结果：

- `evidence/batch` 请求：`required: [subjectIds]`，属性集 `{subjectIds}` ≡ `EvidenceBatchRequestDTO{subjectIds}`
- `evidence/resolve` 请求：`required: [entityType, ids]`，属性集 `{entityType, ids}` ≡ `EvidenceEntityBatchRequestDTO{entityType, ids}`
- `entityType` 枚举 `[SUBJECT, RELATION_SUBJECT, PERSON, CHARACTER, ACTOR]` ≡ `EvidenceEntityType`
- 响应 `items.$ref` → `EvidenceCandidate`，其 22 个属性集与 `EvidenceCandidateVO` 的 22 个字段**完全一致**（无一缺、无一多）

### 3.4 SSE 端点分帧说明（任务 1.5）

两个 stream 端点回退后已正确引用 `ChatRequest` 与 `SSEFrame` 且声明
`text/event-stream`，但 operation `description` 只写了「SSE 流式透传」，
未说明分帧规则。已补充分帧段落：每帧一行 `data: <SSEFrame JSON>` + 空行分隔、
不使用 SSE `event:` 字段、结束以 `is_end=true` 表达。

核验结果（两个端点均通过）：

- 请求体 `$ref` → `ChatRequest`（`{session_id, content}`，皆 required）
- 响应 content 键唯一为 `text/event-stream`
- 响应 schema `$ref` → `SSEFrame`（`required: [content, type, is_end, timestamp]`；
  `type` 枚举 `[answer, thinking, function_call, status]`；`content` 子字段
  `{text, node, parent_node, state, message, result, name, arguments}`）
- `description` 含分帧说明与 `event:` 字段缺失说明

## 4. 修复过程中的一次失误（记录备查）

首次补充分帧说明时，用 Python 字符串写入含 `\\n\\n` 的内容，被解释成真实换行，
产生一个裸行 `` `）作为帧分隔。 ``，使 YAML 扫描器报
`found character '`' that cannot start any token`。已改为「两个换行符」措辞并重新
`yaml.safe_load` 通过。教训：往 YAML 块标量里写字面反斜杠序列时不要经过 Python 转义。

## 5. 边界声明

本记录证明的是**契约文件自身已修复且内部自洽**（`$ref` 可解析、无孤儿 schema、
无夹具路径）。它**不**证明契约与 business Java 源码逐字段一致——除上述 4 个
evidence 相关类与 `EvidenceEntityType` 已人工对照外，其余路径未做逐字段核对。
该边界的完整说明见 `design.md` → Risks 与 `drills.md`。
