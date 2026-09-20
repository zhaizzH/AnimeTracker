from datetime import datetime, timedelta, timezone

from app.agent.client.actions.subject_resolution import (
    build_subject_resolution_tools,
    dedup_ids,
    filter_authoritative,
    normalize_title,
    select_candidate,
    unique_exact_match_ids,
)
from app.agent.client.gateway import _resolve_forced_pending_route
from app.chat.pending_action import (
    SubjectResolutionCandidate,
    SubjectResolutionPendingAction,
    WishlistPendingAction,
    WishlistPendingItem,
    parse_pending_action_json,
)
from app.chat.pending_events import (
    get_pending_action_event,
    reset_pending_action_collector,
    set_pending_action_collector,
)
from app.chat.user import UserInfo


_USER = UserInfo(user_id=2, username="tester", role="USER", token="token")


class FakeBusiness:
    """Business 网关替身：search / batch / collections 状态检查。"""

    def __init__(self, *, search_rows=None, search_error=None, subjects=None,
                 batch_error=None, collected=None):
        self.search_rows = search_rows or []
        self.search_error = search_error
        self.subjects = subjects or {}
        self.batch_error = batch_error
        self.collected = collected or set()
        self.search_calls: list[str] = []
        self.batch_calls: list[tuple] = []

    def search_subjects(self, query, *, token=None, size=15):
        self.search_calls.append(query)
        if self.search_error is not None:
            return self.search_error
        return {"content": self.search_rows, "total": len(self.search_rows), "page": 1, "size": size}

    def batch_subjects(self, subject_ids, *, token=None, exclude_collected=False):
        self.batch_calls.append((list(subject_ids), exclude_collected))
        if self.batch_error is not None:
            return self.batch_error
        items = []
        for sid in subject_ids:
            detail = self.subjects.get(sid)
            if detail is not None:
                items.append({"id": sid, **detail})
        return {
            "items": items,
            "missingIds": [sid for sid in subject_ids if sid not in self.subjects],
            "filteredIds": [],
            "collectedIds": [],
        }

    def request(self, method, path, *, token=None, params=None, json_body=None):
        if method == "GET" and path.startswith("/api/client/collections/"):
            sid = int(path.rsplit("/", 1)[-1])
            if sid in self.collected:
                return {"type": 1}
            return None
        return None


class FakeRetrieval:
    def __init__(self, result=None):
        self.result = result if result is not None else {"available": True, "items": []}
        self.calls: list[tuple] = []

    def execute(self, query, *, mode, user):
        self.calls.append((query.semantic_query, mode))
        return self.result


def _tools(business, retrieval):
    resolve, select = build_subject_resolution_tools(business, retrieval)
    return resolve, select


def _run(fn, **kwargs):
    token = set_pending_action_collector()
    try:
        result = fn(**kwargs)
        event = get_pending_action_event()
    finally:
        reset_pending_action_collector(token)
    return result, event


def _valid(name_cn):
    return {"name": name_cn, "nameCn": name_cn, "type": 2, "nsfw": False, "active": True}


# --------------------------------------------------------------------------- #
# 纯函数
# --------------------------------------------------------------------------- #

def test_normalize_title_is_safe_character_folding_only() -> None:
    assert normalize_title("  Attack　on  TITAN! ") == "attack on titan"
    assert normalize_title("Ｔｅｓｔ") == "test"
    assert normalize_title(None) == ""


def test_normalize_title_does_not_apply_season_semantics() -> None:
    # 「第二季」与「第2季」没有真实别名关系时不得被视作相同
    assert normalize_title("第二季") != normalize_title("第2季")


def test_unique_exact_match_uses_titles_and_real_aliases() -> None:
    items = [
        {"subjectId": 1, "title": "X", "aliases": ["Y", "Z"]},
        {"subjectId": 2, "nameCn": "W"},
    ]
    ids, unique = unique_exact_match_ids("y", items, "subjectId")
    assert ids == [1]
    assert unique is True


def test_unique_exact_match_flags_multiple_distinct_hits() -> None:
    items = [{"id": 1, "nameCn": "同名"}, {"id": 2, "nameCn": "同名"}]
    ids, unique = unique_exact_match_ids("同名", items, "id")
    assert ids == [1, 2]
    assert unique is False


def test_dedup_ids_rejects_bool_and_non_positive() -> None:
    assert dedup_ids([True, 1, 1, 0, -3, "2", 2, None]) == [1, 2]


