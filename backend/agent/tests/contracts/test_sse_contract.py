"""SSE wire 契约：把序列化器的实际输出与契约 ``SSEFrame`` 双向对齐。

对应 spec ``agent-stream-wire-contract``。与既有 ``tests/api/test_sse_serialization.py``
的分工：那个文件锁定**行为**（某一类事件应序列化成什么），本文件锁定**契约一致性**
（序列化器的取值域与字段集必须与 ``docs/spec/openapi.yaml`` 声明的一致）。

双向比较是刻意的：既能发现「契约忘了新类型」，也能发现「序列化器发明了契约不认识的字段」。
"""

from __future__ import annotations

import json

import pytest

from app.api.schemas.sse import AssistantResponse, Content, MessageType, serialize_sse
from app.api.sse import serialize_agent_event
from app.chat.streaming import StreamConfig, stream_agent_events
from app.chat.events import AgentEvent, AgentEventType
from tests.contracts import _contract
from tests.contracts._contract import resolve_ref

STREAM_PATHS = ("/api/admin/agent/chat/stream", "/api/client/agent/stream")


def _frame_schema() -> dict:
    """从契约里取单帧 schema（``SSEFrame``）。"""
    return _contract.schemas()["SSEFrame"]


def _payload(frame: str) -> dict:
    """剥离 ``data: `` 前缀并解析 JSON，同时校验分帧形态。"""
    assert frame.startswith("data: "), f"帧必须以 'data: ' 开头: {frame!r}"
    assert frame.endswith("\n\n"), f"帧必须以后跟空行结束: {frame!r}"
    return json.loads(frame[len("data: "):-2])


def _sample_events() -> list[AgentEvent]:
    """为每个 ``AgentEventType`` 造一个带载荷的代表性事件。"""
    return [
        AgentEvent(type=AgentEventType.ANSWER, text="你好"),
        AgentEvent(type=AgentEventType.THINKING, text="思考中"),
        AgentEvent(
            type=AgentEventType.FUNCTION_CALL,
            node="tool:search",
            parent_node="agent",
            state="end",
            result="success",
            name="搜索番剧",
            arguments='{"query": "进击"}',
            message="搜索番剧调用成功",
        ),
        AgentEvent(type=AgentEventType.STATUS, state="running", message="处理中"),
        AgentEvent(type=AgentEventType.END),
    ]


# --------------------------------------------------------------------------- #
# 4.1 类型取值域封闭，且不含 `end`
# --------------------------------------------------------------------------- #

def test_contract_type_enum_has_no_end() -> None:
    """``end`` 不是 wire 类型——结束以 ``is_end`` 表达。"""
    enum = _frame_schema()["properties"]["type"]["enum"]
    assert "end" not in enum, f"契约 type 枚举不得包含 'end'：{enum}"
    assert set(enum) == {"answer", "thinking", "function_call", "status"}


def test_observed_types_are_subset_of_contract_enum() -> None:
    """序列化器实际产出的每个 type 都必须在契约枚举内。"""
    enum = set(_frame_schema()["properties"]["type"]["enum"])
    observed: set[str] = set()
    for event in _sample_events():
        payload = _payload(serialize_agent_event(event))
        observed.add(payload["type"])
    undeclared = observed - enum
    assert not undeclared, f"序列化器产出了契约未声明的 type：{sorted(undeclared)}"


def test_all_serializable_event_types_are_covered() -> None:
    """双向：``AgentEventType``（去掉内部 END）必须与契约枚举一一对应。"""
    enum = set(_frame_schema()["properties"]["type"]["enum"])
    wire_types = {member.value for member in AgentEventType} - {AgentEventType.END.value}
    assert wire_types == enum, (
        f"契约枚举 {sorted(enum)} 与实现取值域 {sorted(wire_types)} 不一致——"
        "任一侧新增类型都会在此失败"
    )


def test_message_type_matches_agent_event_type() -> None:
    """wire 枚举 ``MessageType`` 与内部 ``AgentEventType``（去 END）必须同步。"""
    message_types = {member.value for member in MessageType}
    enum = set(_frame_schema()["properties"]["type"]["enum"])
    assert message_types == enum


# --------------------------------------------------------------------------- #
# 4.2 帧字段集
# --------------------------------------------------------------------------- #

def test_every_frame_carries_required_fields() -> None:
    required = set(_frame_schema()["required"])
    for event in _sample_events():
        payload = _payload(serialize_agent_event(event))
        missing = required - set(payload)
        assert not missing, f"{event.type} 帧缺少契约声明必填字段 {sorted(missing)}：{payload}"


def test_timestamp_is_integer() -> None:
    for event in _sample_events():
        payload = _payload(serialize_agent_event(event))
        assert isinstance(payload["timestamp"], int), (
            f"{event.type} 帧的 timestamp 不是整数：{payload.get('timestamp')!r}"
        )


def test_absent_optional_content_fields_are_omitted() -> None:
    """空值必须被剔除，不能以 null 出现。"""
    payload = _payload(serialize_agent_event(AgentEvent(type=AgentEventType.ANSWER, text="只有文本")))
    assert "text" in payload["content"]
    for absent in ("state", "message", "result", "name", "arguments", "node", "parent_node"):
        assert absent not in payload["content"], (
            f"未赋值的 {absent!r} 不应出现在 content 中：{payload['content']}"
        )
    assert None not in payload["content"].values()


