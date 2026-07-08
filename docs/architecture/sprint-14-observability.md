# Sprint 14 — Observability

## Status

Completed

## Objective

Introduce application observability without changing the behavior or contracts of the existing RAG engine.

Before this sprint, the application could execute:

```text
POST /documents
    ↓
IngestionPipeline
```

and:

```text
POST /answers
    ↓
RAGPipeline
```

However, when a request succeeded, failed, or became slow, the application did not provide a consistent way to answer:

```text
What happened?
```

```text
How long did it take?
```

```text
Which events belong to the same request?
```

The goal of this sprint was to introduce an observability foundation that provides:

- structured application events
- operation duration measurement
- request correlation
- HTTP request visibility
- pipeline success and failure visibility
- machine-readable JSON logs

without introducing:

- a monitoring vendor
- a metrics platform
- distributed tracing infrastructure
- observability concerns inside the core pipeline implementations

---

## Scope

This sprint includes:

- application-level pipeline decorators
- observed ingestion pipeline
- observed RAG pipeline
- operation duration measurement
- success events
- failure events
- correlation ID context
- HTTP request observability middleware
- generated request IDs
- client request ID reuse
- `X-Request-ID` response propagation
- structured logging fields
- newline-delimited JSON logs
- stdout logging
- exception logging
- privacy-safe operational metadata
- observed pipeline composition
- unit and integration tests

This sprint does not include:

- Prometheus metrics
- OpenTelemetry
- distributed tracing
- trace spans
- dashboards
- alerts
- cloud monitoring integration
- per-stage pipeline timing
- token usage metrics
- embedding model metrics
- LLM model metrics
- log shipping infrastructure
- centralized log storage

These concerns belong to later observability layers.

---

## Problem Before This Sprint

The application already had a complete external RAG lifecycle.

### Knowledge Ingestion

```text
POST /documents
    ↓
DocumentUploadAdapter
    ↓
IngestionPipeline
    ↓
PostgreSQL + pgvector
```

### Question Answering

```text
POST /answers
    ↓
RAGPipeline
    ↓
Retrieval
    ↓
Prompt Augmentation
    ↓
LLM
```

However, the runtime behavior was largely invisible.

For example, if ingestion became slow:

```text
POST /documents
    ↓
5 seconds
    ↓
201 Created
```

the application did not consistently record:

```text
how long ingestion took
```

If generation failed:

```text
POST /answers
    ↓
500 Internal Server Error
```

the application did not provide a structured event showing:

```text
which application operation failed
```

Concurrent requests also had no common identifier.

Logs could appear as:

```text
rag.started
ingestion.started
rag.completed
ingestion.completed
```

without a reliable way to determine which events belonged to which HTTP request.

---

## Observability Goal

The observability foundation should answer three questions.

### What Happened?

Through structured events:

```text
http.request.started
http.request.completed
http.request.failed

ingestion.started
ingestion.completed
ingestion.failed

rag.started
rag.completed
rag.failed
```

### How Long Did It Take?

Through:

```text
duration_ms
```

### Which Request Did It Belong To?

Through:

```text
request_id
```

---

## Selected Architecture

The selected architecture uses two observability layers.

### HTTP Layer

```text
HTTP Request
    ↓
RequestObservabilityMiddleware
```

The middleware observes:

- request start
- request completion
- request failure
- HTTP duration
- HTTP method
- HTTP path
- HTTP status
- request correlation

### Application Operation Layer

```text
ObservedIngestionPipeline
    ↓
DefaultIngestionPipeline
```

and:

```text
ObservedRAGPipeline
    ↓
DefaultRAGPipeline
```

The decorators observe:

- operation start
- operation completion
- operation failure
- operation duration
- operational metadata

---

## Complete Runtime Architecture

```text
HTTP Request
    ↓
RequestObservabilityMiddleware
├── resolve request_id
├── set request context
├── log HTTP start
└── start HTTP timer
    ↓
Route
    ↓
Observed Pipeline
├── log operation start
├── start operation timer
└── delegate
    ↓
Default Pipeline
    ↓
Observed Pipeline
├── log completion or failure
└── record duration
    ↓
Route
    ↓
RequestObservabilityMiddleware
├── add X-Request-ID
├── log HTTP completion
├── record HTTP duration
└── reset request context
    ↓
HTTP Response
```

---

## Why Decorator Pipelines Were Selected

The existing pipelines already contain application orchestration.

