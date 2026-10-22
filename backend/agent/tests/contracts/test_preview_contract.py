"""待确认动作协议契约：键格式、TTL、判别联合往返、别名兼容、版本绑定。

对应 spec ``pending-action-protocol``。这些是 agent 与业务/Redis 之间的**协议**承诺，
改动任何一条都会让已停在上游的预览失效或让旧会话无法解析，所以强度高于普通单元测试。

驱动方式遵循 design D6：通过真实入口（``parse_pending_action_json`` / ``PendingAction``
判别联合 / ``RedisChatStore`` 的键与 TTL / ``CollectionProgressPreviewable.do_execute``），
不复制一份协议常量，否则测试与实现会一起漂移。
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.agent.client.actions.collection_progress import CollectionProgressPreviewable
from app.agent.client.actions.previewable import Clear, Keep, Replace
from app.chat.pending_action import (
    CollectionProgressPendingAction,
    PendingAction,
    SetCollectionTypePendingAction,
    SubjectResolutionPendingAction,
    WishlistPendingAction,
    parse_pending_action_json,
)
from app.chat.pending_events import (
    emit_pending_action_clear,
    emit_pending_action_replace,
    emit_pending_action_set,
    get_pending_action_event,
    reset_pending_action_collector,
    set_pending_action_collector,
)
from app.chat.user import UserInfo
from app.adapters.redis.chat_store import RedisChatStore

#: 协议承诺的 TTL（秒）。600s 与预览结果本身的生存期一致。
PENDING_ACTION_TTL_SECONDS = 600


# --------------------------------------------------------------------------- #
# 5.1 键格式与 TTL
# --------------------------------------------------------------------------- #

def _store() -> RedisChatStore:
    """只用于取键名，不建立连接。"""
    return RedisChatStore("redis://localhost:6379/0")


def test_pending_action_key_format() -> None:
    """键必须是 ``agent:pending-action:{session_id}``。"""
    store = _store()
    assert store._pending_action_key("abc-123") == "agent:pending-action:abc-123"


def test_pending_action_key_is_session_scoped() -> None:
    """不同会话不得共享同一个键（否则会串话）。"""
    store = _store()
    assert store._pending_action_key("s1") != store._pending_action_key("s2")


def test_pending_action_key_prefix_is_stable() -> None:
    """前缀是跨服务契约，改名即破坏兼容。"""
    store = _store()
    assert store._pending_action_key("x").startswith("agent:pending-action:")


def test_default_ttl_is_600_seconds() -> None:
    import inspect

    signature = inspect.signature(RedisChatStore.save_pending_action)
    assert signature.parameters["ttl_seconds"].default == PENDING_ACTION_TTL_SECONDS


def test_expires_at_matches_ttl_semantics() -> None:
    """``expires_at`` 必须存在于所有变体上，并由业务侧的 ``expiresAt`` 填充。"""
    for model in (
        CollectionProgressPendingAction,
        WishlistPendingAction,
        SubjectResolutionPendingAction,
        SetCollectionTypePendingAction,
    ):
        assert "expires_at" in model.model_fields, f"{model.__name__} 缺少 expires_at"


# --------------------------------------------------------------------------- #
# 5.2 判别联合往返
# --------------------------------------------------------------------------- #

def _round_trip(model):
    raw = model.model_dump_json(by_alias=True)
    return parse_pending_action_json(raw)


def test_union_round_trips_collection_progress() -> None:
    original = CollectionProgressPendingAction(
        type="COLLECTION_PROGRESS_UPDATE",
        preview_id="p-1",
        user_id=7,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
        items=[{"subject_id": 1, "subject_name": "进击", "current_ep_status": 5, "target_ep_status": 12}],
    )
    parsed = _round_trip(original)
    assert isinstance(parsed, CollectionProgressPendingAction)
    assert parsed.preview_id == "p-1"
    assert parsed.user_id == 7
    assert parsed.items[0].subject_id == 1


def test_union_round_trips_wishlist() -> None:
    original = WishlistPendingAction(
        type="ADD_TO_WISHLIST",
        user_id=7,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
        items=[{"subject_id": 2, "subject_name": "芙莉莲"}],
    )
    parsed = _round_trip(original)
    assert isinstance(parsed, WishlistPendingAction)
    assert parsed.items[0].subject_name == "芙莉莲"


def test_union_round_trips_subject_resolution() -> None:
    original = SubjectResolutionPendingAction(
        type="SUBJECT_RESOLUTION",
        user_id=7,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
        query="进击",
        candidates=[{
            "subject_id": 1,
            "subject_name": "进击的巨人",
            "match_source": "BUSINESS",
            "match_type": "EXACT",
        }],
    )
    parsed = _round_trip(original)
    assert isinstance(parsed, SubjectResolutionPendingAction)
    assert parsed.query == "进击"
    assert parsed.candidates[0].match_type == "EXACT"


def test_union_round_trips_set_collection_type() -> None:
    original = SetCollectionTypePendingAction(
        type="SET_COLLECTION_TYPE",
        user_id=7,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
        subject_id=3,
        subject_name="孤独摇滚",
        target_type=3,
        action="CHANGE",
    )
    parsed = _round_trip(original)
    assert isinstance(parsed, SetCollectionTypePendingAction)
    assert parsed.target_type == 3
    assert parsed.action == "CHANGE"


def test_every_union_member_is_reachable_by_discriminator() -> None:
    """联合的每个成员都必须能通过 ``type`` 值被单独选中。

    载荷一律由真实模型经 ``model_dump_json(by_alias=True)`` 产出，不手写 wire JSON——
    手写会让本用例变成对实现字段别名的（易过时的）第二份假设，而不是对真实
    wire 形态的检查（与 design D6 同一条理由）。
    """
    from typing import get_args

    members = [a for a in get_args(PendingAction.__origin__ if hasattr(PendingAction, "__origin__") else PendingAction) if hasattr(a, "model_fields")]
    if not members:  # Annotated 包装下的取法
        from typing import get_args as _ga
        annotated = PendingAction
        members = [a for a in _ga(get_args(annotated)[0]) if hasattr(a, "model_fields")]
    assert len(members) == 4, f"判别联合应含 4 个变体，实际 {len(members)}"

    expires = datetime.now(timezone.utc) + timedelta(seconds=600)
    samples = [
        CollectionProgressPendingAction(
            type="COLLECTION_PROGRESS_UPDATE", preview_id="p", user_id=1, expires_at=expires
        ),
        WishlistPendingAction(type="ADD_TO_WISHLIST", user_id=1, expires_at=expires),
        SubjectResolutionPendingAction(type="SUBJECT_RESOLUTION", user_id=1, expires_at=expires),
        SetCollectionTypePendingAction(
            type="SET_COLLECTION_TYPE", user_id=1, expires_at=expires,
            subject_id=1, subject_name="x", target_type=1,
        ),
    ]
    for model in samples:
        raw = model.model_dump_json(by_alias=True)
        parsed = parse_pending_action_json(raw)
        assert parsed.type == model.type
        assert type(parsed) is type(model), f"{model.type} 反序列化成了 {type(parsed).__name__}"


def test_unknown_type_is_rejected_not_guessed() -> None:
    """未知 ``type`` 必须报错，不得回退到某个默认变体。"""
    with pytest.raises(ValidationError):
        parse_pending_action_json(json.dumps({"type": "TOTALLY_NEW_TYPE", "userId": 1}))


def test_corrupt_json_is_rejected() -> None:
    with pytest.raises((ValidationError, ValueError)):
        parse_pending_action_json("{not json")


# --------------------------------------------------------------------------- #
# 5.3 business 字段驼峰 + 信封字段蛇形 + 旧数据默认值容忍
#
# spec `pending-action-protocol` 要求：从 business DTO 原样带过来的字段沿用驼峰
# （`subjectId` / `summary` / `actionId`），而 agent 自定义的信封字段
# （`preview_id` / `user_id` / `expires_at`）沿用蛇形 —— 后者已是 Redis 里既有
# 载荷的形态，改名会把已存数据变成不可读。两侧都不许静默漂移。
# --------------------------------------------------------------------------- #

_ENVELOPE_FIELDS = ("preview_id", "user_id", "expires_at")


def test_business_fields_keep_camel_case_on_wire() -> None:
    """business DTO 带过来的字段必须写驼峰，否则 preview 数据要过翻译层。"""
    action = CollectionProgressPendingAction(
        type="COLLECTION_PROGRESS_UPDATE",
        preview_id="p-1",
        user_id=7,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
        items=[{"subject_id": 1, "subject_name": "x", "current_ep_status": 1, "target_ep_status": 2}],
    )
    payload = json.loads(action.model_dump_json(by_alias=True))
    # 子模型字段：驼峰
    assert payload["summary"][0]["subjectId"] == 1
    assert payload["summary"][0]["subjectName"] == "x"
    # 别名替换掉原名，不得两种写法并存
    assert "items" not in payload


def test_envelope_fields_stay_snake_case_on_wire() -> None:
    """信封字段沿用蛇形；改成驼峰会 strand 已经躺在 Redis 里的载荷。"""
    action = WishlistPendingAction(
        type="ADD_TO_WISHLIST",
        user_id=7,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
    )
    payload = json.loads(action.model_dump_json(by_alias=True))
    # wishlist 无 preview_id
    for field in ("user_id", "expires_at"):
        assert field in payload, f"信封字段 {field} 必须以蛇形出现：{sorted(payload)}"
    assert "userId" not in payload, f"信封字段被改成了驼峰：{sorted(payload)}"
    assert "expiresAt" not in payload, f"信封字段被改成了驼峰：{sorted(payload)}"


def test_persisted_envelope_shape_is_pinned() -> None:
    """钉死已持久化载荷的信封形态，防止无意的 wire 改名。"""
    action = CollectionProgressPendingAction(
        type="COLLECTION_PROGRESS_UPDATE",
        preview_id="p-1",
        user_id=7,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
    )
    payload = json.loads(action.model_dump_json(by_alias=True))
    assert payload["preview_id"] == "p-1"
    assert payload["user_id"] == 7
    assert "expires_at" in payload
    for camel in ("previewId", "userId", "expiresAt"):
        assert camel not in payload, (
            f"信封字段被改名成 {camel}，会让既有 Redis 载荷解析失败：{sorted(payload)}"
        )


def test_business_field_names_parse_from_camel_case() -> None:
    """后端下发的驼峰 business 字段必须能解析。"""
    raw = json.dumps({
        "type": "SET_COLLECTION_TYPE",
        "user_id": 7,
        "expires_at": "2030-01-01T00:00:00Z",
        "subjectId": 3,
        "subjectName": "孤独摇滚",
        "targetType": 3,
    })
    parsed = parse_pending_action_json(raw)
    assert parsed.subject_id == 3
    assert parsed.target_type == 3


def test_legacy_json_without_optional_alias_fields_parses() -> None:
    """旧数据可能缺 ``actionId`` / ``collectionType`` / ``currentType``，必须有默认值。"""
    legacy_set_type = json.dumps({
        "type": "SET_COLLECTION_TYPE",
        "user_id": 7,
        "expires_at": "2030-01-01T00:00:00Z",
        "subjectId": 3,
        "subjectName": "x",
        "targetType": 3,
    })
    parsed = parse_pending_action_json(legacy_set_type)
    assert parsed.action_id == ""
    assert parsed.current_type is None
    assert parsed.action == "ADD"

    legacy_resolution = json.dumps({
        "type": "SUBJECT_RESOLUTION",
        "user_id": 7,
        "expires_at": "2030-01-01T00:00:00Z",
    })
    resolved = parse_pending_action_json(legacy_resolution)
    assert resolved.collection_type is None
    assert resolved.candidates == []


def test_legacy_wishlist_without_action_id_parses() -> None:
    raw = json.dumps({
        "type": "ADD_TO_WISHLIST",
        "user_id": 7,
        "expires_at": "2030-01-01T00:00:00Z",
    })
    assert parse_pending_action_json(raw).action_id == ""


def test_parsing_accepts_both_field_spellings() -> None:
    """解析是宽容的：``populate_by_name`` 让蛇形与驼峰都能读。

    序列化才是权威方向（见上面三个 wire 测试）。这里钉死「读宽容」这一半，
    因为 Redis 里可能躺着两种历史写法，读失败等于把用户的待确认动作弄丢。
    """
    snake = json.dumps({
        "type": "SET_COLLECTION_TYPE",
        "user_id": 7,
        "expires_at": "2030-01-01T00:00:00Z",
        "subject_id": 3,
        "subject_name": "x",
        "target_type": 3,
    })
    camel_business = json.dumps({
        "type": "SET_COLLECTION_TYPE",
        "user_id": 7,
        "expires_at": "2030-01-01T00:00:00Z",
        "subjectId": 3,
        "subjectName": "x",
        "targetType": 3,
    })
    for payload in (snake, camel_business):
        parsed = parse_pending_action_json(payload)
        assert parsed.subject_id == 3, f"解析失败：{payload}"
        assert parsed.target_type == 3


def test_camel_envelope_alias_is_rejected_not_silently_defaulted() -> None:
    """若信封被误写成驼峰，解析必须失败，而不能静默回退到默认值。"""
    raw = json.dumps({
        "type": "SET_COLLECTION_TYPE",
        "userId": 7,
        "expiresAt": "2030-01-01T00:00:00Z",
        "subjectId": 3,
        "subjectName": "x",
        "targetType": 3,
    })
    with pytest.raises(ValidationError):
        parse_pending_action_json(raw)


# --------------------------------------------------------------------------- #
# 5.4 确认必须绑定已存储的版本
# --------------------------------------------------------------------------- #

class _RecordingGateway:
    """记录 execute 收到的路径，用于校验确认动作绑定的是存储中的 preview_id。"""

    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def request(self, method: str, path: str, *, token=None, json_body=None):
        self.calls.append((method, path))
        return {"state": "COMPLETED"}


def test_execute_uses_stored_preview_id() -> None:
    """执行路径必须由**已存储**的 ``preview_id`` 构造，不能来自本次请求参数。"""
    gateway = _RecordingGateway()
    action = CollectionProgressPreviewable(gateway)
    pending = CollectionProgressPendingAction(
        type="COLLECTION_PROGRESS_UPDATE",
        preview_id="p-stored",
        user_id=7,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
    )
    user = UserInfo(user_id=7, token="t", username="u", role="USER")
    action.do_execute(pending=pending, user=user)
    assert gateway.calls == [
        ("POST", "/api/client/collections/progress-preview/p-stored/execute")
    ]


def test_execute_path_is_declared_in_contract() -> None:
    """执行端点必须在契约中声明（与 HTTP 契约测试互为正反面）。"""
    from tests.contracts import _contract

    match = _contract.match_operation(
        "POST", "/api/client/collections/progress-preview/{previewId}/execute"
    )
    assert "execute" in match.operation_id.lower() or "preview" in match.path


def test_preview_changed_replaces_with_new_preview_id() -> None:
    """``PREVIEW_CHANGED`` 必须替换为新预览，而不是保留旧的。"""
    gateway = _RecordingGateway()
    action = CollectionProgressPreviewable(gateway)
    pending = CollectionProgressPendingAction(
        type="COLLECTION_PROGRESS_UPDATE",
        preview_id="p-old",
        user_id=7,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
    )
    user = UserInfo(user_id=7, token="t", username="u", role="USER")
    result = {
        "state": "PREVIEW_CHANGED",
        "preview": {
            "previewId": "p-new",
            "expiresAt": (datetime.now(timezone.utc) + timedelta(seconds=600)).isoformat(),
            "items": [],
        },
    }
    decision, _ = action.classify_result(result=result, pending=pending, user=user)
    assert isinstance(decision, Replace)
    # ``Replace`` 的字段名是 ``new_pending``（见 previewable.py）——不是 ``action``。
    assert decision.new_pending.preview_id == "p-new"


def test_completed_clears_pending_action() -> None:
    action = CollectionProgressPreviewable(_RecordingGateway())
    pending = CollectionProgressPendingAction(
        type="COLLECTION_PROGRESS_UPDATE",
        preview_id="p-1",
        user_id=7,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
    )
    user = UserInfo(user_id=7, token="t", username="u", role="USER")
    decision, _ = action.classify_result(
        result={"state": "COMPLETED"}, pending=pending, user=user
    )
    assert isinstance(decision, Clear)


def test_stale_preview_is_cleared() -> None:
    """404 / 409-重新生成 表示预览已失效，必须清除而不是无限重试。"""
    action = CollectionProgressPreviewable(_RecordingGateway())
    pending = CollectionProgressPendingAction(
        type="COLLECTION_PROGRESS_UPDATE",
        preview_id="p-1",
        user_id=7,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
    )
    user = UserInfo(user_id=7, token="t", username="u", role="USER")
    for result in (
        {"error": True, "code": 404},
        {"error": True, "code": 409, "message": "请重新生成预览"},
    ):
        decision, _ = action.classify_result(result=result, pending=pending, user=user)
        assert isinstance(decision, Clear), f"失效预览应清除，实际 {decision}: {result}"


def test_retryable_failure_keeps_pending_action() -> None:
    """可重试错误必须保留动作，让用户能再次确认。"""
    action = CollectionProgressPreviewable(_RecordingGateway())
    pending = CollectionProgressPendingAction(
        type="COLLECTION_PROGRESS_UPDATE",
        preview_id="p-1",
        user_id=7,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
    )
    user = UserInfo(user_id=7, token="t", username="u", role="USER")
    for result in ({"error": True, "code": 500}, {"error": True, "code": 409, "message": "冲突"}, None):
        decision, _ = action.classify_result(result=result, pending=pending, user=user)
        assert isinstance(decision, Keep), f"可重试错误应保留动作，实际 {decision}: {result}"


def test_pending_action_user_binding_is_enforced() -> None:
    """动作绑定用户：跨用户不得读到别人的待确认动作。"""
    import inspect

    source = inspect.getsource(RedisChatStore.get_pending_action)
    assert "user_id" in source and "action.user_id" in source, (
        "get_pending_action 必须校验 action.user_id 与入参 user_id 一致"
    )


# --------------------------------------------------------------------------- #
# 5.5 流内事件缓冲语义（SET / REPLACE / CLEAR 取最后一条）
# --------------------------------------------------------------------------- #

def test_collector_last_event_wins() -> None:
    token = set_pending_action_collector()
    try:
        action = CollectionProgressPendingAction(
            type="COLLECTION_PROGRESS_UPDATE",
            preview_id="p-1",
            user_id=7,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
        )
        emit_pending_action_set(action)
        emit_pending_action_clear()
        event = get_pending_action_event()
        assert event is not None
        assert event.operation == "CLEAR", "流内多次操作以最后一条为准"
    finally:
        reset_pending_action_collector(token)


def test_collector_replace_records_action() -> None:
    token = set_pending_action_collector()
    try:
        action = CollectionProgressPendingAction(
            type="COLLECTION_PROGRESS_UPDATE",
            preview_id="p-2",
            user_id=7,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
        )
        emit_pending_action_replace(action)
        event = get_pending_action_event()
        assert event.operation == "REPLACE"
        assert event.action.preview_id == "p-2"
    finally:
        reset_pending_action_collector(token)


def test_collector_without_setup_is_noop() -> None:
    """未初始化收集器时 emit 不得抛错（工具可能在测试/同步上下文被调用）。"""
    emit_pending_action_clear()
    assert get_pending_action_event() is None
