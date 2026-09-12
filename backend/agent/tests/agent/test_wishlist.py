from app.agent.client.actions.wishlist import build_wishlist_tools
from app.chat.pending_events import (
    get_pending_action_event,
    reset_pending_action_collector,
    set_pending_action_collector,
)
from app.chat.user import UserInfo


class _Business:
    def request(self, method, path, *, token=None, params=None, json_body=None):
        assert method == "GET"
        assert path.endswith("/collections/84")
        return None


def test_empty_collection_response_creates_pending_item() -> None:
    preview = build_wishlist_tools(_Business())[0]
    user = UserInfo(user_id=2, username="tester", role="USER", token="token")
    collector_token = set_pending_action_collector()
    try:
        result = preview.func(subjects=[{"subjectId": 84, "subjectName": "测试动画"}], user=user)
        pending = get_pending_action_event()
    finally:
        reset_pending_action_collector(collector_token)

    assert result["pendingItems"] == [{"subjectId": 84, "subjectName": "测试动画"}]
    assert result["skippedItems"] == []
    assert pending is not None
    assert pending.action is not None
    assert [item.subject_id for item in pending.action.items] == [84]
