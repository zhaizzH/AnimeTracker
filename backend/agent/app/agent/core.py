import json
from langchain.agents import create_agent
from langchain_community.chat_models.tongyi import ChatTongyi
from app.config import settings
from app.agent.tools import tools
from app.agent.prompt import SYSTEM_PROMPT

# 马尾辫: monkey-patch ChatTongyi.subtract_client_response处理
# 流deltas，其中prev_function缺少 “name” 键。
# langchain中的Bug-社区0.4.2，可以在上游修复时删除。
_orig_subtract = ChatTongyi.subtract_client_response


def _patched_subtract(self, resp, prev_resp):
    resp_copy = json.loads(json.dumps(resp))
    choice = resp_copy["output"]["choices"][0]
    message = choice["message"]
    prev_copy = json.loads(json.dumps(prev_resp))
    prev_message = prev_copy["output"]["choices"][0]["message"]
    message["content"] = message["content"].replace(prev_message["content"], "")
    if message.get("tool_calls") and prev_message.get("tool_calls"):
        for i, tc in enumerate(message["tool_calls"]):
            fn = tc["function"]
            prev_fn = prev_message["tool_calls"][i]["function"]
            if "name" in fn and "name" in prev_fn:
                fn["name"] = fn["name"].replace(prev_fn["name"], "")
            if "arguments" in fn and "arguments" in prev_fn:
                fn["arguments"] = fn["arguments"].replace(prev_fn["arguments"], "")
    return resp_copy


ChatTongyi.subtract_client_response = _patched_subtract


def create_agent_executor():
    llm = ChatTongyi(
        model=settings.llm_model,
        api_key=settings.dashscope_api_key,
        streaming=True,
        model_kwargs={
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
        },
    )

    return create_agent(model=llm, tools=tools, system_prompt=SYSTEM_PROMPT)
