"""agent → business HTTP 契约：每个出站调用都必须能解析到契约中的 operation。

覆盖三个层次（对应 spec ``agent-business-contract``）：

1. **调用点发现**（D2）：AST 静态遍历 ``app/**/*.py``，不维护手写路径清单。
2. **路径/方法解析**（D3）：字面量优先，通配需唯一，歧义即失败。
3. **请求字段声明**（D4）：仅对静态可判定 payload 校验字段，运行时构造的进豁免表。

失败信息一律带上 ``文件:行号`` 与契约侧 operation，便于直接定位（spec 的
「Contract drift reports an actionable failure」）。
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

import pytest

from tests.contracts import _contract
from tests.contracts._contract import (
    ContractError,
    PathAmbiguousError,
    PathNotFoundError,
    declared_body_fields,
    declared_query_params,
    match_operation,
    request_body_schema,
)

APP_DIR = _contract.repo_root() / "backend" / "agent" / "app"

# 契约里 `request(path)` 的接收者形态——用于区分业务调用与适配器内部的 httpx 调用。
_BUSINESS_RECEIVERS = {
    "business",
    "self._business",
    "self.business",
    "_business",
}
_HTTPX_RECEIVERS = {"httpx"}


@dataclass(frozen=True)
class CallSite:
    """一个 agent → business 的 HTTP 调用点。"""

    file: str
    line: int
    method: str
    path: str
    receiver: str
    #: 静态可判定的请求字段；``None`` 表示运行时构造，无法判定（见 EXEMPTIONS）。
    body_fields: tuple[str, ...] | None = None
    query_fields: tuple[str, ...] | None = None
    via_to_thread: bool = False

    @property
    def location(self) -> str:
        return f"{self.file}:{self.line}"

    def __str__(self) -> str:
        return f"{self.method} {self.path} @ {self.location}"


_EXEMPTIONS: dict[tuple[str, int], str] = {
    # key = (相对仓库根的 posix 路径, 行号)；value = 豁免理由。
    # 运行时构造 payload 的调用点：只做路径校验，字段无法静态判定。
    ("backend/agent/app/adapters/business_http.py", 121): (
        "lexical_search 把调用方组装的 query 字典原样透传（json_body=query），"
        "字段集随检索过滤器变化，静态不可判定。其请求 schema 另由 "
        "test_lexical_search_payload_shape 从 RAG 层构造侧覆盖。"
    ),
}


def _module_rel_path(path: Path) -> str:
    return path.resolve().relative_to(_contract.repo_root()).as_posix()


def _joined_str_to_template(node: ast.JoinedStr) -> str:
    """把 f-string 转成以 ``{param}`` 表示动态段的模板。"""
    parts: list[str] = []
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            parts.append(value.value)
        else:
            parts.append("{param}")
    return "".join(parts)


def _literal_or_template(node: ast.expr | None) -> str | None:
    if node is None:
        return None
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return _joined_str_to_template(node)
    if isinstance(node, ast.Name):
        # 模块常量（例如 BUSINESS_LIVENESS_PATH）由调用方另行解析。
        return None
    return None


def _receiver_name(node: ast.expr) -> str:
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - ast.unparse 极少失败
        return "<unknown>"


def _keyword_str_list(call: ast.Call, name: str) -> tuple[str, ...] | None:
    """读取 ``name={...}`` 里的字面量键；``None`` 表示无法静态判定。"""
    for keyword in call.keywords:
        if keyword.arg != name:
            continue
        value = keyword.value
        if isinstance(value, ast.Constant) and value.value is None:
            return ()
        if isinstance(value, ast.Dict):
            keys: list[str] = []
            for key in value.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    keys.append(key.value)
                else:
                    # 非字面量键（**spread 或变量）→ 放弃字段校验
                    return None
            return tuple(keys)
        # 变量或表达式 → 无法静态判定
        return None
    return None


def _subscript_added_keys(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef, local_name: str
) -> tuple[str, ...]:
    """收集函数体内 ``local_name["key"] = ...`` 形式的键。"""
    keys: list[str] = []
    for node in ast.walk(func_node):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (
                isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name)
                and target.value.id == local_name
                and isinstance(target.slice, ast.Constant)
                and isinstance(target.slice.value, str)
            ):
                keys.append(target.slice.value)
    return tuple(keys)


def _dict_bound_to_local(
    func_node: ast.FunctionDef | ast.AsyncFunctionDef, local_name: str
) -> tuple[str, ...] | None:
    """若 ``local_name`` 被赋值为字典字面量，返回其字面量键。"""
    for node in ast.walk(func_node):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == local_name:
                if isinstance(node.value, ast.Dict):
                    keys: list[str] = []
                    for key in node.value.keys:
                        if isinstance(key, ast.Constant) and isinstance(key.value, str):
                            keys.append(key.value)
                        else:
                            return None
                    return tuple(keys)
                return None
    return None


def _payload_fields(
    call: ast.Call,
    func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    keyword_name: str,
) -> tuple[str, ...] | None:
    """解析 ``params=`` / ``json_body=`` 的字段集。

    返回 ``None`` 表示运行时构造、无法静态判定。
    """
    for keyword in call.keywords:
        if keyword.arg != keyword_name:
            continue
        value = keyword.value
        if isinstance(value, ast.Dict):
            keys: list[str] = []
            for key in value.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    keys.append(key.value)
                else:
                    return None
            return tuple(keys)
        if isinstance(value, ast.Name):
            literal = _dict_bound_to_local(func_node, value.id)
            if literal is None:
                return None
            return literal + _subscript_added_keys(func_node, value.id)
        return None
    return ()


def _resolve_constant(module_name: str, name: str) -> str | None:
    """从 ``app.**`` 模块读取字符串常量，避免在测试里硬编码路径。"""
    import importlib

    try:
        module = importlib.import_module(module_name)
    except Exception:  # pragma: no cover - 导入失败则视为不可解析
        return None
    value = getattr(module, name, None)
    return value if isinstance(value, str) else None


def _iter_own_nodes(func_node: ast.FunctionDef | ast.AsyncFunctionDef):
    """遍历函数自身作用域的节点，下钻嵌套函数（嵌套函数会被单独处理）。"""
    stack: list[ast.AST] = list(func_node.body)
    while stack:
        node = stack.pop()
        yield node
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            stack.append(child)


def _walk_file(path: Path) -> list[CallSite]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    rel = _module_rel_path(path)
    sites: list[CallSite] = []

    for func_node in ast.walk(tree):
        if not isinstance(func_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in _iter_own_nodes(func_node):
            if not isinstance(node, ast.Call):
                continue

            # 形态 A：<obj>.request("GET", "/api/...")
            if isinstance(node.func, ast.Attribute) and node.func.attr == "request":
                receiver = _receiver_name(node.func.value)
                if receiver in _HTTPX_RECEIVERS:
                    continue  # 适配器内部转发的真实 httpx 调用，不是业务消费点
                method = _literal_or_template(node.args[0]) if node.args else None
                if method is None or not isinstance(method, str):
                    continue
                raw_path = node.args[1] if len(node.args) > 1 else None
                if raw_path is None:
                    for keyword in node.keywords:
                        if keyword.arg == "path":
                            raw_path = keyword.value
                            break
                resolved = _literal_or_template(raw_path)
                if resolved is None:
                    if isinstance(raw_path, ast.Name):
                        resolved = _resolve_constant("app.api.health", raw_path.id)
                    if resolved is None:
                        continue
                sites.append(
                    CallSite(
                        file=rel,
                        line=node.lineno,
                        method=method.upper(),
                        path=resolved,
                        receiver=receiver,
                        body_fields=_payload_fields(node, func_node, "json_body"),
                        query_fields=_payload_fields(node, func_node, "params"),
                    )
                )
                continue

            # 形态 B：asyncio.to_thread(<obj>.request, "GET", BUSINESS_LIVENESS_PATH, ...)
            if not (isinstance(node.func, ast.Attribute) and node.func.attr == "to_thread"):
                continue
            if not node.args:
                continue
            first = node.args[0]
            if not (isinstance(first, ast.Attribute) and first.attr == "request"):
                continue
            if len(node.args) < 3:
                continue
            method = _literal_or_template(node.args[1])
            if not isinstance(method, str):
                continue
            raw_path = node.args[2]
            resolved = _literal_or_template(raw_path)
            if resolved is None and isinstance(raw_path, ast.Name):
                resolved = _resolve_constant("app.api.health", raw_path.id)
            if resolved is None:
                continue
            sites.append(
                CallSite(
                    file=rel,
                    line=node.lineno,
                    method=method.upper(),
                    path=resolved,
                    receiver=_receiver_name(first.value),
                    body_fields=_payload_fields(node, func_node, "json_body"),
                    query_fields=_payload_fields(node, func_node, "params"),
                    via_to_thread=True,
                )
            )
    return sites


def discover_call_sites() -> list[CallSite]:
    """遍历 ``app/**/*.py`` 收集全部业务调用点。"""
    sites: list[CallSite] = []
    for path in sorted(APP_DIR.rglob("*.py")):
        sites.extend(_walk_file(path))
    # 嵌套函数会被外层的 ast.walk 再次命中；按 (文件, 行, method, path) 去重。
    seen: set[tuple[str, int, str, str]] = set()
    unique: list[CallSite] = []
    for site in sites:
        key = (site.file, site.line, site.method, site.path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(site)
    return unique


CALL_SITES = discover_call_sites()

# 期望总数：24 个 ``<obj>.request(...)`` 业务调用 + 1 个 ``asyncio.to_thread`` 探针。
# 适配器内部的 ``httpx.request`` 已被显式排除，故不计入。
EXPECTED_MIN_CALL_SITES = 24


# --------------------------------------------------------------------------- #
# 遍历器与匹配器的自测
# --------------------------------------------------------------------------- #

def test_matcher_prefers_literal_over_wildcard() -> None:
    """``/collections/counts`` 必须绑定到字面量 operation，而非 ``{subjectId}``。"""
    match = match_operation("GET", "/api/client/collections/counts")
    assert match.path == "/api/client/collections/counts"
    assert match.exact is True


def test_matcher_binds_wildcard_across_placeholder_names() -> None:
    """占位名不同（``{subject_id}`` vs ``{subjectId}``）仍应匹配。"""
    match = match_operation("GET", "/api/client/collections/{subject_id}")
    assert match.path == "/api/client/collections/{subjectId}"
    assert match.exact is False


def test_matcher_rejects_two_way_ambiguity() -> None:
    """
    歧义必须报错，不能猜。

    真实契约里没有两个路径共享同一形状（已核验），所以用合成路径触发该分支：
    同时声明 ``/a/{x}`` 与 ``/a/{y}`` 后，对 ``/a/{param}`` 的匹配不唯一。
    """
    import tests.contracts._contract as module

    synthetic = {
        "/a/{x}": {"get": {"operationId": "first"}},
        "/a/{y}": {"get": {"operationId": "second"}},
    }
    original = module.contract_paths
    module.contract_paths = lambda: synthetic  # type: ignore[assignment]
    try:
        with pytest.raises(PathAmbiguousError):
            module.match_operation("GET", "/a/{param}")
    finally:
        module.contract_paths = original  # type: ignore[assignment]


def test_matcher_reports_missing_operation() -> None:
    with pytest.raises(PathNotFoundError):
        match_operation("GET", "/api/client/definitely-not-a-real-path")


# --------------------------------------------------------------------------- #
# 调用点发现（D2 的防退化守卫）
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# 通配匹配的「字面量吸收」约束（让路径拼写错误变红）
# --------------------------------------------------------------------------- #

# 允许通配匹配的调用点白名单：这些位置的 URL 里确实有运行时 ID，
# 通配绑定是语义正确的。不在表内的调用点若只能通配匹配，则视为路径拼写错误。
_WILDCARD_ALLOWED: set[tuple[str, int]] = {
    ("backend/agent/app/adapters/business_http.py", 92),    # /collections/{id}/save
    ("backend/agent/app/agent/client/actions/collection_progress.py", 35),  # /progress-preview/{id}/execute
    ("backend/agent/app/agent/client/actions/collection_state.py", 23),     # /collections/{id}
    ("backend/agent/app/agent/client/actions/wishlist.py", 82),             # /collections/{id}/wishlist
    ("backend/agent/app/agent/client/collections.py", 51),                  # /collections/{id}
    ("backend/agent/app/agent/tools/subject_catalog.py", 11),               # /subjects/{id}
    ("backend/agent/app/agent/tools/subject_catalog.py", 20),               # /subjects/{id}/episodes
    ("backend/agent/app/agent/tools/subject_catalog.py", 50),               # /tags/{tag}/subjects
    ("backend/agent/app/agent/navigation_emitter.py", 93),                # /subjects/{id}（open_subject 权威回查）
}


def test_wildcard_matches_are_intentional() -> None:
    """只有真带运行时 ID 的调用点才允许通配匹配。

    这条断言是路径拼写错误的捕手：把 ``/collections/counts`` 手误成
    ``/collections/count`` 时，它仍能「通配」匹配 ``/collections/{subjectId}``，
    仅看「能解析」会静默放过。此处要求该类调用点必须要么字面命中，
    要么在 ``_WILDCARD_ALLOWED`` 里显式声明。
    """
    violations: list[str] = []
    for site in CALL_SITES:
        match = match_operation(site.method, site.path)
        if match.exact:
            continue
        if (site.file, site.line) in _WILDCARD_ALLOWED:
            continue
        violations.append(
            f"{site} 只能通配匹配到 {match.path}，但该调用点不含运行时 ID"
            "（疑似路径拼写错误；若确实带 ID，请加入 _WILDCARD_ALLOWED）"
        )
    assert not violations, "契约漂移：\n" + "\n".join(violations)


def test_wildcard_allowlist_entries_are_live_and_used() -> None:
    """白名单不得腐烂：每条都必须对应活调用点，且实际发生了通配匹配。"""
    by_key = {(s.file, s.line): s for s in CALL_SITES}
    stale = [key for key in _WILDCARD_ALLOWED if key not in by_key]
    assert not stale, f"_WILDCARD_ALLOWED 中以下条目已不再对应活调用点：{stale}"
    unused = []
    for key in _WILDCARD_ALLOWED:
        site = by_key[key]
        if match_operation(site.method, site.path).exact:
            unused.append(key)
    assert not unused, (
        f"_WILDCARD_ALLOWED 中以下条目现在已是字面命中，应从白名单移除：{unused}"
    )


def test_literal_path_typo_is_detected() -> None:
    """负向演练（Drill B）：字面量路径手误不得被通配静默吸收。"""
    bad = CallSite(
        file="backend/agent/app/agent/client/collections.py",
        line=60,
        method="GET",
        path="/api/client/collections/count",  # 少了 s
        receiver="business",
    )
    match = match_operation(bad.method, bad.path)
    # 能解析，但是通配——正是必须被守卫拦下的情形
    assert match.exact is False, "count 不应字面命中任何契约路径"
    assert (bad.file, bad.line) not in _WILDCARD_ALLOWED


def test_discovers_enough_call_sites() -> None:
    """走查器坏掉时必须失败，而不是空跑全绿。"""
    assert len(CALL_SITES) >= EXPECTED_MIN_CALL_SITES, (
        f"只发现 {len(CALL_SITES)} 个业务调用点（期望 >= {EXPECTED_MIN_CALL_SITES}）。"
        " AST 走查可能已失效——检查 discover_call_sites 与 app/ 结构。"
        f" 已发现: {[str(s) for s in CALL_SITES]}"
    )


def test_discovers_the_to_thread_probe() -> None:
    """健康探针经 ``asyncio.to_thread`` 分发，必须被单独识别。"""
    probes = [s for s in CALL_SITES if s.via_to_thread]
    assert probes, "未发现 asyncio.to_thread(...) 形态的调用点（健康探针）"
    probe = probes[0]
    assert probe.path == "/actuator/health/liveness"
    assert probe.method == "GET"

def test_call_site_composition_matches_known_surface() -> None:
    """构成必须与 design D2 记录的边界一致：24 个 ``<obj>.request`` + 1 个探针 = 25。

    总数用「至少」而非「等于」是刻意的：新增合法调用点不应无故变红；
    但构成比例（恰好一个经 ``to_thread`` 的探针）是形态事实，值得钉死。
    """
    attribute_calls = [s for s in CALL_SITES if not s.via_to_thread]
    probes = [s for s in CALL_SITES if s.via_to_thread]
    assert len(probes) == 1, (
        f"应恰好 1 个 asyncio.to_thread 探针，实际 {len(probes)}：{[str(s) for s in probes]}"
    )
    assert len(attribute_calls) >= EXPECTED_MIN_CALL_SITES, (
        f"属性调用只有 {len(attribute_calls)} 个（期望 >= {EXPECTED_MIN_CALL_SITES}）"
    )
    assert len(CALL_SITES) == len(attribute_calls) + len(probes)


def test_excludes_adapter_internal_httpx() -> None:
    """适配器内部 ``httpx.request`` 不是业务消费点，不应被计入。"""
    assert all(s.receiver not in _HTTPX_RECEIVERS for s in CALL_SITES)


def test_call_site_count_is_reported(capsys) -> None:
    """spec 要求运行时可看见检查了多少调用点。"""
    print(f"contract call sites checked: {len(CALL_SITES)}")
    captured = capsys.readouterr()
    assert f"contract call sites checked: {len(CALL_SITES)}" in captured.out


# --------------------------------------------------------------------------- #
# 路径/方法解析
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("site", CALL_SITES, ids=lambda s: f"{s.method}-{s.path}-{s.line}")
def test_every_call_resolves_to_declared_operation(site: CallSite) -> None:
    try:
        match = match_operation(site.method, site.path)
    except ContractError as exc:
        pytest.fail(f"契约漂移：{site} 无法解析。{exc}")
    assert match.path, f"{site} 未解析到契约路径"


@pytest.mark.parametrize("site", CALL_SITES, ids=lambda s: f"{s.method}-{s.path}-{s.line}")
def test_every_call_declares_required_response(site: CallSite) -> None:
    match = match_operation(site.method, site.path)
    responses = match.operation.get("responses") or {}
    assert "200" in responses, (
        f"{match.operation_id}（被 {site.location} 调用）未声明 200 响应"
    )


def test_misspelled_path_fails_with_location() -> None:
    """负向演练：路径拼错必须失败，且信息含 method/path/来源位置。"""
    bad = CallSite(
        file="backend/agent/app/agent/client/collections.py",
        line=60,
        method="GET",
        path="/api/client/collection/counts",  # 少了 s，无法通配吸收
        receiver="business",
    )
    with pytest.raises(PathNotFoundError) as excinfo:
        match_operation(bad.method, bad.path)
    message = str(excinfo.value)
    assert "GET" in message and bad.path in message


# --------------------------------------------------------------------------- #
# 请求字段声明（D4）
# --------------------------------------------------------------------------- #

def _field_sites() -> list[CallSite]:
    return [
        s
        for s in CALL_SITES
        if (s.body_fields is not None and s.body_fields)
        or (s.query_fields is not None and s.query_fields)
    ]


def _assert_fields_declared(site: CallSite) -> None:
    """断言单个调用点的静态字段都在契约里声明过。

    抽成函数是为了让负向演练能用**同一份**判定逻辑变红，而不是重写一遍断言
    ——重写只会验证测试自己，永远绿。
    """
    match = match_operation(site.method, site.path)

    if site.body_fields:
        schema = request_body_schema(match.operation)
        if schema is None:
            pytest.fail(
                f"{match.operation_id}（被 {site.location} 调用）未声明 JSON 请求体 schema，"
                f"但 agent 发送了字段 {sorted(site.body_fields)}"
            )
        declared = declared_body_fields(match.operation)
        unexpected = sorted(set(site.body_fields) - declared)
        assert not unexpected, (
            f"契约漂移：{match.operation_id}（{site.location}）发送了契约未声明的请求体字段 "
            f"{unexpected}；契约已声明 {sorted(declared)}"
        )

    if site.query_fields:
        declared_q = declared_query_params(match.operation)
        # 路径参数用 agent 侧 f-string 拼接，不属 query。
        unexpected_q = sorted(set(site.query_fields) - declared_q)
        assert not unexpected_q, (
            f"契约漂移：{match.operation_id}（{site.location}）发送了契约未声明的查询参数 "
            f"{unexpected_q}；契约已声明 {sorted(declared_q)}"
        )


@pytest.mark.parametrize("site", _field_sites(), ids=lambda s: f"{s.method}-{s.path}-{s.line}")
def test_declared_payload_fields(site: CallSite) -> None:
    _assert_fields_declared(site)


def test_undeclared_body_field_is_reported() -> None:
    """负向演练：往 save 操作塞未声明字段，同一份判定逻辑必须指名报出。"""
    live = next(s for s in CALL_SITES if s.path.endswith("/save") and s.body_fields)
    injected = CallSite(
        file=live.file,
        line=live.line,
        method=live.method,
        path=live.path,
        receiver=live.receiver,
        body_fields=live.body_fields + ("definitelyNotAField",),
        query_fields=live.query_fields,
    )
    with pytest.raises(AssertionError) as excinfo:
        _assert_fields_declared(injected)
    message = str(excinfo.value)
    assert "definitelyNotAField" in message, f"失败信息须指名未声明字段：{message}"
    assert "请求体字段" in message, f"失败信息须说明是请求体字段：{message}"
    assert live.location in message, f"失败信息须带调用点位置：{message}"


# --------------------------------------------------------------------------- #
# 豁免表（D4 的诚实缺口）
# --------------------------------------------------------------------------- #

def test_exemptions_still_map_to_live_call_sites() -> None:
    """豁免必须仍对应活调用点，否则覆盖率会静默萎缩。"""
    live = {(s.file, s.line) for s in CALL_SITES}
    stale = [key for key in _EXEMPTIONS if key not in live]
    assert not stale, (
        "以下豁免条目已不对应任何活调用点，请删除："
        f"{stale}；现存活调用点: {sorted(live)}"
    )


def test_exemptions_are_documented_runtime_payloads() -> None:
    """每条豁免都必须有理由，且对应调用点确实无法静态判定字段。"""
    by_key = {(s.file, s.line): s for s in CALL_SITES}
    for key, reason in _EXEMPTIONS.items():
        assert reason.strip(), f"豁免 {key} 缺少理由"
        site = by_key[key]
        assert site.body_fields is None or site.query_fields is None, (
            f"豁免 {key} 声称 payload 无法静态判定，但走查器实际解析出了字段：{site}"
        )


def test_lexical_search_payload_shape() -> None:
    """从构造侧覆盖被豁免的运行时 payload（D4）。

    ``lexical_search`` 的字段无法从调用点静态判定，但构造点是单一的
    （``main.py`` 的 ``_business_fallbacks``），故直接断言契约 schema 包含
    构造器发出的每个键，且必填项一致。
    """
    import ast as _ast

    source = (_contract.repo_root() / "backend" / "agent" / "main.py").read_text(encoding="utf-8")
    tree = _ast.parse(source)

    payload_keys: set[str] | None = None
    for node in _ast.walk(tree):
        # 找到 lexical_search 的 fallback 定义里的 payload 字典
        if not isinstance(node, _ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, _ast.Name)]
        if "payload" not in targets:
            continue
        if not isinstance(node.value, _ast.Dict):
            continue
        keys = {k.value for k in node.value.keys if isinstance(k, _ast.Constant)}
        if "q" in keys:  # 词法检索 payload 的特征键
            payload_keys = keys
            break

    assert payload_keys is not None, "未在 main.py 中找到词法检索 payload 构造点"

    match = match_operation("POST", "/api/client/subjects/lexical-search")
    schema = request_body_schema(match.operation)
    assert schema is not None, f"{match.operation_id} 未声明请求体 schema"
    declared = set(schema.get("properties") or {})
    unexpected = sorted(payload_keys - declared)
    assert not unexpected, (
        f"契约漂移：{match.operation_id} 构造侧发送了契约未声明的字段 {unexpected}；"
        f"契约已声明 {sorted(declared)}"
    )
    required = set(schema.get("required") or [])
    assert required <= payload_keys, (
        f"契约漂移：{match.operation_id} 要求必填 {sorted(required)}，"
        f"但构造侧只发出 {sorted(payload_keys)}"
    )


# --------------------------------------------------------------------------- #
# 契约文件自身结构完整性（3.5）
# --------------------------------------------------------------------------- #

#: 曾经被误混入契约的测试夹具路径（来源 `SecurityConfigAuthorizationTest.java`）。
#: 它们不是对外 API，重新出现即视为契约被污染。
FIXTURE_ONLY_PATHS = (
    "/api/client/subjects/1",
    "/api/client/private",
    "/api/admin/private",
    "/actuator/health",
)

REQUIRED_TOP_LEVEL = ("openapi", "info", "paths", "components")


def test_contract_parses_and_has_required_top_level_keys() -> None:
    document = _contract.load_contract()
    for key in REQUIRED_TOP_LEVEL:
        assert key in document, f"契约缺少顶层键 {key!r}"
    assert document["components"].get("schemas"), "契约缺少 components.schemas"


def test_no_dangling_refs() -> None:
    """每个 ``$ref`` 都必须解析得到。"""
    dangling: list[str] = []
    for ref in _contract.collect_refs():
        try:
            _contract.resolve_ref(ref)
        except ContractError:
            dangling.append(ref)
    assert not dangling, f"契约存在悬空的 $ref：{sorted(set(dangling))}"


def test_no_unreferenced_schemas() -> None:
    """没有孤儿 schema——这曾是被改坏版本的典型特征（38 个 schema 全部无人引用）。"""
    referenced = {
        ref.rsplit("/", 1)[-1]
        for ref in _contract.collect_refs()
        if ref.startswith("#/components/schemas/")
    }
    orphans = sorted(set(_contract.schemas()) - referenced)
    assert not orphans, (
        f"以下 schema 未被任何 $ref 引用：{orphans}。"
        "契约被整体回退时通常会出现这种状态。"
    )


def test_no_fixture_only_paths() -> None:
    """Java 测试夹具路径不得出现在契约里。"""
    present = [p for p in FIXTURE_ONLY_PATHS if p in _contract.contract_paths()]
    assert not present, f"契约混入了测试夹具路径：{present}"


def test_stream_operations_declare_event_stream() -> None:
    """两个 stream 端点必须声明 ``text/event-stream`` 并引用单帧 schema。"""
    for path in ("/api/admin/agent/chat/stream", "/api/client/agent/stream"):
        match = match_operation("POST", path)
        responses = match.operation.get("responses") or {}
        content = (responses.get("200") or {}).get("content") or {}
        assert "text/event-stream" in content, (
            f"{match.operation_id} 未声明 text/event-stream 响应"
        )
        schema = content["text/event-stream"].get("schema") or {}
        ref = schema.get("$ref", "")
        assert ref.startswith("#/components/schemas/"), (
            f"{match.operation_id} 的响应 schema 不是单帧 schema 引用：{schema}"
        )
        _contract.resolve_ref(ref)  # 悬空即抛
        description = match.operation.get("description") or ""
        assert "空行" in description, f"{match.operation_id} 未说明空行分帧"
        assert "`event:`" in description, (
            f"{match.operation_id} 未说明不使用 SSE event: 字段"
        )
