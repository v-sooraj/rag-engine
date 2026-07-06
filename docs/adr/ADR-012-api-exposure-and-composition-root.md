# ADR-012: Expose the RAG Pipeline Through a Thin HTTP Adapter and Explicit Composition Root

## Status

Accepted

## Context

The application already exposes a complete online RAG capability:

```text
RAGPipeline.answer(query)
    ↓
GeneratedAnswer
```

The internal flow is:

```text
Query
 ↓
QueryEmbedder
 ↓
Retriever
 ↓
PromptAugmenter
 ↓
LLM
 ↓
GeneratedAnswer
```

The application needed an external boundary so clients could invoke this capability through HTTP.

The design needed to decide:

- where the FastAPI package should live
- whether the API belongs inside the RAG pipeline package
- where concrete application dependencies should be constructed
- whether `app.py` should construct the complete object graph
- whether to introduce a dependency injection framework
- how FastAPI should receive the RAG pipeline
- how expensive shared resources should be reused
- how API tests should replace real infrastructure
- how application failures should map to HTTP responses

---

## Decision

Introduce a top-level:

```text
rag_engine/api
```

package as an inbound HTTP adapter.

Introduce a separate:

```text
rag_engine/composition
```

package as the application composition root.

Use FastAPI dependency injection to provide:

```text
RAGPipeline
```

to the HTTP endpoint.

Construct the real pipeline once and reuse the application-scoped instance.

Use FastAPI dependency overrides in API tests.

Keep error handling minimal:

```text
invalid HTTP request
    ↓
422
```

```text
unexpected pipeline failure
    ↓
500
```

Do not introduce a dependency injection framework or a new pipeline exception hierarchy.

---

## Decision Drivers

The decision is based on the following requirements:

- expose the completed RAG capability through HTTP
- keep the API layer thin
- preserve the existing RAG pipeline boundary
- prevent FastAPI dependencies from entering the core application
- separate application composition from HTTP application creation
- avoid per-request embedding model loading
- make API tests independent of PostgreSQL and Ollama
- preserve explicit and understandable dependency construction
- avoid unnecessary framework complexity
- avoid premature exception taxonomy design

---

## Considered API Package Locations

### Option A — API Inside RAG Pipeline

```text
rag_engine/
└── rag_pipeline/
    ├── rag_pipeline.py
    ├── default_rag_pipeline.py
    └── api/
```

Advantages:

- keeps code related to question answering together

Disadvantages:

- mixes HTTP concerns with application orchestration
- weakens architectural boundaries
- risks introducing FastAPI dependencies into the pipeline package
- makes the pipeline appear HTTP-specific

This option was rejected.

---

### Option B — Top-Level API Adapter

```text
rag_engine/
├── api/
└── rag_pipeline/
```

Advantages:

- clearly separates HTTP adaptation from orchestration
- preserves dependency direction
- keeps the RAG pipeline framework-independent
- supports future non-HTTP callers

This option was selected.

---

## Dependency Direction

The selected dependency direction is:

```text
HTTP
 ↓
API
 ↓
RAGPipeline
```

The following direction is prohibited:

```text
RAGPipeline
 ↓
FastAPI
```

The application capability remains usable without the HTTP framework.

---

## Thin Adapter Decision

The API endpoint performs:

```text
AnswerRequest
    ↓
extract query
    ↓
RAGPipeline.answer(query)
    ↓
GeneratedAnswer
    ↓
AnswerResponse
```

The API does not perform:

- query embedding
- vector search
- retrieval filtering
- prompt construction
- LLM invocation

These responsibilities remain behind `RAGPipeline`.

---

## API Contract

The selected endpoint is:

```text
POST /answers
```

The request contract is:

```json
{
  "query": "What do vector databases store?"
}
```

The response contract is:

```json
{
  "answer": "Vector databases store embeddings."
}
```

The API uses dedicated request and response models.

---

## Why API Models Are Separate From Domain Models

The application already contains:

```text
GeneratedAnswer
└── content
```

The API exposes:

```text
AnswerResponse
└── answer
```

The HTTP model is not replaced with the internal domain model.

This keeps:

```text
external API contract
```

