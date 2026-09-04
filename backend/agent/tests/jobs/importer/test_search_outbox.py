"""Importer -> generic search_index_job outbox 契约测试。"""

from __future__ import annotations

from dataclasses import dataclass

from app.entities.enums import EntityKind
from app.rag.multi_profile import (
    CharacterProfileSource,
    PersonProfileSource,
    build_character_profile,
    build_person_profile,
)
from app.rag.schemas import SubjectProfileSource
from jobs.importer.normalize import CharacterSummary, PersonSummary, normalize_subject
from jobs.importer.repository import ImportBundle, ImportRepository
from jobs.importer.storage import CoverResult


@dataclass
class _Result:
    row: dict | None = None
    rows: list[dict] | None = None

    def mappings(self):
        return self

    def first(self):
        return self.row

    def all(self):
        return self.rows or []


class _Session:
    def __init__(self, existing: dict | None = None):
        self.existing = existing
        self.calls: list[tuple[str, dict]] = []

    def execute(self, statement, values=None):
        sql = str(statement)
        params = values or {}
        self.calls.append((sql, params))
        if "SELECT id, content_hash, status FROM search_index_job" in sql:
            return _Result(row=self.existing)
        return _Result()


class _Transaction:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class _BundleSession(_Session):
    def begin(self):
        return _Transaction()

    def execute(self, statement, values=None):
        sql = str(statement)
        if "FROM episode e JOIN subject s" in sql:
            self.calls.append((sql, values or {}))
            return _Result(
                rows=[
                    {
                        "id": 1001,
                        "bangumi_ep_id": 10001,
                        "subject_id": 101,
                        "sort": 1,
                        "name": "Episode 1",
                        "name_cn": "第一话",
                        "description": "episode summary",
                        "airdate": "2024-01-01",
                        "subject_title": "Test Anime",
                    }
                ]
            )
        return super().execute(statement, values)


def _profile():
    return build_person_profile(
        PersonProfileSource(name="导演", summary="简介"),
        "text-embedding-v4",
        1024,
    )


def test_search_outbox_insert_is_idempotent_and_keeps_profile_metadata():
    session = _Session()
    repo = ImportRepository(session)
    profile = _profile()

    assert repo._upsert_search_index_job(EntityKind.PERSON, 7, "v1", profile) == "PENDING"

    sql, values = next(call for call in session.calls if "INSERT INTO search_index_job" in call[0])
    assert "profile_version" in sql
    assert values["kind"] == "PERSON"
    assert values["entity_id"] == 7
    assert values["content_hash"] == profile.content_hash


def test_search_outbox_completed_same_hash_does_not_reset_task():
    profile = _profile()
    session = _Session({"id": 11, "content_hash": profile.content_hash, "status": "COMPLETED"})
    repo = ImportRepository(session)

    assert repo._upsert_search_index_job(EntityKind.PERSON, 7, "v1", profile) == "UNCHANGED"
    assert not any("INSERT INTO search_index_job" in sql for sql, _ in session.calls)
    assert not any("UPDATE search_index_job" in sql for sql, _ in session.calls)


def test_search_outbox_failed_same_hash_is_requeued():
    profile = _profile()
    session = _Session({"id": 11, "content_hash": profile.content_hash, "status": "FAILED"})
    repo = ImportRepository(session)

    assert repo._upsert_search_index_job(EntityKind.PERSON, 7, "v1", profile) == "PENDING"
    update = next(values for sql, values in session.calls if "UPDATE search_index_job" in sql)
    assert update["content_hash"] == profile.content_hash
    assert update["profile_version"] == profile.schema_version


