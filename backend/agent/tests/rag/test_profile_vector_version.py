"""画像向量链的版本来源契约。

`_subject_vector_lookup` 必须用 MySQL `search_index_release` 的 ACTIVE 版本拼
Vector Set key，不得用配置 `RAG_INDEX_VERSION` 猜测在线版本
（spec `rag-retrieval-contract.md`）。版本解析失败时 fail-safe 返回 `None` 并告警，
绝不抛出，也不得回退到配置值。
"""

from __future__ import annotations

import logging
from array import array
from typing import Any

import pytest

import main
from app.config import Settings

_ACTIVE = "v-active"
_CONFIGURED = "v-configured"
_DIM = 1024


class _FakeRedis:
    """记录 VEMB 调用；返回一个合法的 1024 维 float32 向量。"""

    def __init__(self, raw: bytes | None = None) -> None:
        self.commands: list[tuple] = []
        self._raw = raw if raw is not None else array("f", [0.5] * _DIM).tobytes()

    def execute_command(self, *args: Any) -> bytes | None:
        self.commands.append(args)
        return self._raw


class _FakeStore:
    def __init__(self, version: Any = _ACTIVE) -> None:
        self._version = version

    def active_version(self):
        if isinstance(self._version, Exception):
            raise self._version
        return self._version


def _settings(**overrides: str) -> Settings:
    return Settings(_env_file=None, **overrides)


class TestActiveVersionResolution:
    """版本解析：以 ACTIVE 为准，异常/非法值 fail-safe。"""

    def test_returns_active_version(self):
        version = main._resolve_active_index_version(
            _settings(rag_index_version=_CONFIGURED),
            store_factory=lambda: _FakeStore(_ACTIVE),
        )
        assert version == _ACTIVE

    def test_ignores_configured_version(self):
        """ACTIVE 与配置版本不同时，必须取 ACTIVE，不得取配置值。"""
        version = main._resolve_active_index_version(
            _settings(rag_index_version=_CONFIGURED),
            store_factory=lambda: _FakeStore(_ACTIVE),
        )
        assert version == _ACTIVE
        assert version != _CONFIGURED

    def test_no_active_release_returns_none(self):
        assert main._resolve_active_index_version(
            _settings(), store_factory=lambda: _FakeStore(None),
        ) is None

    def test_mysql_failure_is_swallowed(self):
        """MySQL 不可达不得外泄异常。"""
        assert main._resolve_active_index_version(
            _settings(), store_factory=lambda: _FakeStore(RuntimeError("mysql down")),
        ) is None

    def test_factory_construction_failure_is_swallowed(self):
        def _boom():
            raise OSError("cannot connect")

        assert main._resolve_active_index_version(_settings(), store_factory=_boom) is None

    @pytest.mark.parametrize("bad", ["", "v:1", "v 1", "v\t1", "  "])
    def test_invalid_version_returns_none(self, bad: str):
        """版本串会拼进 Redis key：含 ':' 或空白必须拒绝（同 activate() 约束）。"""
        assert main._resolve_active_index_version(
            _settings(), store_factory=lambda: _FakeStore(bad),
        ) is None

    @pytest.mark.parametrize("bad", [None, "", "v:1", "v 1"])
    def test_resolution_failure_logs_warning(self, bad: str | None, caplog):
        """解析失败必须可观测：告警日志是区分「版本不可用」与「用户本就无收藏」的手段。"""
        with caplog.at_level(logging.WARNING, logger="main"):
            main._resolve_active_index_version(
                _settings(), store_factory=lambda: _FakeStore(bad),
            )
        assert any("个性化降级" in record.message for record in caplog.records)


class TestSubjectVectorLookupUsesActiveVersion:
    """查询 key 必须使用传入的 ACTIVE 版本。"""

    def test_key_uses_active_version_not_configured(self):
        rag_redis = _FakeRedis()
        lookup = main._subject_vector_lookup(rag_redis, _ACTIVE)
        vector = lookup(42)
        assert vector is not None and len(vector) == _DIM
        assert len(rag_redis.commands) == 1
        assert rag_redis.commands[0][1] == f"rag:vectors:SUBJECT:{_ACTIVE}"

    def test_none_version_returns_none_without_vemb(self):
        """版本缺失即无权威版本可用：直接返回 None，不得发 VEMB、不得猜配置版本。"""
        rag_redis = _FakeRedis()
        lookup = main._subject_vector_lookup(rag_redis, None)
        assert lookup(42) is None
        assert rag_redis.commands == []

    def test_invalid_version_returns_none_without_vemb(self):
        rag_redis = _FakeRedis()
        lookup = main._subject_vector_lookup(rag_redis, "v:1")
        assert lookup(42) is None
        assert rag_redis.commands == []

    def test_malformed_vector_still_returns_none(self):
        rag_redis = _FakeRedis(raw=b"short")
        lookup = main._subject_vector_lookup(rag_redis, _ACTIVE)
        assert lookup(42) is None

    def test_vemb_failure_is_swallowed(self):
        class _FailingRedis:
            def execute_command(self, *args: Any):
                raise RuntimeError("redis down")

        lookup = main._subject_vector_lookup(_FailingRedis(), _ACTIVE)
        assert lookup(42) is None