For ingestion:

```text
DefaultIngestionPipeline
├── load
├── chunk
├── embed
└── store
```

For question answering:

```text
DefaultRAGPipeline
├── embed query
├── retrieve
├── augment prompt
└── generate
```

One possible implementation was to add logging directly inside these classes.

Conceptually:

```text
start timer
 ↓
log
 ↓
execute operation
 ↓
log
 ↓
stop timer
```

This was rejected because observability would become mixed with application orchestration.

Instead:

```text
Observed Pipeline
    ↓
Default Pipeline
```

The default pipeline remains focused on:

```text
business/application orchestration
```

The decorator remains focused on:

```text
operational observation
```

---

## Decorator Contract

The decorator must preserve the underlying application capability.

For ingestion:

```text
IngestionPipeline.ingest(path)
    ↓
UUID
```

The observed pipeline preserves:

```text
ObservedIngestionPipeline.ingest(path)
    ↓
UUID
```

For RAG:

```text
RAGPipeline.answer(query)
    ↓
GeneratedAnswer
```

The observed pipeline preserves:

```text
ObservedRAGPipeline.answer(query)
    ↓
GeneratedAnswer
```

The decorator must preserve:

- input
- output
- exception identity
- application behavior

It adds only:

- logging
- timing
- operational metadata

---

## Composition Root

Observability is applied in the composition root.

Before Sprint 14:

```text
create_ingestion_pipeline()
    ↓
DefaultIngestionPipeline
```

After Sprint 14:

```text
create_ingestion_pipeline()
    ↓
ObservedIngestionPipeline
    ↓
DefaultIngestionPipeline
```

Before Sprint 14:

```text
create_rag_pipeline()
    ↓
DefaultRAGPipeline
```

After Sprint 14:

```text
create_rag_pipeline()
    ↓
ObservedRAGPipeline
    ↓
DefaultRAGPipeline
```

This means every caller of the composed application receives the observed capability.

Observability is not applied only in the API dependency layer.

Therefore:

```text
HTTP Caller
```

and:

```text
Non-HTTP Caller
```

can both receive observed pipelines.

---

## Why Observability Is Not Applied in the API Dependency Layer

The following design was rejected:

```text
API Dependency
    ↓
Wrap Pipeline with Observability
```

That would make observability specific to HTTP callers.

Instead:

```text
Composition Root
    ↓
Observed Application Capability
```

This keeps observability attached to the application operation rather than a specific transport.

The request ID remains optional outside HTTP.

---

## Package Structure

```text
rag_engine/
├── observability/
│   ├── __init__.py
│   ├── context.py
│   ├── json_formatter.py
│   ├── logging_config.py
│   ├── observed_ingestion_pipeline.py
│   └── observed_rag_pipeline.py
│
└── api/
    └── middleware/
        ├── __init__.py
        └── request_observability.py
```

Test structure:

```text
tests/
├── observability/
│   ├── __init__.py
│   ├── test_context.py
│   ├── test_json_formatter.py
│   ├── test_logging_config.py
│   ├── test_observed_ingestion_pipeline.py
│   └── test_observed_rag_pipeline.py
│
└── api/
    └── test_request_observability.py
```

Composition tests also verify that the observed decorators are the outer application capabilities.

---

## Structured Logging

The application uses the Python standard logging library.

Events are emitted using:

```text
logger.info(...)
```

and:

```text
logger.exception(...)
```

with structured fields passed through:

```text
extra
```

Conceptually:

```text
event = ingestion.completed

fields:
├── request_id
├── document_id
└── duration_ms
```

The event name remains the log message.

Operational metadata remains structured fields.

---

## Why Plain Interpolated Messages Were Rejected

A log such as:

```text
Ingested document 123 in 532.4 milliseconds
```

is readable by humans.

However, downstream systems must parse text to recover:

```text
document_id
```

and:

```text
duration_ms
```

The selected structure is:

```text
event = ingestion.completed
document_id = 123
duration_ms = 532.4
```

This keeps operational fields machine-readable.

---

## JSON Logging

Logs are emitted as newline-delimited JSON.

Example:

```json
{
  "timestamp": "2026-07-08T06:49:20.734598+00:00",
  "level": "INFO",
  "logger": "rag_engine.observability.observed_ingestion_pipeline",
  "event": "ingestion.completed",
  "request_id": "abc-123",
  "document_id": "document-uuid",
  "duration_ms": 5430.39
}
```

