# Spec Delta

## Purpose

Guarantees that every HTTP call the agent makes to the business service resolves to a declared operation in the repository's OpenAPI contract, so a renamed path or field fails in CI instead of in production.

## ADDED Requirements

### Requirement: Contract file structural integrity

The OpenAPI contract at `docs/spec/openapi.yaml` SHALL parse as valid YAML and SHALL be internally consistent: every `$ref` to `#/components/schemas/*` MUST resolve to a defined schema, no schema MUST remain unreferenced, and the document MUST NOT declare paths that exist only as test fixtures.

#### Scenario: Dangling schema reference
- **WHEN** a `$ref` points at a schema key that is absent from `components.schemas`
- **THEN** the contract test fails and names the dangling reference

#### Scenario: Unreferenced schema
- **WHEN** a schema under `components.schemas` is not referenced by any `$ref`
- **THEN** the contract test fails and names the orphaned schema

#### Scenario: Test-fixture path smuggled into the contract
- **WHEN** the contract declares a path whose only implementation lives in a Java test class (for example `/api/client/private` or `/actuator/health`)
- **THEN** the contract test fails and names the fixture-only path

#### Scenario: Contract file is readable as a document
- **WHEN** CI parses `docs/spec/openapi.yaml`
- **THEN** parsing succeeds and the document exposes `openapi`, `info`, `paths` and `components.schemas`

### Requirement: Agent HTTP calls resolve to declared operations

Every outbound business HTTP call reachable from agent code SHALL correspond to a method and path template declared in the contract. The contract MAY use templated path segments (for example `/api/client/collections/{subjectId}`) where the agent passes a concrete identifier.

#### Scenario: Declared call
- **WHEN** the agent calls `GET /api/client/collections/counts`
- **THEN** the contract declares that method and path and the test passes

#### Scenario: Undeclared path
- **WHEN** the agent calls a business path that has no matching operation in the contract
- **THEN** the contract test fails and reports the offending method, path and source location

#### Scenario: Path spelling drift
- **WHEN** an agent call site is edited so its path no longer matches any declared template
- **THEN** the contract test fails before the change reaches a deployed environment

#### Scenario: Identifier segment substitution
- **WHEN** the agent calls `POST /api/client/collections/42/wishlist`
- **THEN** the test matches it against the declared template `/api/client/collections/{subjectId}/wishlist`

### Requirement: Request fields are declared by the contract

For every agent call that sends a JSON body or query parameters, each field name sent SHALL be declared in the corresponding operation's request schema or parameter list.

#### Scenario: Declared body field
- **WHEN** the agent posts `{"type": 3, "rate": 8}` to the collection save operation
- **THEN** both `type` and `rate` appear in the declared request schema properties

#### Scenario: Undeclared body field
- **WHEN** the agent sends a body field that the operation's request schema does not declare
- **THEN** the contract test fails and names the operation and the unexpected field

#### Scenario: Undeclared query parameter
- **WHEN** the agent sends a query parameter absent from the operation's `parameters` list
- **THEN** the contract test fails and names the operation and the unexpected parameter

#### Scenario: Operations with placeholder-only schemas are rejected
- **WHEN** an operation the agent calls declares no request schema but the agent sends a body
- **THEN** the contract test fails rather than silently accepting an unmodelled contract

### Requirement: Contract drift reports an actionable failure

When a contract check fails, the failure message SHALL identify the contract location, the agent call site, and the specific mismatch so a reader can act without re-deriving the comparison.

#### Scenario: Failure identifies both sides
- **WHEN** a field-name mismatch is detected
- **THEN** the assertion message includes the operation identifier, the agent source file and line, and the unexpected or missing name

#### Scenario: Whole-suite contract summary
- **WHEN** the contract suite runs
- **THEN** it reports the number of agent call sites checked so an empty or silently skipped run is visible
