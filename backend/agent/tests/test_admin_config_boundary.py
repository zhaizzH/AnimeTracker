import ast
from pathlib import Path
import json


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


def test_model_config_repository_preserves_redis_key_json_and_refresh_cache(monkeypatch):
    from app.adapters.redis import model_config_repository as module

    class FakeRedis:
        def __init__(self):
            self.value = '{"model":"first"}'
            self.get_keys = []
            self.set_calls = []

        def get(self, key):
            self.get_keys.append(key)
            return self.value

        def set(self, key, value):
            self.set_calls.append((key, value))

    redis = FakeRedis()
    times = iter((10.0, 11.0, 16.1))
    monkeypatch.setattr(module.time, "monotonic", lambda: next(times))
    repository = module.RedisModelConfigRepository("redis://contract")
    monkeypatch.setattr(repository, "_redis", lambda: redis)

    assert repository.get() == {"model": "first"}
    redis.value = '{"model":"second"}'
    assert repository.get() == {"model": "first"}
    assert repository.get() == {"model": "second"}
    repository.set({"model": "third", "temperature": 0.2})

    assert redis.get_keys == [module.MODEL_CONFIG_KEY, module.MODEL_CONFIG_KEY]
    assert redis.set_calls == [(module.MODEL_CONFIG_KEY, '{"model": "third", "temperature": 0.2}')]
    assert json.loads(redis.set_calls[0][1]) == {"model": "third", "temperature": 0.2}