def test_filter_authoritative_reports_infra_error() -> None:
    business = FakeBusiness(batch_error={"error": True, "message": "boom"})
    valid, error = filter_authoritative([1], business, "token")
    assert valid is None
    assert error["error"] is True
    assert business.batch_calls == [([1], False)]


def test_select_candidate_by_index_and_name() -> None:
    candidates = [
        SubjectResolutionCandidate(subject_id=1, subject_name="物语系列", match_source="BUSINESS", match_type="CANDIDATE"),
        SubjectResolutionCandidate(subject_id=2, subject_name="物语系列 第二季", match_source="BUSINESS", match_type="CANDIDATE"),
    ]
    picked, code = select_candidate(2, candidates)
    assert picked.subject_id == 2 and code is None
    picked, code = select_candidate("物语系列", candidates)
    assert picked.subject_id == 1 and code is None
    picked, code = select_candidate(99, candidates)
    assert picked is None and code == "invalid_choice"


def test_select_candidate_rejects_ambiguous_name() -> None:
    candidates = [
        SubjectResolutionCandidate(subject_id=1, subject_name="同名", match_source="BUSINESS", match_type="CANDIDATE"),
        SubjectResolutionCandidate(subject_id=2, subject_name="同名", match_source="BUSINESS", match_type="CANDIDATE"),
    ]
    picked, code = select_candidate("同名", candidates)
    assert picked is None and code == "ambiguous_name"


# --------------------------------------------------------------------------- #
# 解析入口
# --------------------------------------------------------------------------- #

def test_business_unique_exact_previews_without_rag() -> None:
    business = FakeBusiness(
        search_rows=[{"id": 84, "name": "ぼっち・ざ・ろっく!", "nameCn": "孤独摇滚！", "type": 2}],
        subjects={84: _valid("孤独摇滚！")},
    )
    retrieval = FakeRetrieval()
    resolve, _ = _tools(business, retrieval)

    result, event = _run(resolve.func, title="孤独摇滚!", user=_USER)

    assert result["resolved"] is True
    assert result["preview"]["pendingItems"] == [{"subjectId": 84, "subjectName": "孤独摇滚！"}]
    assert retrieval.calls == []          # Business 命中不回退 RAG
    assert business.batch_calls == [([84], False)]
    assert event.action.type == "ADD_TO_WISHLIST"
    assert [item.subject_id for item in event.action.items] == [84]


def test_business_error_does_not_trigger_rag_or_preview() -> None:
    business = FakeBusiness(search_error={"error": True, "code": 500, "message": "服务器错误"})
    retrieval = FakeRetrieval(result={"available": True, "items": [{"subjectId": 1, "nameCn": "任意"}]})
    resolve, _ = _tools(business, retrieval)

    result, event = _run(resolve.func, title="任意", user=_USER)

    assert result.get("error") is True
    assert retrieval.calls == []          # Business 异常绝不触发 RAG
    assert business.batch_calls == []
    assert event.operation == "CLEAR"


def test_business_empty_falls_back_to_rag_exact_match() -> None:
    business = FakeBusiness(
        search_rows=[],
        subjects={7: _valid("进击的巨人")},
    )
    retrieval = FakeRetrieval(result={
        "available": True,
        "items": [{"subjectId": 7, "title": "進撃の巨人", "nameCn": "进击的巨人", "aliases": ["Attack on Titan"]}],
    })
    resolve, _ = _tools(business, retrieval)

    result, event = _run(resolve.func, title="进击的巨人", user=_USER)

    assert result["resolved"] is True
    assert retrieval.calls == [("进击的巨人", "search")]
    assert business.batch_calls == [([7], False)]
    assert event.action.type == "ADD_TO_WISHLIST"


def test_rag_unavailable_is_not_masked_as_no_result() -> None:
    business = FakeBusiness(search_rows=[])
    retrieval = FakeRetrieval(result={"available": False, "reason": "rag_unavailable", "items": []})
    resolve, _ = _tools(business, retrieval)

    result, event = _run(resolve.func, title="某番", user=_USER)

    assert result.get("error") is True
    assert "不可用" in result["message"]
    assert business.batch_calls == []
    assert event.operation == "CLEAR"


def test_business_nonempty_without_exact_match_enters_resolution_without_rag() -> None:
    business = FakeBusiness(
        search_rows=[
            {"id": 1, "nameCn": "物语系列 第二季", "type": 2},
            {"id": 2, "nameCn": "物语系列", "type": 2},
        ],
        subjects={1: _valid("物语系列 第二季"), 2: _valid("物语系列")},
    )
    retrieval = FakeRetrieval()
    resolve, _ = _tools(business, retrieval)

    result, event = _run(resolve.func, title="物语", user=_USER)

    assert result["resolved"] is False
    assert result["needsSelection"] is True
    assert len(result["candidates"]) == 2
    assert retrieval.calls == []          # 成功非空但没有唯一精确命中：不回退 RAG
    assert event.action.type == "SUBJECT_RESOLUTION"
    assert event.action.query == "物语"
    assert {c.subject_id for c in event.action.candidates} == {1, 2}


