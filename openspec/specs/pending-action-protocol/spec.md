# pending-action-protocol Specification

## Purpose

Pins the persistence contract behind the preview-then-confirm write protocol so that session-scoped pending actions survive serialization round trips, expire predictably, and cannot be confirmed under a stale or foreign version.

## Requirements

### Requirement: Pending action storage key is stable

A pending action SHALL be stored under the session-scoped key `agent:pending-action:{session_id}`. The key format MUST NOT embed the user identifier, because user binding is enforced by the stored value rather than by key separation.

#### Scenario: Key derivation
- **WHEN** a pending action is saved for a session
- **THEN** the storage key is `agent:pending-action:` followed by the session identifier

#### Scenario: Key format drift is rejected
- **WHEN** the key template changes
- **THEN** the contract test fails and reports the expected and actual templates

### Requirement: Pending action expires after a bounded lifetime

A saved pending action SHALL carry an expiration of 600 seconds by default, and the stored value SHALL additionally carry an `expires_at` timestamp so expiry is enforceable after deserialization.

#### Scenario: Default TTL applied
- **WHEN** a pending action is saved without an explicit lifetime
- **THEN** the storage write applies a 600 second expiration

#### Scenario: Value carries its own deadline
- **WHEN** a pending action is serialized
- **THEN** the stored JSON contains an `expires_at` field

#### Scenario: Expired action is not usable
- **WHEN** a pending action whose `expires_at` is in the past is presented for confirmation
- **THEN** the write is refused and the user is asked to re-initiate

### Requirement: Pending actions round-trip through the discriminated union

Every pending action variant SHALL serialize to JSON and deserialize back to the same variant with equal field values. Unknown or corrupted stored JSON SHALL raise rather than being interpreted as a usable action.

#### Scenario: Round trip preserves variant and fields
- **WHEN** any pending action variant is serialized and parsed back
- **THEN** the parsed value has the same variant type and equivalent field values

#### Scenario: Unknown variant is rejected
- **WHEN** stored JSON carries a `type` value outside the declared variants
- **THEN** parsing raises a validation error and the action is not exposed to the model

#### Scenario: Corrupted JSON is rejected
- **WHEN** stored JSON is malformed
- **THEN** parsing raises a validation error rather than returning a partially populated action

### Requirement: Business-derived fields keep their wire names

Pending action payloads SHALL serialize fields carried over from a business preview response under the same case the business service emits, so a preview can be stored and later parsed without a translation layer.

#### Scenario: Alias serialization
- **WHEN** a pending action built from a business preview response is serialized
- **THEN** fields carried over from the business DTO use the camelCase names the business service produced

### Requirement: Envelope fields keep their persisted spelling

Pending action payloads SHALL serialize the envelope fields the agent defines itself -- `preview_id`, `user_id`, `expires_at` -- under their snake_case names, because that is the shape already present in persisted Redis payloads.

#### Scenario: Persisted payloads stay readable
- **WHEN** a pending action is serialized
- **THEN** the envelope fields appear as `preview_id`, `user_id` and `expires_at`
- **AND** no camelCase variant of those names is emitted

#### Scenario: Renaming an envelope field is drift
- **WHEN** the wire shape changes such that an envelope field is renamed
- **THEN** the change is reported as drift rather than accepted, since already-stored payloads would no longer parse

#### Scenario: Legacy stored payload still parses
- **WHEN** a stored payload omits a field that has a default
- **THEN** parsing succeeds and the field takes its declared default

### Requirement: Confirmation is bound to the stored version

An execution request SHALL derive the preview version from the stored pending action rather than from a model-supplied argument, so a caller cannot confirm a version that was never previewed.

#### Scenario: Preview version comes from storage
- **WHEN** an execution tool runs
- **THEN** the preview version used in the outbound call originates from the persisted pending action

#### Scenario: Stale preview is reported, not silently applied
- **WHEN** the business service reports that the preview has changed
- **THEN** the response is surfaced to the user and the stale action is not treated as applied

#### Scenario: Unsuccessful write preserves retryability
- **WHEN** a write fails for an infrastructure reason rather than a business rejection
- **THEN** the pending action is retained so the user can retry
