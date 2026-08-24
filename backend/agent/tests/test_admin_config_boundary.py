import ast
from pathlib import Path


def imported_modules(path: str) -> set[str]:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    result = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
    return result


def test_static_config_does_not_depend_on_runtime_repository():
    imports = imported_modules("app/config.py")
    assert "app.core.runtime_config" not in imports
    assert "app.llm.models" not in imports


def test_admin_api_does_not_construct_redis_client():
    source = Path("app/api/admin_config.py").read_text(encoding="utf-8")
    assert "Redis.from_url" not in source
    assert "redis_lib" not in source
