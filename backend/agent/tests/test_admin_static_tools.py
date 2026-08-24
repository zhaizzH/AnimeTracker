from pathlib import Path

from app.agent.dependencies import AgentDependencies


ROOT = Path(__file__).resolve().parents[1]


class FakeBusiness:
    pass


class FakeRetrieval:
    pass


class FakeLlmFactory:
    @property
    def provider(self):
        return "deepseek"

    def create(self, *_args, **_kwargs):
        raise AssertionError("admin static tool tests must not create LLMs")


class FakePromptRepository:
    def list_keys(self):
        return ()

    def get(self, *_args, **_kwargs):
        return ""

    def set(self, *_args, **_kwargs):
        pass

    def reset(self, *_args, **_kwargs):
        return ""


class FakeImportService:
    def run(self, *_args, **_kwargs):
        pass


def _dependencies():
    return AgentDependencies(
        business=FakeBusiness(),
        retrieval=FakeRetrieval(),
        llm_factory=FakeLlmFactory(),
        prompt_repository=FakePromptRepository(),
        import_service=FakeImportService(),
    )


def _decoded_name(codepoints: tuple[int, ...]) -> str:
    return "".join(chr(point) for point in codepoints)


def test_admin_tools_are_static_and_expose_expected_names():
    from app.agent.admin.tools import build_admin_tools

    names = [tool.name for tool in build_admin_tools(_dependencies())]
    forbidden_names = {
        _decoded_name((26597, 30475, 21487, 21152, 36733, 24037, 30446, 24405, 24405)),
        _decoded_name((21152, 36733, 31649, 29702, 24037, 20855)),
    }

    assert names == [
        "get_current_time",
        "trigger_recent_import",
        "search_subjects",
        "get_subject_detail",
        "get_episodes",
        "get_subjects_by_tag",
        "get_schedule",
        "get_season_subjects",
        "get_popular_subjects",
        "get_top_rated",
        "get_stats",
    ]
    assert forbidden_names.isdisjoint(names)


def test_admin_agent_passes_static_tool_tuple_without_copy(monkeypatch):
    from app.agent.admin import agent_node

    sentinel_tools = ("alpha", "beta")
    captured = {}

    def fake_build_admin_tools(_dependencies):
        return sentinel_tools

    def fake_run_domain_agent(state, **kwargs):
        captured.update(kwargs)
        return captured

    monkeypatch.setattr(agent_node, "build_admin_tools", fake_build_admin_tools)
    monkeypatch.setattr(agent_node, "run_domain_agent", fake_run_domain_agent)

    agent_node.build_admin_agent(_dependencies())({})

    assert captured["tools"] is sentinel_tools


def test_admin_tools_module_does_not_import_client_or_dynamic_tool_modules():
    source = (ROOT / "app/agent/admin/tools.py").read_text(encoding="utf-8")

    assert "app.agent.client" not in source
    assert "app.core.dynamic_tool" not in source


def test_tool_status_middleware_lives_in_agent_layer():
    from app.agent import run

    assert run.build_tool_status_middleware.__module__ == "app.agent.middleware"


def test_dynamic_tool_framework_file_is_removed():
    assert not (ROOT / "app/core/dynamic_tool.py").exists()
