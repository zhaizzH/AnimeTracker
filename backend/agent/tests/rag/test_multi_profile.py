"""多实体 profile 构建测试。"""

from __future__ import annotations

import pytest

from app.entities.enums import EntityKind
from app.rag.multi_profile import (
    PROFILE_VERSIONS,
    CharacterProfileSource,
    EpisodeProfileSource,
    PersonProfileSource,
    ProfileResult,
    build_character_profile,
    build_episode_profile,
    build_person_profile,
)

MODEL = "text-embedding-v4"
DIMS = 1024


class TestBuildPersonProfile:
    def test_deterministic(self):
        source = PersonProfileSource(name="庵野秀明", career=["导演", "编剧"])
        p1 = build_person_profile(source, MODEL, DIMS)
        p2 = build_person_profile(source, MODEL, DIMS)
        assert p1.content_hash == p2.content_hash
        assert p1.text == p2.text

    def test_contains_name(self):
        source = PersonProfileSource(name="新海誠", aliases=["Makoto Shinkai"])
        profile = build_person_profile(source, MODEL, DIMS)
        assert "新海誠" in profile.text
        assert "Makoto Shinkai" in profile.text

    def test_entity_kind(self):
        source = PersonProfileSource(name="Test")
        profile = build_person_profile(source, MODEL, DIMS)
        assert profile.entity_kind == EntityKind.PERSON
        assert profile.schema_version == PROFILE_VERSIONS[EntityKind.PERSON]

    def test_different_model_different_hash(self):
        source = PersonProfileSource(name="Test")
        p1 = build_person_profile(source, "model-a", DIMS)
        p2 = build_person_profile(source, "model-b", DIMS)
        assert p1.content_hash != p2.content_hash

    def test_company_type_label(self):
        source = PersonProfileSource(name="MAPPA", person_type="COMPANY")
        profile = build_person_profile(source, MODEL, DIMS)
        assert "公司" in profile.text

    def test_hash_is_64_chars(self):
        source = PersonProfileSource(name="Test")
        profile = build_person_profile(source, MODEL, DIMS)
        assert len(profile.content_hash) == 64


class TestBuildCharacterProfile:
    def test_deterministic(self):
        source = CharacterProfileSource(name="初音ミク", voice_actors=("藤田咲",))
        p1 = build_character_profile(source, MODEL, DIMS)
        p2 = build_character_profile(source, MODEL, DIMS)
        assert p1.content_hash == p2.content_hash

    def test_contains_fields(self):
        source = CharacterProfileSource(
            name="エレン・イェーガー",
            aliases=("艾伦·耶格尔",),
            summary="进击的巨人主角",
            appearances=("進撃の巨人",),
            voice_actors=("梶裕貴",),
        )
        profile = build_character_profile(source, MODEL, DIMS)
        assert "エレン・イェーガー" in profile.text
        assert "艾伦·耶格尔" in profile.text
        assert "梶裕貴" in profile.text
        assert profile.entity_kind == EntityKind.CHARACTER

    def test_empty_optional_fields(self):
        source = CharacterProfileSource(name="Test")
        profile = build_character_profile(source, MODEL, DIMS)
        assert "角色名：Test" in profile.text
        assert "别名" not in profile.text


class TestBuildEpisodeProfile:
    def test_deterministic(self):
        source = EpisodeProfileSource(subject_title="進撃の巨人", sort=1.0, name="第1話")
        p1 = build_episode_profile(source, MODEL, DIMS)
        p2 = build_episode_profile(source, MODEL, DIMS)
        assert p1.content_hash == p2.content_hash

    def test_contains_subject_title(self):
        source = EpisodeProfileSource(subject_title="呪術廻戦", sort=24.0, name_cn="第24话")
        profile = build_episode_profile(source, MODEL, DIMS)
        assert "呪術廻戦" in profile.text
        assert "第24话" in profile.text
        assert profile.entity_kind == EntityKind.EPISODE

    def test_no_sort(self):
        source = EpisodeProfileSource(subject_title="Test", name="OVA")
        profile = build_episode_profile(source, MODEL, DIMS)
        assert "集数" not in profile.text
        assert "OVA" in profile.text


class TestProfileVersioning:
    def test_all_entity_kinds_have_versions(self):
        for kind in (EntityKind.SUBJECT, EntityKind.EPISODE, EntityKind.PERSON, EntityKind.CHARACTER):
            assert kind in PROFILE_VERSIONS
            assert PROFILE_VERSIONS[kind].endswith("-v1")

    def test_versions_are_distinct(self):
        versions = list(PROFILE_VERSIONS.values())
        assert len(versions) == len(set(versions))
