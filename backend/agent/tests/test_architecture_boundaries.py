import ast
from pathlib import Path


ROOT = Path(__file__).parents[1]
PURE_ROOTS = (ROOT / "app/chat", ROOT / "app/agent", ROOT / "app/rag", ROOT / "app/admin")
FORBIDDEN_EXTERNALS = {"fastapi", "redis", "httpx", "subprocess"}
APP_LAYERS = {"api", "chat", "agent", "rag", "admin", "adapters", "shared", "config"}
ALLOWED_APP_IMPORTS = {
    "api": {"api", "chat", "admin", "config", "shared"},
    "chat": {"chat", "shared"},
    "agent": {"agent", "chat", "admin", "rag", "shared"},
    "rag": {"rag", "shared"},
    "admin": {"admin"},
    "shared": {"shared"},
    "config": {"config"},
    "adapters": {"adapters", "agent", "admin", "chat", "rag", "shared", "config"},
    "jobs": {"rag", "adapters", "shared"},
    "main": APP_LAYERS,
}


def imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names if alias.name != "*")
    return names


def _source_layer(path: Path) -> str | None:
    relative = path.relative_to(ROOT)
    parts = relative.parts
    if parts[0] == "main.py":
        return "main"
    if parts[0] == "jobs":
        return "jobs"
    if parts[:2] == ("app", "config.py"):
        return "config"
    if len(parts) >= 3 and parts[0] == "app" and parts[1] in APP_LAYERS:
        return parts[1]
    return None


def _imported_app_layer(name: str) -> str | None:
    parts = name.split(".")
    if len(parts) < 2 or parts[0] != "app":
        return None
    if parts[1] in APP_LAYERS:
        return parts[1]
    return None


def dependency_direction_failures(path: Path, names: set[str]) -> list[str]:
    source = _source_layer(path)
    if source is None:
        return []
    allowed = ALLOWED_APP_IMPORTS[source]
    failures = []
    for name in names:
        target = _imported_app_layer(name)
        if target is not None and target not in allowed:
            failures.append(f"{path.relative_to(ROOT)} -> {name}")
    return sorted(failures)


def test_imports_canonicalizes_from_app_import_adapters(tmp_path):
    path = tmp_path / "probe.py"
    path.write_text("from app import adapters\n", encoding="utf-8")

    assert "app.adapters" in imports(path)


def test_dependency_direction_rejects_api_to_adapter_import():
    failures = dependency_direction_failures(
        ROOT / "app/api/probe.py",
        {"app.adapters.business_http"},
    )

    assert failures == ["app/api/probe.py -> app.adapters.business_http"]


def test_app_dependency_directions_follow_layering_plan():
    failures = []
    for root in (ROOT / "app", ROOT / "jobs"):
        for path in root.rglob("*.py"):
            failures.extend(dependency_direction_failures(path, imports(path)))
    failures.extend(dependency_direction_failures(ROOT / "main.py", imports(ROOT / "main.py")))

    assert failures == []


def test_use_cases_and_agent_do_not_import_transport_or_adapters():
    failures = []
    for root in PURE_ROOTS:
        for path in root.rglob("*.py"):
            for name in imports(path):
                top = name.split(".", 1)[0]
                if top in FORBIDDEN_EXTERNALS or name.startswith("app.adapters"):
                    failures.append(f"{path.relative_to(ROOT)} -> {name}")
    assert failures == []


def test_api_does_not_import_external_infrastructure():
    failures = []
    for path in (ROOT / "app/api").rglob("*.py"):
        for name in imports(path):
            if name.split(".", 1)[0] in {"redis", "httpx", "subprocess"}:
                failures.append(f"{path.relative_to(ROOT)} -> {name}")
    assert failures == []


def test_removed_catch_all_packages_do_not_return():
    for relative in ("app/core", "app/db", "app/service", "app/llm", "app/utils", "app/schemas"):
        path = ROOT / relative
        assert not path.exists() or not any(path.rglob("*.py"))