def test_observed_content_keys_are_subset_of_contract() -> None:
    declared = set(_frame_schema()["properties"]["content"]["properties"])
    observed: set[str] = set()
    for event in _sample_events():
        observed |= set(_payload(serialize_agent_event(event))["content"])
    unexpected = observed - declared
    assert not unexpected, f"序列化器产出了契约未声明的 content 子字段：{sorted(unexpected)}"


def test_undeclared_content_key_is_named() -> None:
    """负向演练：契约外的新字段必须被指名报出。"""
    declared = set(_frame_schema()["properties"]["content"]["properties"])
    rogue = "definitelyNotAContentField"
    assert rogue not in declared
    with pytest.raises(AssertionError) as excinfo:
        assert not {rogue}, f"序列化器产出了契约未声明的 content 子字段：{[rogue]}"
    assert rogue in str(excinfo.value)


def test_contract_content_properties_match_implementation() -> None:
    """双向：``Content`` 模型的字段集与契约 content 子字段集必须一致。"""
    declared = set(_frame_schema()["properties"]["content"]["properties"])
    implemented = set(Content.model_fields)
    assert declared == implemented, (
        f"契约 content 字段 {sorted(declared)} 与模型字段 {sorted(implemented)} 不一致"
    )


# --------------------------------------------------------------------------- #
# 4.3 分帧形态
# --------------------------------------------------------------------------- #

def test_frame_shape_is_single_data_line() -> None:
    for event in _sample_events():
        frame = serialize_agent_event(event)
        assert frame.startswith("data: ")
        assert frame.endswith("\n\n")
        body = frame[len("data: "):-2]
        assert "\n" not in body, f"载荷必须单行，实际含换行：{body!r}"
        assert isinstance(json.loads(body), dict)
        assert not frame.startswith("event:"), "不得使用 SSE event: 字段"


def test_frame_contains_exactly_one_json_object() -> None:
    frame = serialize_agent_event(AgentEvent(type=AgentEventType.ANSWER, text="a\nb\tc"))
    payload = _payload(frame)
    assert payload["content"]["text"] == "a\nb\tc", "换行等特殊字符必须转义在 JSON 内"


# --------------------------------------------------------------------------- #
# 4.4 错误表达的两种约定
# --------------------------------------------------------------------------- #

def test_tool_failure_uses_function_call_with_end_state() -> None:
    """工具失败 = ``function_call`` + ``state=end`` + ``result=error``。"""
    event = AgentEvent(
        type=AgentEventType.FUNCTION_CALL,
        node="tool:search",
        state="end",
        result="error",
        name="搜索番剧",
        message="搜索番剧调用失败",
    )
    payload = _payload(serialize_agent_event(event))
    assert payload["type"] == "function_call"
    assert payload["content"]["state"] == "end"
    assert payload["content"]["result"] == "error"


def test_persistence_failure_uses_status_with_error_state() -> None:
    """持久化失败 = ``status`` + ``state=error`` + 非空 message。"""
    event = AgentEvent(
        type=AgentEventType.STATUS,
        state="error",
        message="回答保存失败，请稍后重试",
    )
    payload = _payload(serialize_agent_event(event))
    assert payload["type"] == "status"
    assert payload["content"]["state"] == "error"
    assert payload["content"]["message"].strip()


def test_state_error_only_on_status_frames() -> None:
    """``state=error`` 只允许出现在 ``status`` 帧上，不得混入工具帧。"""
    tool_frames = [
        AgentEvent(type=AgentEventType.FUNCTION_CALL, state="end", result="error", name="x"),
        AgentEvent(type=AgentEventType.FUNCTION_CALL, state="end", result="success", name="x"),
    ]
    for event in tool_frames:
        payload = _payload(serialize_agent_event(event))
        assert payload["content"].get("state") != "error", (
            f"工具帧不得使用 state=error：{payload}"
        )


def test_status_error_does_not_claim_success() -> None:
    """``status`` 报错时不得同时声明成功。"""
    event = AgentEvent(type=AgentEventType.STATUS, state="error", message="失败",
                       meta={"persistence": "answer", "success": False})
    payload = _payload(serialize_agent_event(event))
    assert payload["content"]["state"] == "error"
    assert payload["content"].get("result") != "success"


# --------------------------------------------------------------------------- #
# 4.5 恰好一个收尾帧
# --------------------------------------------------------------------------- #

class _FakeWorkflow:
    """驱动真实 ``stream_agent_events`` 的最小工作流替身。

    ``stream_agent_events`` 本身是流的唯一收尾责任人（``finally`` 前唯一一处
    ``yield END``），所以这里必须走真实生成器而不是自造循环，否则测试只是在
    验证自己写的假生产者。
    """

    def __init__(self, chunks: list[dict] | None = None, *, raise_after: int | None = None):
        self._chunks = chunks or []
        self._raise_after = raise_after

    async def astream(self, _state, stream_mode=None):
        for index, chunk in enumerate(self._chunks):
            if self._raise_after is not None and index == self._raise_after:
                raise RuntimeError("工作流中途失败")
            yield "values", chunk


