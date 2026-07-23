import json
import logging
from langchain_community.chat_models.tongyi import ChatTongyi

logger = logging.getLogger(__name__)


def _patch_chat_tongyi():
    """修复 langchain-community ChatTongyi 流式 delta 合并问题。
    如果上游修复可移除此 monkey-patch。"""
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
    logger.info("已应用chatongyi monkey-用于流式delta合并的补丁")


def create_llm(settings):
    """创建并返回 ChatTongyi 实例（已应用 monkey-patch）"""
    _patch_chat_tongyi()
    return ChatTongyi(
        model=settings.llm_model,
        api_key=settings.dashscope_api_key,
        streaming=True,
        model_kwargs={
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
        },
    )
