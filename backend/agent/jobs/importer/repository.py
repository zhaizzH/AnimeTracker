"""导入器的单条目事务仓储。"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy import text

from app.rag.profile import build_subject_profile
from app.rag.schemas import SubjectProfileSource
from jobs.importer.db import upsert_episodes, upsert_relations, upsert_tags
from jobs.importer.normalize import NormalizedSubject
from jobs.importer.storage import CoverResult


@dataclass(frozen=True)
class ImportBundle:
    subject: NormalizedSubject
    cover: CoverResult
    episodes: tuple[dict, ...] = ()
    relations: tuple[dict, ...] = ()


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
            self._upsert_aliases(subject_id, bundle.subject)
            self._upsert_meta_tags(subject_id, bundle.subject)
            upsert_tags(self._session, subject_id, [tag.__dict__ for tag in bundle.subject.free_tags])
            self._upsert_credits(subject_id, bundle.subject)
            upsert_episodes(self._session, subject_id, list(bundle.episodes))
            upsert_relations(self._session, subject_id, list(bundle.relations))
            profile = build_subject_profile(
                self._profile_source(subject_id), self._embedding_model, self._embedding_dimensions
            )
            status = self._upsert_index_job(subject_id, index_version, profile.content_hash)
        return ImportWriteResult(subject_id, profile.content_hash, status)

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
            "rating_total": subject.rating_total,
            "rating_count_json": json.dumps(subject.rating_counts),
            "collection_wish": subject.collection_counts.get("wish", 0),
            "collection_collect": subject.collection_counts.get("collect", 0),
            "collection_doing": subject.collection_counts.get("doing", 0),
            "collection_on_hold": subject.collection_counts.get("on_hold", 0),
            "collection_dropped": subject.collection_counts.get("dropped", 0),
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
                "INSERT INTO subject (bangumi_id, name, name_cn, summary, type, image, import_status, "
                "last_imported_at, created_at, updated_at, rating_total, rating_count_json, collection_wish, "
                "collection_collect, collection_doing, collection_on_hold, collection_dropped, image_source_url, "
                "image_storage_status, image_checked_at, source_fetched_at) VALUES "
                "(:bangumi_id, :name, :name_cn, :summary, 2, :image, 1, :now, :now, :now, :rating_total, "
                "CAST(:rating_count_json AS JSON), :collection_wish, :collection_collect, :collection_doing, "
                ":collection_on_hold, :collection_dropped, :image_source_url, :image_storage_status, "
                ":image_checked_at, :source_fetched_at)"
            ),
            values,
        )
        return int(result.lastrowid)

    def _upsert_aliases(self, subject_id: int, subject: NormalizedSubject) -> None:
        now = datetime.now()
        for alias in subject.aliases:
            self._session.execute(
                text(
                    "INSERT INTO subject_alias (subject_id, name, language, source, created_at, updated_at) "
                    "VALUES (:subject_id, :name, 'und', :source, :now, :now) "
                    "ON DUPLICATE KEY UPDATE source=:source, updated_at=:now"
                ),
                {"subject_id": subject_id, "name": alias.name, "source": alias.kind, "now": now},
            )

    def _upsert_meta_tags(self, subject_id: int, subject: NormalizedSubject) -> None:
        now = datetime.now()
        for name in subject.meta_tags:
            self._session.execute(
                text(
                    "INSERT INTO subject_meta_tag (subject_id, name, created_at) VALUES (:subject_id, :name, :now) "
                    "ON DUPLICATE KEY UPDATE name=:name"
                ),
                {"subject_id": subject_id, "name": name, "now": now},
            )

    def _upsert_credits(self, subject_id: int, subject: NormalizedSubject) -> None:
        now = datetime.now()
        for order, credit in enumerate(subject.credits):
            self._session.execute(
                text(
                    "INSERT INTO subject_credit (subject_id, bangumi_person_id, name, role, credit_type, sort_order, created_at, updated_at) "
                    "VALUES (:subject_id, :person_id, :name, :role, 'MAIN', :sort_order, :now, :now) "
                    "ON DUPLICATE KEY UPDATE bangumi_person_id=:person_id, credit_type='MAIN', "
                    "sort_order=:sort_order, updated_at=:now"
                ),
                {
                    "subject_id": subject_id,
                    "person_id": credit.person_id,
                    "name": credit.name,
                    "role": credit.role,
                    "sort_order": order,
                    "now": now,
                },
            )

    def _profile_source(self, subject_id: int) -> SubjectProfileSource:
        row = self._session.execute(
            text(
                "SELECT s.name AS title, s.summary, "
                "(SELECT GROUP_CONCAT(name ORDER BY name SEPARATOR '\\n') FROM subject_alias WHERE subject_id=s.id) AS aliases, "
                "(SELECT GROUP_CONCAT(name ORDER BY name SEPARATOR '\\n') FROM subject_meta_tag WHERE subject_id=s.id) AS meta_tags, "
                "(SELECT GROUP_CONCAT(CONCAT(role, '：', name) ORDER BY sort_order, name SEPARATOR '\\n') FROM subject_credit WHERE subject_id=s.id) AS credits, "
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
