# agent-stream-wire-contract Specification

## Purpose

Pins the SSE wire format the agent emits so that the event type vocabulary, the end-of-stream marker, and the error signalling convention cannot drift silently between the backend serializer and its consumers.

## Requirements

### Requirement: Event type vocabulary is closed

The wire `type` field of a streamed frame SHALL take one of exactly four values: `answer`, `thinking`, `function_call`, `status`. The contract MUST NOT declare an `end` type, because end of stream is expressed by `is_end` rather than by an event type.

#### Scenario: Every emitted event maps to a declared type
- **WHEN** any internal event kind is serialized to the wire
- **THEN** its `type` value is a member of the four-value set declared in the contract

#### Scenario: End of stream is not a type
- **WHEN** the stream terminates
- **THEN** the terminating frame sets `is_end` to true and its `type` remains one of the four declared values

#### Scenario: Undeclared type is rejected
- **WHEN** a new event type is introduced in the serializer without extending the contract
- **THEN** the contract test fails and names the undeclared value

### Requirement: Frame field set matches the contract

A serialized frame SHALL contain `type`, `content`, `is_end` and `timestamp` on every frame, and `content` SHALL be restricted to the declared sub-field set: `text`, `node`, `parent_node`, `state`, `message`, `result`, `name`, `arguments`.

#### Scenario: Always-present fields
- **WHEN** any event is serialized
- **THEN** the frame contains `type`, `content`, `is_end` and an integer `timestamp`

#### Scenario: Absent optional fields are omitted
- **WHEN** an event carries no value for an optional content sub-field
- **THEN** that key is absent from the serialized frame rather than present as null

#### Scenario: Undeclared content sub-field is rejected
- **WHEN** a content sub-field is emitted that the contract does not declare
- **THEN** the contract test fails and names the unexpected key

### Requirement: Stream framing is a single data line per frame

Each frame SHALL be emitted as one `data: ` line followed by a blank line, with the payload as JSON on that line and no SSE `event:` field.

#### Scenario: Frame shape
- **WHEN** any event is serialized
- **THEN** the output starts with `data: `, ends with two newline characters, and the remainder parses as a JSON object

### Requirement: Error signalling distinguishes tool failure from status error

A failed tool call SHALL be expressed as a `function_call` frame with `state=end` and `result=error`. A `state=error` value SHALL appear only on `status` frames and SHALL carry a human-readable `message`. The two conventions MUST NOT be conflated.

#### Scenario: Tool failure
- **WHEN** a tool raises during execution
- **THEN** the emitted frame has type `function_call`, `state=end` and `result=error`

#### Scenario: Persistence failure
- **WHEN** answer or pending-action persistence fails after the answer stream
- **THEN** the emitted frame has type `status`, `state=error` and a non-empty `message`

#### Scenario: Status error never reports success
- **WHEN** a `status` frame carries `state=error`
- **THEN** the frame does not also claim a successful tool result

### Requirement: Exactly one terminating frame closes the stream

A completed stream SHALL end with exactly one frame whose `is_end` is true, and no frame after it. When the stream terminates because of an error, the terminating frame is still produced.

#### Scenario: Normal completion
- **WHEN** the agent finishes an answer normally
- **THEN** exactly one frame has `is_end` true and it is the last frame

#### Scenario: Error completion
- **WHEN** the workflow raises mid-stream
- **THEN** an error is surfaced and the stream still terminates with exactly one `is_end` frame

#### Scenario: No frames after termination
- **WHEN** a consumer reads a frame with `is_end` true
- **THEN** the implementation emits no further frames for that stream

### Requirement: Contract declares the stream response media type

The contract SHALL declare both agent stream operations as responding with `text/event-stream` and referencing a single-frame schema, and SHALL state in prose that frames are separated by a blank line and that the payload is JSON rather than an SSE `event:` field.

#### Scenario: Media type declared
- **WHEN** the contract is inspected for an agent stream operation
- **THEN** its success response declares `text/event-stream` content

#### Scenario: Frame schema referenced
- **WHEN** the contract is inspected for an agent stream operation
- **THEN** its success response schema resolves to the single-frame schema rather than a placeholder

#### Scenario: Framing is described
- **WHEN** a reader consults the contract for the stream framing rule
- **THEN** the document states the blank-line separation and the absence of an `event:` field