Each log record is one JSON object.

The common fields are:

```text
timestamp
level
logger
event
```

Additional fields depend on the event.

---

## JSON Formatter

The custom JSON formatter converts:

```text
LogRecord
```

into:

```text
JSON object
```

It includes:

```text
timestamp
level
logger
event
```

and safe custom fields supplied through:

```text
extra
```

For failures, it also includes formatted exception information.

Non-JSON-native values are converted to strings.

---

## Logging Configuration

Logging is configured once during application creation.

The flow is:

```text
create_app()
    ↓
configure_logging()
    ↓
Root Logger
    ↓
stdout StreamHandler
    ↓
JsonFormatter
```

The application therefore emits structured logs to:

```text
stdout
```

This avoids coupling the application to:

- a cloud vendor
- a log collector
- a monitoring platform

Deployment infrastructure can later collect stdout.

---

## Why stdout Was Selected

The application does not write directly to:

- local log files
- cloud logging APIs
- external monitoring SDKs

Instead:

```text
Application
    ↓
stdout
```

Future deployment infrastructure can route stdout to:

```text
Container Logs
```

```text
Cloud Logging
```

```text
Log Aggregation Platform
```

without changing application code.

---

## Duration Measurement

Elapsed duration is measured using:

```text
time.perf_counter()
```

The flow is:

```text
started_at = perf_counter()
    ↓
execute operation
    ↓
perf_counter() - started_at
```

The result is converted to:

```text
milliseconds
```

and rounded to two decimal places.

---

## Why perf_counter Was Selected

Elapsed duration is not wall-clock time.

The application needs to measure:

```text
how long an operation took
```

not:

```text
what time the operation occurred
```

`perf_counter()` is designed for elapsed duration measurement.

---

## Correlation IDs

The application introduces:

```text
request_id
```

for HTTP request correlation.

Without a correlation ID:

```text
http.request.started
rag.started
http.request.started
ingestion.started
rag.completed
```

cannot reliably be grouped by request.

With correlation IDs:

```text
request_id = abc-123

http.request.started
rag.started
rag.completed
http.request.completed
```

can be connected.

---

## Request ID Resolution

The middleware checks:

```text
X-Request-ID
```

### Client Supplies Request ID

```text
Request
X-Request-ID: client-request-123
    ↓
reuse client-request-123
```

### Client Does Not Supply Request ID

```text
Request
    ↓
generate UUID
```

The resolved request ID is returned in:

```text
X-Request-ID
```

on the response.

---

## Correlation Context

The request ID is stored using:

```text
ContextVar
```

The flow is:

```text
Middleware
    ↓
set request_id
    ↓
Route
    ↓
Observed Pipeline
    ↓
get request_id
```

This avoids changing application contracts.

The application does not need:

```text
ingest(path, request_id)
```

or:

```text
answer(query, request_id)
```

Correlation is operational context.

It is not business input.

---

## Context Reset

Setting a `ContextVar` returns a token.

The middleware uses:

```text
set request_id
    ↓
receive token
```

and finally:

```text
reset request ID using token
```

This restores the previous context.

The middleware does not simply set the request ID to:

```text
None
```

because nested or previous context may exist.

---

## Request ID Outside HTTP

The observed pipelines can execute without HTTP.

In that case:

```text
request_id = None
```

The event is still logged.

The `request_id` field is omitted.

This allows:

```text
CLI caller
```

```text
test caller
```

```text
background caller
```

to use the same composed application capability.

---

## HTTP Observability Events

The middleware emits:

```text
http.request.started
```

with:

```text
request_id
method
path
```

A successful request emits:

```text
http.request.completed
```

with:

```text
request_id
method
path
status_code
duration_ms
```

A failed request emits:

```text
http.request.failed
```

with:

```text
request_id
method
path
duration_ms
exception_type
exception
```

---

## Ingestion Observability Events

The observed ingestion pipeline emits:

```text
ingestion.started
```

with:

```text
request_id
document_filename
```

A successful ingestion emits:

```text
ingestion.completed
```

with:

```text
request_id
document_id
duration_ms
```

A failed ingestion emits:

```text
ingestion.failed
```

with:

```text
request_id
duration_ms
exception_type
exception
```

---

## RAG Observability Events

The observed RAG pipeline emits:

```text
rag.started
```

with:

```text
request_id
```

A successful operation emits:

