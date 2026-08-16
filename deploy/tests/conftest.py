"""部署契约测试共享 fixtures。

``compose_config`` 合并 compose.yml 与 compose.prod.yml(浅合并 service 键,
environment 字典按 compose 语义逐键覆盖);``nginx_template`` 返回新的
client-next 代理模板原文。PyYAML 由 backend/agent/requirements.txt 提供。
"""

from pathlib import Path

import pytest

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[2]


def _load_yaml(relative: str) -> dict:
    path = ROOT / relative
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _merge_service(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if key == "environment" and isinstance(value, dict):
            env = dict(merged.get("environment") or {})
            env.update(value)
            merged[key] = env
        else:
            merged[key] = value
    return merged


@pytest.fixture(scope="session")
def compose_config() -> dict:
    """合并 compose.yml 与 compose.prod.yml 后的解析配置。"""
    if yaml is None:
        pytest.skip("需要 PyYAML 才能解析 compose 配置")
    merged = _load_yaml("compose.yml")
    services = merged.setdefault("services", {})
    for name, override in (_load_yaml("compose.prod.yml").get("services") or {}).items():
        services[name] = _merge_service(services.get(name, {}), override)
    return merged


@pytest.fixture(scope="session")
def nginx_template() -> str:
    """新的 client-next Nginx 代理模板原文。"""
    return (ROOT / "deploy/nginx/client-next.conf.template").read_text(encoding="utf-8")
