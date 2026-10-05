"""API 层测试脚手架。

被测应用只挂载带 ``include_health`` 的客户端聊天路由，
并用替身填充 ``app.state``。真实 lifespan 永不启动：
它会连接 Redis/MySQL 并构建 LangGraph。
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.chat import create_chat_router


class NoopStore:
    """PING 成功的存储替身。"""

    def __init__(self) -> None:
        self.ping_count = 0

    async def init_db(self) -> None:
        self.ping_count += 1


class NoopBusiness:
    """成功响应存活探测的业务网关替身。"""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return {"status": "UP"}


def fake_settings(*, rag_enabled: bool = False, llm_configured: bool = True) -> SimpleNamespace:
    """``resolve_llm_provider`` 的 settings 替身。

    它必须暴露该函数读取的每个属性，否则 LLM 检查会因错误的原因失败
    （抛 AttributeError 而非缺少 key）。
    ``llm_configured=False`` 会让解析抛异常。
    """
    return SimpleNamespace(
        rag_enabled=rag_enabled,
        llm_provider="deepseek" if llm_configured else "",
        llm_reasoning_effort="high",
        deepseek_api_key="test-key" if llm_configured else "",
        deepseek_model="deepseek-v4-flash",
        deepseek_model_route="deepseek-v4-flash",
        deepseek_base_url="https://api.deepseek.com",
        dashscope_api_key="",
        dashscope_model="qwen3.7-plus",
        dashscope_model_route="qwen3.7-plus",
    )


def _auth_dep():
    raise AssertionError("health 端点不得注入鉴权依赖")


@pytest.fixture
def make_client():
    """在手工组装的 ``app.state`` 上构建 TestClient。

    ``with_state=False`` 会让 ``app.state`` 保持为空，以验证失败即闭合路径
    （处理器回退到进程级 settings 单例来执行 LLM 检查）。
    """

    def build(*, store=None, business=None, rag_redis=None, settings_obj=None, with_state=True):
        app = FastAPI()
        if with_state:
            app.state.store = NoopStore() if store is None else store
            app.state.business_gateway = NoopBusiness() if business is None else business
            app.state.rag_redis = rag_redis
            app.state.settings = fake_settings() if settings_obj is None else settings_obj
        app.include_router(
            create_chat_router(prefix="/api/client/agent", auth_dep=_auth_dep, include_health=True)
        )
        return TestClient(app)

    return build