def test_season_variant_is_not_auto_selected() -> None:
    business = FakeBusiness(
        search_rows=[{"id": 5, "nameCn": "某动画 第二季", "type": 2}],
        subjects={5: _valid("某动画 第二季")},
    )
    retrieval = FakeRetrieval()
    resolve, _ = _tools(business, retrieval)

    result, event = _run(resolve.func, title="某动画 第2季", user=_USER)

    assert result.get("resolved") is not True     # 没有真实别名关系不得自动预览
    assert result["needsSelection"] is True
    assert event.action.type == "SUBJECT_RESOLUTION"


def test_explicit_subject_id_skips_search_but_validates() -> None:
    business = FakeBusiness(subjects={84: _valid("孤独摇滚！")})
    retrieval = FakeRetrieval()
    resolve, _ = _tools(business, retrieval)

    result, event = _run(resolve.func, subject_id=84, user=_USER)

    assert result["resolved"] is True
    assert business.search_calls == []    # 跳过名称搜索
    assert business.batch_calls == [([84], False)]
    assert event.action.type == "ADD_TO_WISHLIST"


def test_batch_filter_removes_unsafe_candidates() -> None:
    business = FakeBusiness(
        search_rows=[
            {"id": 1, "nameCn": "安全", "type": 2},
            {"id": 2, "nameCn": "NSFW", "type": 2},
            {"id": 3, "nameCn": "未导入", "type": 2},
        ],
        subjects={
            1: _valid("安全"),
            2: {"nameCn": "NSFW", "name": "NSFW", "type": 2, "nsfw": True, "active": True},
            3: {"nameCn": "未导入", "name": "未导入", "type": 2, "nsfw": False, "active": False},
        },
    )
    retrieval = FakeRetrieval()
    resolve, _ = _tools(business, retrieval)

    result, event = _run(resolve.func, title="随便", user=_USER)

    # 歧义集合过滤后只剩 1 个，但不是唯一精确命中，仍需用户选择而非自动预览
    assert result["needsSelection"] is True
    assert [c["subjectId"] for c in result["candidates"]] == [1]
    assert [c.subject_id for c in event.action.candidates] == [1]


def test_batch_filter_to_zero_returns_no_match() -> None:
    business = FakeBusiness(
        subjects={99: {"nameCn": "未导入", "name": "未导入", "type": 2, "nsfw": False, "active": False}},
    )
    retrieval = FakeRetrieval()
    resolve, _ = _tools(business, retrieval)

    result, event = _run(resolve.func, subject_id=99, user=_USER)

    assert result["resolved"] is False
    assert result["message"] == "没有找到匹配项"
    assert event.operation == "CLEAR"


# --------------------------------------------------------------------------- #
# 候选选择
# --------------------------------------------------------------------------- #

def _resolution_action(candidates, *, user_id=2, expires_in=600):
    return SubjectResolutionPendingAction(
        type="SUBJECT_RESOLUTION",
        user_id=user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
        query="物语",
        candidates=candidates,
    )


def _two_candidates():
    return [
        SubjectResolutionCandidate(subject_id=1, subject_name="物语系列", match_source="BUSINESS", match_type="CANDIDATE"),
        SubjectResolutionCandidate(subject_id=2, subject_name="物语系列 第二季", match_source="BUSINESS", match_type="CANDIDATE"),
    ]


def test_select_by_index_revalidates_and_previews() -> None:
    business = FakeBusiness(subjects={1: _valid("物语系列"), 2: _valid("物语系列 第二季")})
    _, select = _tools(business, FakeRetrieval())
    pending = _resolution_action(_two_candidates())

    result, event = _run(select.func, choice=1, pending=pending, user=_USER)

    assert result["resolved"] is True
    assert result["selected"]["subjectId"] == 1
    assert business.batch_calls == [([1], False)]   # 选择后重新做 /batch 校验
    assert event.action.type == "ADD_TO_WISHLIST"
    assert [item.subject_id for item in event.action.items] == [1]


