from pathlib import Path

from app.agent.dependencies import AgentDependencies
from app.agent.client import discover, recommend, search


ROOT = Path(__file__).resolve().parents[1]


class FakeBusiness:
    pass


class FakeRetrieval:
    pass


def _dependencies():
    return AgentDependencies(business=FakeBusiness(), retrieval=FakeRetrieval())


def _registered_names(monkeypatch, module, factory):
    captured = {}

    def fake_run_domain_agent(state, **kwargs):
        captured.update(kwargs)
        return captured

    monkeypatch.setattr(module, "run_domain_agent", fake_run_domain_agent)
    return [item.name for item in factory(_dependencies())({})["tools"]]


def test_domains_register_real_rag_candidate_tools(monkeypatch):
    assert "rag_search_subjects" in _registered_names(monkeypatch, search, search.build_search_agent)
    discover_names = _registered_names(monkeypatch, discover, discover.build_discover_agent)
    assert "rag_discover_subjects" in discover_names
    assert "get_schedule" in discover_names
    assert "rag_recommend_subjects" in _registered_names(monkeypatch, recommend, recommend.build_recommend_agent)


def test_managed_prompts_only_describe_registered_rag_candidates():
    search_prompt = (ROOT / "resources/prompt/client/search_agent_prompt.md").read_text(encoding="utf-8")
    discover_prompt = (ROOT / "resources/prompt/client/discover_agent_prompt.md").read_text(encoding="utf-8")
    recommend_prompt = (ROOT / "resources/prompt/client/recommend_agent_prompt.md").read_text(encoding="utf-8")

    assert "get_tags" not in search_prompt and "rag_search_subjects" in search_prompt
    assert "rag_discover_subjects" in discover_prompt and "get_schedule" in discover_prompt
    assert "rag_recommend_subjects" in recommend_prompt
    assert "get_season_subjects" not in recommend_prompt
    for prompt in (search_prompt, discover_prompt, recommend_prompt):
        assert "subjectId" in prompt


def test_candidate_domains_do_not_expose_unhydrated_candidate_tools(monkeypatch):
    search_names = _registered_names(monkeypatch, search, search.build_search_agent)
    discover_names = _registered_names(monkeypatch, discover, discover.build_discover_agent)

    assert "search_subjects" not in search_names
    assert "get_subjects_by_tag" not in search_names
    assert "get_season_subjects" not in discover_names
    assert "get_popular_subjects" not in discover_names
    assert "get_top_rated" not in discover_names
