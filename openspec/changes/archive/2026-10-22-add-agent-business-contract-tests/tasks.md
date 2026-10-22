# Tasks

## 1. Repair the contract baseline

- [x] 1.1 Confirm the precondition: `git status --porcelain docs/spec/openapi.yaml` is empty, and `git log --oneline 00993ff3..HEAD -- docs/spec/openapi.yaml` lists only `22d7cb63`. Record both outputs in the task notes; if either differs, stop and report before editing.
- [x] 1.2 Restore `docs/spec/openapi.yaml` to `00993ff3` state (`git show 00993ff3:docs/spec/openapi.yaml > docs/spec/openapi.yaml`), then remove the four fixture-only paths `/api/client/subjects/1`, `/api/client/private`, `/api/admin/private`, `/actuator/health`. Verify: `git diff --stat` touches only this file, and `python -c "import yaml;yaml.safe_load(open('docs/spec/openapi.yaml',encoding='utf-8'))"` exits 0.
- [x] 1.3 Declare `GET /actuator/health/liveness` in the restored contract, matching what `app/api/health.py` actually probes and what `management.endpoint.health.probes.enabled: true` exposes in `backend/business/app/src/main/resources/application.yml`. Verify: the path exists and `info.description` documents it as an ops probe rather than a business API.
- [x] 1.4 Fill field-level definitions for the two operations the restore still leaves coarse: `/api/client/evidence/batch` and `/api/client/evidence/resolve` request bodies and responses, cross-checked against `EvidenceController.java`, `EvidenceBatchRequestDTO.java`, `EvidenceEntityBatchRequestDTO.java` and `EvidenceCandidateVO.java`. Verify: request `required` and property names in the contract equal the DTO fields, and the response schema property set equals `EvidenceCandidateVO`'s fields.
- [x] 1.5 Confirm both `*/agent/stream` operations reference `ChatRequest` and `SSEFrame` and declare `text/event-stream`. Verify: a script asserts each stream operation's success response content key is `text/event-stream` and its schema `$ref` resolves.
- [x] 1.6 Record the restore evidence: a short section in this change's `design.md` or a `contract-restore.md` note capturing the before/after counts (`$ref` count, schema count, `securitySchemes` presence, info.description length) and the commands used. Verify: the recorded numbers match a fresh run of the same commands.

## 2. Contract test scaffold

- [x] 2.1 Create `backend/agent/tests/contracts/__init__.py` and `_contract.py` exposing: a loader that parses `docs/spec/openapi.yaml` once per session, a path-template matcher implementing exact-match-first then unique-wildcard (D3), and a resolver for `#/components/schemas/*`. Verify: a self-test in `test_http_contract.py` asserts the matcher binds `/api/client/collections/counts` to the literal operation, binds an f-string `/api/client/collections/{subject_id}` to `{subjectId}`, and raises on a two-way ambiguity.
- [x] 2.2 Declare `PyYAML>=6.0` in `backend/agent/pyproject.toml` `[project].dependencies` instead of relying on the transitive `uvicorn[standard]` pull. Verify: `uv sync --dev` succeeds and `uv run python -c "import yaml"` works; the `uv.lock` diff is limited to that declaration.

## 3. HTTP contract suite

- [x] 3.1 Implement the call-site walker in `tests/contracts/test_http_contract.py`: AST walk over `app/**/*.py` collecting `<obj>.request(...)` and `asyncio.to_thread(<obj>.request, ...)`, extracting literal method, literal/f-string path (f-string parts become `{param}`), and resolving `BUSINESS_LIVENESS_PATH` from `app.api.health`. Exclude the adapter's internal `httpx.request`. Verify: the collected count equals 25 (24 attribute calls + 1 to_thread probe) and a guard assertion fails the run if fewer than 24 are found, so a broken walker cannot pass vacuously.
- [x] 3.2 Assert every discovered method+path resolves to a declared operation. Verify: the test passes on the repaired contract, and a parametrized case with a deliberately misspelled path fails with a message naming method, path and source `file:line`.
- [x] 3.3 Assert request fields for the statically-literal payload sites (dict literals passed directly, dict literals bound to a local then passed, and string-subscript additions to such a local) are declared in the operation's request schema properties or `parameters`. Verify: posting an undeclared field to the collection save operation fails and names the unexpected field; a normal run passes.
- [x] 3.4 Add the explicit exemption table for payload sites whose body is built at runtime (currently `lexical_search` forwarding a caller-built query dict), each entry carrying file, line and reason, plus an assertion that every exemption still maps to a live call site. Verify: deleting a call site makes the exemption test fail rather than silently shrinking coverage.
- [x] 3.5 Assert contract structural integrity: no dangling `$ref`, no unreferenced schema, no fixture-only path from the deny-list (`/api/client/subjects/1`, `/api/client/private`, `/api/admin/private`, `/actuator/health`), and required top-level keys present. Verify: the suite passes on the repaired contract; re-introducing any one fixture path or a dangling `$ref` makes exactly the corresponding assertion fail.

## 4. SSE wire contract suite

