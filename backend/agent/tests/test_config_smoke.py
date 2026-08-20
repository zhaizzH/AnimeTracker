# backend/agent/tests/test_config_smoke.py
def test_import_app_config_succeeds():
    # 仅验证 agent 包可导入、Settings 可实例化
    from app.config import Settings
    s = Settings(_env_file=None)
    assert s.llm_provider in ("", "deepseek", "dashscope")
    assert s.llm_max_tokens > 0
