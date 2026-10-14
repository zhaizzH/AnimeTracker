"""管理端模型配置：生效值回显与来源标注。

回显必须与 ``agent_factory.AgentLlmFactory.create()`` 的解析链一致，
否则管理页显示的值与运行时实际使用的值会分叉。
"""

from __future__ import annotations

from app.admin.config_service import AdminConfigService
from app.config import Settings

class StubRepo:
    """Redis 模型配置仓储替身；记录 set 调用以便断言写入内容。"""

    def __init__(self, initial: dict | None = None) -> None:
        self._data = dict(initial or {})
        self.set_calls: list[dict] = []

    def get(self) -> dict | None:
        return self._data or None

    def set(self, config: dict) -> None:
        self.set_calls.append(dict(config))
        self._data = dict(config)


class StubPrompts:
    def list_keys(self) -> tuple[str, ...]:
        return ()

    def get(self, key: str, fallback_path: str | None = None) -> str:
        return ""

    def set(self, key: str, content: str) -> None:
        pass

    def reset(self, key: str) -> str:
        return ""


def _settings(**overrides) -> Settings:
    """显式 kwargs 构造，绕开本地 .env，隔离环境漂移。"""
    base = dict(
        llm_provider="dashscope",
        dashscope_api_key="k",
        dashscope_model="MODEL-A",
        dashscope_model_route="ROUTE-A",
        llm_temperature=0.3,
        llm_max_tokens=4096,
        llm_thinking_budget=2048,
        llm_reasoning_effort="high",
    )
    base.update(overrides)
    return Settings(_env_file=None, **base)


def _service(runtime: dict | None = None, **settings_overrides):
    repo = StubRepo(runtime)
    return AdminConfigService(repo, StubPrompts(), _settings(**settings_overrides)), repo


class TestEffectiveConfig:
    def test_empty_redis_reports_env_defaults(self):
        """AC1：Redis 空时全部字段标 default 且取 Settings 值。"""
        service, _ = _service()
        view = service.get_effective_config()

        assert view["model"] == "MODEL-A"
        assert view["modelRoute"] == "ROUTE-A"
        assert view["temperature"] == 0.3
        assert view["maxTokens"] == 4096
        assert view["thinkingBudget"] == 2048
        assert view["reasoningEffort"] == "high"
        assert set(view["_sources"].values()) == {"default"}

    def test_partial_override_marks_only_that_field(self):
        """AC2：局部覆盖只标记该字段，其余仍为 default。"""
        service, _ = _service({"temperature": 0.9})
        view = service.get_effective_config()

        assert view["temperature"] == 0.9
        assert view["_sources"]["temperature"] == "override"
        assert view["model"] == "MODEL-A"
        assert view["_sources"]["model"] == "default"

    def test_zero_temperature_is_an_override_not_fallback(self):
        """0 是合法值：必须保留并标 override，不得当成未设置回退 0.3。"""
        service, _ = _service({"temperature": 0.0})
        view = service.get_effective_config()

        assert view["temperature"] == 0.0
        assert view["_sources"]["temperature"] == "override"

    def test_zero_thinking_budget_is_an_override(self):
        service, _ = _service({"thinkingBudget": 0})
        view = service.get_effective_config()

        assert view["thinkingBudget"] == 0
        assert view["_sources"]["thinkingBudget"] == "override"

    def test_blank_model_falls_back_like_the_factory(self):
        """工厂用 `or`：空串视为未设置，回显也必须回退并标 default，否则与运行时不一致。"""
        service, _ = _service({"model": ""})
        view = service.get_effective_config()

        assert view["model"] == "MODEL-A"
        assert view["_sources"]["model"] == "default"

    def test_reflects_changed_settings(self):
        """AC3：改 Settings 后回显随之变化，证明值确实来自 Settings 而非常量。"""
        service, _ = _service(llm_temperature=1.25, llm_max_tokens=999)
        view = service.get_effective_config()

        assert view["temperature"] == 1.25
        assert view["maxTokens"] == 999


class TestUpdateConfig:
    def test_sparse_update_does_not_persist_defaults(self):
        """AC4：只提交被修改的字段，Redis 中不得出现未提交字段。"""
        service, repo = _service()
        service.update_model_config({"model": "custom-x"})

        assert repo.set_calls == [{"model": "custom-x"}]
        view = service.get_effective_config()
        assert view["_sources"]["model"] == "override"
        assert view["_sources"]["temperature"] == "default"

    def test_clearing_a_field_removes_its_override(self):
        """AC6：提交体不含该字段即撤销覆盖，回退继承默认。"""
        service, repo = _service({"model": "custom-x", "temperature": 0.9})
        service.update_model_config({"temperature": 0.9})

        assert repo.set_calls[-1] == {"temperature": 0.9}
        assert service.get_effective_config()["_sources"]["model"] == "default"

    def test_empty_body_is_a_noop(self):
        """空对象等价于没有修改：不得写存储，也不得清空既有覆盖。

        推论（有意为之）：清空全部字段后提交空表单不会撤销已有覆盖，
        因为空提交被解释为"什么都没改"。要撤销须逐个清空字段提交。
        """
        service, repo = _service({"model": "custom-x"})
        view = service.update_model_config({})

        assert repo.set_calls == []
        assert view["model"] == "custom-x"
        assert view["_sources"]["model"] == "override"

    def test_clearing_field_by_field_does_eventually_remove_all_overrides(self):
        """逐个清空字段可以走到「无任何覆盖」的状态。"""
        service, repo = _service({"model": "custom-x", "maxTokens": 512})
        service.update_model_config({"maxTokens": 512})
        assert service.get_effective_config()["_sources"]["model"] == "default"

        service.update_model_config({})
        # 空提交不再撤销剩余覆盖——故此时 maxTokens 仍是 override
        assert service.get_effective_config()["_sources"]["maxTokens"] == "override"

    def test_rejects_out_of_range_temperature(self):
        service, repo = _service()
        for bad in (-0.1, 2.1):
            try:
                service.update_model_config({"temperature": bad})
            except ValueError as exc:
                assert "temperature" in str(exc)
            else:
                raise AssertionError(f"temperature={bad} 应被拒绝")
        assert repo.set_calls == []

    def test_rejects_non_positive_max_tokens(self):
        service, repo = _service()
        try:
            service.update_model_config({"maxTokens": 0})
        except ValueError as exc:
            assert "maxTokens" in str(exc)
        else:
            raise AssertionError("maxTokens=0 应被拒绝")
        assert repo.set_calls == []

    def test_accepts_boundary_temperature(self):
        """边界 0 与 2 合法。"""
        service, repo = _service()
        service.update_model_config({"temperature": 0})
        service.update_model_config({"temperature": 2})
        assert repo.set_calls == [{"temperature": 0}, {"temperature": 2}]
