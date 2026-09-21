from datetime import datetime, timedelta, timezone

from app.agent.client.actions.collection_type import (
    build_collection_type_preview,
    build_collection_type_tools,
)
from app.agent.client.actions.subject_resolution import build_subject_resolution_tools
from app.chat.pending_action import (
    SetCollectionTypePendingAction,
    SubjectResolutionCandidate,
    SubjectResolutionPendingAction,
    parse_pending_action_json,
)
from app.chat.pending_events import (
    get_pending_action_event,
    reset_pending_action_collector,
    set_pending_action_collector,
)
from app.chat.user import UserInfo


_USER = UserInfo(user_id=2, username="tester", role="USER", token="token")


def _valid(name_cn):
    return {"name": name_cn, "nameCn": name_cn, "type": 2, "nsfw": False, "active": True}


class FakeBusiness:
    def __init__(self, *, search_rows=None, subjects=None, collected=None,
                 save_result=None, request_error=None):
        self.search_rows = search_rows or []
        self.subjects = subjects or {}
        self.collected = collected or {}       # subjectId -> 当前收藏类型
        self.save_result = save_result         # None=成功；或 {"error":True,...}
        self.request_error = request_error
        self.search_calls = []
        self.batch_calls = []
        self.save_calls = []

    def search_subjects(self, query, *, token=None, size=15):
        self.search_calls.append(query)
        return {"content": self.search_rows, "total": len(self.search_rows), "page": 1, "size": size}

    def batch_subjects(self, subject_ids, *, token=None, exclude_collected=False):
        self.batch_calls.append((list(subject_ids), exclude_collected))
        items = [{"id": sid, **self.subjects[sid]} for sid in subject_ids if sid in self.subjects]
        return {"items": items,
                "missingIds": [sid for sid in subject_ids if sid not in self.subjects],
                "filteredIds": [], "collectedIds": []}

    def save_collection(self, subject_id, *, collection_type, token=None, rate=None, ep_status=None):
        self.save_calls.append((subject_id, collection_type))
        return self.save_result

    def request(self, method, path, *, token=None, params=None, json_body=None):
        if self.request_error is not None:
            return self.request_error
        if method == "GET" and path.startswith("/api/client/collections/"):
            sid = int(path.rsplit("/", 1)[-1])
            if sid in self.collected:
                return {"type": self.collected[sid]}
            return None
        return None


class FakeRetrieval:
    def __init__(self, result=None):
        self.result = result if result is not None else {"available": True, "items": []}
        self.calls = []

    def execute(self, query, *, mode, user):
        self.calls.append((query.semantic_query, mode))
        return self.result


def _run(fn, *args, **kwargs):
    token = set_pending_action_collector()
    try:
        result = fn(*args, **kwargs)
        event = get_pending_action_event()
    finally:
        reset_pending_action_collector(token)
    return result, event


def _set_action(**overrides):
    base = dict(type="SET_COLLECTION_TYPE", user_id=2,
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
                subject_id=84, subject_name="孤独摇滚！", target_type=3,
                current_type=None, action="ADD")
    base.update(overrides)
    return SetCollectionTypePendingAction(**base)


# --------------------------------------------------------------------------- #
# 预览三态
# --------------------------------------------------------------------------- #

def test_preview_add_when_not_collected() -> None:
    business = FakeBusiness()
    result, event = _run(build_collection_type_preview, 84, "孤独摇滚！", 3, _USER, business)
    assert result["action"] == "ADD"
    assert result["targetType"] == 3 and result["currentType"] is None
    assert event.action.type == "SET_COLLECTION_TYPE"
    assert event.action.target_type == 3 and event.action.action == "ADD"


def test_preview_noop_when_already_target_type() -> None:
    business = FakeBusiness(collected={84: 3})
    result, event = _run(build_collection_type_preview, 84, "孤独摇滚！", 3, _USER, business)
    assert result["action"] == "NOOP"
    assert event is None          # 已在目标类型：不发待确认动作、不写入


def test_preview_change_when_different_type() -> None:
    business = FakeBusiness(collected={84: 1})
    result, event = _run(build_collection_type_preview, 84, "孤独摇滚！", 3, _USER, business)
    assert result["action"] == "CHANGE"
    assert result["currentType"] == 1 and result["targetType"] == 3
    assert "改为" in result["message"]      # 变更必须在预览可见
    assert event.action.action == "CHANGE"
    assert event.action.current_type == 1


def test_preview_propagates_state_error() -> None:
    business = FakeBusiness(request_error={"error": True, "code": 500, "message": "服务器错误"})
    result, _ = _run(build_collection_type_preview, 84, "X", 3, _USER, business)
    assert result.get("error") is True