```text
rag.completed
```

with:

```text
request_id
duration_ms
```

A failed operation emits:

```text
rag.failed
```

with:

```text
request_id
duration_ms
exception_type
exception
```

---

## Privacy-Safe Logging

The observability layer deliberately does not log:

- full document paths
- document contents
- chunk contents
- embeddings
- user questions
- retrieved context
- augmented prompts
- generated answers

These values may contain:

- sensitive information
- private information
- large payloads
- confidential document content

The selected default is operational metadata only.

---

## Document Path Privacy

The ingestion pipeline receives:

```text
filesystem path
```

The observed decorator does not log the full path.

For example:

```text
C:\private\temporary-directory\document.pdf
```

is not logged.

Only:

```text
document.pdf
```

is logged through:

```text
document_filename
```

---

## Query and Answer Privacy

The observed RAG pipeline receives:

```text
query
```

and returns:

```text
GeneratedAnswer
```

Neither is logged.

The decorator records:

```text
operation started
operation completed
operation failed
duration
request correlation
```

without recording user content.

---

## Exception Behavior

The decorators preserve the original exception.

The failure flow is:

```text
Delegate Raises Exception
    ↓
Observed Decorator Logs Failure
    ↓
Same Exception Propagates
```

The decorator does not:

- replace the exception
- wrap the exception
- translate the exception
- suppress the exception

This preserves application behavior.

---

## Middleware Failure Behavior

When request execution raises an exception:

```text
call_next()
    ↓
Exception
```

the middleware emits:

```text
http.request.failed
```

and re-raises the original exception.

The middleware remains an observer.

It does not become an HTTP error-mapping layer.

---

## Observability Bug Discovered During Integration Testing

The first observed ingestion implementation logged:

```text
filename
```

through:

```text
extra
```

Conceptually:

```python
extra={
    "filename": "document.pdf"
}
```

This caused:

```text
KeyError
```

with:

```text
Attempt to overwrite 'filename' in LogRecord
```

---

## Why the Logging Failure Occurred

Python `LogRecord` already contains:

```text
filename
```

as a built-in attribute.

Passing:

```text
filename
```

through:

```text
extra
```

attempted to overwrite the existing field.

The failure happened during:

```text
LogRecord creation
```

before the JSON formatter executed.

Therefore the request flow became:

```text
Valid Document Upload
    ↓
ObservedIngestionPipeline
    ↓
logger.info(...)
    ↓
LogRecord Field Collision
    ↓
KeyError
    ↓
HTTP 500
```

The ingestion business logic was valid.

The observability code broke it.

---

## Final Logging Field

The custom field was renamed from:

```text
filename
```

to:

```text
document_filename
```

The final event is:

```text
ingestion.started
├── request_id
└── document_filename
```

This avoids collision with Python logging internals.

---

## Why the JSON Formatter Could Not Fix the Collision

The failure happened before formatting.

The sequence is:

```text
logger.info(...)
    ↓
Create LogRecord
    ↓
Merge extra fields
    ↓
KeyError
```

The formatter runs only after:

```text
LogRecord created successfully
```

Therefore adding `filename` to formatter filtering rules would not solve the problem.

The custom field itself had to be renamed.

---

## Observability Must Be Behavior-Preserving

The logging collision demonstrated an important rule.

Before observability:

```text
Valid Request
    ↓
Successful Ingestion
```

After incorrect observability:

```text
Valid Request
    ↓
Logging Failure
    ↓
HTTP 500
```

Therefore:

```text
Observability code is production code.
```

It can introduce:

- exceptions
- performance cost
- data exposure
- behavior changes

Instrumentation must be tested as part of the runtime system.

---

## Why the Real HTTP Integration Test Was Valuable Again

The isolated API tests replace:

```text
IngestionPipeline
```

with:

```text
Mock IngestionPipeline
```

Therefore they do not execute:

```text
ObservedIngestionPipeline
```

The real HTTP ingestion test executes:

```text
POST /documents
    ↓
real dependency
    ↓
ObservedIngestionPipeline
    ↓
DefaultIngestionPipeline
```

That test exposed the logging field collision.

The lesson is:

```text
Mocked boundary tests prove HTTP behavior.
```

```text
Real composition tests prove runtime integration.
```

Both are necessary.

---

## Test Strategy

Sprint 14 uses multiple test levels.

### Context Tests

Verify:

```text
default request ID
set request ID
read request ID
reset request ID
restore previous request ID
```

