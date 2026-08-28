from datetime import datetime, timezone

from jobs.importer.normalize import normalize_subject
from jobs.importer.repository import ImportRepository
from jobs.importer.storage import CoverResult


class _Result:
    def __init__(self, scalar_value=None, lastrowid=None):
        self._scalar_value = scalar_value
        self.lastrowid = lastrowid

    def scalar(self):
        return self._scalar_value


class _Session:
    def __init__(self, existing_id=None):
        self.existing_id = existing_id
        self.calls = []

    def execute(self, statement, values):
        sql = str(statement)
        self.calls.append((sql, values))
        if sql.startswith("SELECT id FROM subject"):
            return _Result(scalar_value=self.existing_id)
        return _Result(lastrowid=42)


def _normalized_subject():
    raw = {
        "id": 123,
        "type": 2,
        "nsfw": False,
        "name": "Test",
        "rating": {"score": 8.7, "rank": 321, "total": 456, "count": {}},
        "collection": {"wish": 11, "collect": 22, "doing": 33, "on_hold": 44, "dropped": 55},
    }
    return normalize_subject(raw, [])


def _cover():
    return CoverResult("cover.jpg", "source.jpg", None, "SOURCE_FALLBACK", datetime.now(timezone.utc))


def test_normalize_subject_preserves_score_rank_and_collected_total():
    subject = _normalized_subject()

    assert subject is not None
    assert subject.score == 8.7
    assert subject.rank == 321
    assert subject.collection_total == 22


def test_repository_updates_subject_metrics():
    session = _Session(existing_id=7)

    ImportRepository(session)._upsert_subject(_normalized_subject(), _cover())

    sql, values = session.calls[-1]
    assert "score=:score" in sql
    assert "`rank`=:rank" in sql
    assert "collection_total=:collection_total" in sql
    assert values["score"] == 8.7
    assert values["rank"] == 321
    assert values["collection_total"] == 22


def test_repository_inserts_subject_metrics():
    session = _Session()

    ImportRepository(session)._upsert_subject(_normalized_subject(), _cover())

    sql, values = session.calls[-1]
    assert "score" in sql
    assert "`rank`" in sql
    assert "collection_total" in sql
    assert values["score"] == 8.7
    assert values["rank"] == 321
    assert values["collection_total"] == 22
