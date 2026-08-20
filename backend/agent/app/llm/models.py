import json
import logging
from typing import Literal

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import AIMessageChunk
from langchain_deepseek import ChatDeepSeek

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


def _patch_chat_openai_reasoning():
    """langchain-openai 丢弃 OpenAI 兼容流式响应里的 reasoning_content,补丁把它存入 additional_kwargs。"""
    from langchain_openai.chat_models import base as _lc_base

    _orig = _lc_base._convert_delta_to_message_chunk

    def _patched(delta, default_class):
        chunk = _orig(delta, default_class)
        reasoning = delta.get("reasoning_content")
        if reasoning and isinstance(chunk, AIMessageChunk):
            ak = dict(chunk.additional_kwargs or {})
            ak["reasoning_content"] = reasoning
            chunk.additional_kwargs = ak
        return chunk

    _patched.__name__ = "patched_convert_delta_to_message_chunk"
    _lc_base._convert_delta_to_message_chunk = _patched
    logger.info("已应用 deepseek reasoning_content 增量捕获补丁")


_patch_chat_openai_reasoning()


def create_llm(*, provider: Literal["deepseek", "dashscope"], model: str, temperature: float,
               api_key: str, max_tokens: int, base_url: str | None = None,
               thinking_budget: int = 2048, reasoning_effort: str = "high"):
    """按已解析的 provider 创建对应供应商客户端。DeepSeek 显式开启思考；百炼 qwen3 显式开启 enable_thinking。"""
    if provider == "deepseek":
        # base_url=None 时不传,让 BaseChatOpenAI 用默认地址(显式传 None 会触发校验失败)
        deepseek_kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "api_key": api_key,
            "reasoning_effort": reasoning_effort,
            "extra_body": {"thinking": {"type": "enabled"}},
        }
        if base_url:
            deepseek_kwargs["base_url"] = base_url
        return ChatDeepSeek(**deepseek_kwargs)
    model_kwargs: dict = {"temperature": temperature, "max_tokens": max_tokens}
    if model.startswith("qwen3"):
        # qwen3 系列默认不输出思考,需显式开启;qwen-plus 等不支持该参数
        model_kwargs["enable_thinking"] = True
        # 限制思考长度,否则会一直想到 max_tokens,响应明显变慢
        if thinking_budget:
            model_kwargs["thinking_budget"] = thinking_budget
    return ChatTongyi(
        model=model,
        api_key=api_key,
        streaming=True,
        model_kwargs=model_kwargs,
    )
