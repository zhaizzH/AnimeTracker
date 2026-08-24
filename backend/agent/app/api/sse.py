from collections.abc import AsyncIterator

from fastapi.responses import StreamingResponse

from app.api.schemas.sse import AssistantResponse, Content, MessageType, serialize_sse
from app.chat.events import AgentEvent, AgentEventType


def serialize_agent_event(event: AgentEvent) -> str:
    if event.type is AgentEventType.END:
        return serialize_sse(AssistantResponse(content=Content(), is_end=True))
    return serialize_sse(AssistantResponse(
        type=MessageType(event.type.value),
        content=Content(
            text=event.text,
            node=event.node,
            parent_node=event.parent_node,
            state=event.state,
            message=event.message,
            result=event.result,
            name=event.name,
            arguments=event.arguments,
        ),
        meta=event.meta or None,
    ))


def create_sse_response(events: AsyncIterator[AgentEvent]) -> StreamingResponse:
    async def body():
        async for event in events:
            yield serialize_agent_event(event)

    return StreamingResponse(
        body(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