# --------------------------------------------------------------------------- #
# set_subject_collection
# --------------------------------------------------------------------------- #

def test_set_collection_unique_exact_previews_add() -> None:
    business = FakeBusiness(
        search_rows=[{"id": 84, "nameCn": "孤独摇滚！", "type": 2}],
        subjects={84: _valid("孤独摇滚！")},
    )
    retrieval = FakeRetrieval()
    set_tool = build_collection_type_tools(business, retrieval)[0]

    result, event = _run(set_tool.func, collection_type=3, title="孤独摇滚!", user=_USER)

    assert result["resolved"] is True
    assert result["preview"]["action"] == "ADD"
    assert retrieval.calls == []                 # Business 命中不回退 RAG
    assert business.batch_calls == [([84], False)]
    assert event.action.type == "SET_COLLECTION_TYPE"
    assert event.action.target_type == 3


def test_set_collection_multi_enters_resolution_with_target_type() -> None:
    business = FakeBusiness(
        search_rows=[{"id": 1, "nameCn": "物语系列", "type": 2},
                     {"id": 2, "nameCn": "物语系列 第二季", "type": 2}],
        subjects={1: _valid("物语系列"), 2: _valid("物语系列 第二季")},
    )
    set_tool = build_collection_type_tools(business, FakeRetrieval())[0]

    result, event = _run(set_tool.func, collection_type=3, title="物语", user=_USER)

    assert result["needsSelection"] is True
    assert event.action.type == "SUBJECT_RESOLUTION"
    assert event.action.collection_type == 3     # 选中后要设的目标类型被记住


def test_set_collection_noop_clears_state() -> None:
    business = FakeBusiness(
        search_rows=[{"id": 84, "nameCn": "孤独摇滚！", "type": 2}],
        subjects={84: _valid("孤独摇滚！")},
        collected={84: 3},
    )
    set_tool = build_collection_type_tools(business, FakeRetrieval())[0]

    result, event = _run(set_tool.func, collection_type=3, title="孤独摇滚!", user=_USER)

    assert result["preview"]["action"] == "NOOP"
    assert event.operation == "CLEAR"            # 无需写入，不残留待确认动作
    assert business.save_calls == []


def test_set_collection_explicit_id_skips_search() -> None:
    business = FakeBusiness(subjects={84: _valid("孤独摇滚！")})
    set_tool = build_collection_type_tools(business, FakeRetrieval())[0]

    result, _ = _run(set_tool.func, collection_type=2, subject_id=84, user=_USER)

    assert result["preview"]["action"] == "ADD"
    assert business.search_calls == []
    assert business.batch_calls == [([84], False)]


def test_set_collection_no_match() -> None:
    business = FakeBusiness(subjects={99: {"nameCn": "x", "name": "x", "type": 2, "nsfw": False, "active": False}})
    set_tool = build_collection_type_tools(business, FakeRetrieval())[0]

    result, event = _run(set_tool.func, collection_type=3, subject_id=99, user=_USER)

    assert result["resolved"] is False
    assert result["message"] == "没有找到匹配项"
    assert event.operation == "CLEAR"


# --------------------------------------------------------------------------- #
# execute_set_collection_type
# --------------------------------------------------------------------------- #

def test_execute_success_saves_and_clears() -> None:
    business = FakeBusiness(save_result=None)
    execute = build_collection_type_tools(business, FakeRetrieval())[1]

    result, event = _run(execute.func, pending=_set_action(), user=_USER, write_confirmed=True)

    assert result["state"] == "SAVED"
    assert business.save_calls == [(84, 3)]
    assert event.operation == "CLEAR"


def test_execute_409_reports_already_collected() -> None:
    business = FakeBusiness(save_result={"error": True, "code": 409, "message": "该条目已收藏"})
    execute = build_collection_type_tools(business, FakeRetrieval())[1]

    result, event = _run(execute.func, pending=_set_action(), user=_USER, write_confirmed=True)

    assert result["state"] == "ALREADY_COLLECTED"
    assert event.operation == "CLEAR"


def test_execute_404_clears_and_errors() -> None:
    business = FakeBusiness(save_result={"error": True, "code": 404, "message": "条目不存在"})
    execute = build_collection_type_tools(business, FakeRetrieval())[1]

    result, event = _run(execute.func, pending=_set_action(), user=_USER, write_confirmed=True)

    assert result.get("error") is True
    assert event.operation == "CLEAR"


