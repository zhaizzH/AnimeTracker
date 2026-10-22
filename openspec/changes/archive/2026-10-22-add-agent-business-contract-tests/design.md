# Design

## Context

See `proposal.md` — Why for motivation, including the contract-baseline regression found in `22d7cb63`.

Facts that shape the approach, all verified against the working tree:

- `backend/business` has no springdoc dependency in any `pom.xml`, so there is no generated OpenAPI document. `docs/spec/openapi.yaml` (5823 lines) is the only machine-readable contract and is hand-maintained.
- The agent reaches business through 25 `request(...)` call sites across 7 files: 24 are `<obj>.request(...)` calls with a literal method and a literal or f-string path, and 1 is the adapter's own internal `httpx.request`. A 26th boundary crossing, the health probe, dispatches via `asyncio.to_thread(business.request, "GET", BUSINESS_LIVENESS_PATH)` and so is invisible to an attribute-call walk.
- Contract path parameters use different placeholder names than agent f-strings: the contract says `/api/client/collections/{subjectId}`, the agent builds `/api/client/collections/{subject_id}`. Matching therefore cannot be string equality on the template.
- The agent's liveness probe calls `GET /actuator/health/liveness`. That is a real cross-boundary dependency but has no declared operation anywhere.
- `serialize_agent_event` is already the single serialization entry point and is covered by `tests/api/test_sse_serialization.py`, which asserts wire behaviour but not the contract document.
- `parse_pending_action_json` is already the single deserialization entry point for stored pending actions.
- `PyYAML` is present in the resolved environment only transitively via `uvicorn[standard]`; the dependency is not declared in `pyproject.toml`.
- Baseline test count is 668, `pytest` collects everything under `tests/` with no `testpaths` restriction.

## Goals / Non-Goals

**Goals:**

- Make contract drift a red test rather than a production discovery, for the three boundaries the parent task names: HTTP path/field, SSE wire frame, preview write protocol.
- Make the contract document's own integrity a test subject, so the `22d7cb63` class of regression cannot silently recur.
- Keep every check inside `backend/agent/tests/`, with zero edits to runtime code and zero edits to business Java.

**Non-Goals:**

- Proving the contract matches business Java sources. The suite proves agent matches contract; it cannot prove contract matches Java. See Risks for why this limit is accepted rather than closed.
- Full field-level modelling of all 71 contract paths. Only the operations the agent actually calls plus the document's internal integrity.
- Replacing or rewriting the existing 668 tests, including `tests/api/test_sse_serialization.py`, which stays as the behaviour-level companion to the new contract-level assertions.

## Decisions

### D1. Repair the contract baseline before writing any assertion

Restore `docs/spec/openapi.yaml` from `00993ff3` (the last complete state), because `git log 00993ff3..HEAD -- docs/spec/openapi.yaml` shows `22d7cb63` is the only intervening commit and it contains no intentional contract change.

Then apply two deliberate deltas on top of the restore:

1. Remove the four fixture-only paths that do not belong in a contract: `/api/client/subjects/1`, `/api/client/private`, `/api/admin/private`, `/actuator/health`. Their only source is `SecurityConfigAuthorizationTest.java`, a MockMvc security test that declares `@GetMapping` handlers inside the test class.
2. Declare `GET /actuator/health/liveness` instead, since the agent's health probe genuinely calls it and Spring Boot exposes it (`management.endpoint.health.probes.enabled: true`).

Why not build on the current file: the current file has zero `$ref`s, 38 unreferenced schemas, no `securitySchemes`, and placeholder bodies for six operations the agent calls. Assertions written against it would lock in the damage.

Why not keep the fixture paths: a contract that lists `/api/client/private` invites a future reader to treat a test artifact as an API, and the integrity test in `agent-business-contract` explicitly forbids it.

Alternative considered: regenerate the contract from Java. Rejected — it requires touching the business build, which the parent task forbids, and would create a second source of truth alongside the hand-maintained file.

### D2. Discover agent call sites by static AST walk, not by a hand-kept list

Walk `app/**/*.py` with `ast`, collect every `<expr>.request(...)` call, and extract:

- method: only when the first argument is a string constant
- path: when the second argument is a string constant, or a `JoinedStr` (f-string) whose non-constant parts become `{param}` placeholders

This yields all 24 business call sites. Two adjustments are needed:

- `httpx.request` inside the adapter body is not a business call; exclude it explicitly so the count stays honest.
- The health probe is not an attribute call at all — it passes `business.request` as a callable to `asyncio.to_thread`. The walker MUST additionally detect `to_thread(<obj>.request, ...)` and read `BUSINESS_LIVENESS_PATH` from the imported module rather than hardcoding the string.

Why not a hand-kept list of paths: it becomes a second copy of the truth and drifts exactly like the contract did.

Why not runtime monkeypatching of `request()`: coverage-dependent, and a call site that stops being exercised silently stops being checked.

Guarding against a silently empty run: the suite asserts a minimum discovered call-site count and reports the count, so a refactor that breaks the walker fails loudly instead of vacuously passing.

### D3. Match paths structurally, with literal match taking precedence

Normalize each agent path into segments. Compare against contract path keys segment by segment, treating any `{...}` segment on either side as a wildcard.

Resolution order:

1. Exact literal match wins — so `/api/client/collections/counts` binds to the counts operation and not to `/api/client/collections/{subjectId}`.
2. Otherwise a wildcard match is accepted only if exactly one contract path matches.
3. Two or more wildcard matches is an ambiguity failure, not a pass.

