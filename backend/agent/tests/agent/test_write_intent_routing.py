from datetime import datetime, timedelta, timezone

from app.agent.client.gateway import (
    _is_explicit_recommendation_request,
    _resolve_forced_pending_route,
)
from app.chat.pending_action import (
    SetCollectionTypePendingAction,
    SubjectResolutionCandidate,
    SubjectResolutionPendingAction,
)


def test_write_intent_phrases_route_to_recommend() -> None:
    for text in (
        "把相反的你和我第二季添加到我的追番",
        "把这部加入在看",
        "标记为看过",
        "把X设为搁置",
        "改成抛弃",
        "把X标记为想看",
    ):
        assert _is_explicit_recommendation_request(text), text


def test_negated_write_intent_is_not_triggered() -> None:
    assert not _is_explicit_recommendation_request("不要加入追番")
    assert not _is_explicit_recommendation_request("别标记为看过")
    assert not _is_explicit_recommendation_request("取消添加到在看")


def test_query_intents_are_not_mistaken_for_writes() -> None:
    # 只提到“追番/在看/收藏”字样、但没有写入动词短语的查询不得被误触发
    for text in (
        "我的追番进度怎么样了",
        "查一下追番日程",
        "我在看什么",
        "我收藏了哪些番剧",
        "看看这周的更新",
        "搜索科幻动画",
    ):
        assert not _is_explicit_recommendation_request(text), text


def _set_action():
    return SetCollectionTypePendingAction(
        type="SET_COLLECTION_TYPE", user_id=2,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
        subject_id=84, subject_name="X", target_type=3, current_type=None, action="ADD",
    )


def test_confirmation_forced_route_for_set_collection_type() -> None:
    state = {"pending_action": _set_action(), "current_question": "确认"}
    assert _resolve_forced_pending_route(state) == {"routing": {"route_target": "recommend_agent"}}


def test_non_confirmation_not_forced_for_set_collection_type() -> None:
    state = {"pending_action": _set_action(), "current_question": "换个番吧"}
    assert _resolve_forced_pending_route(state) is None


def test_resolution_state_with_collection_type_still_routes() -> None:
    pending = SubjectResolutionPendingAction(
        type="SUBJECT_RESOLUTION", user_id=2,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=600),
        query="物语", collection_type=3,
        candidates=[SubjectResolutionCandidate(subject_id=1, subject_name="A", match_source="BUSINESS", match_type="CANDIDATE")],
    )
    state = {"pending_action": pending, "current_question": "1"}
    assert _resolve_forced_pending_route(state) == {"routing": {"route_target": "recommend_agent"}}
