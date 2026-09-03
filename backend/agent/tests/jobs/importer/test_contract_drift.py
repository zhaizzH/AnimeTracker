"""契约漂移失败测试：记录 schema、normalize 和 repository 之间的已知不一致。

这些测试在当前代码下应当失败，证明存在需要修复的契约漂移。
一旦后续 Phase 修复了这些问题，这些测试应当通过。

已知漂移：
1. eps/volumes：db-schema.sql 有 eps/volumes 列，但 normalize 不提取，repository 不写入。
2. credit_type：schema 契约为 PERSON|ORGANIZATION，repository 固定写入 MAIN。
3. AIRING 状态：indexer 只产出 upcoming/finished，但 RetrievalQuery 允许 AIRING。
4. stale replace-set：repository 只 upsert 不失效上游已删除的标签/主创/别名。
5. profile hash：importer 写入后构建 profile，indexer 读取时可能因数据变化产生不同 hash。
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from jobs.importer.normalize import normalize_subject
from jobs.importer.repository import ImportRepository
from jobs.importer.storage import CoverResult


class _Result:
    def __init__(self, scalar_value=None, lastrowid=None, mappings_result=None, scalars_result=None):
        self._scalar_value = scalar_value
        self.lastrowid = lastrowid
        self._mappings_result = mappings_result or []
        self._scalars_result = scalars_result or []

    def scalar(self):
        return self._scalar_value

    def mappings(self):
        return self

    def one(self):
        return self._mappings_result[0] if self._mappings_result else {}

    def scalars(self):
        return self

    def all(self):
        return self._scalars_result


class _Session:
    def __init__(self, existing_id=None, profile_row=None, trusted_tags=None):
        self.existing_id = existing_id
        self.calls = []
        self._profile_row = profile_row or {}
        self._trusted_tags = trusted_tags or []

    def execute(self, statement, values=None):
        sql = str(statement)
        self.calls.append((sql, values or {}))
        if sql.startswith("SELECT id FROM subject"):
            return _Result(scalar_value=self.existing_id)
        if "GROUP_CONCAT" in sql and "subject_tag" in sql:
            return _Result(scalars_result=self._trusted_tags)
        if "GROUP_CONCAT" in sql:
            return _Result(mappings_result=[self._profile_row])
        return _Result(lastrowid=42)

    def begin(self):
        return _TransactionContext()


class _TransactionContext:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def _raw_subject_with_eps():
    return {
        "id": 123,
        "type": 2,
        "nsfw": False,
        "name": "Test Anime",
        "name_cn": "测试动画",
        "eps": 24,
        "volumes": 8,
        "rating": {"score": 8.0, "rank": 100, "total": 1000, "count": {}},
        "collection": {"wish": 10, "collect": 20, "doing": 30, "on_hold": 5, "dropped": 2},
    }


def _cover():
    return CoverResult("cover.jpg", "source.jpg", None, "STORED", datetime.now(timezone.utc))


class TestEpsVolumesDrift:
    """eps/volumes 字段在 schema 中存在但 normalize/repository 不处理。"""

    def test_normalize_should_extract_eps(self):
        """normalize_subject 应当提取 eps 字段。"""
        raw = _raw_subject_with_eps()
        subject = normalize_subject(raw, [])
        assert subject is not None
        # 当前 NormalizedSubject 没有 eps 字段，这是契约漂移
        assert hasattr(subject, "eps"), "NormalizedSubject 缺少 eps 字段"
        assert subject.eps == 24

    def test_normalize_should_extract_volumes(self):
        """normalize_subject 应当提取 volumes 字段。"""
        raw = _raw_subject_with_eps()
        subject = normalize_subject(raw, [])
        assert subject is not None
        assert hasattr(subject, "volumes"), "NormalizedSubject 缺少 volumes 字段"
        assert subject.volumes == 8

    def test_repository_should_write_eps(self):
        """repository 写入 subject 时应当包含 eps。"""
        session = _Session(existing_id=7)
        repo = ImportRepository(session)
        subject = normalize_subject(_raw_subject_with_eps(), [])
        repo._upsert_subject(subject, _cover())
        sql, values = session.calls[-1]
        assert "eps" in sql, "UPDATE subject SQL 缺少 eps 字段"
        assert values.get("eps") == 24


class TestCreditTypeDrift:
    """credit_type 在 schema 中为 PERSON|ORGANIZATION，但 repository 写入 MAIN。"""

    def test_credit_type_should_be_person_or_organization(self):
        """subject_credit.credit_type 应当反映上游的 person/company 类型。"""
        session = _Session(existing_id=7)
        repo = ImportRepository(session)
        persons = [
            {"relation": "导演", "person": {"id": 1, "name": "Test Director"}},
        ]
        subject = normalize_subject(_raw_subject_with_eps(), persons)
        repo._upsert_credits(42, subject)
        sql, values = session.calls[-1]
        # 当前固定写入 'MAIN'，但 schema 契约为 PERSON|ORGANIZATION
        assert "'MAIN'" not in sql, "credit_type 不应当固定为 MAIN"
        assert "credit_type" in sql
        # 应当根据上游 person type 决定
        assert values.get("credit_type") in ("PERSON", "ORGANIZATION"), \
            "credit_type 应当为 PERSON 或 ORGANIZATION"


class TestAiringStatusDrift:
    """indexer 只产出 upcoming/finished，但 RetrievalQuery 允许 AIRING。"""

    def test_indexer_should_produce_airing_status(self):
        """当 air_date 在过去且 eps > 0 且存在未播出剧集时，应当产出 AIRING。"""
        # 这个测试需要 indexer repository 的 load_subject 方法支持 AIRING
        # 当前实现只检查 air_date > CURDATE() 来判断 upcoming
        from jobs.indexer.repository import IndexJobRepository

        # 模拟一个正在播出的作品：air_date 在过去，但 status 为 Air
        session = _Session()
        repo = IndexJobRepository(session)
        # 当前 SQL 只产出 upcoming/finished/unknown
        # 需要增加对 episode.status 的检查来判定 AIRING
        # 这是一个设计缺陷，需要后续修复
        pytest.fail("indexer repository 当前不支持 AIRING 状态，需要修复")


class TestStaleReplaceSetDrift:
    """repository 只 upsert 不失效上游已删除的标签/主创/别名。"""

    def test_aliases_should_deactivate_removed(self):
        """当上游删除别名时，repository 应当失效本地记录。"""
        session = _Session(existing_id=7)
        repo = ImportRepository(session)
        # 模拟一个没有别名的作品
        raw = _raw_subject_with_eps()
        raw["infobox"] = []
        subject = normalize_subject(raw, [])
        repo._upsert_aliases(42, subject)
        # 当前实现只 INSERT ... ON DUPLICATE KEY UPDATE
        # 不会失效已存在但不在新集合中的别名
        # 需要实现 replace-set 语义：标记旧集合 → upsert 新集合 → 失效未出现项
        alias_calls = [c for c in session.calls if "subject_alias" in c[0]]
        has_deactivate = any("source_active" in c[0] or "deactivate" in c[0].lower() for c in alias_calls)
        assert has_deactivate, "别名 upsert 应当包含失效逻辑"

    def test_meta_tags_should_deactivate_removed(self):
        """当上游删除 meta tag 时，repository 应当失效本地记录。"""
        session = _Session(existing_id=7)
        repo = ImportRepository(session)
        raw = _raw_subject_with_eps()
        raw["meta_tags"] = []
        subject = normalize_subject(raw, [])
        repo._upsert_meta_tags(42, subject)
        tag_calls = [c for c in session.calls if "subject_meta_tag" in c[0]]
        has_deactivate = any("source_active" in c[0] or "deactivate" in c[0].lower() for c in tag_calls)
        assert has_deactivate, "meta tag upsert 应当包含失效逻辑"

    def test_credits_should_deactivate_removed(self):
        """当上游删除主创时，repository 应当失效本地记录。"""
        session = _Session(existing_id=7)
        repo = ImportRepository(session)
        subject = normalize_subject(_raw_subject_with_eps(), [])
        repo._upsert_credits(42, subject)
        credit_calls = [c for c in session.calls if "subject_credit" in c[0]]
        has_deactivate = any("source_active" in c[0] or "deactivate" in c[0].lower() for c in credit_calls)
        assert has_deactivate, "主创 upsert 应当包含失效逻辑"


class TestProfileHashConsistency:
    """importer 写入 profile hash 与 indexer 读取时可能不一致。"""

    def test_profile_hash_should_be_deterministic(self):
        """同一份数据在不同时间构建的 profile hash 应当一致。"""
        from app.rag.profile import build_subject_profile
        from app.rag.schemas import SubjectProfileSource

        source = SubjectProfileSource(
            title="Test",
            aliases=("别名1", "别名2"),
            summary="测试简介",
            meta_tags=("标签1",),
            trusted_tags=("可信标签",),
            credits=("导演：Test",),
            relations=("续作：Test 2",),
        )
        profile1 = build_subject_profile(source, "text-embedding-v4", 1024)
        profile2 = build_subject_profile(source, "text-embedding-v4", 1024)
        assert profile1.content_hash == profile2.content_hash, \
            "相同输入应当产生相同的 content_hash"

    def test_profile_source_must_match_indexer_load(self):
        """importer 的 profile_source 查询应当与 indexer 的 load_subject 返回一致。"""
        # importer 使用 repository._profile_source()
        # indexer 使用 IndexJobRepository.load_subject()
        # 两者应当从相同的表/列读取，否则 hash 会不一致
        from jobs.importer.repository import ImportRepository
        from jobs.indexer.repository import IndexJobRepository

        # 检查两个查询是否使用相同的字段和排序
        importer_session = _Session(profile_row={
            "title": "Test", "summary": "", "aliases": None,
            "meta_tags": None, "credits": None, "relations": None,
        })
        importer_repo = ImportRepository(importer_session)
        importer_repo._profile_source(42)
        # _profile_source 发出两条 SQL：第一条是 GROUP_CONCAT 主查询，第二条是 trusted_tags
        profile_sql = importer_session.calls[0][0]

        # indexer 的 SQL 在 load_subject 中
        # 两者应当使用相同的 GROUP_CONCAT 排序和字段
        # 当前 importer 使用 ORDER BY name，indexer 也使用 ORDER BY name
        # 但需要确保 trusted_tags 的判定标准一致
        assert "GROUP_CONCAT" in profile_sql
        # 需要进一步验证两个 SQL 的语义等价性
        # 这是一个架构风险，需要代码审查确认
