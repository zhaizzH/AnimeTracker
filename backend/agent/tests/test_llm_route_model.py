"""`route_model` 只由 `*_MODEL_ROUTE` 决定的契约。

`AgentLlmFactory` 用 `resolved.route_model` 做路由兜底。此前两条显式
`LLM_PROVIDER` 分支误传 `*_MODEL`，导致显式配置下路由模型被静默忽略，
而按 key 兜底的分支却是正确的——同一环境下走哪条路径结果不同。

2026-10-19 起对话模型只剩 DeepSeek：`dashscope` 分支已移除，
`LLM_PROVIDER=dashscope` 会明确报错（`DASHSCOPE_API_KEY` 只服务 RAG 嵌入）。
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
    """显式 deepseek 与 key 兜底两条路径。"""

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

    def test_route_and_model_are_independent_fields(self):
        """两个字段可分别取值：路由模型不跟随对话模型。"""
        settings = _settings(deepseek_model=_MODEL, deepseek_model_route=_ROUTE)
        assert settings.deepseek_model != settings.deepseek_model_route

class TestDashScopeRemoved:
    """百炼对话模型已移除；`DASHSCOPE_API_KEY` 仍存在但只服务 RAG 嵌入。"""

    def test_explicit_dashscope_is_rejected(self):
        """必须报错而非静默回退到 DeepSeek：静默回退会让人以为在用百炼。"""
        with pytest.raises(ValueError, match="仅支持 deepseek"):
            resolve_llm_provider(_settings(
                llm_provider="dashscope",
                dashscope_api_key="k",
                deepseek_api_key="k",
            ))

    def test_key_fallback_with_only_dashscope_key_raises(self):
        """只有 DASHSCOPE_API_KEY 时无法创建对话模型——它不参与对话。

        必须显式传 `deepseek_api_key=""`：某些测试会 import `main.py`，
        它调用 `load_dotenv()` 把真实 `.env` 灌进 `os.environ`，
        即使 `_env_file=None` 也能读到真实 Key（既有测试隔离隐患）。
        """
        with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
            resolve_llm_provider(_settings(
                llm_provider="", dashscope_api_key="k", deepseek_api_key="",
            ))

    def test_both_keys_present_still_picks_deepseek(self):
        """两个 Key 都在时 DeepSeek 优先；此时嵌入选型不受影响。"""
        resolved = resolve_llm_provider(_settings(
            llm_provider="",
            deepseek_api_key="k",
            dashscope_api_key="k",
            deepseek_model=_MODEL,
            deepseek_model_route=_ROUTE,
        ))
        assert resolved.provider == "deepseek"
        assert resolved.route_model == _ROUTE