### JSON Formatter Tests

Verify:

```text
valid JSON output
common fields
custom fields
non-JSON-native values
```

### Logging Configuration Tests

Verify:

```text
JSON output to stdout
root logger configuration
handler replacement
```

### Observed Ingestion Pipeline Tests

Verify:

```text
delegate invocation
same UUID returned
start event
completion event
failure event
duration
request ID propagation
request ID omission outside HTTP
document filename without full path
same exception propagation
```

### Observed RAG Pipeline Tests

Verify:

```text
delegate invocation
same GeneratedAnswer returned
start event
completion event
failure event
duration
request ID propagation
query privacy
answer privacy
same exception propagation
```

### HTTP Middleware Tests

Verify:

```text
generated request ID
client request ID reuse
X-Request-ID response header
document endpoint correlation
```

### Composition Tests

Verify:

```text
create_ingestion_pipeline()
    ↓
ObservedIngestionPipeline
```

and:

```text
create_rag_pipeline()
    ↓
ObservedRAGPipeline
```

### Real HTTP Integration Test

Verifies that the complete observed composition still supports real ingestion.

---

## Test Count

Before Sprint 14:

```text
143 tests
```

Sprint 14 added:

```text
27 tests
```

The complete suite now contains:

```text
170 tests passing
```

---

## Architecture Before and After

### Before Sprint 14

```text
HTTP Request
    ↓
Route
    ↓
Pipeline
    ↓
Response
```

Runtime execution was mostly invisible.

### After Sprint 14

```text
HTTP Request
    ↓
HTTP Observability
    ↓
Route
    ↓
Application Operation Observability
    ↓
Pipeline
    ↓
Application Operation Observability
    ↓
HTTP Observability
    ↓
Response
```

The application now provides:

```text
correlation
timing
success visibility
failure visibility
structured output
```

---

## Example Successful Ingestion Trace

```text
request_id = abc-123
```

```text
http.request.started
    ↓
ingestion.started
    ↓
ingestion.completed
    ↓
http.request.completed
```

All events can be connected through:

```text
request_id
```

---

## Example Failed RAG Trace

```text
request_id = xyz-456
```

```text
http.request.started
    ↓
rag.started
    ↓
rag.failed
    ↓
http.request.failed
```

The failure events include:

```text
exception_type
```

and exception information.

---

## Current Observability Level

The application currently provides:

```text
Level 1
```

application-operation observability.

It can answer:

```text
Did the HTTP request succeed?
```

```text
How long did the HTTP request take?
```

```text
Did ingestion succeed?
```

```text
How long did ingestion take?
```

```text
Did RAG generation succeed?
```

```text
How long did the RAG operation take?
```

```text
Which events belong to the same request?
```

It cannot yet answer:

```text
Which internal stage was slow?
```

For example:

```text
ingestion duration = 5000 ms
```

does not yet distinguish:

```text
loading
chunking
embedding
storage
```

That belongs to a later observability layer.

---

## Key Learning Outcomes

This sprint established that:

- observability can be added through decorators without changing core pipeline logic
- application capabilities should preserve their original contracts when decorated
- observability belongs in composition rather than only in HTTP dependencies
- correlation IDs are operational context rather than business input
- `ContextVar` allows correlation without changing method signatures
- request context must be reset using the returned token
- elapsed duration should use `perf_counter`
- structured logs are more machine-readable than interpolated messages
- JSON logs can be emitted using only the Python standard library
- stdout keeps the application independent of monitoring vendors
- sensitive user and document content should not be logged by default
- custom logging fields must avoid built-in `LogRecord` attributes
- logging failures can break valid application requests
- observability code must be behavior-preserving
- isolated tests cannot prove the complete observed runtime composition
- real integration tests remain valuable after adding cross-cutting concerns

---

## Sprint Outcome

Sprint 14 introduced a complete first observability layer.

The application now provides:

```text
HTTP Correlation
    +
HTTP Timing
    +
Application Operation Timing
    +
Success Events
    +
Failure Events
    +
JSON Logs
```

The final runtime architecture is:

```text
HTTP Request
    ↓
RequestObservabilityMiddleware
    ↓
Observed Application Capability
    ↓
Default Application Capability
    ↓
Structured JSON Events
```

The application remains independent of:

- monitoring vendors
- metrics platforms
- tracing platforms

The complete suite passes:

```text
170 tests
```