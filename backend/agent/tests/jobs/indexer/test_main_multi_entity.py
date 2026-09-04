"""生产 indexer 入口的多实体消费回归测试。"""

from __future__ import annotations

from datetime import datetime

from app.entities.enums import EntityKind
from app.rag.multi_profile import (
    CharacterProfileSource,
    EpisodeProfileSource,
    PersonProfileSource,
    build_character_profile,
    build_episode_profile,
    build_person_profile,
)
from app.rag.profile import build_subject_profile
from app.rag.schemas import SubjectProfileSource
from jobs.indexer.entity_index import EntityIndexDocument, RedisEntityIndex
from jobs.indexer.entity_loader import CharacterEntity, EpisodeEntity, PersonEntity
from jobs.indexer.main import run_search_batch
from jobs.indexer.repository import IndexSubject
from jobs.indexer.search_repository import ClaimedJob


NOW = datetime(2026, 9, 4, 12, 0, 0)
MODEL = "text-embedding-v4"


def _job(kind: EntityKind, entity_id: int, content_hash: str, number: int) -> ClaimedJob:
    return ClaimedJob(
        id=number,
        entity_kind=kind,
        entity_id=entity_id,
        index_version="v-test",
        profile_version="v1",
        content_hash=content_hash,
        embedding_provider="dashscope",
        embedding_model=MODEL,
        embedding_dimensions=1024,
        attempts=1,
        status="CLAIMED",
        claimed_at=NOW,
    )


class _Repo:
    def __init__(self, jobs=(), tombstones=()):
        self.jobs = list(jobs)
        self.tombstones = list(tombstones)
        self.completed = []
        self.failed = []
        self.enqueued = []

    def tombstone_batch(self, index_version, limit):
        result, self.tombstones = self.tombstones[:limit], self.tombstones[limit:]
        return result

    def claim_batch(self, limit, *, index_version):
        result, self.jobs = self.jobs[:limit], self.jobs[limit:]
        return result

    def mark_completed(self, job_id, *, claimed_at=None):
        self.completed.append((job_id, claimed_at))
        return True

    def mark_failed(self, job_id, **kwargs):
        self.failed.append((job_id, kwargs))
        return True

    def enqueue(self, *args, **kwargs):
        self.enqueued.append((args, kwargs))
        return "PENDING"


class _Loader:
    def __init__(self, person=None, character=None, episode=None):
        self.person = person
        self.character = character
        self.episode = episode

    def load_person(self, entity_id):
        return self.person

    def load_character(self, entity_id):
        return self.character

    def load_episode(self, entity_id):
        return self.episode


class _LegacyRepository:
    def __init__(self, subject):
        self.subject = subject

    def load_subject(self, job):
        return self.subject


class _RedisIndex:
    def __init__(self):
        self.ensure_calls = []
        self.writes = []
        self.deletes = []

    def ensure_version(self, index_version):
        self.ensure_calls.append(index_version)
        return f"idx:rag:entity:{index_version}"

    def write(self, document):
        self.writes.append(document)

    def delete(self, index_version, entity_kind, entity_id):
        self.deletes.append((index_version, entity_kind, entity_id))


class _Embedding:
    def __init__(self, error=None):
        self.error = error
        self.texts = []

    def embed_documents(self, texts):
        self.texts.extend(texts)
        if self.error:
            raise self.error
        return [[0.0] * 1024 for _ in texts]


def _subject_and_hash():
    subject = IndexSubject(
        subject_id=100,
        title="测试动画",
        summary="摘要",
        aliases=("Test Anime",),
        meta_tags=("科幻",),
        trusted_tags=(),
        credits=("导演：某人",),
        relations=(),
        year=2026,
        quarter=1,
        score=8.0,
        rating_total=10,
        collection_total=20,
        air_status="finished",
        type=2,
        nsfw=False,
    )
    profile = build_subject_profile(
        SubjectProfileSource(
            title=subject.title,
            summary=subject.summary,
            aliases=subject.aliases,
            meta_tags=subject.meta_tags,
            trusted_tags=subject.trusted_tags,
            credits=subject.credits,
            relations=subject.relations,
        ),
        MODEL,
        1024,
    )
    return subject, profile.content_hash