separate from:

```text
internal application contract
```

The two models may evolve independently.

---

## Request Validation Decision

The HTTP request model validates:

- query presence
- string type
- non-null value
- non-empty value
- non-blank value

Invalid requests return:

```text
422 Unprocessable Entity
```

The RAG pipeline also retains its own query validation.

---

## Why Validation Exists at Both Boundaries

The API and RAG pipeline are separate public boundaries.

The responsibility is:

```text
API
└── validate HTTP request contract
```

```text
RAGPipeline
└── validate application operation contract
```

This is intentional.

The pipeline may be called without HTTP.

The API should not depend on downstream validation to define its request contract.

---

## Considered Composition Locations

### Option A — Construct Everything in app.py

```text
app.py
├── create SentenceTransformer
├── create QueryEmbedder
├── create Retriever
├── create PromptAugmenter
├── create LLM
├── create RAGPipeline
├── create FastAPI
└── register routes
```

Advantages:

- fewer files
- simple initial implementation

Disadvantages:

- mixes object graph construction with HTTP application creation
- makes `app.py` infrastructure-heavy
- weakens responsibility separation
- becomes difficult to maintain as the object graph grows

This option was rejected.

---

### Option B — Dedicated Composition Root

```text
rag_engine/
└── composition/
    └── application.py
```

The composition root:

```text
constructs concrete dependencies
    ↓
connects dependencies
    ↓
produces RAGPipeline
```

Advantages:

- explicit object graph
- separate from HTTP concerns
- easy to inspect and debug
- central location for application construction

This option was selected.

---

## Composition Root Responsibility

The composition root currently creates:

```text
SentenceTransformer
```

```text
LocalQueryEmbedder
```

```text
PostgresRetriever
```

```text
DefaultPromptAugmenter
```

```text
OllamaLLM
```

and:

```text
DefaultRAGPipeline
```

The composition root decides:

```text
which concrete implementations
```

The pipeline decides:

```text
how capabilities are orchestrated
```

The API decides:

```text
how HTTP is adapted
```

---

## No Dependency Injection Framework

A dedicated dependency injection framework was not introduced.

Advantages of avoiding one at the current scale:

- fewer dependencies
- less indirection
- explicit construction
- easier debugging
- easier learning
- simpler tests

The application object graph is currently small enough to construct directly.

This decision can be revisited if composition becomes significantly more complex.

---

## Considered Pipeline Injection Approaches

### Option A — Module-Level Global Pipeline

```text
module import
    ↓
construct pipeline
    ↓
route uses global object
```

Advantages:

- minimal code

Disadvantages:

- expensive initialization may happen during import
- global state is harder to replace in tests
- route becomes coupled to one concrete instance
- test isolation becomes weaker

This option was rejected.

---

### Option B — FastAPI Dependency Injection

```text
route
 ↓
Depends(get_rag_pipeline)
 ↓
RAGPipeline
```

Advantages:

- route depends on the abstraction
- production composition remains replaceable
- tests can override the dependency
- API tests avoid real infrastructure

This option was selected.

---

## Application-Scoped Pipeline Decision

The pipeline is not constructed for every request.

The composition function returns a cached application-scoped instance.

The lifecycle is:

```text
first resolution
    ↓
construct complete pipeline
    ↓
cache
```

then:

```text
later request
    ↓
reuse pipeline
```

---

## Why Pipeline Reuse Is Required

The pipeline contains a local query embedder backed by a sentence-transformer model.

Repeated per-request construction would cause:

- repeated model loading
- unnecessary memory usage
- increased request latency
- wasted CPU or GPU initialization

Therefore the expensive application graph is reused.

---

## Production Dependency Resolution

The production flow is:

```text
FastAPI Endpoint
    ↓
get_rag_pipeline()
    ↓
create_rag_pipeline()
    ↓
cached real RAGPipeline
```

The endpoint sees only the capability it needs.

---

## Test Dependency Resolution

The test flow is:

```text
FastAPI TestClient
    ↓
dependency override
    ↓
Mock RAGPipeline
```

The tests do not create:

- sentence-transformer models
- database connections
- pgvector queries
- Ollama HTTP calls