- [x] 4.1 Assert the type vocabulary is closed and `end` is absent: build every `AgentEventType` member, serialize with `serialize_agent_event`, and compare observed `type` values against the contract `SSEFrame.properties.type.enum`. Verify: the observed set equals the enum set, the enum contains no `end`, and the live `AgentEventType` members minus `END` equal the enum set (fails if either side gains a value).
- [x] 4.2 Assert the frame field set: every frame carries `type`, `content`, `is_end`, integer `timestamp`; absent optional content fields are omitted rather than null; observed `content` keys are a subset of the contract's declared `content` properties. Verify: a case emitting an undeclared content key fails and names the key.
- [x] 4.3 Assert framing shape: output begins `data: `, ends with a blank line, and the payload parses as one JSON object. Verify: the assertion set fails when the serializer is fed a frame whose text contains no special handling and passes on the real serializer.
- [x] 4.4 Assert error-signalling separation: tool failure produces `type=function_call` with `state=end` and `result=error`; persistence failure produces `type=status` with `state=error` and a non-empty `message`; and no `status` frame carrying `state=error` also claims a successful result. Verify: all three assertions pass, and flipping the tool-failure convention to `state=error` makes 4.4 fail.
- [x] 4.5 Assert exactly one terminating frame: driving the stream producer for a normal completion and for a mid-stream exception each yields exactly one `is_end=true` frame, positioned last, with no frames after it. Verify: both cases pass; a producer variant that omits the terminating frame on error makes the error case fail.
- [x] 4.6 Assert the contract declares the stream response properly for both agent stream operations: `text/event-stream` content present, schema resolves to the single-frame schema, and the operation `description` states blank-line framing and the absence of an `event:` field. Verify: the assertion set fails if either stream operation's content type is reverted to a placeholder.

## 5. Pending-action protocol suite

- [x] 5.1 Assert the storage key template: import the store's key-derivation behaviour and assert the template equals `agent:pending-action:{session_id}`, and that the template does not embed a user identifier. Verify: the test fails if the prefix or placeholder changes.
- [x] 5.2 Assert the TTL default is 600 seconds and that the serialized value carries `expires_at`. Verify: both assertions pass; changing the default TTL to 300 makes the test fail.
- [x] 5.3 Assert discriminated-union round trips: for every variant in the `PendingAction` union, construct an instance, `model_dump_json(by_alias=True)`, then `parse_pending_action_json`, and assert the variant type and all field values survive. Verify: all variants pass; an unknown `type` value and malformed JSON each raise a validation error rather than returning a usable action.
- [x] 5.4 Assert camelCase alias compatibility and legacy tolerance: serialized keys are the camelCase aliases, and a stored payload missing a defaulted field still parses to the declared default. Verify: both assertions pass, and removing a default makes the legacy case fail.
- [x] 5.5 Assert confirmation is bound to the stored version: drive the progress previewable's execute path with a stub gateway and assert the outbound URL contains the `preview_id` taken from the persisted pending action, and that a differing model-supplied tool argument does not change it. Verify: the assertion fails if the implementation prefers the argument over the stored value.
- [x] 5.6 Assert stale-preview and retryability semantics: a business "preview changed" response is surfaced rather than treated as applied, and an infrastructure failure retains the pending action for retry. Verify: both assertions pass; forcing the infrastructure branch to clear the action makes the second one fail.

## 6. CI and integration

- [x] 6.1 Add an explicit contract step to the `backend-python` job in `.github/workflows/ci.yml` running `uv run pytest tests/contracts -q` before the full suite, labelled so a failure reads as contract drift. Verify: the workflow file parses as YAML and the step command runs locally with the same working directory and exits 0.
- [x] 6.2 Run the full backend suite and confirm no regression: `cd backend/agent && uv run pytest -q`. Verify: baseline 668 collected previously; final count equals 668 plus the new contract tests, with zero failures and zero previously-passing tests now failing.
- [x] 6.3 Confirm the runtime-untouched constraint: `git status --porcelain` shows changes only under `docs/spec/openapi.yaml`, `backend/agent/tests/contracts/`, `backend/agent/pyproject.toml`, `backend/agent/uv.lock`, `.github/workflows/ci.yml` and this change's directory. Verify: `backend/agent/app/**`, `backend/business/**` and `frontend/**` have no diff.

## 7. Red-drill verification

- [x] 7.1 Drill A — contract-side drift: temporarily rename a field asserted by the HTTP suite (for example `epStatus` → `ep_status`) in `docs/spec/openapi.yaml`, run `uv run pytest tests/contracts -q`, capture the failure output, then revert. Verify: the run is red, the message names the operation and the field, and after revert the suite is green.
- [x] 7.2 Drill B — agent-side drift: temporarily misspell a path in an agent call site (for example `counts` → `count`), run `uv run pytest tests/contracts -q`, capture the failure output, then revert. Verify: the run is red and names the call site `file:line`; after revert it is green.
- [x] 7.3 Record both drills (command, observed failure text, revert confirmation) in the change directory as `drills.md`, and state plainly in it that the drills prove agent↔contract binding only, not contract↔Java binding. Verify: the file exists and its recorded failure text matches what the drills produced.

## 8. Documentation

- [x] 8.1 Update `.trellis/spec/guides/cross-layer-thinking-guide.md` line stating "仍**无 CI 自动校验漂移**" to reflect that the contract suite now exists for the agent↔contract boundary, while keeping the honest limitation that contract↔Java remains unverified. Verify: the guide no longer claims zero automated drift checking, and still states the remaining gap.
- [x] 8.2 Add a docstring to `tests/contracts/__init__.py` (or a `README.md` in that directory) stating the suite's scope and its explicit non-goal, so a future reader does not over-trust it. Verify: the stated scope matches spec `agent-business-contract` Purpose, and the non-goal sentence matches the Risks section of `design.md`.
- [x] 8.3 Confirm `backend/agent/README.md` and `docs/README.md` statements about the contract counting 68 paths still hold, or update them if the restore changed the path count. Verify: `grep -cE '^  /' docs/spec/openapi.yaml` matches the number quoted in both documents.

## Workflow follow-up

- Archive the change after review requirements are satisfied.
- After archive, verify the three new capabilities appear under `openspec/specs/` with their Purpose sections intact.
- Sync the parent Trellis task `10-20-agent-module-optimization` (sub-task 4 of 4) once this change lands.
