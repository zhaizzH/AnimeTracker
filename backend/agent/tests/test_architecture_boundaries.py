import ast
from pathlib import Path


ROOT = Path(__file__).parents[1]
PURE_ROOTS = (ROOT / "app/chat", ROOT / "app/agent", ROOT / "app/rag", ROOT / "app/admin")
FORBIDDEN_EXTERNALS = {"fastapi", "redis", "httpx", "subprocess"}


def imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


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