def test_select_by_unique_name() -> None:
    business = FakeBusiness(subjects={1: _valid("物语系列"), 2: _valid("物语系列 第二季")})
    _, select = _tools(business, FakeRetrieval())
    pending = _resolution_action(_two_candidates())

    result, _ = _run(select.func, choice="物语系列 第二季", pending=pending, user=_USER)

    assert result["selected"]["subjectId"] == 2


def test_select_rejects_user_mismatch_and_clears() -> None:
    business = FakeBusiness(subjects={1: _valid("物语系列"), 2: _valid("物语系列 第二季")})
    _, select = _tools(business, FakeRetrieval())
    pending = _resolution_action(_two_candidates(), user_id=999)

    result, event = _run(select.func, choice=1, pending=pending, user=_USER)

    assert result.get("error") is True
    assert event.operation == "CLEAR"
    assert business.batch_calls == []


def test_select_rejects_expired_and_clears() -> None:
    business = FakeBusiness(subjects={1: _valid("物语系列"), 2: _valid("物语系列 第二季")})
    _, select = _tools(business, FakeRetrieval())
    pending = _resolution_action(_two_candidates(), expires_in=-10)

    result, event = _run(select.func, choice=1, pending=pending, user=_USER)

    assert result.get("error") is True
    assert event.operation == "CLEAR"


def test_select_without_pending_state_errors() -> None:
    _, select = _tools(FakeBusiness(), FakeRetrieval())
    result, _ = _run(select.func, choice=1, pending=None, user=_USER)
    assert result.get("error") is True


def test_select_keeps_state_on_invalid_choice() -> None:
    business = FakeBusiness(subjects={1: _valid("物语系列"), 2: _valid("物语系列 第二季")})
    _, select = _tools(business, FakeRetrieval())
    pending = _resolution_action(_two_candidates())

    result, event = _run(select.func, choice=99, pending=pending, user=_USER)

    assert result.get("error") is True
    assert result["reason"] == "invalid_choice"
    assert event is None            # 不清理，允许重新选择


def test_select_clears_when_already_collected() -> None:
    business = FakeBusiness(subjects={1: _valid("物语系列"), 2: _valid("物语系列 第二季")}, collected={1})
    _, select = _tools(business, FakeRetrieval())
    pending = _resolution_action(_two_candidates())

    result, event = _run(select.func, choice=1, pending=pending, user=_USER)

    assert result["preview"]["pendingItems"] == []
    assert result["preview"]["skippedItems"][0]["subjectId"] == 1
    assert event.operation == "CLEAR"


def test_select_clears_when_candidate_no_longer_valid() -> None:
    business = FakeBusiness(
        subjects={1: {"nameCn": "物语系列", "name": "物语系列", "type": 2, "nsfw": False, "active": False},
                  2: _valid("物语系列 第二季")},
    )
    _, select = _tools(business, FakeRetrieval())
    pending = _resolution_action(_two_candidates())

    result, event = _run(select.func, choice=1, pending=pending, user=_USER)

    assert result.get("error") is True
    assert event.operation == "CLEAR"


# --------------------------------------------------------------------------- #
# 路由 / 序列化
# --------------------------------------------------------------------------- #

def test_gateway_routes_resolution_state_for_bare_ordinal() -> None:
    pending = _resolution_action(_two_candidates())
    state = {"pending_action": pending, "current_question": "1"}
    assert _resolve_forced_pending_route(state) == {"routing": {"route_target": "recommend_agent"}}


def test_gateway_confirmation_under_resolution_is_not_a_write_confirmation() -> None:
    # 确认词仍路由到 recommend_agent，但写入只对 ADD_TO_WISHLIST 生效；此处只断言路由目标
    pending = _resolution_action(_two_candidates())
    state = {"pending_action": pending, "current_question": "确认"}
    assert _resolve_forced_pending_route(state) == {"routing": {"route_target": "recommend_agent"}}


def test_gateway_wishlist_without_confirmation_is_not_forced() -> None:
    pending = WishlistPendingAction(
        type="ADD_TO_WISHLIST", user_id=2,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
        items=[WishlistPendingItem(subject_id=1, subject_name="A")],
    )
    assert _resolve_forced_pending_route({"pending_action": pending, "current_question": "1"}) is None


def test_resolution_action_roundtrips_through_discriminated_union() -> None:
    action = _resolution_action(_two_candidates())
    parsed = parse_pending_action_json(action.model_dump_json(by_alias=True))
    assert parsed.type == "SUBJECT_RESOLUTION"
    assert parsed.query == "物语"
    assert [c.subject_id for c in parsed.candidates] == [1, 2]
    assert parsed.candidates[0].match_source == "BUSINESS"
