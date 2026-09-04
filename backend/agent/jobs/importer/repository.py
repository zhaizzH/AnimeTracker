"""导入器的单条目事务仓储。"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy import bindparam, text

from app.entities.enums import EntityKind
from app.rag.multi_profile import (
    CharacterProfileSource,
    EpisodeProfileSource,
    PersonProfileSource,
    ProfileResult,
    build_character_profile,
    build_episode_profile,
    build_person_profile,
)
from app.rag.profile import build_subject_profile
from app.rag.schemas import SubjectProfileSource
from jobs.importer.db import upsert_episodes, upsert_relations, upsert_tags
from jobs.importer.normalize import MAIN_CREDIT_ROLES, CharacterSummary, NormalizedSubject, PersonSummary
from jobs.importer.storage import CoverResult


@dataclass(frozen=True)
class ImportBundle:
    subject: NormalizedSubject
    cover: CoverResult
    episodes: tuple[dict, ...] = ()
    relations: tuple[dict, ...] = ()
    persons: tuple[PersonSummary, ...] = ()
    characters: tuple[CharacterSummary, ...] = ()
    # A collection is replaced only after its upstream response completed.  The
    # defaults preserve the old ImportBundle API for callers that only import a
    # subject and episodes.
    aliases_complete: bool = True
    tags_complete: bool = True
    meta_tags_complete: bool = True
    persons_complete: bool = True
    characters_complete: bool = True
    episodes_complete: bool = True
    relations_complete: bool = True
    import_record_id: int | None = None


@dataclass(frozen=True)
class ImportWriteResult:
    subject_id: int
    content_hash: str
    index_status: Literal["PENDING", "UNCHANGED"]


@dataclass(frozen=True)
class ImportCheckpoint:
    mode: str
    offset: int
    last_subject_id: int | None
    scanned_ids_sha256: str

    def as_json(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "offset": self.offset,
            "lastSubjectId": self.last_subject_id,
            "scannedIdsSha256": self.scanned_ids_sha256,
        }

    @classmethod
    def from_json(cls, value: dict[str, object]) -> "ImportCheckpoint":
        expected = {"mode", "offset", "lastSubjectId", "scannedIdsSha256"}
        if set(value) != expected or not isinstance(value["mode"], str) or not isinstance(value["offset"], int):
            raise ValueError("导入断点格式无效")
        last_subject_id = value["lastSubjectId"]
        if last_subject_id is not None and not isinstance(last_subject_id, int):
            raise ValueError("导入断点格式无效")
        if not isinstance(value["scannedIdsSha256"], str):
            raise ValueError("导入断点格式无效")
        return cls(value["mode"], value["offset"], last_subject_id, value["scannedIdsSha256"])


class ImportRepository:
    """保持导入数据与向量任务一致的最小写入边界。"""

    def __init__(
        self,
        session,
        *,
        embedding_model: str = "text-embedding-v4",
        embedding_dimensions: int = 1024,
        trusted_tag_min_count: int | None = None,
    ):
        self._session = session
        self._embedding_model = embedding_model
        self._embedding_dimensions = embedding_dimensions
        self._trusted_tag_min_count = trusted_tag_min_count if trusted_tag_min_count is not None else int(
            os.getenv("RAG_TRUSTED_TAG_MIN_COUNT", "100")
        )

    def write_bundle(self, bundle: ImportBundle, index_version: str) -> ImportWriteResult:
        with self._session.begin():
            subject_id = self._upsert_subject(bundle.subject, bundle.cover)
            if bundle.aliases_complete:
                self._upsert_aliases(subject_id, bundle.subject)
            if bundle.tags_complete:
                self._replace_free_tags(subject_id, bundle.subject)
            if bundle.meta_tags_complete:
                self._upsert_meta_tags(subject_id, bundle.subject)

            persons = bundle.persons or bundle.subject.persons
            characters = bundle.characters or bundle.subject.characters
            person_ids = self._upsert_persons(persons, bundle.import_record_id)
            actor_summaries = _unique_actor_summaries(characters)
            for source_id, local_id in self._upsert_persons(actor_summaries, bundle.import_record_id).items():
                person_ids.setdefault(source_id, local_id)
            # Credits from the persons endpoint are retained in full, including
            # roles that are not part of the legacy six-role UI subset.
            if bundle.persons_complete:
                self._upsert_credits(subject_id, bundle.subject, person_ids=person_ids)
                self._upsert_subject_person_credits(subject_id, bundle.subject, person_ids)

            character_ids = self._upsert_characters(characters, bundle.import_record_id)
            if bundle.characters_complete:
                self._upsert_subject_characters(subject_id, characters, character_ids)
                self._upsert_character_actors(subject_id, characters, character_ids, person_ids)

            if bundle.episodes_complete:
                self._replace_episodes(subject_id, list(bundle.episodes))
            if bundle.relations_complete:
                # upsert_relations returns False when a related subject is not
                # present locally; it intentionally leaves the old set intact.
                upsert_relations(self._session, subject_id, list(bundle.relations))
            profile = build_subject_profile(
                self._profile_source(subject_id), self._embedding_model, self._embedding_dimensions
            )
            status = self._upsert_index_job(subject_id, index_version, profile.content_hash)
            # Keep the legacy Subject queue for the online index, while also
            # publishing one deterministic task per searchable entity.  The
            # helper uses the current transaction directly (rather than the
            # standalone SearchIndexJobRepository, which starts its own
            # transaction and cannot be nested here).
            self._upsert_search_index_job(
                EntityKind.SUBJECT,
                subject_id,
                index_version,
                profile,
            )
            if bundle.persons_complete or bundle.characters_complete:
                self._enqueue_entity_search_jobs(
                    subject_id,
                    index_version,
                    persons=persons,
                    characters=characters,
                    actor_summaries=actor_summaries,
                    person_ids=person_ids,
                    character_ids=character_ids,
                    persons_complete=bundle.persons_complete,
                    characters_complete=bundle.characters_complete,
                )
            if bundle.episodes_complete:
                self._enqueue_episode_search_jobs(
                    subject_id,
                    index_version,
                    tuple(bundle.episodes),
                )
        return ImportWriteResult(subject_id, profile.content_hash, status)

    def _enqueue_entity_search_jobs(
        self,
        subject_id: int,
        index_version: str,
        *,
        persons: tuple[PersonSummary, ...],
        characters: tuple[CharacterSummary, ...],
        actor_summaries: tuple[PersonSummary, ...],
        person_ids: dict[int, int],
        character_ids: dict[int, int],
        persons_complete: bool,
        characters_complete: bool,
    ) -> None:
        """Publish Person/Character tasks only for complete upstream sets.

        Actor summaries are valid Person inputs when the Character endpoint was
        complete, even if the separate Subject persons endpoint was not.  The
        profile's relational fields are read after edge writes, so a retry by
        the indexer computes the same text/hash from MySQL.
        """
        person_sources: dict[int, PersonSummary] = {}
        if persons_complete:
            person_sources.update({person.bangumi_id: person for person in persons})
        if characters_complete:
            for actor in actor_summaries:
                person_sources.setdefault(actor.bangumi_id, actor)

        for source_id, source in person_sources.items():
            local_id = person_ids.get(source_id)
            if local_id is None:
                continue
            profile = self._person_profile(local_id, source)
            self._upsert_search_index_job(EntityKind.PERSON, local_id, index_version, profile)

        if not characters_complete:
            return
        for character in characters:
            local_id = character_ids.get(character.bangumi_id)
            if local_id is None:
                continue
            profile = self._character_profile(local_id, character)
            self._upsert_search_index_job(EntityKind.CHARACTER, local_id, index_version, profile)

    def _enqueue_episode_search_jobs(
        self,
        subject_id: int,
        index_version: str,
        episodes: tuple[dict, ...],
    ) -> None:
        """Publish only episode rows belonging to the completed response."""
        if not episodes:
            return
        bangumi_ids = tuple(
            sorted({int(episode["id"]) for episode in episodes if episode.get("id")})
        )
        if not bangumi_ids:
            return
        rows = self._session.execute(
            text(
                "SELECT e.id, e.bangumi_ep_id, e.subject_id, e.sort, e.name, e.name_cn, "
                "e.description, e.airdate, s.name AS subject_title "
                "FROM episode e JOIN subject s ON s.id=e.subject_id "
                "WHERE e.subject_id=:subject_id AND e.bangumi_ep_id IN :bangumi_ids"
            ).bindparams(bindparam("bangumi_ids", expanding=True)),
            {"subject_id": subject_id, "bangumi_ids": bangumi_ids},
        ).mappings().all()
        for row in rows:
            profile = build_episode_profile(
                EpisodeProfileSource(
                    subject_title=str(row["subject_title"] or ""),
                    sort=float(row["sort"]) if row["sort"] is not None else None,
                    name=str(row["name"] or ""),
                    name_cn=str(row["name_cn"] or ""),
                    description=str(row["description"] or ""),
                    airdate=str(row["airdate"] or ""),
                ),
                self._embedding_model,
                self._embedding_dimensions,
            )
            self._upsert_search_index_job(
                EntityKind.EPISODE,
                int(row["id"]),
                index_version,
                profile,
            )

    def _person_profile(self, local_id: int, source: PersonSummary) -> ProfileResult:
        person_row = self._session.execute(
            text("SELECT name, person_type, summary, career_json FROM person WHERE id=:person_id AND source_active=1"),
            {"person_id": local_id},
        ).mappings().first()
        aliases = self._session.execute(
            text("SELECT name FROM person_alias WHERE person_id=:person_id AND source_active=1 ORDER BY name"),
            {"person_id": local_id},
        ).scalars().all()
        works = self._session.execute(
            text(
                "SELECT s.name FROM subject_person_credit spc "
                "JOIN subject s ON s.id=spc.subject_id "
                "WHERE spc.person_id=:person_id AND spc.source_active=1 "
                "AND s.type=2 AND s.nsfw=0 ORDER BY s.score DESC LIMIT 5"
            ),
            {"person_id": local_id},
        ).scalars().all()
        career = _json_values(person_row["career_json"]) if person_row else tuple(str(value) for value in source.career)
        return build_person_profile(
            PersonProfileSource(
                name=str(person_row["name"] or source.name) if person_row else source.name,
                person_type=str(person_row["person_type"] or source.person_type) if person_row else source.person_type,
                aliases=tuple(str(value) for value in aliases),
                summary=str(person_row["summary"] or "") if person_row else source.summary,
                career=career,
                representative_works=tuple(str(value) for value in works),
            ),
            self._embedding_model,
            self._embedding_dimensions,
        )

    def _character_profile(self, local_id: int, source: CharacterSummary) -> ProfileResult:
        character_row = self._session.execute(
            text("SELECT name, character_type, summary FROM `character` WHERE id=:character_id AND source_active=1"),
            {"character_id": local_id},
        ).mappings().first()
        aliases = self._session.execute(
            text("SELECT name FROM character_alias WHERE character_id=:character_id AND source_active=1 ORDER BY name"),
            {"character_id": local_id},
        ).scalars().all()
        appearances = self._session.execute(
            text(
                "SELECT s.name FROM subject_character sc JOIN subject s ON s.id=sc.subject_id "
                "WHERE sc.character_id=:character_id AND sc.source_active=1 "
                "AND s.type=2 AND s.nsfw=0 ORDER BY s.score DESC LIMIT 5"
            ),
            {"character_id": local_id},
        ).scalars().all()
        voice_actors = self._session.execute(
            text(
                "SELECT p.name FROM character_actor ca JOIN person p ON p.id=ca.person_id "
                "WHERE ca.character_id=:character_id AND ca.source_active=1 "
                "AND ca.actor_relation='VA' ORDER BY ca.sort_order LIMIT 3"
            ),
            {"character_id": local_id},
        ).scalars().all()
        return build_character_profile(
            CharacterProfileSource(
                name=str(character_row["name"] or source.name) if character_row else source.name,
                character_type=str(character_row["character_type"] or source.character_type) if character_row else source.character_type,
                aliases=tuple(str(value) for value in aliases),
                summary=str(character_row["summary"] or "") if character_row else source.summary,
                appearances=tuple(str(value) for value in appearances),
                voice_actors=tuple(str(value) for value in voice_actors),
            ),
            self._embedding_model,
            self._embedding_dimensions,
        )

    def _upsert_persons(
        self, persons: tuple[PersonSummary, ...], import_record_id: int | None = None
    ) -> dict[int, int]:
        """Upsert summary entities and enqueue detail work without blocking Subject."""
        now = datetime.now()
        ids: dict[int, int] = {}
        for person in persons:
            existing = self._session.execute(
                text("SELECT id FROM person WHERE bangumi_person_id=:bangumi_id"),
                {"bangumi_id": person.bangumi_id},
            ).scalar()
            values = {
                "bangumi_id": person.bangumi_id,
                "person_type": person.person_type,
                "name": person.name,
                "summary": person.summary or None,
                "career": json.dumps(list(person.career), ensure_ascii=False, default=str),
                "image_source_url": person.image_source_url,
                "last_seen_import_id": import_record_id,
                "now": now,
            }
            if existing:
                local_id = int(existing)
                self._session.execute(
                    text(
                        "UPDATE person SET person_type=:person_type, name=:name, "
                        "summary=COALESCE(:summary, summary), career_json=CASE WHEN :career='[]' THEN career_json ELSE CAST(:career AS JSON) END, "
                        "image_source_url=COALESCE(:image_source_url, image_source_url), "
                        "last_seen_import_id=COALESCE(:last_seen_import_id, last_seen_import_id), "
                        "source_fetched_at=:now, source_active=1, detail_status=CASE WHEN detail_status='FAILED' THEN 'PENDING' ELSE detail_status END, updated_at=:now WHERE id=:id"
                    ),
                    values | {"id": local_id},
                )
            else:
                result = self._session.execute(
                    text(
                        "INSERT INTO person (bangumi_person_id, person_type, name, summary, career_json, "
                        "image_source_url, detail_status, source_fetched_at, source_active, last_seen_import_id, created_at, updated_at) "
                        "VALUES (:bangumi_id, :person_type, :name, :summary, CAST(:career AS JSON), :image_source_url, "
                        "'SUMMARY_ONLY', :now, 1, :last_seen_import_id, :now, :now)"
                    ),
                    values,
                )
                local_id = int(result.lastrowid)
            ids[person.bangumi_id] = local_id
            self._enqueue_detail_job("PERSON", local_id, person.bangumi_id, now)
        return ids

    def _upsert_characters(
        self, characters: tuple[CharacterSummary, ...], import_record_id: int | None = None
    ) -> dict[int, int]:
        """Upsert character summaries and their independent detail jobs."""
        now = datetime.now()
        ids: dict[int, int] = {}
        for character in characters:
            existing = self._session.execute(
                text("SELECT id FROM `character` WHERE bangumi_character_id=:bangumi_id"),
                {"bangumi_id": character.bangumi_id},
            ).scalar()
            values = {
                "bangumi_id": character.bangumi_id,
                "character_type": character.character_type,
                "name": character.name,
                "summary": character.summary or None,
                "image_source_url": character.image_source_url,
                "last_seen_import_id": import_record_id,
                "now": now,
            }
            if existing:
                local_id = int(existing)
                self._session.execute(
                    text(
                        "UPDATE `character` SET character_type=:character_type, name=:name, "
                        "summary=COALESCE(:summary, summary), image_source_url=COALESCE(:image_source_url, image_source_url), "
                        "last_seen_import_id=COALESCE(:last_seen_import_id, last_seen_import_id), source_fetched_at=:now, source_active=1, "
                        "detail_status=CASE WHEN detail_status='FAILED' THEN 'PENDING' ELSE detail_status END, updated_at=:now WHERE id=:id"
                    ),
                    values | {"id": local_id},
                )
            else:
                result = self._session.execute(
                    text(
                        "INSERT INTO `character` (bangumi_character_id, character_type, name, summary, "
                        "image_source_url, detail_status, source_fetched_at, source_active, last_seen_import_id, created_at, updated_at) "
                        "VALUES (:bangumi_id, :character_type, :name, :summary, :image_source_url, 'SUMMARY_ONLY', :now, 1, "
                        ":last_seen_import_id, :now, :now)"
                    ),
                    values,
                )
                local_id = int(result.lastrowid)
            ids[character.bangumi_id] = local_id
            self._enqueue_detail_job("CHARACTER", local_id, character.bangumi_id, now)
        return ids

    def _enqueue_detail_job(self, entity_kind: str, entity_id: int, source_id: int, now: datetime) -> None:
        self._session.execute(
            text(
                "INSERT INTO entity_detail_job (entity_kind, entity_id, source_id, status, attempts, created_at, updated_at) "
                "VALUES (:kind, :entity_id, :source_id, 'PENDING', 0, :now, :now) "
                "ON DUPLICATE KEY UPDATE source_id=:source_id, "
                "status=CASE WHEN status IN ('COMPLETED', 'ABANDONED', 'CLAIMED', 'RUNNING') "
                "THEN status ELSE 'PENDING' END, updated_at=:now"
            ),
            {"kind": entity_kind, "entity_id": entity_id, "source_id": source_id, "now": now},
        )

    def _replace_free_tags(self, subject_id: int, subject: NormalizedSubject) -> None:
        """Replace tags only after a complete Subject response."""
        upsert_tags(self._session, subject_id, [tag.__dict__ for tag in subject.free_tags])
        names = [tag.name for tag in subject.free_tags]
        if names:
            self._session.execute(
                text("DELETE FROM subject_tag WHERE subject_id=:subject_id AND name NOT IN :names").bindparams(
                    bindparam("names", expanding=True)
                ),
                {"subject_id": subject_id, "names": names},
            )
        else:
            self._session.execute(
                text("DELETE FROM subject_tag WHERE subject_id=:subject_id"),
                {"subject_id": subject_id},
            )

    def _replace_episodes(self, subject_id: int, episodes: list[dict]) -> None:
        """Replace episodes after all pages have been read successfully."""
        upsert_episodes(self._session, subject_id, episodes)
        ids = [episode.get("id") for episode in episodes if episode.get("id")]
        if ids:
            self._session.execute(
                text("DELETE FROM episode WHERE subject_id=:subject_id AND bangumi_ep_id NOT IN :ids").bindparams(
                    bindparam("ids", expanding=True)
                ),
                {"subject_id": subject_id, "ids": ids},
            )
        else:
            self._session.execute(text("DELETE FROM episode WHERE subject_id=:subject_id"), {"subject_id": subject_id})

    def _upsert_subject_person_credits(
        self, subject_id: int, subject: NormalizedSubject, person_ids: dict[int, int]
    ) -> None:
        now = datetime.now()
        # Mark all old edges stale first; reactivating the exact natural keys below
        # makes removal and duplicate handling deterministic.
        self._session.execute(
            text("UPDATE subject_person_credit SET source_active=0, updated_at=:now WHERE subject_id=:subject_id"),
            {"subject_id": subject_id, "now": now},
        )
        for order, credit in enumerate(subject.credits):
            local_id = person_ids.get(credit.person_id)
            if local_id is None:
                continue
            relation = "MAIN" if credit.role in MAIN_CREDIT_ROLES else "SUB"
            self._session.execute(
                text(
                    "INSERT INTO subject_person_credit (subject_id, person_id, role, relation, sort_order, source_active, created_at, updated_at) "
                    "VALUES (:subject_id, :person_id, :role, :relation, :sort_order, 1, :now, :now) "
                    "ON DUPLICATE KEY UPDATE relation=:relation, sort_order=:sort_order, source_active=1, updated_at=:now"
                ),
                {"subject_id": subject_id, "person_id": local_id, "role": credit.role, "relation": relation, "sort_order": order, "now": now},
            )

    def _upsert_subject_characters(
        self, subject_id: int, characters: tuple[CharacterSummary, ...], character_ids: dict[int, int]
    ) -> None:
        now = datetime.now()
        self._session.execute(
            text("UPDATE subject_character SET source_active=0, updated_at=:now WHERE subject_id=:subject_id"),
            {"subject_id": subject_id, "now": now},
        )
        for order, character in enumerate(characters):
            local_id = character_ids.get(character.bangumi_id)
            if local_id is None:
                continue
            self._session.execute(
                text(
                    "INSERT INTO subject_character (subject_id, character_id, relation, sort_order, source_active, created_at, updated_at) "
                    "VALUES (:subject_id, :character_id, :relation, :sort_order, 1, :now, :now) "
                    "ON DUPLICATE KEY UPDATE relation=:relation, sort_order=:sort_order, source_active=1, updated_at=:now"
                ),
                {"subject_id": subject_id, "character_id": local_id, "relation": character.relation, "sort_order": order, "now": now},
            )

    def _upsert_character_actors(
        self,
        subject_id: int,
        characters: tuple[CharacterSummary, ...],
        character_ids: dict[int, int],
        person_ids: dict[int, int],
    ) -> None:
        now = datetime.now()
        self._session.execute(
            text("UPDATE character_actor SET source_active=0, updated_at=:now WHERE subject_id=:subject_id"),
            {"subject_id": subject_id, "now": now},
        )
        for character in characters:
            character_id = character_ids.get(character.bangumi_id)
            if character_id is None:
                continue
            for order, actor in enumerate(character.actors):
                actor_id = person_ids.get(actor.bangumi_id)
                if actor_id is None:
                    continue
                self._session.execute(
                    text(
                        "INSERT INTO character_actor (subject_id, character_id, person_id, actor_relation, sort_order, source_active, created_at, updated_at) "
                        "VALUES (:subject_id, :character_id, :person_id, 'VA', :sort_order, 1, :now, :now) "
                        "ON DUPLICATE KEY UPDATE actor_relation='VA', sort_order=:sort_order, source_active=1, updated_at=:now"
                    ),
                    {"subject_id": subject_id, "character_id": character_id, "person_id": actor_id, "sort_order": order, "now": now},
                )

    def save_checkpoint(self, record_id: int, checkpoint: ImportCheckpoint) -> None:
        self._session.execute(
            text(
                "UPDATE import_record SET checkpoint_json = CAST(:checkpoint AS JSON), "
                "heartbeat_at = :now WHERE id = :id"
            ),
            {"id": record_id, "checkpoint": json.dumps(checkpoint.as_json()), "now": datetime.now()},
        )

    def _upsert_subject(self, subject: NormalizedSubject, cover: CoverResult) -> int:
        now = datetime.now()
        existing = self._session.execute(
            text("SELECT id FROM subject WHERE bangumi_id = :bangumi_id"),
            {"bangumi_id": subject.bangumi_id},
        ).scalar()
        values = {
            "bangumi_id": subject.bangumi_id,
            "name": subject.name,
            "name_cn": subject.name_cn,
            "summary": subject.summary,
            "air_date": subject.air_date,
            "air_weekday": subject.air_weekday,
            "eps": subject.eps,
            "volumes": subject.volumes,
            "score": subject.score,
            "rank": subject.rank,
            "rating_total": subject.rating_total,
            "rating_count_json": json.dumps(subject.rating_counts),
            "collection_wish": subject.collection_counts.get("wish", 0),
            "collection_collect": subject.collection_counts.get("collect", 0),
            "collection_doing": subject.collection_counts.get("doing", 0),
            "collection_on_hold": subject.collection_counts.get("on_hold", 0),
            "collection_dropped": subject.collection_counts.get("dropped", 0),
            "collection_total": subject.collection_total,
            "image": cover.display_url,
            "image_source_url": cover.source_url or subject.image_source_url,
            "image_storage_status": cover.status,
            "image_checked_at": cover.checked_at.replace(tzinfo=None),
            "source_fetched_at": subject.source_fetched_at.replace(tzinfo=None),
            "now": now,
        }
        if existing:
            self._session.execute(
                text(
                    "UPDATE subject SET name=:name, name_cn=:name_cn, summary=:summary, "
                    "air_date=:air_date, air_weekday=:air_weekday, eps=:eps, volumes=:volumes, "
                    "score=:score, `rank`=:rank, collection_total=:collection_total, "
                    "rating_total=:rating_total, rating_count_json=CAST(:rating_count_json AS JSON), "
                    "collection_wish=:collection_wish, collection_collect=:collection_collect, "
                    "collection_doing=:collection_doing, collection_on_hold=:collection_on_hold, "
                    "collection_dropped=:collection_dropped, image=:image, image_source_url=:image_source_url, "
                    "image_storage_status=:image_storage_status, image_checked_at=:image_checked_at, "
                    "source_fetched_at=:source_fetched_at, import_status=1, last_imported_at=:now, "
                    "updated_at=:now WHERE id=:id"
                ),
                values | {"id": existing},
            )
            return int(existing)
        result = self._session.execute(
            text(
                "INSERT INTO subject (bangumi_id, name, name_cn, summary, type, air_date, air_weekday, eps, volumes, image, import_status, "
                "last_imported_at, created_at, updated_at, score, `rank`, collection_total, rating_total, rating_count_json, collection_wish, "
                "collection_collect, collection_doing, collection_on_hold, collection_dropped, image_source_url, "
                "image_storage_status, image_checked_at, source_fetched_at) VALUES "
                "(:bangumi_id, :name, :name_cn, :summary, 2, :air_date, :air_weekday, :eps, :volumes, :image, 1, :now, :now, :now, :score, :rank, :collection_total, :rating_total, "
                "CAST(:rating_count_json AS JSON), :collection_wish, :collection_collect, :collection_doing, "
                ":collection_on_hold, :collection_dropped, :image_source_url, :image_storage_status, "
                ":image_checked_at, :source_fetched_at)"
            ),
            values,
        )
        return int(result.lastrowid)

    def _upsert_aliases(self, subject_id: int, subject: NormalizedSubject) -> None:
        now = datetime.now()
        active_names: list[str] = []
        for alias in subject.aliases:
            active_names.append(alias.name)
            self._session.execute(
                text(
                    "INSERT INTO subject_alias (subject_id, name, language, source, source_active, created_at, updated_at) "
                    "VALUES (:subject_id, :name, 'und', :source, 1, :now, :now) "
                    "ON DUPLICATE KEY UPDATE source=:source, source_active=1, updated_at=:now"
                ),
                {"subject_id": subject_id, "name": alias.name, "source": alias.kind, "now": now},
            )
        # replace-set: 失效不在新集合中的旧别名
        deactivate_sql = text(
            "UPDATE subject_alias SET source_active=0, updated_at=:now "
            "WHERE subject_id=:subject_id AND source_active=1 AND name NOT IN :active_names"
        ).bindparams(bindparam("active_names", expanding=True))
        self._session.execute(
            deactivate_sql,
            {"subject_id": subject_id, "now": now, "active_names": active_names or ["__never_match__"]},
        )

    def _upsert_meta_tags(self, subject_id: int, subject: NormalizedSubject) -> None:
        now = datetime.now()
        active_names: list[str] = []
        for name in subject.meta_tags:
            active_names.append(name)
            self._session.execute(
                text(
                    "INSERT INTO subject_meta_tag (subject_id, name, source_active, created_at) "
                    "VALUES (:subject_id, :name, 1, :now) "
                    "ON DUPLICATE KEY UPDATE source_active=1"
                ),
                {"subject_id": subject_id, "name": name, "now": now},
            )
        # replace-set: 失效不在新集合中的旧标签
        deactivate_sql = text(
            "UPDATE subject_meta_tag SET source_active=0 "
            "WHERE subject_id=:subject_id AND source_active=1 AND name NOT IN :active_names"
        ).bindparams(bindparam("active_names", expanding=True))
        self._session.execute(
            deactivate_sql,
            {"subject_id": subject_id, "active_names": active_names or ["__never_match__"]},
        )

    def _upsert_credits(
        self,
        subject_id: int,
        subject: NormalizedSubject,
        *,
        person_ids: dict[int, int] | None = None,
    ) -> None:
        now = datetime.now()
        # Mark the complete old set stale first.  This avoids using name-only
        # predicates, which could incorrectly keep a removed role for a person
        # who still has another role.
        self._session.execute(
            text("UPDATE subject_credit SET source_active=0, updated_at=:now WHERE subject_id=:subject_id"),
            {"subject_id": subject_id, "now": now},
        )
        for order, credit in enumerate(subject.credits):
            self._session.execute(
                text(
                    "INSERT INTO subject_credit (subject_id, bangumi_person_id, name, role, credit_type, sort_order, source_active, created_at, updated_at) "
                    "VALUES (:subject_id, :person_id, :name, :role, :credit_type, :sort_order, 1, :now, :now) "
                    "ON DUPLICATE KEY UPDATE bangumi_person_id=:person_id, credit_type=:credit_type, "
                    "sort_order=:sort_order, source_active=1, updated_at=:now"
                ),
                {
                    "subject_id": subject_id,
                    "person_id": credit.person_id,
                    "name": credit.name,
                    "role": credit.role,
                    "credit_type": credit.person_type,
                    "sort_order": order,
                    "now": now,
                },
            )

    def _profile_source(self, subject_id: int) -> SubjectProfileSource:
        row = self._session.execute(
            text(
                "SELECT s.name AS title, s.summary, "
                "(SELECT GROUP_CONCAT(name ORDER BY name SEPARATOR '\\n') FROM subject_alias WHERE subject_id=s.id AND source_active=1) AS aliases, "
                "(SELECT GROUP_CONCAT(name ORDER BY name SEPARATOR '\\n') FROM subject_meta_tag WHERE subject_id=s.id AND source_active=1) AS meta_tags, "
                "(SELECT GROUP_CONCAT(CONCAT(role, '：', name) ORDER BY sort_order, name SEPARATOR '\\n') FROM subject_credit WHERE subject_id=s.id AND source_active=1) AS credits, "
                "(SELECT GROUP_CONCAT(CONCAT(sr.relation, '：', related.name) ORDER BY related.name SEPARATOR '\\n') "
                " FROM subject_relation sr JOIN subject related ON related.id=sr.related_subject_id WHERE sr.subject_id=s.id) AS relations "
                "FROM subject s WHERE s.id=:subject_id"
            ),
            {"subject_id": subject_id},
        ).mappings().one()
        trusted = self._session.execute(
            text(
                "SELECT current_tag.name FROM subject_tag current_tag JOIN "
                "(SELECT name, COUNT(DISTINCT subject_id) AS coverage, SUM(count) AS total_count FROM subject_tag GROUP BY name) stats "
                "ON stats.name=current_tag.name WHERE current_tag.subject_id=:subject_id "
                "AND CHAR_LENGTH(current_tag.name)<=24 AND stats.coverage>=3 AND stats.total_count>=:min_count "
                "ORDER BY current_tag.name"
            ),
            {"subject_id": subject_id, "min_count": self._trusted_tag_min_count},
        ).scalars().all()
        return SubjectProfileSource(
            title=row["title"],
            summary=row["summary"] or "",
            aliases=_split_values(row["aliases"]),
            meta_tags=_split_values(row["meta_tags"]),
            trusted_tags=tuple(trusted),
            credits=_split_values(row["credits"]),
            relations=_split_values(row["relations"]),
        )

    def _upsert_search_index_job(
        self,
        entity_kind: EntityKind,
        entity_id: int,
        index_version: str,
        profile: ProfileResult,
    ) -> Literal["PENDING", "UNCHANGED"]:
        """Write one idempotent generic index task in the caller's transaction."""
        if entity_id < 1:
            raise ValueError("entity_id 必须是正整数")
        if not index_version:
            raise ValueError("index_version 不能为空")
        if len(profile.content_hash) != 64:
            raise ValueError("profile content_hash 无效")
        now = datetime.now()
        kind = entity_kind.value if isinstance(entity_kind, EntityKind) else str(entity_kind)
        existing = self._session.execute(
            text(
                "SELECT id, content_hash, status FROM search_index_job "
                "WHERE entity_kind=:kind AND entity_id=:entity_id AND index_version=:version"
            ),
            {"kind": kind, "entity_id": entity_id, "version": index_version},
        ).mappings().first()
        if existing is not None:
            same_hash = str(existing["content_hash"]) == profile.content_hash
            if same_hash and str(existing["status"]) in ("COMPLETED", "PENDING", "CLAIMED"):
                return "UNCHANGED"
            self._session.execute(
                text(
                    "UPDATE search_index_job SET content_hash=:content_hash, profile_version=:profile_version, "
                    "embedding_provider='dashscope', embedding_model=:model, embedding_dimensions=:dimensions, "
                    "status='PENDING', attempts=0, last_error_code=NULL, last_error_message=NULL, "
                    "next_retry_at=NULL, claimed_at=NULL, indexed_at=NULL, updated_at=:now WHERE id=:id"
                ),
                {
                    "id": int(existing["id"]),
                    "content_hash": profile.content_hash,
                    "profile_version": profile.schema_version,
                    "model": self._embedding_model,
                    "dimensions": self._embedding_dimensions,
                    "now": now,
                },
            )
            return "PENDING"

        self._session.execute(
            text(
                "INSERT INTO search_index_job "
                "(entity_kind, entity_id, index_version, profile_version, content_hash, embedding_provider, "
                "embedding_model, embedding_dimensions, status, attempts, max_attempts, created_at, updated_at) "
                "VALUES (:kind, :entity_id, :version, :profile_version, :content_hash, 'dashscope', :model, "
                ":dimensions, 'PENDING', 0, 5, :now, :now)"
            ),
            {
                "kind": kind,
                "entity_id": entity_id,
                "version": index_version,
                "profile_version": profile.schema_version,
                "content_hash": profile.content_hash,
                "model": self._embedding_model,
                "dimensions": self._embedding_dimensions,
                "now": now,
            },
        )
        return "PENDING"

    def _upsert_index_job(self, subject_id: int, index_version: str, content_hash: str) -> Literal["PENDING", "UNCHANGED"]:
        existing = self._session.execute(
            text("SELECT content_hash FROM rag_index_job WHERE subject_id=:subject_id AND index_version=:index_version"),
            {"subject_id": subject_id, "index_version": index_version},
        ).scalar()
        if existing == content_hash:
            return "UNCHANGED"
        self._session.execute(
            text(
                "INSERT INTO rag_index_job (subject_id, index_version, content_hash, embedding_provider, embedding_model, "
                "embedding_dimensions, status, attempts, created_at, updated_at) VALUES "
                "(:subject_id, :index_version, :content_hash, 'dashscope', :model, :dimensions, 'PENDING', 0, :now, :now) "
                "ON DUPLICATE KEY UPDATE content_hash=:content_hash, embedding_provider='dashscope', "
                "embedding_model=:model, embedding_dimensions=:dimensions, status='PENDING', attempts=0, "
                "last_error_code=NULL, last_error_message=NULL, next_retry_at=NULL, indexed_at=NULL, updated_at=:now"
            ),
            {
                "subject_id": subject_id,
                "index_version": index_version,
                "content_hash": content_hash,
                "model": self._embedding_model,
                "dimensions": self._embedding_dimensions,
                "now": datetime.now(),
            },
        )
        return "PENDING"


def _split_values(value: str | None) -> tuple[str, ...]:
    return tuple(item for item in (value or "").split("\n") if item)


def _json_values(value: object) -> tuple[str, ...]:
    """Read a JSON list without allowing malformed detail data to break import."""
    if not value:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value if item)
    try:
        parsed = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return ()
    if not isinstance(parsed, list):
        return ()
    return tuple(str(item) for item in parsed if item)


def _unique_actor_summaries(characters: tuple[CharacterSummary, ...]) -> tuple[PersonSummary, ...]:
    """Flatten actor summaries while preserving source order and deduplicating IDs."""
    result: list[PersonSummary] = []
    seen: set[int] = set()
    for character in characters:
        for actor in character.actors:
            if actor.bangumi_id not in seen:
                seen.add(actor.bangumi_id)
                result.append(actor)
    return tuple(result)
