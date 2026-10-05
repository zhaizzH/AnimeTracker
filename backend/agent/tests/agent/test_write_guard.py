from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.agent.client.actions.write_guard import require_confirmed_write
from app.agent.client.gateway import build_gateway_router
from app.chat.pending_action import (
    SetCollectionTypePendingAction,
    WishlistPendingAction,
    WishlistPendingItem,
)
from app.chat.user import UserInfo


_USER = UserInfo(user_id=2, username="t", role="USER", token="tok")


def _action(*, user_id=2, expires_in=600, type_="SET_COLLECTION_TYPE"):
    expires = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    if type_ == "SET_COLLECTION_TYPE":
        return SetCollectionTypePendingAction(
            type="SET_COLLECTION_TYPE", user_id=user_id, expires_at=expires,
            subject_id=84, subject_name="X", target_type=3, current_type=None, action="ADD",
        )
    return WishlistPendingAction(
        type="ADD_TO_WISHLIST", user_id=user_id, expires_at=expires,
        items=[WishlistPendingItem(subject_id=84, subject_name="X")],
    )


# --------------------------------------------------------------------------- #
# require_confirmed_write（要求已确认写入）
# --------------------------------------------------------------------------- #

def test_guard_passes_when_all_conditions_met() -> None:
    assert require_confirmed_write(
        user=_USER, pending=_action(), expected_type="SET_COLLECTION_TYPE", write_confirmed=True
    ) is None


def test_guard_rejects_missing_user() -> None:
    assert require_confirmed_write(
        user=None, pending=_action(), expected_type="SET_COLLECTION_TYPE", write_confirmed=True
    )["error"] is True


def test_guard_rejects_missing_or_wrong_type_action() -> None:
    assert require_confirmed_write(
        user=_USER, pending=None, expected_type="SET_COLLECTION_TYPE", write_confirmed=True
    )["error"] is True
    assert require_confirmed_write(
        user=_USER, pending=_action(type_="ADD_TO_WISHLIST"),
        expected_type="SET_COLLECTION_TYPE", write_confirmed=True
    )["error"] is True


def test_guard_rejects_other_user() -> None:
    assert require_confirmed_write(
        user=_USER, pending=_action(user_id=999),
        expected_type="SET_COLLECTION_TYPE", write_confirmed=True
    )["error"] is True


def test_guard_rejects_expired() -> None:
    assert require_confirmed_write(
        user=_USER, pending=_action(expires_in=-10),
        expected_type="SET_COLLECTION_TYPE", write_confirmed=True
    )["error"] is True


def test_guard_rejects_unconfirmed_turn() -> None:
    result = require_confirmed_write(
        user=_USER, pending=_action(), expected_type="SET_COLLECTION_TYPE", write_confirmed=False
    )
    assert result["error"] is True
    assert "确认" in result["message"]


# --------------------------------------------------------------------------- #
# gateway 设置 write_confirmed（确定性分支，不触发 LLM）
# --------------------------------------------------------------------------- #

def _router():
    return build_gateway_router(SimpleNamespace(llm_factory=None, prompt_repository=None))


def test_gateway_sets_write_confirmed_true_on_explicit_confirmation() -> None:
    router = _router()
    state = {"pending_action": _action(type_="ADD_TO_WISHLIST"), "current_question": "确认"}
    out = router(state)
    assert out["routing"]["route_target"] == "recommend_agent"
    assert out["write_confirmed"] is True


def test_gateway_write_confirmed_false_on_write_intent_that_is_not_confirmation() -> None:
    router = _router()
    # 明确写入意图（非确认词）→ 路由 recommend_agent，但 write_confirmed=False
    state = {"pending_action": None, "current_question": "把某番加入想看"}
    out = router(state)
    assert out["routing"]["route_target"] == "recommend_agent"
    assert out["write_confirmed"] is False
