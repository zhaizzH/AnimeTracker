"""多实体确定性 profile 构建。

为 SUBJECT/EPISODE/PERSON/CHARACTER 建立可重现的向量文本。
只向量化语义正文；评分、排名、收藏人数等数值仅作为 TAG/NUMERIC/SORTABLE 字段。

profile_version 规则：
- 每种实体类型有独立的 schema version
- 文本构建逻辑变更时必须递增版本号
- content_hash 包含 schema version + embedding 参数 + 文本，确保任何变更都产生新 hash
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from app.entities.enums import EntityKind


# 各实体类型的 profile schema 版本
PROFILE_VERSIONS: dict[EntityKind, str] = {
    EntityKind.SUBJECT: "subject-profile-v1",
    EntityKind.EPISODE: "episode-profile-v1",
    EntityKind.PERSON: "person-profile-v1",
    EntityKind.CHARACTER: "character-profile-v1",
}

_EMBEDDING_PROVIDER = "dashscope"


@dataclass(frozen=True)
class ProfileResult:
    """构建结果：向量文本 + 内容哈希 + schema 版本。"""

    text: str
    content_hash: str
    schema_version: str
    entity_kind: EntityKind


@dataclass(frozen=True)
class PersonProfileSource:
    """构建 Person profile 所需的资料。"""

    name: str
    person_type: str = "PERSON"
    aliases: tuple[str, ...] = ()
    summary: str = ""
    career: tuple[str, ...] = ()
    representative_works: tuple[str, ...] = ()


@dataclass(frozen=True)
class CharacterProfileSource:
    """构建 Character profile 所需的资料。"""

    name: str
    character_type: str = "CHARACTER"
    aliases: tuple[str, ...] = ()
    summary: str = ""
    appearances: tuple[str, ...] = ()
    voice_actors: tuple[str, ...] = ()


@dataclass(frozen=True)
class EpisodeProfileSource:
    """构建 Episode profile 所需的资料。"""

    subject_title: str
    sort: float | None = None
    name: str = ""
    name_cn: str = ""
    description: str = ""
    airdate: str = ""


def build_person_profile(
    source: PersonProfileSource,
    model: str,
    dimensions: int,
) -> ProfileResult:
    """构建 Person 的确定性向量文本。"""
    schema_version = PROFILE_VERSIONS[EntityKind.PERSON]
    text = "\n".join(
        filter(
            None,
            (
                f"姓名：{source.name}",
                f"类型：{_person_type_label(source.person_type)}",
                f"别名：{'、'.join(source.aliases)}" if source.aliases else "",
                f"简介：{source.summary}" if source.summary else "",
                f"职业：{'、'.join(source.career)}" if source.career else "",
                f"代表作品：{'、'.join(source.representative_works)}" if source.representative_works else "",
            ),
        )
    )
    return _make_result(text, schema_version, EntityKind.PERSON, model, dimensions)


def build_character_profile(
    source: CharacterProfileSource,
    model: str,
    dimensions: int,
) -> ProfileResult:
    """构建 Character 的确定性向量文本。"""
    schema_version = PROFILE_VERSIONS[EntityKind.CHARACTER]
    text = "\n".join(
        filter(
            None,
            (
                f"角色名：{source.name}",
                f"别名：{'、'.join(source.aliases)}" if source.aliases else "",
                f"简介：{source.summary}" if source.summary else "",
                f"登场作品：{'、'.join(source.appearances)}" if source.appearances else "",
                f"声优：{'、'.join(source.voice_actors)}" if source.voice_actors else "",
            ),
        )
    )
    return _make_result(text, schema_version, EntityKind.CHARACTER, model, dimensions)


def build_episode_profile(
    source: EpisodeProfileSource,
    model: str,
    dimensions: int,
) -> ProfileResult:
    """构建 Episode 的确定性向量文本。"""
    schema_version = PROFILE_VERSIONS[EntityKind.EPISODE]
    ep_label = f"第{source.sort}话" if source.sort is not None else ""
    text = "\n".join(
        filter(
            None,
            (
                f"作品：{source.subject_title}",
                f"集数：{ep_label}" if ep_label else "",
                f"标题：{source.name_cn or source.name}" if (source.name_cn or source.name) else "",
                f"简介：{source.description}" if source.description else "",
                f"播出日期：{source.airdate}" if source.airdate else "",
            ),
        )
    )
    return _make_result(text, schema_version, EntityKind.EPISODE, model, dimensions)


def _make_result(
    text: str,
    schema_version: str,
    entity_kind: EntityKind,
    model: str,
    dimensions: int,
) -> ProfileResult:
    envelope = {
        "schema": schema_version,
        "provider": _EMBEDDING_PROVIDER,
        "model": model,
        "dimensions": dimensions,
        "text": text,
    }
    content_hash = hashlib.sha256(
        json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return ProfileResult(
        text=text,
        content_hash=content_hash,
        schema_version=schema_version,
        entity_kind=entity_kind,
    )


def _person_type_label(person_type: str) -> str:
    labels = {"PERSON": "个人", "COMPANY": "公司", "GROUP": "组合"}
    return labels.get(person_type, person_type)
