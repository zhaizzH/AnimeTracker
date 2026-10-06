"""``upsert_episodes`` 对畸形 ``duration`` 的截断防护。

背景：Bangumi v0 的 ``/v0/episodes`` 对部分 SP/ED 条目会把**剧集区间文本**
塞进 ``duration`` 字段（实测 ``'第0话 - 第12话, 第14话 - 第25话'``，23 字符），
而 ``episode.duration`` 列宽有限。不截断时 MySQL 抛
``DataError (1406, "Data too long for column 'duration'")``，导致**整个条目的
事务回滚**——一部番剧的 subject/episode/person/character 全部丢失。

本测试锁定「超长值必须被截断而非上抛」这一契约。用假 Session 捕获绑定参数，
不连真实数据库。
"""

from __future__ import annotations

from jobs.importer.db import upsert_episodes

OVERLONG = "第0话 - 第12话, 第14话 - 第25话" * 3  # 69 字符，远超列宽

class _FakeResult:
    def scalar(self):
        return None  # 不存在既有行 → 走 INSERT 分支

class _FakeSession:
    """记录所有 execute 调用及其参数。"""

    def __init__(self):
        self.calls = []

    def execute(self, statement, params=None):
        self.calls.append((str(statement), params))
        return _FakeResult()

def _episode(duration):
    return {
        "id": 103233,
        "type": 3,
        "sort": 1,
        "name": "THE REAL FOLK BLUES",
        "name_cn": None,
        "duration": duration,
        "airdate": "1998-06-26",
        "desc": "",
    }

def _inserted_duration(session):
    """取出 INSERT 语句绑定的 duration 值。"""
    for sqltext, params in session.calls:
        if "INSERT INTO episode" in sqltext:
            return params["duration"]
    raise AssertionError("未捕获到 INSERT INTO episode")

def test_overlong_duration_is_truncated_not_raised():
    session = _FakeSession()

    upsert_episodes(session, subject_id=42, episodes=[_episode(OVERLONG)])

    value = _inserted_duration(session)
    assert value is not None
    assert len(value) == 64, f"应截断到 64 字符，实际 {len(value)}"

def test_normal_duration_passes_through_unchanged():
    session = _FakeSession()

    upsert_episodes(session, subject_id=42, episodes=[_episode("00:24:43")])

    assert _inserted_duration(session) == "00:24:43"

def test_none_duration_stays_none():
    session = _FakeSession()

    upsert_episodes(session, subject_id=42, episodes=[_episode(None)])

    assert _inserted_duration(session) is None
