"""`navigation_emitter`：纯函数把 NavigationIntent 翻译成 path + label 并发 ui_action（design D3/D4）。"""
from types import SimpleNamespace

import pytest

from app.chat.event_sink import reset_event_sink, set_event_sink
from app.chat.events import AgentEvent, AgentEventType

from app.agent.navigation_emitter import build_navigation_emitter

class _Collector:
    def __init__(self) -> None:
        self.events: list[AgentEvent] = []

    def emit(self, event: AgentEvent) -> None:
        self.events.append(event)

@pytest.fixture
def collector():
    sink = _Collector()
    token = set_event_sink(sink)
    try:
        yield sink
    finally:
        reset_event_sink(token)

class _Business:
    def __init__(self, detail=None) -> None:
        self.detail = detail

    def request(self, method, path, *, params=None, token=None, json_body=None):  # noqa: ANN001, ANN201
        assert method == "GET"
        assert path == "/api/client/subjects/84"
        return self.detail

def _run(intent: dict, *, detail=None) -> tuple[dict, list[AgentEvent]]:
    sink = _Collector()
    token = set_event_sink(sink)
    try:
        emitter = build_navigation_emitter(SimpleNamespace(business=_Business(detail)))
        result = emitter({"navigation_intent": intent})
    finally:
        reset_event_sink(token)
    return result, sink.events

def _single_action(intent: dict, *, detail=None) -> AgentEvent:
    result, events = _run(intent, detail=detail)
    assert result == {"navigation_intent": None}
    assert len(events) == 1
    assert events[0].type is AgentEventType.UI_ACTION
    return events[0]

def test_empty_intent_emits_nothing() -> None:
    result, events = _run(None)

    assert result == {}
    assert events == []

def test_open_profile_maps_to_profile_page() -> None:
    event = _single_action({"action": "open_profile", "params": {}})

    assert event.meta == {"action": "open_profile", "params": {}, "path": "/profile", "label": "「个人中心」"}

def test_open_anime_index_builds_query_and_skips_defaults() -> None:
    event = _single_action({
        "action": "open_anime_index",
        "params": {"q": "孤独摇滚", "sort": "score", "order": "desc", "page": 1},
    })

    assert event.meta["path"] == "/anime?q=%E5%AD%A4%E7%8B%AC%E6%91%87%E6%BB%9A"
    assert event.meta["label"] == "「番剧索引」 · 「孤独摇滚」"

def test_open_anime_index_keeps_non_default_filters() -> None:
    event = _single_action({
        "action": "open_anime_index",
        "params": {"year": 2022, "weekday": 3, "sort": "rank", "order": "asc", "page": 2},
    })

    assert event.meta["path"] == "/anime?page=2&sort=rank&order=asc&year=2022&weekday=3"
    assert event.meta["label"] == "「番剧索引」 · 2022 年"

def test_open_anime_index_tags_become_repeated_tag_keys() -> None:
    event = _single_action({"action": "open_anime_index", "params": {"tags": ["科幻", "治愈"]}})

    assert event.meta["path"] == "/anime?tag=%E7%A7%91%E5%B9%BB&tag=%E6%B2%BB%E6%84%88"

def test_open_schedule_maps_year_quarter_tab() -> None:
    event = _single_action({"action": "open_schedule", "params": {"year": 2022, "quarter": "spring", "tab": "1"}})

    assert event.meta["path"] == "/schedule?year=2022&quarter=spring&tab=1"
    assert event.meta["label"] == "「追番日程」 · 2022 年 · 春季"

def test_open_collections_skips_default_tab_but_labels_non_default() -> None:
    default = _single_action({"action": "open_collections", "params": {"tab": "all", "page": 1}})
    non_default = _single_action({"action": "open_collections", "params": {"tab": "3"}})

    assert default.meta["path"] == "/my-collections"
    assert default.meta["label"] == "「我的收藏」"
    assert non_default.meta["path"] == "/my-collections?tab=3"
    assert non_default.meta["label"] == "「我的收藏」 · 在看"

def test_open_subject_uses_looked_up_name() -> None:
    event = _single_action(
        {"action": "open_subject", "params": {"subject_id": 84}},
        detail={"id": 84, "name": "孤独摇滚！"},
    )

    assert event.meta["path"] == "/subject/84"
    assert event.meta["label"] == "「孤独摇滚！」"

def test_open_subject_lookup_failure_emits_nothing_but_clears_intent() -> None:
    for detail in ({"error": True}, None, "boom"):
        result, events = _run({"action": "open_subject", "params": {"subject_id": 84}}, detail=detail)

        assert result == {"navigation_intent": None}
        assert events == []

def test_unknown_action_in_handwritten_state_emits_nothing_but_clears_intent() -> None:
    """工具已白名单校验，但手写 state 仍可能塞入白名单外 action：不发事件、不残留 intent。"""
    # 正向基线：同一入口喂合法 action 必须发事件，否则下面的「没发事件」可能只是入口没通
    _, baseline = _run({"action": "open_profile", "params": {}})
    assert [e.type for e in baseline] == [AgentEventType.UI_ACTION]

    result, events = _run({"action": "open_admin_panel", "params": {}})

    assert result == {"navigation_intent": None}
    assert events == []

def test_emitter_never_emits_answer_text() -> None:
    _, events = _run({"action": "open_profile", "params": {}})

    assert [e.type for e in events] == [AgentEventType.UI_ACTION]
    assert all(e.text is None for e in events)
