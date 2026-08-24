from app.agent.admin.import_tool import build_trigger_recent_import_tool
from app.agent.dependencies import AgentDependencies
from app.agent.time_tool import get_current_time
from app.agent.tools import build_subject_catalog_tools


def build_admin_tools(dependencies: AgentDependencies) -> tuple:
    return (
        get_current_time,
        build_trigger_recent_import_tool(dependencies.import_service),
        *build_subject_catalog_tools(dependencies.business),
    )
