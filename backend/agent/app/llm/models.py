import json
import logging

from langchain_community.chat_models.tongyi import ChatTongyi

logger = logging.getLogger(__name__)


def _patch_chat_tongyi():
    """修复 langchain-community ChatTongyi 流式 delta 合并问题。"""
    _orig = ChatTongyi.subtract_client_response

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

    _patched_subtract.__name__ = "patched_subtract_client_response"
    ChatTongyi.subtract_client_response = _patched_subtract
    logger.info("已应用 chatongyi 流式 delta 合并补丁")


_patch_chat_tongyi()


def create_llm(*, model: str, temperature: float, api_key: str, max_tokens: int) -> ChatTongyi:
    model_kwargs: dict = {"temperature": temperature, "max_tokens": max_tokens}
    if model.startswith("qwen3"):
        # qwen3 系列默认不输出思考,需显式开启;qwen-plus 等不支持该参数
        model_kwargs["enable_thinking"] = True
    return ChatTongyi(
        model=model,
        api_key=api_key,
        streaming=True,
        model_kwargs=model_kwargs,
    )