def _config(workflow) -> StreamConfig:
    return StreamConfig(
        workflow=workflow,
        build_initial_state=lambda: {"messages": []},
    )


async def _stream(config: StreamConfig) -> list[dict]:
    """跑真实生成器，逐帧解析。"""
    frames: list[dict] = []
    async for event in stream_agent_events(config):
        frames.append(_payload(serialize_agent_event(event)))
    return frames


@pytest.mark.asyncio
async def test_normal_completion_has_exactly_one_end_frame() -> None:
    workflow = _FakeWorkflow([{"messages": []}])
    frames = await _stream(_config(workflow))
    ends = [i for i, f in enumerate(frames) if f["is_end"]]
    assert len(ends) == 1, f"应恰好一个 is_end 帧，实际 {len(ends)}"
    assert ends[0] == len(frames) - 1, "is_end 帧必须是最后一帧"


@pytest.mark.asyncio
async def test_end_frame_is_emitted_even_without_answer() -> None:
    """空流也必须收尾。"""
    frames = await _stream(_config(_FakeWorkflow([{"messages": []}])))
    assert sum(1 for f in frames if f["is_end"]) == 1


@pytest.mark.asyncio
async def test_workflow_error_still_terminates_once() -> None:
    """工作流抛错时，真实生成器必须仍产出唯一收尾帧。"""
    workflow = _FakeWorkflow([{"messages": []}, {"messages": []}], raise_after=1)
    frames = await _stream(_config(workflow))
    ends = [i for i, f in enumerate(frames) if f["is_end"]]
    assert len(ends) == 1, f"错误路径应恰好一个 is_end 帧，实际 {len(ends)}"
    assert ends[0] == len(frames) - 1


@pytest.mark.asyncio
async def test_persistence_error_still_terminates_once() -> None:
    """持久化失败时追加 status 错误帧，且仍只有一个收尾帧。"""

    def boom(_answer: str, _tools: list[str]) -> None:
        raise RuntimeError("写库失败")

    config = StreamConfig(
        workflow=_FakeWorkflow([{"messages": []}]),
        build_initial_state=lambda: {"messages": []},
        on_answer_completed=boom,
    )
    frames = await _stream(config)
    ends = [i for i, f in enumerate(frames) if f["is_end"]]
    assert len(ends) == 1
    assert ends[0] == len(frames) - 1
    status_errors = [
        f for f in frames if f["type"] == "status" and f["content"].get("state") == "error"
    ]
    assert status_errors, "持久化失败应产出 status/error 帧"
    assert status_errors[0]["content"]["message"].strip()


@pytest.mark.asyncio
async def test_missing_terminating_frame_is_detectable() -> None:
    """负向演练：构造一个确实漏发 END 的生成器，证明断言能变红。"""

    async def broken():
        yield AgentEvent(type=AgentEventType.ANSWER, text="答案")

    frames = [_payload(serialize_agent_event(e)) async for e in broken()]
    ends = [i for i, f in enumerate(frames) if f["is_end"]]
    assert len(ends) != 1, "此断言证明「缺少收尾帧」是可检出的"


# --------------------------------------------------------------------------- #
# 4.6 契约声明了 stream 响应
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("path", STREAM_PATHS)
def test_stream_operation_declares_event_stream(path: str) -> None:
    match = _contract.match_operation("POST", path)
    content = (match.operation.get("responses") or {}).get("200", {}).get("content") or {}
    assert "text/event-stream" in content, f"{match.operation_id} 未声明 text/event-stream"


@pytest.mark.parametrize("path", STREAM_PATHS)
def test_stream_operation_references_single_frame_schema(path: str) -> None:
    match = _contract.match_operation("POST", path)
    content = match.operation["responses"]["200"]["content"]
    schema = content["text/event-stream"]["schema"]
    ref = schema.get("$ref")
    assert ref, f"{match.operation_id} 响应 schema 未引用单帧 schema：{schema}"
    resolved = resolve_ref(ref)
    assert resolved is _frame_schema() or resolved == _frame_schema()


@pytest.mark.parametrize("path", STREAM_PATHS)
def test_stream_operation_describes_framing(path: str) -> None:
    match = _contract.match_operation("POST", path)
    description = match.operation.get("description") or ""
    assert "空行" in description, f"{match.operation_id} 未说明空行分帧"
    assert "`event:`" in description, f"{match.operation_id} 未说明不使用 event: 字段"


@pytest.mark.parametrize("path", STREAM_PATHS)
def test_stream_request_body_is_chat_request(path: str) -> None:
    match = _contract.match_operation("POST", path)
    schema = match.operation["requestBody"]["content"]["application/json"]["schema"]
    assert schema.get("$ref") == "#/components/schemas/ChatRequest"
    chat = _contract.schemas()["ChatRequest"]
    assert set(chat["properties"]) == {"session_id", "content"}
    assert set(chat["required"]) == {"session_id", "content"}
