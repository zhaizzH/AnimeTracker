from pathlib import Path


PROMPT_DIR = Path(__file__).resolve().parents[2] / "resources" / "prompt" / "client"
DOMAIN_PROMPTS = {
    "search_agent_prompt.md": "rag_search_subjects",
    "discover_agent_prompt.md": "rag_discover_subjects",
    "recommend_agent_prompt.md": "rag_recommend_subjects",
}


def test_domain_prompts_require_simplified_chinese_reasoning() -> None:
    for filename in DOMAIN_PROMPTS:
        content = (PROMPT_DIR / filename).read_text(encoding="utf-8")

        assert "语言约束（最高优先级）" in content
        assert "第一个 reasoning token 开始使用简体中文" in content


def test_domain_prompts_report_registered_rag_capability() -> None:
    for filename, tool_name in DOMAIN_PROMPTS.items():
        content = (PROMPT_DIR / filename).read_text(encoding="utf-8")

        assert "具备 AnimeTracker 的 RAG 检索能力" in content
        assert tool_name in content
        assert "不得回答“没有 RAG”" in content
        assert "不要猜测或声称当前功能开关状态" in content


def test_domain_prompts_document_request_navigation() -> None:
    for filename in DOMAIN_PROMPTS:
        content = (PROMPT_DIR / filename).read_text(encoding="utf-8")

        assert "request_navigation" in content
        assert "open_anime_index" in content
        assert "严禁编造" in content

def test_recommend_prompt_preserves_structured_constraints() -> None:
    content = (PROMPT_DIR / "recommend_agent_prompt.md").read_text(encoding="utf-8")

    assert "年份、季度、最低评分、最低评分人数或播出状态" in content
    assert "不得在重试或改写语义查询时丢失这些条件" in content

def test_recommend_prompt_requires_navigation_after_write_completes() -> None:
    """复合指令（design D4）：先写后导航，预览/取消/过期/error 时不得导航。"""
    content = (PROMPT_DIR / "recommend_agent_prompt.md").read_text(encoding="utf-8")

    assert "复合指令：写入后跳转" in content
    assert "严格先完成写入，再调用 `request_navigation`" in content
    assert "预览阶段、等待用户确认时，不得调用 `request_navigation`" in content
    assert "用户取消、否定，或待确认动作已过期时，不得调用 `request_navigation`" in content
    assert "多候选标题场景下，须等「选中 → 预览 → 确认」全部完成后才可调用" in content
    assert "写入工具返回 error 时，不得调用 `request_navigation`" in content
    assert "一次回合最多调用一次 `request_navigation`" in content

def test_search_and_discover_prompts_do_not_carry_write_gate_rules() -> None:
    """search / discover 没有写工具，不需要复合指令规则。"""
    for filename in ("search_agent_prompt.md", "discover_agent_prompt.md"):
        content = (PROMPT_DIR / filename).read_text(encoding="utf-8")

        assert "复合指令：写入后跳转" not in content
