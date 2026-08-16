# 确定性 Agent 评测（Eval）

离线确定性评测：复用生产 `build_graph()`/gateway/domain agent/PendingAction 边界，仅把
LLM 与 `call_api` 替换为确定性替身，零网络、零副作用。每个 required case 必须离线 PASS，
无平均分阈值。

## 离线模式（CI 门禁）

```bash
python -m evals.runner --mode offline
```

- 加载 `evals/cases/*.yaml`（≥30 个 required case，五类：routing / recommendation /
  collection_progress / wishlist / safety）。
- 退出码：`0` 全部通过，`1` 有断言失败，`2` 数据集格式/校验错误。
- 运行前会临时把 `settings.deepseek_api_key` 设为假 Key，仅让真实图路径走通，不用于断言。

## Live 模式（诊断用，不作 CI 门禁）

```bash
ALLOW_LIVE_AGENT_EVAL=true python -m evals.runner --mode live --sample 10
```

- 必须显式设置 `ALLOW_LIVE_AGENT_EVAL=true` 且至少配置一个供应商 Key，否则立即失败。
- 供应商解析直接复用生产 `resolve_llm_provider(settings)`：两 Key 都在选 DeepSeek，
  只有百炼选百炼，都空抛错。
- `--provider deepseek|dashscope` 可显式覆盖优先级；显式指定但对应 Key 缺失 → 立即失败，不回退。
- Business 写接口仍走 dry-run 替身，禁止修改真实用户数据。
- 报告输出模型名、配置版本、通过率、延迟 p50/p95。

## 数据集与门禁测试

```bash
.venv/Scripts/python.exe -m pytest tests/test_eval_dataset.py -v   # 30+ case 离线门禁
.venv/Scripts/python.exe -m pytest tests/test_eval_runner.py -v   # 执行器/CLI 单元测试
```

隐私红线：报告与日志只含工具名、路由目标、挂起动作类型/操作、Business (method, path)、
错误类别，绝不包含用户输入、JWT/API key、工具参数、完整回答或 Business 响应体。
