"""Subject endpoint relation 摘要的规范化契约。"""

from datetime import datetime

import pytest

from jobs.importer.main import _validate_summary_items
from jobs.importer.client import BangumiClient
from jobs.importer.normalize import normalize_subject
from jobs.importer.repository import ImportRepository


class _RecordingSession:
    def __init__(self):
        self.calls = []

    def execute(self, statement, values=None):
        self.calls.append((str(statement), values or {}))


def _recording_repo():
    session = _RecordingSession()
    return ImportRepository(session), session


def _subject():
    return {
        "id": 1,
        "type": 2,
        "nsfw": False,
        "name": "Test Anime",
        "tags": [],
        "meta_tags": [],
        "infobox": [],
    }


def test_normalize_keeps_all_person_roles_and_source_type():
    result = normalize_subject(
        _subject(),
        [
            {"id": 10, "name": "Director", "type": 1, "relation": "导演"},
            {"id": 11, "name": "Publisher", "type": 2, "relation": "发行"},
        ],
    )

    assert result is not None
    assert [(item.person_id, item.role, item.person_type) for item in result.credits] == [
        (10, "导演", "PERSON"),
        (11, "发行", "ORGANIZATION"),
    ]
    assert [(item.bangumi_id, item.person_type) for item in result.persons] == [
        (10, "PERSON"),
        (11, "COMPANY"),
    ]


def test_normalize_keeps_character_actor_summary_and_deduplicates_ids():
    result = normalize_subject(
        _subject(),
        [],
        [
            {
                "id": 20,
                "name": "Hero",
                "type": 1,
                "summary": "hero",
                "relation": "主角",
                "actors": [
                    {"id": 30, "name": "Actor", "type": 1},
                    {"id": 30, "name": "Actor duplicate", "type": 1},
                ],
            },
            {"id": 20, "name": "Hero duplicate", "type": 1, "relation": "配角"},
        ],
    )

    assert result is not None
    assert len(result.characters) == 1
    assert result.characters[0].relation == "MAIN"
    assert [(actor.bangumi_id, actor.name) for actor in result.characters[0].actors] == [(30, "Actor")]


def test_repository_writes_normalized_credit_and_character_edges():
    result = normalize_subject(
        _subject(),
        [{"id": 10, "name": "Director", "type": 1, "relation": "导演"}],
        [{
            "id": 20,
            "name": "Hero",
            "type": 1,
            "relation": "主角",
            "actors": [{"id": 30, "name": "Actor", "type": 1}],
        }],
    )
    assert result is not None
    repo, session = _recording_repo()
    repo._upsert_subject_person_credits(7, result, {10: 100})
    repo._upsert_subject_characters(7, result.characters, {20: 200})
    repo._upsert_character_actors(7, result.characters, {20: 200}, {30: 300})

    sql = "\n".join(statement for statement, _ in session.calls)
    assert "subject_person_credit" in sql
    assert "subject_character" in sql
    assert "character_actor" in sql
    inserts = [values for statement, values in session.calls if "INSERT INTO subject_person_credit" in statement]
    assert inserts[0]["role"] == "导演"
    assert inserts[0]["relation"] == "MAIN"


def test_summary_validation_rejects_incomplete_relation_fields():
    with pytest.raises(ValueError, match="persons response"):
        _validate_summary_items([{"id": 10, "name": "Director"}], "persons")

    with pytest.raises(ValueError, match="characters response"):
        _validate_summary_items([{"id": 20, "name": "Hero", "actors": []}], "characters")


def test_summary_validation_accepts_documented_bare_related_person():
    _validate_summary_items(
        [{"id": 10, "name": "Director", "type": 1, "relation": "导演"}],
        "persons",
    )


def test_episode_pagination_rejects_short_success_response():
    client = BangumiClient(base_url="http://example.invalid")
    pages = iter([{"data": [], "total": 1}])
    client.get_episodes = lambda *args, **kwargs: next(pages)

    with pytest.raises(ValueError, match="ended before total"):
        client.get_all_episodes(1)


def test_detail_enqueue_does_not_reset_claimed_or_running_job():
    repo, session = _recording_repo()

    repo._enqueue_detail_job("PERSON", 100, 10, datetime.now())

    sql = "\n".join(statement for statement, _ in session.calls)
    assert "'CLAIMED'" in sql
    assert "'RUNNING'" in sql
