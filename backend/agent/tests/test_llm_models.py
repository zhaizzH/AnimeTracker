from app.adapters.llm.agent_factory import create_llm

def test_deepseek_llm_sets_reasoning_effort_and_thinking():
    llm = create_llm(
        provider="deepseek", model="deepseek-v4-pro",
        temperature=0.3, api_key="k", max_tokens=4096,
        reasoning_effort="high",
    )
    assert llm.reasoning_effort == "high"
    # thinking 通过 extra_body 显式开启（BaseChatOpenAI 原生字段）
    assert llm.extra_body == {"thinking": {"type": "enabled"}}

def test_deepseek_llm_default_effort_high():
    llm = create_llm(provider="deepseek", model="deepseek-v4-flash",
                     temperature=0.3, api_key="k", max_tokens=4096)
    assert llm.reasoning_effort == "high"

def test_dashscope_qwen3_enables_thinking():
    llm = create_llm(provider="dashscope", model="qwen3.7-plus",
                     temperature=0.3, api_key="k", max_tokens=4096,
                     thinking_budget=2048)
    assert llm.model_kwargs.get("enable_thinking") is True
    assert llm.model_kwargs.get("thinking_budget") == 2048
