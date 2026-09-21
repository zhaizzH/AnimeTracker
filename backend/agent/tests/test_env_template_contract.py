"""`.env.example` 与 `Settings` 的防漂移契约。

Agent 的 `Settings` 使用 `extra="forbid"`：模板里出现任何未声明的键，照抄模板
启动就会 `ValidationError: extra_forbidden`。本测试以真实模板文件为输入（不复制
键列表，避免测试自己成为第二个漂移源），断言「模板键 ⊆ Settings 字段」。

反向（Settings 有而模板无）不作为失败条件：`animetracker_log` 这类纯内部字段
不在模板中属于合理。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.config import Settings

_TEMPLATE = Path(__file__).resolve().parent.parent / ".env.example"
_KEY_PATTERN = re.compile(r"^([A-Z][A-Z0-9_]*)=", re.MULTILINE)


def template_keys() -> set[str]:
    """解析真实 `.env.example`，只取形如 `KEY=` 的行（跳过注释与空行）。"""
    return set(_KEY_PATTERN.findall(_TEMPLATE.read_text(encoding="utf-8")))


def settings_fields() -> set[str]:
    return {name.upper() for name in Settings.model_fields}


class TestEnvTemplateContract:
    """模板键必须全部被 `Settings` 声明。"""

    def test_template_file_exists(self):
        assert _TEMPLATE.is_file(), f"缺少配置模板: {_TEMPLATE}"

    def test_every_template_key_is_declared(self):
        undeclared = template_keys() - settings_fields()
        assert not undeclared, f"模板含 Settings 未声明的键，照抄模板启动即崩: {sorted(undeclared)}"

    def test_removed_alias_key_is_gone(self):
        """`RAG_INDEX_ALIAS` 已随 Redis alias 移除，模板不得再出现。"""
        assert "RAG_INDEX_ALIAS" not in template_keys()
        assert "rag_index_alias" not in Settings.model_fields

    def test_route_model_keys_are_declared(self):
        keys = template_keys()
        assert {"DEEPSEEK_MODEL_ROUTE", "DASHSCOPE_MODEL_ROUTE"} <= keys

    def test_template_is_directly_loadable(self, tmp_path: Path):
        """AC1：照抄模板即可构造 `Settings`，且无额外变量。"""
        env_file = tmp_path / ".env"
        env_file.write_bytes(_TEMPLATE.read_bytes())
        Settings(_env_file=str(env_file))

    def test_dotenv_sourced_dimension_is_accepted(self, tmp_path: Path):
        """dotenv 值恒为字符串：Literal[1024] 不做 str→int，模板里的 1024 曾直接崩。"""
        env_file = tmp_path / ".env"
        env_file.write_text("RAG_EMBEDDING_DIM=1024\n", encoding="utf-8")
        assert Settings(_env_file=str(env_file)).rag_embedding_dim == 1024

    def test_invalid_dimension_is_still_rejected(self, tmp_path: Path):
        """宽容转换不得放宽契约：非 1024 仍必须在启动时失败。"""
        env_file = tmp_path / ".env"
        env_file.write_text("RAG_EMBEDDING_DIM=768\n", encoding="utf-8")
        with pytest.raises(ValueError):
            Settings(_env_file=str(env_file))


class TestJobsPassthroughKeys:
    """D2：6 个 jobs 专用键必须能容身共享 `.env`，且 Agent 侧不读取。"""

    JOBS_KEYS = {
        "RAG_PROFILE_VERSION": "subject-profile-v1",
        "SEARCH_INDEX_LEASE_SECONDS": "300",
        "BACKFILL_BATCH_SIZE": "50",
        "BACKFILL_MAX_BATCHES": "10",
        "BUSINESS_BASE_URL": "http://127.0.0.1:8080",
        "RAG_TRUSTED_TAG_MIN_COUNT": "100",
    }

    @pytest.mark.parametrize("key", sorted(JOBS_KEYS))
    def test_key_is_accepted(self, key: str, tmp_path: Path):
        """键存在时 `Settings` 构造成功（当前 extra=forbid 下曾直接崩溃）。"""
        env_file = tmp_path / ".env"
        env_file.write_text(f"{key}={self.JOBS_KEYS[key]}\n", encoding="utf-8")
        assert Settings(_env_file=str(env_file)) is not None

    @pytest.mark.parametrize("key", sorted(JOBS_KEYS))
    def test_declared_as_str_passthrough(self, key: str):
        """声明为 str：非法值只该影响 jobs，不得让 Agent 启动失败。"""
        field = Settings.model_fields[key.lower()]
        assert field.annotation is str
        assert field.default == self.JOBS_KEYS[key]

    @pytest.mark.parametrize("key", sorted(JOBS_KEYS))
    def test_agent_side_has_no_read_point(self, key: str):
        """Agent 侧无读取点；这些键仅由 jobs/* 通过 os.getenv 消费。"""
        agent_root = _TEMPLATE.parent
        sources = list((agent_root / "app").rglob("*.py")) + [agent_root / "main.py"]
        for path in sources:
            source = path.read_text(encoding="utf-8")
            for accessor in (f'getenv("{key}"', f"getenv('{key}'", f'"{key}"', f"'{key}'"):
                assert accessor not in source, f"{path} 读取了 jobs 专用键 {key}（{accessor}）"

    def test_business_base_url_differs_from_backend_base_url(self):
        """两者语义不同，禁止合并：默认值必须保持不同。"""
        fields = Settings.model_fields
        assert fields["business_base_url"].default != fields["backend_base_url"].default
