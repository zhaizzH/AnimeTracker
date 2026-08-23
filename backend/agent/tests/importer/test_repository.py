from contextlib import contextmanager
from datetime import datetime, timezone

import pytest

from importer.normalize import Alias, Credit, NormalizedSubject, Tag
from importer.storage import CoverResult


class Result:
    def __init__(self, scalar=None, lastrowid=None):
        self._scalar = scalar
        self.lastrowid = lastrowid

    def scalar(self):
        return self._scalar

    def mappings(self):
        return self

    def scalars(self):
        return self

    def one(self):
        return self._scalar

    def all(self):
        return self._scalar or []


class FakeSession:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.fail_table = None
        self.index_hash = None
        self.queries = []

    def fail_on(self, table):
        self.fail_table = table

    @contextmanager
    def begin(self):
        try:
            yield self
        except Exception:
            self.rollbacks += 1
            raise
        else:
            self.commits += 1

    def execute(self, statement, params=None):
        sql = str(statement)
        self.queries.append(sql)
        if self.fail_table and self.fail_table in sql:
            raise RuntimeError(f"forced {self.fail_table} failure")
        if "SELECT id FROM subject" in sql:
            return Result(7)
        if "SELECT content_hash" in sql:
            return Result(self.index_hash)
        if "SELECT s.name" in sql:
            return Result({
                "title": "测试番剧", "summary": "简介", "aliases": "别名", "meta_tags": "动画",
                "trusted_tags": "治愈", "credits": "导演：甲", "relations": "续集：续作",
            })
        if "SELECT current_tag.name" in sql:
            return Result(["治愈"])
        if "INSERT INTO rag_index_job" in sql:
            self.index_hash = params["content_hash"]
        return Result(lastrowid=7)


SUBJECT = NormalizedSubject(
    bangumi_id=42,
    name="测试番剧",
    name_cn="测试番剧",
    summary="简介",
    aliases=(Alias("别名", "中文名"),),
    meta_tags=("动画",),
    free_tags=(Tag("治愈", 100),),
    credits=(Credit(3, "甲", "导演"),),
    rating_total=5,
    rating_counts={"10": 5},
    collection_counts={"collect": 5},
    image_source_url="https://image.example/42.jpg",
    source_fetched_at=datetime.now(timezone.utc),
)
COVER = CoverResult("https://image.example/42.jpg", "https://image.example/42.jpg", None, "SOURCE_FALLBACK", datetime.now(timezone.utc))


@pytest.fixture
def session():
    return FakeSession()


@pytest.fixture
def repo(session):
    from importer.repository import ImportRepository

    return ImportRepository(session, embedding_model="text-embedding-v4", embedding_dimensions=1024, trusted_tag_min_count=1)


def bundle():
    from importer.repository import ImportBundle

    return ImportBundle(subject=SUBJECT, cover=COVER, episodes=(), relations=())


def test_bundle_rolls_back_when_child_write_fails(repo, session):
    session.fail_on("subject_credit")

    with pytest.raises(RuntimeError):
        repo.write_bundle(bundle(), "v1")

    assert session.commits == 0
    assert session.rollbacks == 1


def test_unchanged_profile_does_not_requeue_index(repo):
    first = repo.write_bundle(bundle(), "v1")
    second = repo.write_bundle(bundle(), "v1")

    assert first.index_status == "PENDING"
    assert second.index_status == "UNCHANGED"
    assert first.content_hash == second.content_hash


def test_checkpoint_is_saved_with_fixed_shape(repo, session):
    from importer.repository import ImportCheckpoint

    repo.save_checkpoint(9, ImportCheckpoint("sample", 2, 42, "abc"))

    query = next(sql for sql in session.queries if "checkpoint_json" in sql)
    assert "heartbeat_at" in query