def test_execute_infra_error_keeps_pending() -> None:
    business = FakeBusiness(save_result={"error": True, "message": "后端服务超时"})  # code 为 None
    execute = build_collection_type_tools(business, FakeRetrieval())[1]

    result, event = _run(execute.func, pending=_set_action(), user=_USER, write_confirmed=True)

    assert result.get("error") is True and result.get("retryable") is True
    assert event is None                          # 结果不确定：保留待确认动作供重试


def test_execute_without_pending_errors() -> None:
    execute = build_collection_type_tools(FakeBusiness(), FakeRetrieval())[1]
    result, _ = _run(execute.func, pending=None, user=_USER)
    assert result.get("error") is True


def test_execute_refuses_without_confirmation_turn() -> None:
    # 硬门禁：有待确认动作但当前回合非明确确认（write_confirmed 默认 False）→ 拒写
    business = FakeBusiness(save_result=None)
    execute = build_collection_type_tools(business, FakeRetrieval())[1]

    result, event = _run(execute.func, pending=_set_action(), user=_USER)

    assert result.get("error") is True
    assert business.save_calls == []            # Business 未收到任何写请求
    assert event is None                        # 未清理，保留待确认动作


def test_execute_refuses_other_users_action() -> None:
    business = FakeBusiness(save_result=None)
    execute = build_collection_type_tools(business, FakeRetrieval())[1]

    result, event = _run(execute.func, pending=_set_action(user_id=999), user=_USER, write_confirmed=True)

    assert result.get("error") is True
    assert business.save_calls == []


# --------------------------------------------------------------------------- #
# 选择后按目标类型分派
# --------------------------------------------------------------------------- #

def test_select_dispatches_to_collection_type_preview() -> None:
    business = FakeBusiness(subjects={1: _valid("物语系列"), 2: _valid("物语系列 第二季")})
    select = build_subject_resolution_tools(business, FakeRetrieval())[1]
    pending = SubjectResolutionPendingAction(
        type="SUBJECT_RESOLUTION", user_id=2,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
        query="物语", collection_type=3,
        candidates=[
            SubjectResolutionCandidate(subject_id=1, subject_name="物语系列", match_source="BUSINESS", match_type="CANDIDATE"),
            SubjectResolutionCandidate(subject_id=2, subject_name="物语系列 第二季", match_source="BUSINESS", match_type="CANDIDATE"),
        ],
    )

    result, event = _run(select.func, choice=2, pending=pending, user=_USER)

    assert result["selected"]["subjectId"] == 2
    assert result["preview"]["action"] == "ADD"
    assert business.batch_calls == [([2], False)]     # 选择后重新 /batch 校验
    assert event.action.type == "SET_COLLECTION_TYPE"
    assert event.action.target_type == 3


# --------------------------------------------------------------------------- #
# 序列化 / schema
# --------------------------------------------------------------------------- #

def test_set_collection_action_roundtrips() -> None:
    action = _set_action(action="CHANGE", current_type=1)
    parsed = parse_pending_action_json(action.model_dump_json(by_alias=True))
    assert parsed.type == "SET_COLLECTION_TYPE"
    assert parsed.target_type == 3 and parsed.current_type == 1 and parsed.action == "CHANGE"


def test_preview_generates_action_id() -> None:
    business = FakeBusiness()
    _, event = _run(build_collection_type_preview, 84, "X", 3, _USER, business)
    assert event.action.action_id != ""


def test_legacy_json_without_action_id_defaults_empty() -> None:
    action = _set_action()
    legacy = action.model_dump(by_alias=True)
    legacy.pop("actionId")
    import json as _json
    parsed = parse_pending_action_json(_json.dumps(legacy, default=str))
    assert parsed.type == "SET_COLLECTION_TYPE"
    assert parsed.action_id == ""


def test_resolution_collection_type_roundtrips_and_defaults_none() -> None:
    action = SubjectResolutionPendingAction(
        type="SUBJECT_RESOLUTION", user_id=2,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
        query="q", collection_type=4,
        candidates=[SubjectResolutionCandidate(subject_id=1, subject_name="A", match_source="BUSINESS", match_type="CANDIDATE")],
    )
    parsed = parse_pending_action_json(action.model_dump_json(by_alias=True))
    assert parsed.collection_type == 4
    # 旧 JSON 缺 collectionType 字段时按 None 解析（向后兼容）
    legacy = action.model_dump(by_alias=True)
    legacy.pop("collectionType")
    import json as _json
    legacy_parsed = parse_pending_action_json(_json.dumps(legacy, default=str))
    assert legacy_parsed.collection_type is None


def test_set_tool_exposes_collection_type_arg() -> None:
    set_tool = build_collection_type_tools(FakeBusiness(), FakeRetrieval())[0]
    assert "collection_type" in set_tool.args
    assert "title" in set_tool.args
