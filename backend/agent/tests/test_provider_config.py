"""LLM 供应商解析优先级与失败即止校验。

供应商由密钥是否存在决定（DeepSeek 优先，其次 DashScope），禁止从模型名前缀推断。
"""

import pytest

from app.config import Settings, resolve_llm_provider


def make_settings(deepseek: str, dashscope: str) -> Settings:
    return Settings(deepseek_api_key=deepseek, dashscope_api_key=dashscope, _env_file=None)


@pytest.mark.parametrize("deepseek,dashscope,expected", [
    ("d", "", "deepseek"), ("", "q", "dashscope"), ("d", "q", "deepseek")
])
def test_provider_precedence(deepseek, dashscope, expected):
    assert resolve_llm_provider(make_settings(deepseek, dashscope)).provider == expected


def test_missing_keys_fail_fast():
    with pytest.raises(ValueError, match="LLM API Key"):
        resolve_llm_provider(make_settings("", ""))
