"""Person/Character 详情回填 worker。

低速批次消费 entity_detail_job，尊重上游限速预算，
避免与 Subject importer 争用同一锁。

详情失败只影响该实体的丰富字段，不删除已有摘要与关系。
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.entities.enums import EntityKind
from jobs.backfill.repository import DetailJob, EntityDetailJobRepository, compute_source_hash
from jobs.importer.client import BangumiClient

logger = logging.getLogger(__name__)

# 回填默认限速：每次请求间隔（秒），避免与 importer 争用
DEFAULT_REQUEST_DELAY = 1.5


class BackfillWorker:
    """渐进回填 Person/Character 详情。"""

    def __init__(
        self,
        client: BangumiClient,
        repo: EntityDetailJobRepository,
        session,
        *,
        batch_size: int = 5,
        request_delay: float = DEFAULT_REQUEST_DELAY,
        max_batches: int | None = None,
    ):
        self._client = client
        self._repo = repo
        self._session = session
        self._batch_size = batch_size
        self._request_delay = request_delay
        self._max_batches = max_batches

    def run(self) -> dict[str, int]:
        """执行回填循环，返回统计。"""
        stats = {"processed": 0, "completed": 0, "failed": 0, "abandoned": 0}
        batches_run = 0

        while True:
            if self._max_batches is not None and batches_run >= self._max_batches:
                logger.info("达到最大批次数 %d，停止回填", self._max_batches)
                break

            jobs = self._repo.claim_batch(self._batch_size)
            if not jobs:
                logger.info("无待处理任务，回填结束")
                break

            batches_run += 1
            for job in jobs:
                stats["processed"] += 1
                try:
                    self._process_job(job)
                    self._session.commit()
                    stats["completed"] += 1
                except Exception as e:
                    self._session.rollback()
                    logger.warning("回填 %s#%d 失败: %s", job.entity_kind, job.source_id, e)
                    self._repo.mark_failed(
                        job.id,
                        error_code=type(e).__name__,
                        error_message=str(e),
                    )
                    self._session.commit()
                    stats["failed"] += 1
                time.sleep(self._request_delay)

        return stats

    def _process_job(self, job: DetailJob) -> None:
        """处理单条回填任务。"""
        if job.entity_kind == EntityKind.PERSON:
            self._backfill_person(job)
        elif job.entity_kind == EntityKind.CHARACTER:
            self._backfill_character(job)
        else:
            raise ValueError(f"不支持的 entity_kind: {job.entity_kind}")

    def _backfill_person(self, job: DetailJob) -> None:
        """获取 Person 详情并幂等写入。"""
        from sqlalchemy import text

        raw = self._client.get_person(job.source_id)
        source_hash = compute_source_hash(raw)

        # 检查 hash 是否变化（避免无意义写入）
        existing = self._session.execute(
            text("SELECT source_hash FROM person WHERE id=:id"),
            {"id": job.entity_id},
        ).scalar()
        if existing == source_hash:
            # 数据未变化，直接标记完成
            self._repo.mark_completed(job.id, source_hash=source_hash)
            return

        # 规范化并写入详情
        infobox = raw.get("infobox") or []
        # PersonDetail exposes career as a first-class field.  Keep that payload
        # when present; infobox parsing remains a compatibility fallback for
        # older snapshots.
        career = raw.get("career") or _extract_career(infobox)
        summary = raw.get("summary") or ""
        images = raw.get("images") or {}
        image_url = images.get("large")

        now = _now()
        self._session.execute(
            text(
                "UPDATE person SET summary=:summary, career_json=CAST(:career AS JSON), "
                "infobox_json=CAST(:infobox AS JSON), image_source_url=:image_source_url, "
                "detail_status='COMPLETE', source_hash=:source_hash, source_fetched_at=:now, "
                "updated_at=:now WHERE id=:id"
            ),
            {
                "id": job.entity_id,
                "summary": summary,
                "career": _json_dumps(career),
                "infobox": _json_dumps(infobox),
                "image_source_url": image_url,
                "source_hash": source_hash,
                "now": now,
            },
        )
        # 写入别名
        aliases = _extract_aliases(infobox)
        self._replace_person_aliases(job.entity_id, aliases)

        # Persist a replay-safe checkpoint before completing the job.  Detail
        # endpoints are single responses today, but keeping the source/hash
        # envelope makes pause/resume and future paginated payloads idempotent.
        self._repo.save_checkpoint(
            job.id,
            {"sourceId": job.source_id, "sourceHash": source_hash, "entityKind": "PERSON"},
        )
        self._repo.mark_completed(job.id, source_hash=source_hash)

    def _backfill_character(self, job: DetailJob) -> None:
        """获取 Character 详情并幂等写入。"""
        from sqlalchemy import text

        raw = self._client.get_character(job.source_id)
        source_hash = compute_source_hash(raw)

        existing = self._session.execute(
            text("SELECT source_hash FROM character WHERE id=:id"),
            {"id": job.entity_id},
        ).scalar()
        if existing == source_hash:
            self._repo.mark_completed(job.id, source_hash=source_hash)
            return

        infobox = raw.get("infobox") or []
        summary = raw.get("summary") or ""
        images = raw.get("images") or {}
        image_url = images.get("large")

        now = _now()
        self._session.execute(
            text(
                "UPDATE `character` SET summary=:summary, "
                "infobox_json=CAST(:infobox AS JSON), image_source_url=:image_source_url, "
                "detail_status='COMPLETE', source_hash=:source_hash, source_fetched_at=:now, "
                "updated_at=:now WHERE id=:id"
            ),
            {
                "id": job.entity_id,
                "summary": summary,
                "infobox": _json_dumps(infobox),
                "image_source_url": image_url,
                "source_hash": source_hash,
                "now": now,
            },
        )
        aliases = _extract_aliases(infobox)
        self._replace_character_aliases(job.entity_id, aliases)

        self._repo.save_checkpoint(
            job.id,
            {"sourceId": job.source_id, "sourceHash": source_hash, "entityKind": "CHARACTER"},
        )
        self._repo.mark_completed(job.id, source_hash=source_hash)

    def _replace_person_aliases(self, person_id: int, aliases: list[str]) -> None:
        """replace-set 写入 person_alias。"""
        from sqlalchemy import bindparam, text

        now = _now()
        for name in aliases:
            self._session.execute(
                text(
                    "INSERT INTO person_alias (person_id, name, language, source, source_active, created_at, updated_at) "
                    "VALUES (:person_id, :name, 'und', 'infobox', 1, :now, :now) "
                    "ON DUPLICATE KEY UPDATE source_active=1, updated_at=:now"
                ),
                {"person_id": person_id, "name": name, "now": now},
            )
        deactivate = text(
            "UPDATE person_alias SET source_active=0, updated_at=:now "
            "WHERE person_id=:person_id AND source_active=1 AND name NOT IN :names"
        ).bindparams(bindparam("names", expanding=True))
        self._session.execute(deactivate, {"person_id": person_id, "now": now, "names": aliases})

    def _replace_character_aliases(self, character_id: int, aliases: list[str]) -> None:
        """replace-set 写入 character_alias。"""
        from sqlalchemy import bindparam, text

        now = _now()
        for name in aliases:
            self._session.execute(
                text(
                    "INSERT INTO character_alias (character_id, name, language, source, source_active, created_at, updated_at) "
                    "VALUES (:character_id, :name, 'und', 'infobox', 1, :now, :now) "
                    "ON DUPLICATE KEY UPDATE source_active=1, updated_at=:now"
                ),
                {"character_id": character_id, "name": name, "now": now},
            )
        deactivate = text(
            "UPDATE character_alias SET source_active=0, updated_at=:now "
            "WHERE character_id=:character_id AND source_active=1 AND name NOT IN :names"
        ).bindparams(bindparam("names", expanding=True))
        self._session.execute(deactivate, {"character_id": character_id, "now": now, "names": aliases})


def _extract_career(infobox: list[dict]) -> list[str]:
    """从 infobox 提取职业信息。"""
    careers = []
    for field in infobox:
        if field.get("key") in ("职业", "career", "occupation"):
            value = field.get("value")
            if isinstance(value, list):
                careers.extend(str(v) for v in value)
            elif value:
                careers.append(str(value))
    return careers


def _extract_aliases(infobox: list[dict]) -> list[str]:
    """从 infobox 提取别名。"""
    alias_keys = ("别名", "中文名", "英文名", "日文名", "罗马音", "alias", "name_en", "name_cn", "name_jp")
    aliases = []
    seen: set[str] = set()
    for field in infobox:
        key = field.get("key", "")
        if key not in alias_keys:
            continue
        value = field.get("value")
        parts: list[str] = []
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    parts.append(str(item.get("v", item.get("value", ""))))
                else:
                    parts.append(str(item))
        elif isinstance(value, str):
            parts = [p.strip() for p in value.split("/")]
        for part in parts:
            part = part.strip()
            if part and part not in seen:
                seen.add(part)
                aliases.append(part)
    return aliases


def _json_dumps(value: Any) -> str:
    import json
    return json.dumps(value, ensure_ascii=False, default=str)


def _now():
    from datetime import datetime
    return datetime.now()
