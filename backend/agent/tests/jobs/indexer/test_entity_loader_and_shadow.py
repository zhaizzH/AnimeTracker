"""MultiEntityLoader 和影子索引管理单元测试。"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.entities.enums import EntityKind
from jobs.indexer.entity_loader import (
    CharacterEntity,
    EpisodeEntity,
    MultiEntityLoader,
    PersonEntity,
    _parse_career,
)
from jobs.indexer.shadow import (
    ShadowIndexManager,
    SwitchPlan,
    _parse_ft_info,
)


class _FakeMappingResult:
    def __init__(self, rows: list):
        self._rows = rows
        self.rowcount = len(rows)

    def mappings(self):
        return self

    def scalars(self):
        return self

    def first(self):
        return self._rows[0] if self._rows else None

    def all(self):
        return self._rows


class _FakeSession:
    def __init__(self, *, responses: dict[str, Any] | None = None):
        self.calls: list[tuple[str, dict]] = []
        self._responses = responses or {}

    def begin(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, stmt, params=None):
        sql = str(stmt.text) if hasattr(stmt, "text") else str(stmt)
        self.calls.append((sql, params or {}))
        for pattern, response in self._responses.items():
            if pattern in sql:
                if callable(response):
                    return response(sql, params)
                return response
        return _FakeMappingResult([])


class TestParseCareer:
    def test_parses_json_array(self):
        assert _parse_career('["声优", "歌手"]') == ("声优", "歌手")

    def test_returns_empty_for_none(self):
        assert _parse_career(None) == ()

    def test_returns_empty_for_invalid_json(self):
        assert _parse_career("not json") == ()

    def test_returns_empty_for_non_list(self):
        assert _parse_career('{"key": "value"}') == ()


class TestMultiEntityLoaderPerson:
    def test_loads_person_with_aliases_and_works(self):
        session = _FakeSession(responses={
            "SELECT id, name, person_type": _FakeMappingResult([
                {"id": 1, "name": "花泽香菜", "person_type": "PERSON", "summary": "日本声优", "career_json": '["声优"]'}
            ]),
            "SELECT name FROM person_alias": _FakeMappingResult(["はなざわ かな", "Hanazawa Kana"]),
            "SELECT s.name FROM subject_person_credit": _FakeMappingResult(["进击的巨人", "PSYCHO-PASS"]),
        })
        loader = MultiEntityLoader(session)
        person = loader.load_person(1)
        assert person is not None
        assert person.name == "花泽香菜"
        assert person.person_type == "PERSON"
        assert person.career == ("声优",)
        assert len(person.aliases) == 2
        assert len(person.representative_works) == 2

    def test_returns_none_for_missing_person(self):
        session = _FakeSession(responses={
            "SELECT id, name, person_type": _FakeMappingResult([]),
        })
        loader = MultiEntityLoader(session)
        assert loader.load_person(999) is None


class TestMultiEntityLoaderCharacter:
    def test_loads_character_with_voice_actors(self):
        session = _FakeSession(responses={
            "SELECT id, name, character_type": _FakeMappingResult([
                {"id": 5, "name": "阿尔米塔", "character_type": "CHARACTER", "summary": "主角"}
            ]),
            "SELECT name FROM character_alias": _FakeMappingResult(["アルミタ"]),
            "SELECT s.name FROM subject_character": _FakeMappingResult(["某作品"]),
            "SELECT p.name FROM character_actor": _FakeMappingResult(["早见沙织"]),
        })
        loader = MultiEntityLoader(session)
        char = loader.load_character(5)
        assert char is not None
        assert char.name == "阿尔米塔"
        assert char.voice_actors == ("早见沙织",)

    def test_returns_none_for_missing_character(self):
        session = _FakeSession(responses={
            "SELECT id, name, character_type": _FakeMappingResult([]),
        })
        loader = MultiEntityLoader(session)
        assert loader.load_character(999) is None


class TestMultiEntityLoaderEpisode:
    def test_loads_episode_with_subject_title(self):
        session = _FakeSession(responses={
            "SELECT e.id": _FakeMappingResult([
                {
                    "id": 10, "subject_id": 1, "sort": 1.0,
                    "name": "Episode 1", "name_cn": "第一话",
                    "description": "开始", "airdate": "2026-01-05",
                    "subject_title": "某动画",
                }
            ]),
        })
        loader = MultiEntityLoader(session)
        ep = loader.load_episode(10)
        assert ep is not None
        assert ep.subject_title == "某动画"
        assert ep.sort == 1.0
        assert ep.name_cn == "第一话"

    def test_returns_none_for_missing_episode(self):
        session = _FakeSession(responses={
            "SELECT e.id": _FakeMappingResult([]),
        })
        loader = MultiEntityLoader(session)
        assert loader.load_episode(999) is None


class TestParseFtInfo:
    def test_parses_flat_list(self):
        raw = [b"index_name", b"idx:rag:subject:v1", b"num_docs", b"1500"]
        result = _parse_ft_info(raw)
        assert result["index_name"] == "idx:rag:subject:v1"
        assert result["num_docs"] == "1500"

    def test_handles_dict_input(self):
        raw = {"index_name": "test", "num_docs": "100"}
        assert _parse_ft_info(raw) == raw


class TestShadowIndexManager:
    def test_list_indexes_filters_flat_redis_response(self):
        redis = MagicMock()
        redis.execute_command.return_value = [
            b"idx:rag:subject:v1",
            b"unrelated:index",
            b"idx:rag:subject:v2",
        ]
        manager = ShadowIndexManager(redis)

        assert manager.list_indexes() == ["idx:rag:subject:v1", "idx:rag:subject:v2"]
        redis.execute_command.assert_called_once_with("FT._LIST")

    def test_get_info_returns_document_count(self):
        redis = MagicMock()
        redis.execute_command.return_value = [
            b"index_name", b"idx:rag:subject:v2026-09",
            b"num_docs", b"5000",
        ]
        manager = ShadowIndexManager(redis)
        info = manager.get_info("v2026-09")
        assert info is not None
        assert info.document_count == 5000
        assert info.index_name == "idx:rag:subject:v2026-09"

    def test_get_info_returns_none_for_missing_index(self):
        redis = MagicMock()
        redis.execute_command.side_effect = Exception("Unknown index name")
        manager = ShadowIndexManager(redis)
        assert manager.get_info("nonexistent") is None

    def test_execute_switch_refuses_without_gate(self):
        redis = MagicMock()
        manager = ShadowIndexManager(redis)
        plan = SwitchPlan(
            current_alias_target="idx:rag:subject:old",
            new_index_version="v2026-09",
            new_index_name="idx:rag:subject:v2026-09",
            document_count=5000,
            gate_passed=False,
            gate_reasons=("coverage below threshold",),
        )
        result = manager.execute_switch(plan)
        assert result.success is False
        assert "gate not passed" in result.error
        redis.execute_command.assert_not_called()

    def test_execute_switch_succeeds_with_gate(self):
        redis = MagicMock()
        redis.execute_command.return_value = b"OK"
        manager = ShadowIndexManager(redis)
        plan = SwitchPlan(
            current_alias_target="idx:rag:subject:old",
            new_index_version="v2026-09",
            new_index_name="idx:rag:subject:v2026-09",
            document_count=5000,
            gate_passed=True,
        )
        result = manager.execute_switch(plan)
        assert result.success is True
        assert result.old_target == "idx:rag:subject:old"
        redis.execute_command.assert_called_once_with(
            "FT.ALIASUPDATE", "idx:rag:subject:active", "idx:rag:subject:v2026-09"
        )

    def test_rollback_switches_to_previous(self):
        redis = MagicMock()
        redis.execute_command.return_value = b"OK"
        manager = ShadowIndexManager(redis)
        result = manager.rollback("v2026-08")
        assert result.success is True
        assert "v2026-08" in result.new_target

    def test_prepare_switch_includes_gate_info(self):
        redis = MagicMock()
        redis.execute_command.return_value = [
            b"index_name", b"idx:rag:subject:v2026-09",
            b"num_docs", b"3000",
        ]
        manager = ShadowIndexManager(redis)
        plan = manager.prepare_switch("v2026-09", gate_passed=True)
        assert plan.gate_passed is True
        assert plan.document_count == 3000
        assert plan.new_index_version == "v2026-09"
