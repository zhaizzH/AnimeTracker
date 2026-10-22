# 漂移演练记录

两次演练的目的：证明契约测试套件在**真的漂移**时会变红，而不是写完之后永远绿。
每次演练都是「临时改坏 → 跑 → 记录 → 原样还原 → 确认回绿」。

运行环境：`cd backend/agent && uv run pytest tests/contracts -q`，基线 **146 passed**。

---

## Drill A — 契约侧漂移（改 `docs/spec/openapi.yaml`）

**改坏方式**：把 `POST /api/client/collections/{subjectId}/save` 请求体里的
`epStatus` 改名为 `ep_status`（`docs/spec/openapi.yaml:2108`）。

```bash
cp docs/spec/openapi.yaml .tmp-drill/drill-before.yaml
sed -i '2108s/epStatus/ep_status/' docs/spec/openapi.yaml
cd backend/agent && uv run pytest tests/contracts -q
```

**观察到的失败**（原文）：

```
E           AssertionError: 契约漂移：POST /api/client/collections/{subjectId}/save（backend/agent/app/adapters/business_http.py:92）发送了契约未声明的请求体字段 ['epStatus']；契约已声明 ['ep_status', 'rate', 'type']
E           assert not ['epStatus']

tests\contracts\test_http_contract.py:565: AssertionError
FAILED tests/contracts/test_http_contract.py::test_declared_payload_fields[POST-/api/client/collections/{param}/save-92]
1 failed, 145 passed
```

三个要素都点到了：操作 `operationId`（`POST /api/client/collections/{subjectId}/save`）、
未声明字段名（`epStatus`）、以及发出该字段的调用点（`business_http.py:92`）。

> 备注：第一次演练时我误改的是 `:1918` 的 `epStatus`，那处在响应体里、套件不断言，
> 结果 146 全绿。这本身是个有价值的观察——**套件只断言 agent 实际发送的字段，
> 不覆盖无人调用的响应字段**，符合设计里「只钉住 agent↔contract 实际边界」的取舍，
> 不应被误读成套件失效。

**还原与回绿**：`cp .tmp-drill/drill-before.yaml docs/spec/openapi.yaml`，
再跑一遍 → `146 passed`。

---

## Drill B — Agent 侧漂移（改调用点里的路径）

**改坏方式**：把 `backend/agent/app/agent/client/collections.py:60` 的
`/api/client/collections/counts` 手误成 `/api/client/collections/count`。

```bash
cp backend/agent/app/agent/client/collections.py .tmp-drill/drillB-before.py
sed -i '60s|/counts|/count|' backend/agent/app/agent/client/collections.py
cd backend/agent && uv run pytest tests/contracts -q
```

**观察到的失败**（原文）：

```
E       AssertionError: 契约漂移：
E         GET /api/client/collections/count @ backend/agent/app/agent/client/collections.py:60 只能通配匹配到 /api/client/collections/{subjectId}，但该调用点不含运行时 ID（疑似路径拼写错误；若确实带 ID，请加入 _WILDCARD_ALLOWED）
E       assert not ['GET /api/client/collections/count @ backend/agent/app/agent/client/collections.py:60 只能通配匹配到 /api/client/collections/{subjectId}，但该调用点不含运行时 ID（疑似路径拼写错误；若确实带 ID，请加入 _WILDCARD_ALLOWED）']

tests\contracts\test_http_contract.py:419: AssertionError
FAILED tests/contracts/test_http_contract.py::test_wildcard_matches_are_intentional
1 failed, 145 passed
```

这条尤其说明为什么「能解析到某个操作」不足以作为判定：`/collections/count`
确实能通配落到 `/collections/{subjectId}` 上，只看解析结果会静默放过。是
`test_wildcard_matches_are_intentional` 里「字面命中或显式进白名单」这条附加约束
把它拽住的。失败信息带了 `file:line`。

**还原与回绿**：`cp .tmp-drill/drillB-before.py backend/agent/app/agent/client/collections.py`，
再跑一遍 → `146 passed`。

---

## 这两个演练**不**证明什么

说清楚边界，免得后来者高估这套测试：

- 两个演练都只在 **agent ↔ `docs/spec/openapi.yaml`** 这条边上制造漂移。
- 它们**完全没有**触及 `backend/business/**` 的 Java 源码。也就是说，
  如果 business 侧的 `CollectionController.java` 单方面改了字段而 `openapi.yaml`
  没跟着改，本套件**依然全绿**——它信任 `openapi.yaml` 是事实源。
- `docs/spec/openapi.yaml` 是手工维护的导出产物（不是从 Java 注解自动生成的），
  所以「contract ↔ Java」这条边目前**没有任何自动校验**。
- 结论：本套件保证「agent 写出去的请求，和文档里写的一致」；
  它**不**保证「文档里写的，和 Java 真正接收的一致」。后者仍是人工 review 的责任。