def test_run_search_batch_consumes_all_entity_kinds():
    subject, subject_hash = _subject_and_hash()
    person = PersonEntity(1, "某导演", "PERSON", "人物", (), (), ("测试动画",))
    character = CharacterEntity(2, "主角", "CHARACTER", "角色", (), ("测试动画",), ("某声优",))
    episode = EpisodeEntity(3, 100, "测试动画", 1.0, "Episode 1", "第一话", "开场", "2026-01-01")
    person_hash = build_person_profile(
        PersonProfileSource(
            name=person.name,
            person_type=person.person_type,
            summary=person.summary,
            representative_works=person.representative_works,
        ),
        MODEL,
        1024,
    ).content_hash
    character_hash = build_character_profile(
        CharacterProfileSource(
            name=character.name,
            character_type=character.character_type,
            summary=character.summary,
            appearances=character.appearances,
            voice_actors=character.voice_actors,
        ),
        MODEL,
        1024,
    ).content_hash
    episode_hash = build_episode_profile(
        EpisodeProfileSource(
            subject_title=episode.subject_title,
            sort=episode.sort,
            name=episode.name,
            name_cn=episode.name_cn,
            description=episode.description,
            airdate=episode.airdate,
        ),
        MODEL,
        1024,
    ).content_hash
    jobs = [
        _job(EntityKind.SUBJECT, 100, subject_hash, 1),
        _job(EntityKind.PERSON, 1, person_hash, 2),
        _job(EntityKind.CHARACTER, 2, character_hash, 3),
        _job(EntityKind.EPISODE, 3, episode_hash, 4),
    ]
    repo = _Repo(jobs=jobs)
    redis_index = _RedisIndex()
    result = run_search_batch(
        limit=10,
        index_version="v-test",
        repository=repo,
        entity_loader=_Loader(person=person, character=character, episode=episode),
        legacy_repository=_LegacyRepository(subject),
        embedding_client=_Embedding(),
        redis_index=redis_index,
    )

    assert result.claimed == 4
    assert result.indexed == 4
    assert result.failed == 0
    assert [document.entity_kind for document in redis_index.writes] == [
        EntityKind.SUBJECT,
        EntityKind.PERSON,
        EntityKind.CHARACTER,
        EntityKind.EPISODE,
    ]
    assert len(repo.completed) == 4
    assert redis_index.ensure_calls == ["v-test"]


def test_run_search_batch_deletes_tombstone_without_embedding():
    repo = _Repo(tombstones=[_job(EntityKind.CHARACTER, 2, "", 9)])
    redis_index = _RedisIndex()
    embedding = _Embedding()
    result = run_search_batch(
        limit=1,
        index_version="v-test",
        repository=repo,
        entity_loader=_Loader(),
        legacy_repository=_LegacyRepository(None),
        embedding_client=embedding,
        redis_index=redis_index,
    )

    assert result.claimed == 1
    assert result.indexed == 1
    assert not embedding.texts
    assert redis_index.deletes == [("v-test", EntityKind.CHARACTER, 2)]
    assert repo.completed[0][0] == 9


def test_run_search_batch_reschedules_profile_hash_drift():
    person = PersonEntity(1, "某导演", "PERSON", "人物", (), (), ())
    repo = _Repo(jobs=[_job(EntityKind.PERSON, 1, "stale-hash", 2)])
    embedding = _Embedding()
    result = run_search_batch(
        limit=1,
        index_version="v-test",
        repository=repo,
        entity_loader=_Loader(person=person),
        legacy_repository=_LegacyRepository(None),
        embedding_client=embedding,
        redis_index=_RedisIndex(),
    )

    assert result.claimed == 1
    assert result.retried == 1
    assert not embedding.texts
    args, kwargs = repo.enqueued[0]
    assert args[:3] == (EntityKind.PERSON, 1, "v-test")
    assert len(args[3]) == 64
    assert kwargs["profile_version"] == "person-profile-v1"


def test_run_search_batch_marks_embedding_failure_for_retry():
    person = PersonEntity(1, "某导演", "PERSON", "人物", (), (), ())
    profile_hash = build_person_profile(PersonProfileSource(name=person.name, summary=person.summary), MODEL, 1024).content_hash
    repo = _Repo(jobs=[_job(EntityKind.PERSON, 1, profile_hash, 2)])
    result = run_search_batch(
        limit=1,
        index_version="v-test",
        repository=repo,
        entity_loader=_Loader(person=person),
        legacy_repository=_LegacyRepository(None),
        embedding_client=_Embedding(RuntimeError("embedding temporarily unavailable")),
        redis_index=_RedisIndex(),
    )

    assert result.retried == 1
    assert result.failed == 0
    assert repo.failed[0][1]["error_code"] == "REDIS_UNAVAILABLE"


def test_redis_entity_index_writes_versioned_hash_and_deletes():
    class Redis:
        def __init__(self):
            self.commands = []
            self.hashes = {}
            self.deleted = []

        def execute_command(self, *args):
            self.commands.append(args)
            return "OK"

        def hset(self, key, *, mapping):
            self.hashes[key] = mapping

        def delete(self, key):
            self.deleted.append(key)

    redis = Redis()
    index = RedisEntityIndex(redis)
    profile = build_person_profile(PersonProfileSource(name="某人"), MODEL, 1024)
    index.ensure_version("v-test")
    index.write(EntityIndexDocument(
        entity_kind=EntityKind.PERSON,
        entity_id=1,
        index_version="v-test",
        profile=profile,
        vector=[0.0] * 1024,
        name="某人",
    ))
    index.delete("v-test", EntityKind.PERSON, 1)

    assert redis.commands[0][0:2] == ("FT.CREATE", "idx:rag:entity:v-test")
    assert redis.hashes["rag:entity:v-test:PERSON:1"]["content_hash"] == profile.content_hash
    assert redis.deleted == ["rag:entity:v-test:PERSON:1"]
