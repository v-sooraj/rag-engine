# ADR-015: Add Application Observability Through Decorators and Correlation Context

## Status

Accepted

## Context

The application exposes two primary capabilities:

```text
IngestionPipeline.ingest(path)
```

and:

```text
RAGPipeline.answer(query)
```

The application also exposes these capabilities through:

```text
POST /documents
```

and:

```text
POST /answers
```

Before this decision, the application lacked a consistent way to observe:

- operation start
- operation completion
- operation failure
- operation duration
- HTTP request duration
- request correlation

The design needed to decide:

- where observability should be introduced
- whether core pipelines should contain logging code
- how durations should be measured
- how concurrent events should be correlated
- how logs should be represented
- where observed pipelines should be composed
- what information should not be logged

---

## Decision

Introduce observability through:

```text
application-level decorator pipelines
```

and:

```text
HTTP request middleware
```

The final architecture is:

```text
HTTP Request
    ↓
RequestObservabilityMiddleware
    ↓
ObservedIngestionPipeline / ObservedRAGPipeline
    ↓
DefaultIngestionPipeline / DefaultRAGPipeline
```

Use:

- Python standard logging
- structured `extra` fields
- `perf_counter()` for duration
- `ContextVar` for request correlation
- `X-Request-ID` for HTTP correlation
- newline-delimited JSON logs
- stdout as the log destination

Apply observed pipelines in the composition root.

Do not log user or document content by default.

---

## Decision Drivers

The decision is based on the following requirements:

- preserve existing application contracts
- keep core pipeline orchestration clean
- avoid coupling to a monitoring vendor
- support HTTP and non-HTTP callers
- correlate concurrent request events
- measure elapsed operation duration
- produce machine-readable logs
- protect user and document content
- keep the first observability layer small
- allow future extension to metrics and tracing

---

## Considered Option: Logging Directly Inside Default Pipelines

Conceptually:

```text
DefaultIngestionPipeline
├── start timer
├── log
├── load
├── chunk
├── embed
├── store
├── log
└── stop timer
```

Advantages:

- simple implementation
- direct access to internal stages

Disadvantages:

- mixes observability with application orchestration
- increases pipeline responsibility
- makes core logic harder to read
- introduces logging concerns into business execution
- makes observability harder to remove or replace

This option was rejected.

---

## Considered Option: Decorate Every Internal Capability

Conceptually:

```text
ObservedDocumentLoader
    ↓
PdfLoader

ObservedDocumentChunker
    ↓
RecursiveDocumentChunker

ObservedChunkEmbedder
    ↓
LocalChunkEmbedder

ObservedVectorStore
    ↓
PostgresVectorStore
```

Advantages:

- detailed per-stage timing
- detailed component visibility

Disadvantages:

- many wrapper classes
- significantly more composition complexity
- larger initial observability scope
- premature instrumentation without a demonstrated need

This option was rejected for the first observability layer.

It may be reconsidered if stage-level metrics become necessary.

---

## Selected Option: Application-Level Decorators

The selected architecture is:

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

The decorators observe the complete application operation.

They record:

- started
- completed
- failed
- duration

They do not change the internal pipeline implementation.

---

## Contract Preservation Decision

The observed pipelines implement the same abstractions as their delegates.

For ingestion:

```text
IngestionPipeline
```

For question answering:

```text
RAGPipeline
```

The decorator must preserve:

```text
same input
same output
same exception
```

Observability is additional behavior only.

---

## Composition Decision

Apply decorators in the composition root.

The selected graph is:

```text
create_ingestion_pipeline()
    ↓
ObservedIngestionPipeline
    ↓
DefaultIngestionPipeline
```

and:

```text
create_rag_pipeline()
    ↓
ObservedRAGPipeline
    ↓
DefaultRAGPipeline
```

This ensures observability applies to every composed caller.

---

## Rejected Composition Option: API-Only Decoration

The following was rejected:

```text
FastAPI Dependency
    ↓
Create Observed Pipeline
```

This would make observability dependent on the HTTP transport.

Non-HTTP callers would receive unobserved pipelines.

The selected design attaches observability to the composed application capability instead.

---

## Logging Decision

Use the Python standard logging library.

Emit events using:

```text
logger.info
```

and:

```text
logger.exception
```

Use structured fields through:

```text
extra
```

Do not introduce an external logging framework in this sprint.

---

## Event Naming Decision

Use stable event names:

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

The event name is stored as:

```text
event
```

in JSON output.

---

## Duration Decision

Use:

```text
time.perf_counter()
```

for elapsed duration.

Convert elapsed time to:

```text
duration_ms
```