def test_incomplete_entity_responses_publish_no_person_or_character_tasks():
    session = _Session()
    repo = ImportRepository(session)
    jobs: list[tuple[EntityKind, int]] = []
    repo._person_profile = lambda local_id, source: _profile()  # type: ignore[method-assign]
    repo._character_profile = lambda local_id, source: build_character_profile(  # type: ignore[method-assign]
        CharacterProfileSource(name=source.name), "text-embedding-v4", 1024
    )
    repo._upsert_search_index_job = lambda kind, entity_id, version, profile: jobs.append(  # type: ignore[method-assign]
        (kind, entity_id)
    )

    repo._enqueue_entity_search_jobs(
        1,
        "v1",
        persons=(PersonSummary(10, "P", "PERSON"),),
        characters=(CharacterSummary(20, "C", "CHARACTER"),),
        actor_summaries=(),
        person_ids={10: 100},
        character_ids={20: 200},
        persons_complete=False,
        characters_complete=False,
    )

    assert jobs == []
    assert session.calls == []


def test_write_bundle_publishes_legacy_and_generic_outboxes_for_complete_entities(monkeypatch):
    subject = normalize_subject(
        {
            "id": 1,
            "type": 2,
            "nsfw": False,
            "name": "Test Anime",
            "summary": "summary",
            "tags": [],
            "meta_tags": [],
            "infobox": [],
        },
        [{"id": 10, "name": "Director", "type": 1, "relation": "导演"}],
        [
            {
                "id": 20,
                "name": "Hero",
                "type": 1,
                "relation": "主角",
                "actors": [{"id": 30, "name": "Actor", "type": 1}],
            }
        ],
    )
    assert subject is not None
    session = _BundleSession()
    repo = ImportRepository(session)
    monkeypatch.setattr(repo, "_upsert_subject", lambda subject, cover: 101)
    monkeypatch.setattr(repo, "_upsert_aliases", lambda *args: None)
    monkeypatch.setattr(repo, "_replace_free_tags", lambda *args: None)
    monkeypatch.setattr(repo, "_upsert_meta_tags", lambda *args: None)
    monkeypatch.setattr(repo, "_upsert_persons", lambda people, import_record_id=None: {
        person.bangumi_id: person.bangumi_id + 100 for person in people
    })
    monkeypatch.setattr(repo, "_upsert_credits", lambda *args, **kwargs: None)
    monkeypatch.setattr(repo, "_upsert_subject_person_credits", lambda *args, **kwargs: None)
    monkeypatch.setattr(repo, "_upsert_characters", lambda chars, import_record_id=None: {
        character.bangumi_id: character.bangumi_id + 200 for character in chars
    })
    monkeypatch.setattr(repo, "_upsert_subject_characters", lambda *args: None)
    monkeypatch.setattr(repo, "_upsert_character_actors", lambda *args: None)
    monkeypatch.setattr(repo, "_replace_episodes", lambda *args: None)
    monkeypatch.setattr("jobs.importer.repository.upsert_relations", lambda *args: None)
    monkeypatch.setattr(repo, "_profile_source", lambda subject_id: SubjectProfileSource(title="Test Anime"))
    monkeypatch.setattr(repo, "_upsert_index_job", lambda *args: "PENDING")
    person_profile = _profile()
    character_profile = build_character_profile(
        CharacterProfileSource(name="Hero"), "text-embedding-v4", 1024
    )
    monkeypatch.setattr(repo, "_person_profile", lambda local_id, source: person_profile)
    monkeypatch.setattr(repo, "_character_profile", lambda local_id, source: character_profile)
    jobs: list[tuple[EntityKind, int, str]] = []
    monkeypatch.setattr(
        repo,
        "_upsert_search_index_job",
        lambda kind, entity_id, version, profile: jobs.append((kind, entity_id, profile.schema_version)) or "PENDING",
    )

    result = repo.write_bundle(
        ImportBundle(
            subject=subject,
            cover=CoverResult("", "", None, "MISSING", subject.source_fetched_at),
            episodes=({"id": 10001},),
            persons=subject.persons,
            characters=subject.characters,
        ),
        "v1",
    )

    assert result.subject_id == 101
    assert jobs == [
        (EntityKind.SUBJECT, 101, "subject-profile-v1"),
        (EntityKind.PERSON, 110, "person-profile-v1"),
        (EntityKind.PERSON, 130, "person-profile-v1"),
        (EntityKind.CHARACTER, 220, "character-profile-v1"),
        (EntityKind.EPISODE, 1001, "episode-profile-v1"),
    ]
