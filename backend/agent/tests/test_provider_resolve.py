import pytest
from pydantic import ValidationError
from app.config import Settings


def test_default_provider_empty():
    s = Settings(_env_file=None)
    assert s.llm_provider == ""
    assert s.llm_reasoning_effort == "high"


def test_extra_forbid_rejects_unknown_env():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{"LLM_NONEXISTENT": "x"})
