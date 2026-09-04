"""多实体数据加载器。

从 MySQL 加载 Person/Character/Episode 资料，用于构建多实体 profile。
与 IndexJobRepository.load_subject() 对称，支持 search_index_job 的所有实体类型。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from sqlalchemy import text

from app.entities.enums import EntityKind


@dataclass(frozen=True)
class PersonEntity:
    """加载用于 Person profile 构建的完整资料。"""

    person_id: int
    name: str
    person_type: str
    summary: str
    aliases: tuple[str, ...]
    career: tuple[str, ...]
    representative_works: tuple[str, ...]


@dataclass(frozen=True)
class CharacterEntity:
    """加载用于 Character profile 构建的完整资料。"""

    character_id: int
    name: str
    character_type: str
    summary: str
    aliases: tuple[str, ...]
    appearances: tuple[str, ...]
    voice_actors: tuple[str, ...]


@dataclass(frozen=True)
class EpisodeEntity:
    """加载用于 Episode profile 构建的完整资料。"""

    episode_id: int
    subject_id: int
    subject_title: str
    sort: float | None
    name: str
    name_cn: str
    description: str
    airdate: str


class MultiEntityLoader:
    """从 MySQL 加载多实体数据供索引 profile 构建使用。"""

    def __init__(self, session, *, trusted_tag_min_count: int | None = None):
        self._session = session

    def load_person(self, entity_id: int) -> PersonEntity | None:
        """加载 Person 实体资料（含别名、职业、代表作品）。"""
        with self._session.begin():
            row = self._session.execute(
                text(
                    "SELECT id, name, person_type, summary, career_json "
                    "FROM person WHERE id=:id AND source_active=1"
                ),
                {"id": entity_id},
            ).mappings().first()
            if row is None:
                return None

            aliases = self._session.execute(
                text(
                    "SELECT name FROM person_alias WHERE person_id=:id AND source_active=1 "
                    "ORDER BY name"
                ),
                {"id": entity_id},
            ).scalars().all()

            works = self._session.execute(
                text(
                    "SELECT s.name FROM subject_person_credit spc "
                    "JOIN subject s ON s.id=spc.subject_id "
                    "WHERE spc.person_id=:id AND spc.source_active=1 AND s.type=2 AND s.nsfw=0 "
                    "ORDER BY s.score DESC LIMIT 5"
                ),
                {"id": entity_id},
            ).scalars().all()

        career = _parse_career(row["career_json"])
        return PersonEntity(
            person_id=int(row["id"]),
            name=str(row["name"] or ""),
            person_type=str(row["person_type"] or "PERSON"),
            summary=str(row["summary"] or ""),
            aliases=tuple(str(a) for a in aliases),
            career=career,
            representative_works=tuple(str(w) for w in works),
        )

    def load_character(self, entity_id: int) -> CharacterEntity | None:
        """加载 Character 实体资料（含别名、登场作品、声优）。"""
        with self._session.begin():
            row = self._session.execute(
                text(
                    "SELECT id, name, character_type, summary "
                    "FROM character WHERE id=:id AND source_active=1"
                ),
                {"id": entity_id},
            ).mappings().first()
            if row is None:
                return None

            aliases = self._session.execute(
                text(
                    "SELECT name FROM character_alias WHERE character_id=:id AND source_active=1 "
                    "ORDER BY name"
                ),
                {"id": entity_id},
            ).scalars().all()

            appearances = self._session.execute(
                text(
                    "SELECT s.name FROM subject_character sc "
                    "JOIN subject s ON s.id=sc.subject_id "
                    "WHERE sc.character_id=:id AND sc.source_active=1 AND s.type=2 AND s.nsfw=0 "
                    "ORDER BY s.score DESC LIMIT 5"
                ),
                {"id": entity_id},
            ).scalars().all()

            actors = self._session.execute(
                text(
                    "SELECT p.name FROM character_actor ca "
                    "JOIN person p ON p.id=ca.person_id "
                    "WHERE ca.character_id=:id AND ca.source_active=1 AND ca.actor_relation='VA' "
                    "ORDER BY ca.sort_order LIMIT 3"
                ),
                {"id": entity_id},
            ).scalars().all()

        return CharacterEntity(
            character_id=int(row["id"]),
            name=str(row["name"] or ""),
            character_type=str(row["character_type"] or "CHARACTER"),
            summary=str(row["summary"] or ""),
            aliases=tuple(str(a) for a in aliases),
            appearances=tuple(str(a) for a in appearances),
            voice_actors=tuple(str(v) for v in actors),
        )

    def load_episode(self, entity_id: int) -> EpisodeEntity | None:
        """加载 Episode 实体资料（含关联 Subject 标题）。"""
        with self._session.begin():
            row = self._session.execute(
                text(
                    "SELECT e.id, e.subject_id, e.sort, e.name, e.name_cn, e.description, e.airdate, "
                    "s.name AS subject_title "
                    "FROM episode e JOIN subject s ON s.id=e.subject_id "
                    "WHERE e.id=:id AND s.type=2 AND s.nsfw=0"
                ),
                {"id": entity_id},
            ).mappings().first()
            if row is None:
                return None

        return EpisodeEntity(
            episode_id=int(row["id"]),
            subject_id=int(row["subject_id"]),
            subject_title=str(row["subject_title"] or ""),
            sort=float(row["sort"]) if row["sort"] is not None else None,
            name=str(row["name"] or ""),
            name_cn=str(row["name_cn"] or ""),
            description=str(row["description"] or ""),
            airdate=str(row["airdate"] or ""),
        )


def _parse_career(career_json: Any) -> tuple[str, ...]:
    """解析 career_json 字段（JSON 数组字符串或 None）。"""
    if not career_json:
        return ()
    import json

    try:
        parsed = json.loads(str(career_json))
        if isinstance(parsed, list):
            return tuple(str(item) for item in parsed if item)
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return ()