This avoids using wall-clock time for performance measurement.

---

## Correlation Decision

Introduce:

```text
request_id
```

at the HTTP boundary.

If the client supplies:

```text
X-Request-ID
```

reuse it.

Otherwise:

```text
generate UUID
```

Return the resolved request ID through:

```text
X-Request-ID
```

on the response.

---

## Context Propagation Decision

Store the request ID in:

```text
ContextVar
```

The middleware sets the context.

Observed pipelines read the context.

The application contracts remain unchanged.

Rejected:

```text
ingest(path, request_id)
```

Rejected:

```text
answer(query, request_id)
```

Request correlation is operational context.

It is not domain input.

---

## Context Cleanup Decision

Use the token returned by:

```text
ContextVar.set(...)
```

and restore context with:

```text
ContextVar.reset(token)
```

This preserves previous context correctly.

---

## Request ID Outside HTTP

The request ID is optional.

When an observed pipeline executes outside HTTP:

```text
request_id = None
```

The event remains valid.

The request ID field is omitted.

This preserves support for non-HTTP callers.

---

## Output Format Decision

Emit newline-delimited JSON.

Each log event contains:

```text
timestamp
level
logger
event
```

plus event-specific fields.

This format is:

- machine-readable
- easy to test
- compatible with future log collection systems

---

## Output Destination Decision

Emit logs to:

```text
stdout
```

Do not write directly to:

- files
- cloud logging APIs
- external monitoring services

Infrastructure can collect stdout later.

---

## Privacy Decision

Do not log:

- document contents
- chunk contents
- embeddings
- full document paths
- user questions
- retrieved chunks
- augmented prompts
- generated answers

Log only operational metadata required for runtime visibility.

---

## Document Metadata Logging Decision

Log:

```text
document_filename
```

Do not log:

```text
full path
```

The filename provides useful operational identity without exposing the complete local path.

---

## Logging Field Collision Discovered

The initial implementation used:

```text
filename
```

as a custom structured field.

Python logging already defines:

```text
LogRecord.filename
```

Therefore:

```text
extra={"filename": ...}
```

raised:

```text
KeyError
```

during `LogRecord` creation.

The valid application request became:

```text
HTTP 500
```

because the logging code failed.

---

## Logging Field Correction

Rename the custom field to:

```text
document_filename
```

The final ingestion start event is:

```text
ingestion.started
├── request_id
└── document_filename
```

---

## Consequence of the Logging Collision

The failure demonstrated that:

```text
observability code can change application behavior
```

if it fails.

Therefore instrumentation must be treated as production code.

It requires:

- naming discipline
- tests
- integration verification
- privacy review
- performance awareness

---

## Exception Decision

On pipeline failure:

```text
log failure
    ↓
propagate same exception
```

Do not:

- wrap
- replace
- suppress
- translate

The decorator remains behavior-preserving.

---

## Middleware Failure Decision

On HTTP execution failure:

```text
log http.request.failed
    ↓
re-raise original exception
```

The middleware does not become an error handler.

---

## Testing Decision

Use multiple test levels.

### Unit Tests

Verify:

- context behavior
- JSON formatting
- logging configuration
- observed ingestion behavior
- observed RAG behavior

### API Tests

Verify:

- generated request IDs
- client request ID reuse
- response correlation headers

### Composition Tests

Verify:

```text
Observed Pipeline
```

is the outer composed capability.

### Real Integration Test

Verify that the complete observed application still executes real HTTP ingestion successfully.

---

## Consequences

### Positive

- core pipelines remain unchanged
- application contracts remain unchanged
- HTTP requests become correlatable
- application operations become measurable
- failures become visible
- logs become machine-readable
- user content is not logged by default
- no monitoring vendor dependency is introduced
- future metrics and tracing can build on the same architecture

### Negative

- decorators add another layer to the runtime object graph
- JSON logs are less visually compact than plain text
- operation-level timing does not reveal internal stage timing
- custom logging fields must avoid `LogRecord` collisions

### Neutral

The current observability layer is intentionally limited to:

```text
logs
correlation
operation timing
```

Detailed metrics and tracing remain future decisions.

---

## Final Decision

Use application-level decorator pipelines for operation observability.

Use HTTP middleware for request observability.

Use `ContextVar` for correlation context.

Use `X-Request-ID` for HTTP request correlation.

Use `perf_counter()` for elapsed duration.

Emit newline-delimited JSON logs to stdout.

Apply decorators in the composition root.

Do not log user or document content by default.

Preserve application inputs, outputs, and exceptions unchanged.

Treat observability code as production behavior that must be tested through real composition.