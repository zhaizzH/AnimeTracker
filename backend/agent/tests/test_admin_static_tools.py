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


def _dependencies():
    return AgentDependencies(
        business=FakeBusiness(),
        retrieval=FakeRetrieval(),
        llm_factory=FakeLlmFactory(),
        prompt_repository=FakePromptRepository(),
    )


def test_admin_tools_are_static_and_expose_expected_names():
    from app.agent.admin.tools import build_admin_tools

    names = [tool.name for tool in build_admin_tools(_dependencies())]

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
    assert "查看可加载工具目录" not in names
    assert "加载管理工具" not in names


def test_admin_tools_module_does_not_import_client_or_dynamic_tool_modules():
    source = (ROOT / "app/agent/admin/tools.py").read_text(encoding="utf-8")

    assert "app.agent.client" not in source
    assert "app.core.dynamic_tool" not in source


def test_tool_status_middleware_lives_in_agent_layer():
    from app.agent import run

    assert run.build_tool_status_middleware.__module__ == "app.agent.middleware"


def test_dynamic_tool_framework_file_is_removed():
    assert not (ROOT / "app/core/dynamic_tool.py").exists()
