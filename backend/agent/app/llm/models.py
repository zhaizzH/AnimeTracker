import json
import logging

from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import AIMessageChunk
from langchain_openai import ChatOpenAI

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
    logger.info("已应用 opencode reasoning_content 增量捕获补丁")


_patch_chat_openai_reasoning()


# opencode-go 网关模型→端点归属;表外/新增模型默认走 chat/completions,加一行即可
_ANTHROPIC_ENDPOINT_MODELS = {
    "minimax-m3", "minimax-m2.7", "minimax-m2.5",
    "qwen3.8-max", "qwen3.7-max", "qwen3.7-plus", "qwen3.6-plus", "qwen3.5-plus",
}
_RESPONSES_ENDPOINT_MODELS = {"gpt-5.6-luna"}


def create_opencode_llm(*, model: str, temperature: float, max_tokens: int):
    # 延迟导入避免循环: config -> models
    from app.config import settings

    base = settings.opencode_base_url
    if model in _ANTHROPIC_ENDPOINT_MODELS:
        # anthropic SDK 会在 base_url 后追加 /v1/messages,故需去掉末尾 /v1
        anthropic_url = base.rstrip("/").removesuffix("/v1")
        return ChatAnthropic(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            anthropic_api_key=settings.opencode_api_key,
            anthropic_api_url=anthropic_url,
        )
    # chat/completions 与 responses 共用 ChatOpenAI,openai SDK 自行追加 /chat/completions 或 /responses
    return ChatOpenAI(
        model_name=model,
        max_tokens=max_tokens,
        temperature=temperature,
        openai_api_key=settings.opencode_api_key,
        openai_api_base=base,
        use_responses_api=model in _RESPONSES_ENDPOINT_MODELS,
    )


def create_llm(*, model: str, temperature: float, api_key: str, max_tokens: int,
               thinking_budget: int = 2048):
    if model.startswith("opencode-go/"):
        # provider 优先:opencode 模型一律不进 ChatTongyi 分支,避免 qwen3.8-max 误带 enable_thinking
        return create_opencode_llm(
            model=model.removeprefix("opencode-go/"),
            temperature=temperature,
            max_tokens=max_tokens,
        )
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
