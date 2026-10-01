"""``_resolve_routing_result``：gateway 结构化路由结果的解析与失败语义。

既有 gateway 测试只覆盖 ``build_gateway_router`` 的确定性分支（``write_confirmed``、
``_resolve_forced_pending_route``、``_is_explicit_confirmation``），且一律以
``llm_factory=None`` 绕过 LLM。本文件补齐 ``_resolve_routing_result`` 本身的判定：
非法输入必须抛 ``ValueError``，不得静默回退到某个默认路由。
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.agent.client.gateway import _ALLOWED_TARGETS, _resolve_routing_result

def _message(content):
    """构造 ``extract_text`` 可读的消息替身（读 ``.content``）。"""
    return SimpleNamespace(content=content)

def _payload(*, content, messages: int = 1) -> dict:
    return {"messages": [_message(content) for _ in range(messages)]}

# --------------------------------------------------------------------------- #
# 合法输入
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("target", _ALLOWED_TARGETS)
def test_valid_route_target_is_returned(target: str) -> None:
    raw = _payload(content=f'{{"route_target": "{target}"}}')
    assert _resolve_routing_result(raw) == {"route_target": target}

def test_uses_last_message_when_history_present() -> None:
    raw = {
        "messages": [
            _message('{"route_target": "search_agent"}'),
            _message('{"route_target": "recommend_agent"}'),
        ]
    }
    assert _resolve_routing_result(raw)["route_target"] == "recommend_agent"

def test_content_block_list_is_flattened_by_extract_text() -> None:
    """部分模型返回 content 块列表而非裸字符串。"""
    raw = _payload(content=[{"type": "text", "text": '{"route_target": "discover_agent"}'}])
    assert _resolve_routing_result(raw)["route_target"] == "discover_agent"

# --------------------------------------------------------------------------- #
# 非法输入：必须抛 ValueError（fail-closed）
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        (None, "非 mapping"),
        ("not-a-dict", "非 mapping"),
        ([], "非 mapping"),
    ],
)
def test_non_mapping_payload_raises(raw, reason: str) -> None:
    with pytest.raises(ValueError, match="must be a mapping"):
        _resolve_routing_result(raw)

@pytest.mark.parametrize("raw", [{}, {"messages": []}, {"messages": None}])
def test_empty_messages_raises(raw) -> None:
    with pytest.raises(ValueError, match="messages cannot be empty"):
        _resolve_routing_result(raw)

@pytest.mark.parametrize("blank", ["", "   ", "\n"])
def test_blank_last_message_content_raises(blank: str) -> None:
    with pytest.raises(ValueError, match="content is empty"):
        _resolve_routing_result(_payload(content=blank))

def test_non_text_content_block_raises_as_empty() -> None:
    """content 块列表无 text 项时 extract_text 返回空串。"""
    with pytest.raises(ValueError, match="content is empty"):
        _resolve_routing_result(_payload(content=[{"type": "image", "url": "x"}]))

@pytest.mark.parametrize("bad_json", ["not json", '{"route_target": ', "[]extra"])
def test_invalid_json_raises(bad_json: str) -> None:
    with pytest.raises(ValueError, match="invalid JSON"):
        _resolve_routing_result(_payload(content=bad_json))

@pytest.mark.parametrize(
    "target",
    ["", "   ", "search", "SEARCH_AGENT", "admin_agent", "'; DROP TABLE"],
)
def test_unsupported_route_target_raises(target: str) -> None:
    with pytest.raises(ValueError, match="unsupported route_target"):
        _resolve_routing_result(_payload(content=f'{{"route_target": "{target}"}}'))

def test_surrounding_whitespace_is_tolerated() -> None:
    """值在合法目标上时前后空白被 strip，不视为非法。"""
    raw = _payload(content='{"route_target": "  search_agent  "}')
    assert _resolve_routing_result(raw) == {"route_target": "search_agent"}

@pytest.mark.parametrize("body", ["{}", '{"route_target": null}', '{"other": "x"}'])
def test_missing_route_target_raises(body: str) -> None:
    with pytest.raises(ValueError, match="unsupported route_target"):
        _resolve_routing_result(_payload(content=body))

@pytest.mark.xfail(
    reason="已知缺陷：JSON 为标量/数组时 `data.get` 抛 AttributeError 而非 ValueError（见 T-gateway-scalar-json）",
    raises=AttributeError,
    strict=True,
)
@pytest.mark.parametrize("content", ['"x"', "123", "true", '["a"]'])
def test_scalar_or_array_json_should_raise_value_error(content: str) -> None:
    """JSON 合法但非对象 → 应归入非法 route_target 语义，而非 AttributeError。

    当前实现直接对 ``data`` 调 ``.get``；``data`` 为 str/int/bool/list 时抛
    ``AttributeError``，不是 ``ValueError`` 子类，调用方按 ``ValueError`` 捕获会漏掉。
    生产代码修复后本用例转为通过断言（去掉 xfail 标记）。
    """
    with pytest.raises(ValueError, match="unsupported route_target"):
        _resolve_routing_result(_payload(content=content))

def test_allowed_targets_is_the_frozen_contract() -> None:
    assert _ALLOWED_TARGETS == ("search_agent", "discover_agent", "recommend_agent")