Why not normalize placeholder names: the contract and the agent legitimately use different names (`subjectId` vs `subject_id`). Placeholder names are not part of the URL, so requiring them to agree would produce false failures with no signal.

### D4. Check request fields only where they are statically literal

Field checks apply to:

- dict literals passed as `json_body=` or `params=`
- dict literals bound to a local name in the same function and then passed as `params=`
- string-subscript assignments to such a local within the same function (`params["year"] = year`)

Sites passing a variable payload (currently `lexical_search`, which forwards a caller-built query dict) are path-checked only. Each such site MUST be listed in an explicit exemption table in the test module with the reason, and the suite asserts that every exemption still corresponds to a live call site.

Rationale: guessing at runtime-built payloads would produce checks that pass regardless of content, which is worse than an honest documented gap. The contract for those payloads is still covered from the other side — `lexical-search`'s request schema is asserted against the fields the RAG layer actually constructs by a focused unit assertion in the same module.

### D5. Bind the SSE test to the serializer, not to a copy of its output

The SSE contract test imports `serialize_agent_event` and `AgentEventType`, and compares observed wire output against the contract's frame schema:

- observed `type` values ⊆ contract `enum`, and the contract `enum` contains no `end`
- per-frame keys ⊇ contract `required`, and observed `content` keys ⊆ contract `content.properties`
- the live `AgentEventType` member set, minus `END`, equals the contract enum set

Bidirectional comparison is deliberate: it catches both "contract forgot the new type" and "serializer invented a field the contract doesn't know".

`result=error` vs `state=error` separation and the single-terminating-frame rule are asserted by driving `serialize_agent_event` with the frames the streaming layer actually produces, plus one assertion that reads the existing middleware/streaming behaviour rather than reimplementing it.

Alternative considered: parse the docstring/prose description. Rejected — prose is not machine-checkable, and the spec only requires that prose exist, which is asserted separately by string containment.

### D6. Exercise the preview protocol through its real entry points

The pending-action test uses `parse_pending_action_json`, the `PendingAction` union, and the Redis store's key/ttl constants rather than re-deriving them. For the "confirmation is bound to the stored version" requirement, drive `CollectionProgressPreviewable.do_execute` with a stub gateway and assert the outgoing URL contains the stored `preview_id` while a differently-named tool argument has no effect.

Why not assert on source text: a source-text assertion locks formatting, not behaviour, and breaks on harmless refactors.

### D7. Declare PyYAML explicitly

Add `PyYAML>=6.0` to `[project].dependencies`. It is currently importable only as a transitive side effect of `uvicorn[standard]`, and this change makes it a direct test dependency; leaving it transitive means an unrelated dependency change could break the contract suite.

### D8. Give contract failures their own CI step

`backend-python` already runs `uv run pytest`, which collects the new suite automatically. Add an explicit step that runs `tests/contracts/` alone before the full run, so a contract failure is labelled as a contract failure in the CI log instead of appearing as one of 690 anonymous test failures.

## Risks / Trade-offs

- **The suite cannot detect business-side drift.** If a Java DTO field is renamed and the hand-maintained contract is not updated, the agent still matches the (now stale) contract and the suite stays green. → Accepted, and stated plainly in the test module docstring and in the spec's Purpose. Closing this needs either springdoc export or Java source parsing, both explicitly out of scope. The suite does close the far more common failure: agent-side drift and contract-file damage.
- **Restoring the contract reverts a committed change.** `22d7cb63` touched the file, so the restore is a visible revert of part of that commit. → Mitigated by putting the evidence table in `proposal.md`, keeping the restore as its own commit with a message that states the reason, and making the integrity test prevent recurrence.
- **AST heuristics are brittle against future refactors.** A refactor that builds paths through a helper will silently drop a call site. → Mitigated by the minimum-call-count assertion and by failing on ambiguous matches rather than skipping.
- **Literal-only field coverage can lull.** A reader may assume all payloads are field-checked. → Mitigated by the explicit exemption table plus an assertion that exemptions stay live.
- **The contract remains hand-maintained.** Tests bind to a document a human edits, so a human can also edit both sides consistently. → Accepted; the suite's value is catching one-sided edits, which is the observed failure mode.
- **Contract restore may conflict with uncommitted local edits.** → Checked: `git status --porcelain docs/spec/openapi.yaml` was clean at planning time; the task states this precondition explicitly.

## Migration Plan

1. Restore `docs/spec/openapi.yaml` from `00993ff3`, then remove the four fixture paths and declare `/actuator/health/liveness`. Commit alone. Verify with a YAML parse, a `$ref` resolution check, and `git diff --stat` showing only that file changed.
2. Add `tests/contracts/` with the shared OpenAPI loader, then the three suites. No runtime file is touched.
3. Declare `PyYAML` in `pyproject.toml`; re-run `uv sync --dev` and confirm the lock file diff is limited to that declaration.
4. Add the CI step for the contract suite.
5. Perform the two red-drill verifications described in the proposal, record the commands and observed failures, then revert the drill edits.

Rollback: revert the commits. Because no runtime code, protocol, Redis key, TTL or Java source changes, rollback carries no data or compatibility risk. The contract restore is reversible by re-applying the reverse diff.

## Open Questions

None. The two decisions that would have changed scope — contract source and red-drill method — were resolved with the user before this design was written.
