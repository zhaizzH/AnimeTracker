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


def _package_parts(path: Path) -> list[str]:
    relative = path.relative_to(ROOT)
    if relative.name == "__init__.py":
        return list(relative.parent.parts)
    return list(relative.parent.parts)


def _resolve_import_from(path: Path, node: ast.ImportFrom) -> str | None:
    if node.level == 0:
        return node.module
    package = _package_parts(path)
    keep = len(package) - node.level + 1
    if keep < 0:
        return None
    parts = package[:keep]
    if node.module:
        parts.extend(node.module.split("."))
    return ".".join(parts) if parts else None


def imports_from_source(path: Path, source: str) -> set[str]:
    tree = ast.parse(source)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = _resolve_import_from(path, node)
            if module:
                names.add(module)
                names.update(f"{module}.{alias.name}" for alias in node.names if alias.name != "*")
    return names


def imports(path: Path) -> set[str]:
    return imports_from_source(path, path.read_text(encoding="utf-8"))


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


def _imported_layer(name: str) -> str | None:
    parts = name.split(".")
    if parts[0] == "jobs":
        return "jobs"
    if len(parts) >= 2 and parts[0] == "app" and parts[1] in APP_LAYERS:
        return parts[1]
    return None


def dependency_direction_failures(path: Path, names: set[str]) -> list[str]:
    source = _source_layer(path)
    if source is None:
        return []
    allowed = ALLOWED_APP_IMPORTS[source]
    failures = []
    for name in names:
        target = _imported_layer(name)
        if source == "jobs" and target == "jobs":
            continue
        if target is not None and target not in allowed:
            if any(other != name and other.startswith(f"{name}.") for other in names):
                continue
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


def test_relative_import_to_forbidden_layer_is_canonicalized_and_rejected():
    path = ROOT / "app/api/probe.py"
    names = imports_from_source(path, "from ..adapters import business_http\n")

    assert "app.adapters.business_http" in names
    assert dependency_direction_failures(path, names) == ["app/api/probe.py -> app.adapters.business_http"]


def test_app_layers_reject_absolute_and_relative_imports_of_jobs():
    path = ROOT / "app/adapters/probe.py"

    absolute = imports_from_source(path, "from jobs.importer import db\n")
    relative = imports_from_source(path, "from ...jobs.importer import db\n")

    expected = ["app/adapters/probe.py -> jobs.importer.db"]
    assert dependency_direction_failures(path, absolute) == expected
    assert dependency_direction_failures(path, relative) == expected


def test_jobs_can_import_other_jobs_modules():
    failures = dependency_direction_failures(
        ROOT / "jobs/importer/probe.py",
        {"jobs.importer.db"},
    )

    assert failures == []


def test_same_package_relative_import_is_canonicalized_and_allowed():
    path = ROOT / "app/api/probe.py"
    names = imports_from_source(path, "from .schemas import chat\n")

    assert "app.api.schemas.chat" in names
    assert dependency_direction_failures(path, names) == []


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