This keeps API tests focused and fast.

---

## Application Factory Decision

Expose:

```text
create_app()
```

for application construction.

Also expose:

```text
app
```

for Uvicorn.

This supports:

```text
production runtime
```

and:

```text
isolated test application creation
```

without duplicating route registration.

---

## Considered Error Handling Approaches

### Option A — Detailed Exception Mapping

Examples:

```text
LLM failure
 ↓
503
```

```text
retrieval failure
 ↓
500
```

```text
invalid application input
 ↓
400
```

Advantages:

- more expressive HTTP behavior

Disadvantages:

- requires a stable application failure taxonomy
- requires decisions about retryability
- requires error response models
- risks premature mapping without operational requirements

This option was deferred.

---

### Option B — Minimal HTTP Error Behavior

```text
invalid HTTP request
 ↓
422
```

```text
unexpected pipeline failure
 ↓
500
```

Advantages:

- sufficient for initial API exposure
- preserves existing application exceptions
- avoids speculative error architecture

This option was selected.

---

## OpenAPI Decision

Use FastAPI's generated:

```text
/docs
```

and:

```text
/openapi.json
```

without introducing separate API documentation tooling.

Tests verify that both are available.

---

## Testing Decision

Use FastAPI's test client with dependency overrides.

The API test suite verifies:

- Swagger UI availability
- OpenAPI schema availability
- successful answer response
- exact query forwarding
- missing query rejection
- empty query rejection
- blank query rejection
- null query rejection
- non-string query rejection
- unexpected pipeline failure behavior

---

## Test Client Server Exception Behavior

The test client is configured so unexpected application exceptions become HTTP responses during API tests.

This allows the test suite to verify:

```text
unexpected pipeline failure
    ↓
500 response
```

instead of re-raising the exception into the test process.

---

## Real Runtime Verification Decision

Automated API tests intentionally replace the real pipeline.

Therefore a real runtime smoke test was also performed.

The real test exercised:

```text
HTTP Client
    ↓
FastAPI
    ↓
real composition root
    ↓
real RAGPipeline
    ↓
real PostgreSQL retrieval
    ↓
real Ollama generation
    ↓
HTTP Response
```

This complements, rather than duplicates, the mocked API tests.

---

## Real Runtime Result

The real request used:

```json
{
  "query": "What do vector databases store?"
}
```

The real response was:

```json
{
  "answer": "The provided context is empty. I do not have enough information to answer the question."
}
```

The database contained no relevant context for the question.

The result proved the complete runtime path and confirmed the existing empty-retrieval grounding behavior.

---

## Consequences

### Positive

- the RAG engine is externally accessible through HTTP
- the API remains thin
- FastAPI does not enter the core RAG pipeline
- application composition has one explicit location
- expensive resources are reused
- routes depend on the `RAGPipeline` abstraction
- API tests are independent of infrastructure
- request and response contracts are explicit
- OpenAPI documentation is automatically available
- real runtime composition has been verified

### Negative

- the API currently exposes only question answering
- endpoint execution remains synchronous
- model generation blocks the request thread
- error responses are not yet domain-specific
- pipeline construction currently contains fixed composition defaults

### Neutral

The API and pipeline both validate query input because they protect different public boundaries.

---

## Future Considerations

Future versions may introduce:

- document ingestion endpoints
- API versioning
- async execution
- streaming responses
- structured error responses
- exception-to-status mapping
- authentication
- authorization
- rate limiting
- request IDs
- tracing
- metrics
- health endpoints
- readiness endpoints
- deployment lifecycle management
- configurable retrieval depth
- composition lifecycle hooks

These additions should preserve the dependency direction:

```text
HTTP Adapter
    ↓
Application Capability
```

---

## Final Decision

Expose the completed RAG pipeline through a top-level FastAPI inbound adapter.

Keep the API layer thin.

Construct concrete application dependencies in an explicit composition root.

Use FastAPI dependency injection to provide one application-scoped `RAGPipeline` instance to the endpoint.

Use dependency overrides for isolated API testing.

Validate HTTP requests at the API boundary.

Keep unexpected application failures as generic server errors until a concrete error contract is required.