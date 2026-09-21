"""`route_model` 只由 `*_MODEL_ROUTE` 决定的契约。

`AgentLlmFactory` 用 `resolved.route_model` 做路由兜底。此前两条显式
`LLM_PROVIDER` 分支误传 `*_MODEL`，导致显式配置下路由模型被静默忽略，
而按 key 兜底的分支却是正确的——同一环境下走哪条路径结果不同。
"""

from __future__ import annotations

import pytest

from app.config import Settings, resolve_llm_provider

_MODEL = "MODEL-X"
_ROUTE = "ROUTE-Y"


def _settings(**overrides: str) -> Settings:
    """用显式 kwargs 构造，绕开本地 .env，隔离环境漂移。"""
    return Settings(_env_file=None, **overrides)


class TestRouteModelContract:
    """四种组合：显式 deepseek/dashscope 与两条 key 兜底路径。"""

    def test_explicit_deepseek_uses_route_model(self):
        resolved = resolve_llm_provider(_settings(
            llm_provider="deepseek",
            deepseek_api_key="k",
            deepseek_model=_MODEL,
            deepseek_model_route=_ROUTE,
        ))
        assert resolved.provider == "deepseek"
        assert resolved.model == _MODEL
        assert resolved.route_model == _ROUTE

    def test_explicit_dashscope_uses_route_model(self):
        resolved = resolve_llm_provider(_settings(
            llm_provider="dashscope",
            dashscope_api_key="k",
            dashscope_model=_MODEL,
            dashscope_model_route=_ROUTE,
        ))
        assert resolved.provider == "dashscope"
        assert resolved.model == _MODEL
        assert resolved.route_model == _ROUTE

    def test_key_fallback_deepseek_uses_route_model(self):
        """LLM_PROVIDER 未配置时按 key 兜底；该路径原本就正确，行为不得变。"""
        resolved = resolve_llm_provider(_settings(
            llm_provider="",
            deepseek_api_key="k",
            deepseek_model=_MODEL,
            deepseek_model_route=_ROUTE,
        ))
        assert resolved.provider == "deepseek"
        assert resolved.route_model == _ROUTE

    def test_key_fallback_dashscope_uses_route_model(self):
        resolved = resolve_llm_provider(_settings(
            llm_provider="",
            deepseek_api_key="",
            dashscope_api_key="k",
            dashscope_model=_MODEL,
            dashscope_model_route=_ROUTE,
        ))
        assert resolved.provider == "dashscope"
        assert resolved.route_model == _ROUTE

    def test_key_fallback_deepseek_wins_both_keys_present(self):
        """按 key 兜底时 DeepSeek 优先；该路径的 route_model 不受影响。"""
        resolved = resolve_llm_provider(_settings(
            llm_provider="",
            deepseek_api_key="k",
            dashscope_api_key="k",
            deepseek_model=_MODEL,
            deepseek_model_route=_ROUTE,
        ))
        assert resolved.provider == "deepseek"
        assert resolved.route_model == _ROUTE

    def test_route_and_model_are_independent_fields(self):
        """两个字段可分别取值：路由模型不跟随对话模型。"""
        settings = _settings(deepseek_model=_MODEL, deepseek_model_route=_ROUTE)
        assert settings.deepseek_model != settings.deepseek_model_route
