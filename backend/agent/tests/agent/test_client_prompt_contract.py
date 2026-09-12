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


def test_recommend_prompt_preserves_structured_constraints() -> None:
    content = (PROMPT_DIR / "recommend_agent_prompt.md").read_text(encoding="utf-8")

    assert "年份、季度、最低评分、最低评分人数或播出状态" in content
    assert "不得在重试或改写语义查询时丢失这些条件" in content
