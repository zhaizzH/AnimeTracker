"""OpenAPI 契约的加载、路径模板匹配与 ``$ref`` 解析。

本模块是契约测试的共用底座，只做「读契约 + 结构化比对」，不复制任何运行时代码逻辑。

设计依据（见 ``design.md``）：

- **D3**：路径按段结构匹配，字面量优先于通配符。契约用 ``{subjectId}``、agent 用
  ``{subject_id}``，占位名不是 URL 的一部分，故不参与比较。
- 契约只解析一次（``lru_cache``），避免每个用例重复读 6000 行 YAML。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator

import yaml

HTTP_METHODS = ("get", "post", "put", "delete", "patch", "head", "options")

_PLACEHOLDER_RE = re.compile(r"^\{[^{}]+\}$")


class ContractError(Exception):
    """契约比对失败的基类。"""


class PathAmbiguousError(ContractError):
    """同一 method+path 匹配到多个契约路径，无法判定正确 operation。"""


class PathNotFoundError(ContractError):
    """method+path 在契约中没有对应 operation。"""


def repo_root() -> Path:
    """向上查找仓库根（以 ``docs/spec/openapi.yaml`` 的存在为标记）。"""
    for parent in Path(__file__).resolve().parents:
        if (parent / "docs" / "spec" / "openapi.yaml").is_file():
            return parent
    raise ContractError(
        "找不到仓库根：从 tests/contracts 向上未发现 docs/spec/openapi.yaml"
    )


def contract_path() -> Path:
    return repo_root() / "docs" / "spec" / "openapi.yaml"


@lru_cache(maxsize=1)
def load_contract() -> dict[str, Any]:
    """解析契约文件。整个 pytest session 内只读一次。"""
    path = contract_path()
    with path.open(encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    if not isinstance(document, dict):
        raise ContractError(f"契约根节点不是 mapping: {path}")
    return document


def contract_paths() -> dict[str, Any]:
    paths = load_contract().get("paths")
    if not isinstance(paths, dict):
        raise ContractError("契约缺少 paths 或类型不是 mapping")
    return paths


def schemas() -> dict[str, Any]:
    components = load_contract().get("components") or {}
    result = components.get("schemas")
    if not isinstance(result, dict):
        raise ContractError("契约缺少 components.schemas 或类型不是 mapping")
    return result


def iter_operations() -> Iterator[tuple[str, str, dict[str, Any]]]:
    """遍历 ``(path, method, operation)``。"""
    for path, item in contract_paths().items():
        if not isinstance(item, dict):
            continue
        for method, operation in item.items():
            if method in HTTP_METHODS and isinstance(operation, dict):
                yield path, method, operation


def resolve_ref(ref: str) -> Any:
    """解析契约内部的 ``$ref``（支持 ``#/a/b/c`` 形式）。

    悬空的 ``$ref`` 抛 :class:`ContractError`，使契约结构损坏立刻可见。
    """
    if not ref.startswith("#/"):
        raise ContractError(f"只支持文档内部 $ref，收到: {ref!r}")
    node: Any = load_contract()
    for raw in ref[2:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or key not in node:
            raise ContractError(f"悬空的 $ref: {ref!r}（在 {key!r} 处断裂）")
        node = node[key]
    return node


def collect_refs() -> list[str]:
    """收集契约中出现的全部 ``$ref`` 字符串。"""
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "$ref" and isinstance(value, str):
                    found.append(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(load_contract())
    return found


# --------------------------------------------------------------------------- #
# 路径模板匹配（D3）
# --------------------------------------------------------------------------- #

def split_segments(path: str) -> tuple[str, ...]:
    """把路径拆成段。前导 ``/`` 不产生空段。"""
    return tuple(segment for segment in path.strip("/").split("/") if segment != "")


def _is_placeholder(segment: str) -> bool:
    return bool(_PLACEHOLDER_RE.match(segment))


@dataclass(frozen=True)
class Match:
    """一次成功的路径解析结果。"""

    path: str
    method: str
    operation: dict[str, Any]
    exact: bool
    #: 通配匹配时，agent 侧动态段的数量。0 表示字面量全等。
    dynamic_segments: int = 0

    @property
    def operation_id(self) -> str:
        return self.operation.get("operationId") or f"{self.method.upper()} {self.path}"


def _segments_match(agent: tuple[str, ...], declared: tuple[str, ...]) -> bool:
    """逐段比对。

    agent 侧的 ``{param}`` 是 f-string 插值位，只能对应契约中的**占位符段**；
    反之契约占位符段可以吸收 agent 的任何字面段（调用方传入了具体 id）。
    这样 ``/collections/{param}`` 不会误撞 ``/collections/counts``，
    而 ``/collections/{subject_id}`` 仍能绑定 ``/collections/{subjectId}``。
    """
    if len(agent) != len(declared):
        return False
    for left, right in zip(agent, declared):
        if left == right:
            continue
        if _is_placeholder(left):
            # agent 的动态段只能匹配契约里的占位符段
            if not _is_placeholder(right):
                return False
            continue
        if _is_placeholder(right):
            # 契约占位符段可吸收 agent 的字面段
            continue
        return False
    return True


def match_operation(method: str, agent_path: str) -> Match:
    """把 agent 的 method+path 解析到契约里唯一的 operation。

    解析顺序（D3）：

    1. 字面量全等优先——``/api/client/collections/counts`` 绑定到同名 operation，
       而不是 ``/api/client/collections/{subjectId}``。
    2. 否则接受通配匹配，但**必须唯一**。
    3. 多个通配候选视为歧义失败，不是通过。
    """
    method = method.lower()
    if method not in HTTP_METHODS:
        raise ContractError(f"非法 HTTP method: {method!r}")

    agent_segments = split_segments(agent_path)
    candidates: list[tuple[str, dict[str, Any], bool]] = []

    for declared_path, item in contract_paths().items():
        if not isinstance(item, dict) or method not in item:
            continue
        declared_segments = split_segments(declared_path)
        if not _segments_match(agent_segments, declared_segments):
            continue
        exact = agent_segments == declared_segments
        candidates.append((declared_path, item[method], exact))

    dynamic = sum(1 for segment in agent_segments if _is_placeholder(segment))

    exact_hits = [c for c in candidates if c[2]]
    if len(exact_hits) == 1:
        path, operation, _ = exact_hits[0]
        return Match(path=path, method=method, operation=operation, exact=True, dynamic_segments=0)
    if len(exact_hits) > 1:
        raise PathAmbiguousError(
            f"{method.upper()} {agent_path} 字面量匹配到多个契约路径: "
            f"{[c[0] for c in exact_hits]}"
        )

    if len(candidates) == 1:
        path, operation, _ = candidates[0]
        return Match(
            path=path, method=method, operation=operation, exact=False,
            dynamic_segments=dynamic,
        )
    if not candidates:
        raise PathNotFoundError(
            f"{method.upper()} {agent_path} 在契约中没有对应 operation"
        )
    raise PathAmbiguousError(
        f"{method.upper()} {agent_path} 通配匹配到多个契约路径，无法判定: "
        f"{sorted(c[0] for c in candidates)}"
    )


# --------------------------------------------------------------------------- #
# operation 的请求字段
# --------------------------------------------------------------------------- #

def request_body_schema(operation: dict[str, Any]) -> dict[str, Any] | None:
    """取 JSON 请求体 schema（``$ref`` 已解析）。"""
    body = operation.get("requestBody") or {}
    content = body.get("content") or {}
    media = content.get("application/json")
    if not media:
        return None
    schema = media.get("schema")
    if not isinstance(schema, dict):
        return None
    ref = schema.get("$ref")
    if isinstance(ref, str):
        resolved = resolve_ref(ref)
        return resolved if isinstance(resolved, dict) else None
    return schema


def declared_body_fields(operation: dict[str, Any]) -> set[str]:
    """请求体 schema 声明的顶层属性名。"""
    schema = request_body_schema(operation)
    if schema is None:
        return set()
    properties = schema.get("properties") or {}
    return set(properties) if isinstance(properties, dict) else set()


def declared_query_params(operation: dict[str, Any]) -> set[str]:
    """operation 的 ``in: query`` 参数名。"""
    names: set[str] = set()
    for parameter in operation.get("parameters") or []:
        if not isinstance(parameter, dict):
            continue
        if parameter.get("in") == "query" and isinstance(parameter.get("name"), str):
            names.add(parameter["name"])
    return names
