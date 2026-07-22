from unittest.mock import patch, MagicMock
from app.llm.models import create_llm
from app.config import Settings


def test_create_llm_returns_chat_model():
    s = Settings(dashscope_api_key="test-key")
    llm = create_llm(s)
    assert llm is not None


def test_monkey_patch_applied():
    """verify monkey-patch replaces subtract_client_response"""
    from langchain_community.chat_models.tongyi import ChatTongyi
    s = Settings(dashscope_api_key="test-key")
    _ = create_llm(s)
    assert "patched" in ChatTongyi.subtract_client_response.__name__
