# Sprint 11 — API Exposure

## Status

Completed

## Objective

Expose the completed online RAG pipeline through an HTTP API.

Before this sprint, the application already exposed one complete application-level operation:

```text
User Query
    ↓
RAGPipeline.answer(query)
    ↓
GeneratedAnswer
```

However, only Python callers could invoke that capability directly.

This sprint introduces the first inbound adapter:

```text
HTTP Client
    ↓
FastAPI
    ↓
RAGPipeline.answer(query)
    ↓
GeneratedAnswer
    ↓
HTTP Response
```

The API layer exposes the existing RAG capability without reimplementing:

- query embedding
- vector retrieval
- prompt augmentation
- LLM generation

---

## Scope

The sprint includes:

- FastAPI integration
- top-level API inbound-adapter package
- FastAPI application factory
- question-answering endpoint
- request API model
- response API model
- HTTP request validation
- dedicated application composition root
- construction of the complete RAG pipeline
- application-scoped pipeline reuse
- FastAPI dependency injection
- test-time dependency overrides
- focused API tests
- OpenAPI documentation verification
- real API runtime smoke testing

The sprint does not include:

- document ingestion API
- asynchronous endpoint execution
- streaming responses
- conversation history
- authentication
- authorization
- rate limiting
- API versioning
- custom pipeline exception hierarchy
- detailed exception-to-HTTP translation
- observability
- tracing
- metrics
- deployment configuration

These concerns belong to later stages.

---

## Problem Before This Sprint

Before API exposure, the completed online application flow was:

```text
Python Caller
    ↓
RAGPipeline.answer(query)
    ↓
GeneratedAnswer
```

The core RAG engine could already:

1. validate a query
2. generate a query embedding
3. retrieve relevant chunks
4. construct an augmented prompt
5. call the configured LLM
6. return a generated answer

However, there was no external application boundary.

A consumer needed direct Python access to the project in order to invoke:

```python
answer = pipeline.answer(query)
```

The application therefore needed an inbound adapter capable of translating:

```text
HTTP Request
```

into:

```text
RAGPipeline invocation
```

and translating:

```text
GeneratedAnswer
```

into:

```text
HTTP Response
```

---

## API Position in the Architecture

The API is an inbound adapter.

The dependency direction is:

```text
HTTP Client
    ↓
API
    ↓
RAGPipeline
```

The RAG pipeline does not depend on FastAPI.

The complete dependency direction is:

```text
HTTP
 ↓
FastAPI
 ↓
RAGPipeline
 ↓
Core Capabilities
 ↓
Infrastructure Adapters
```

The API exposes the application capability.

It does not become part of the RAG engine's internal orchestration.

---

## Package Structure

```text
rag_engine/
├── api/
│   ├── __init__.py
│   ├── app.py
│   ├── dependencies.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── answer_request.py
│   │   └── answer_response.py
│   └── routes/
│       ├── __init__.py
│       └── answers.py
│
├── composition/
│   ├── __init__.py
│   └── application.py
│
├── rag_pipeline/
├── query_embedding/
├── retrieval/
├── prompt_augmentation/
└── llm/
```

Test structure:

```text
tests/
└── api/
    ├── __init__.py
    ├── conftest.py
    ├── test_app.py
    └── test_answers.py
```

---

## API Boundary Decision

Two package designs were considered.

### API Inside the RAG Pipeline Package

```text
rag_engine/
└── rag_pipeline/
    ├── rag_pipeline.py
    ├── default_rag_pipeline.py
    └── api/
```

This would mix:

```text
application orchestration
```

with:

```text
HTTP adaptation
```

The design was rejected.

---

### Top-Level API Package

The selected structure is:

```text
rag_engine/
├── api/
└── rag_pipeline/
```

The responsibilities are:

```text
api
└── inbound HTTP adapter
```

```text
rag_pipeline
└── application orchestration
```

This preserves the dependency rule:

```text
api
 ↓
rag_pipeline
```

and prevents:

```text
rag_pipeline
 ↓
FastAPI
```

---

## HTTP Endpoint

The API exposes:

```text
POST /answers
```

The request body is:

```json
{
  "query": "What do vector databases store?"
}
```

The successful response body is:

```json
{
  "answer": "Vector databases store embeddings."
}
```

The endpoint flow is:

```text
POST /answers
    ↓
AnswerRequest
    ↓
RAGPipeline.answer(query)
    ↓
GeneratedAnswer
    ↓
AnswerResponse
```

---

## Thin API Layer

The route performs only HTTP adaptation.

It receives:

```text
AnswerRequest
```

extracts:

```text
query
```

calls:

```text
RAGPipeline.answer(query)
```

and maps:

```text
GeneratedAnswer.content
```

to:

```text
AnswerResponse.answer
```

The route does not know about:

- embedding models
- query embeddings
- PostgreSQL
- pgvector
- cosine distance
- retrieved chunks
- prompt construction
- Ollama
- model inference

These concerns remain behind the application capability.

---

## Request Model

The API request model is:

```text
AnswerRequest
└── query: str
```

The HTTP boundary rejects:

- missing query
- null query
- non-string query
- empty query
- blank query

Invalid requests return:

```text
422 Unprocessable Entity
```

before the RAG pipeline is called.

---

## Why the API Validates the Query

`RAGPipeline` already validates:

```text
empty query
blank query
```

The API also validates its own HTTP request contract.

The responsibilities are:

```text
HTTP API
└── validates HTTP request input
```

```text
RAGPipeline
└── validates application operation input
```

This is intentional boundary validation.

The API does not assume that application validation should be responsible for HTTP request semantics.

The pipeline does not assume that every caller is an HTTP caller.

---

## Response Model

The API response model is:

```text
AnswerResponse
└── answer: str
```

The application domain model remains:

```text
GeneratedAnswer
└── content: str
```

The route maps:

```text
GeneratedAnswer.content
    ↓
AnswerResponse.answer
```

This prevents the HTTP contract from becoming identical to the internal domain model by accident.

The API owns its external representation.

---

## Application Composition Problem

`DefaultRAGPipeline` requires:

```text
QueryEmbedder
Retriever
PromptAugmenter
LLM
top_k
```

The current concrete object graph is:

```text
DefaultRAGPipeline
├── LocalQueryEmbedder
├── PostgresRetriever
├── DefaultPromptAugmenter
├── OllamaLLM
└── top_k
```

These concrete implementations must be created somewhere.

The API route should not own this responsibility.

---

## Composition Root

A dedicated composition package was introduced:

```text
rag_engine/
└── composition/
    └── application.py
```

The composition root owns:

```text
construct concrete implementations
    ↓
configure implementations
    ↓
connect implementations
    ↓
produce RAGPipeline
```

The API receives the completed application capability.

---

## Why Composition Does Not Belong in app.py

A possible design was:

```text
app.py
├── create embedding model
├── create query embedder
├── create retriever
├── create prompt augmenter
├── create LLM
├── create pipeline
├── create FastAPI
└── register routes
```

This was rejected because `app.py` would own two different responsibilities:

```text
HTTP application creation
```

and:

```text
application object graph construction
```

The selected separation is:

```text
composition
└── construct application capabilities
```

```text
api/app.py
└── construct HTTP application
```

---

## No Dependency Injection Framework

The project does not introduce a dependency injection framework.

The composition root is explicit Python code.

Conceptually:

```text
create embedding model
    ↓
create QueryEmbedder
    ↓
create Retriever
    ↓
create PromptAugmenter
    ↓
create LLM
    ↓
create DefaultRAGPipeline
```

This keeps object construction:

- visible
- explicit
- easy to debug
- easy to test

The current project does not need a more complex container abstraction.

---

## Current Application Composition

The composition root creates:

```text
SentenceTransformer
    ↓
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

and combines them into:

```text
DefaultRAGPipeline
```

The complete graph is:

```text
SentenceTransformer
    ↓
LocalQueryEmbedder
        \
         \
PostgresRetriever
          \
           \
DefaultPromptAugmenter
             \
              \
OllamaLLM ------→ DefaultRAGPipeline
                       ↑
                     top_k
```

---

## Application-Scoped Pipeline

The pipeline must not be recreated for every HTTP request.

The composition root uses cached construction so that:

```text
First Pipeline Resolution
    ↓
construct embedding model
    ↓
construct capabilities
    ↓
construct RAG pipeline
    ↓
cache pipeline
```

Later requests perform:

```text
Pipeline Resolution
    ↓
reuse existing pipeline
```

This is important because the local embedding model is an expensive shared resource.

The application does not reload the sentence-transformer model for every request.

---

## FastAPI Dependency Injection

The endpoint does not import or construct the concrete pipeline directly.

Instead, it depends on:

```text
RAGPipeline
```

through FastAPI dependency injection.

The production flow is:

```text
Endpoint
    ↓
get_rag_pipeline()
    ↓
composition root
    ↓
application-scoped RAGPipeline
```

The route remains dependent on the abstraction.

---

## Why FastAPI Dependency Injection Was Selected

A module-level global pipeline was considered.

Conceptually:

```text
module import
    ↓
construct pipeline
    ↓
route accesses global pipeline
```

This approach was rejected because:

- imports could trigger expensive model loading
- tests would need to patch global state
- the route would be coupled to one concrete object
- test isolation would be weaker

The selected approach is:

```text
FastAPI Depends
    ↓
get_rag_pipeline
    ↓
RAGPipeline
```

This supports both production composition and test overrides.

---

## Production Dependency Flow

The production dependency flow is:

```text
HTTP Request
    ↓
FastAPI Route
    ↓
get_rag_pipeline()
    ↓
create_rag_pipeline()
    ↓
cached application-scoped RAGPipeline
    ↓
answer(query)
```

The pipeline is created once and reused.

---

## Test Dependency Flow

The test dependency flow is:

```text
TestClient
    ↓
FastAPI Application
    ↓
dependency override
    ↓
Mock RAGPipeline
```

API tests do not:

- load a sentence-transformer model
- connect to PostgreSQL
- execute pgvector retrieval
- call Ollama
- require GPU access

The tests focus only on the HTTP adapter.

---

## FastAPI Application Factory

The API provides:

```text
create_app()
```

which creates and configures the FastAPI application.

The application factory:

- creates the FastAPI instance
- configures API metadata
- registers the answers router

The module also exposes:

```text
app
```

for Uvicorn.

This supports:

```text
production
└── import app
```

and:

```text
tests
└── create isolated application instance
```

---

## OpenAPI Support

FastAPI automatically exposes:

```text
/docs
```

and:

```text
/openapi.json
```

The API tests verify that both are available.

The application therefore exposes interactive API documentation without additional implementation.

---

## Error Handling

The sprint uses minimal HTTP error behavior.

Invalid HTTP request input results in:

```text
422 Unprocessable Entity
```

Unexpected pipeline or infrastructure failures result in:

```text
500 Internal Server Error
```

The sprint does not introduce:

```text
RAGPipelineError
```

or a large API-specific exception hierarchy.

---

## Why Detailed Error Mapping Was Deferred

The current pipeline can expose failures from:

- query embedding
- retrieval
- prompt augmentation
- LLM generation

The API could introduce detailed mappings such as:

```text
LLM unavailable
    ↓
503 Service Unavailable
```

or:

```text
retrieval failure
    ↓
500 Internal Server Error
```

However, a full error contract requires deliberate decisions about:

- which failures are retryable
- which failures are safe to expose
- which failures are client errors
- which failures are server errors
- response error models
- observability and correlation

Those concerns are larger than the minimum API exposure goal.

For this sprint:

```text
invalid request
    ↓
422
```

```text
unexpected application failure
    ↓
500
```

is sufficient.

---

## API Unit Testing Strategy

The API tests use:

```text
FastAPI TestClient
```

with:

```text
dependency_overrides
```

The real pipeline dependency is replaced by:

```text
Mock(spec=RAGPipeline)
```

This proves the API boundary independently of infrastructure.

---

## Application Tests

The API tests verify:

```text
GET /docs
    ↓
200
```

and:

```text
GET /openapi.json
    ↓
200
```

This proves that the FastAPI application is correctly created and exposes its generated documentation.

---

## Successful Request Tests

The API tests prove:

```text
valid request
    ↓
RAGPipeline.answer(query)
    ↓
GeneratedAnswer
    ↓
200 response
```

They verify:

- the original query is passed to the pipeline
- the pipeline is called exactly once
- `GeneratedAnswer.content` becomes the HTTP `answer`
- the response status is `200`

---

## Request Validation Tests

The API tests verify rejection of:

```text
missing query
```

```text
empty query
```

```text
blank query
```

```text
null query
```

```text
non-string query
```

For every invalid request:

```text
HTTP validation failure
    ↓
422
    ↓
RAGPipeline is not called
```

---

## Failure Test

The API tests also prove:

```text
RAGPipeline failure
    ↓
FastAPI
    ↓
500 Internal Server Error
```

The test client is configured not to re-raise server exceptions so the actual HTTP response can be verified.

---

## API Test Count

Sprint 11 added:

```text
10 API tests
```

The complete suite now contains:

```text
106 tests passing
```

The API tests prove:

```text
Application
├── Swagger UI available
└── OpenAPI schema available
```

```text
Successful Request
├── accepts query
├── calls RAGPipeline
├── preserves original query
└── maps GeneratedAnswer to HTTP response
```

```text
Request Validation
├── missing query → 422
├── empty query → 422
├── blank query → 422
├── null query → 422
└── non-string query → 422
```

```text
Unexpected Failure
└── pipeline failure → 500
```

---

## Test Dependency Warning

The test suite currently reports a dependency deprecation warning related to the FastAPI, Starlette, and HTTP client testing stack.

The warning does not originate from application code.

The API tests pass successfully.

No application code or test behavior was changed solely to suppress the dependency warning.

Dependency compatibility can be reviewed separately during dependency maintenance.

---

## Real API Runtime Verification

After automated testing, the real API was started using Uvicorn.

The runtime flow was:

```text
HTTP Client
    ↓
FastAPI
    ↓
real dependency resolution
    ↓
real composition root
    ↓
real DefaultRAGPipeline
    ↓
real LocalQueryEmbedder
    ↓
real PostgresRetriever
    ↓
real DefaultPromptAugmenter
    ↓
real OllamaLLM
    ↓
real qwen3:4b
    ↓
HTTP Response
```

The request was:

```json
{
  "query": "What do vector databases store?"
}
```

The response was:

```json
{
  "answer": "The provided context is empty. I do not have enough information to answer the question."
}
```

---

## What the Real Smoke Test Proved

The real runtime test proved:

- Uvicorn could load the application
- FastAPI could receive the request
- request validation succeeded
- the real dependency function resolved
- the real composition root executed
- the real pipeline was constructed
- the local embedding model was available
- query embedding executed
- PostgreSQL retrieval executed
- empty retrieval results were handled
- prompt augmentation executed
- Ollama was reachable
- `qwen3:4b` generated a response
- `GeneratedAnswer` was mapped to the API response
- the client received a successful HTTP response

---

## Real Verification of Empty Retrieval Behavior

The database did not contain relevant context for the question.

The real flow was:

```text
User Query
    ↓
Query Embedding
    ↓
Retriever
    ↓
No Retrieved Chunks
    ↓
PromptAugmenter
    ↓
AugmentedPrompt with Empty Context
    ↓
LLM
    ↓
Insufficient-Information Answer
```

This validates a Sprint 10 design decision through the real HTTP application boundary.

The pipeline did not:

- fail
- create a hard-coded fallback
- bypass the LLM

Instead, the existing prompt grounding policy controlled the answer.

---

## Complete Runtime Architecture

The complete online runtime architecture is now:

```text
HTTP Client
    ↓
POST /answers
    ↓
FastAPI
    ↓
AnswerRequest
    ↓
RAGPipeline Dependency
    ↓
DefaultRAGPipeline
    ↓
LocalQueryEmbedder
    ↓
Query Embedding
    ↓
PostgresRetriever
    ↓
Retrieved Chunks
    ↓
DefaultPromptAugmenter
    ↓
AugmentedPrompt
    ↓
OllamaLLM
    ↓
Ollama
    ↓
qwen3:4b
    ↓
GeneratedAnswer
    ↓
AnswerResponse
    ↓
HTTP Client
```

---

## Complete Application Architecture

The project now contains three major flows.

### Ingestion

```text
PDF
 ↓
DocumentLoader
 ↓
DocumentChunker
 ↓
ChunkEmbedder
 ↓
VectorStore
 ↓
PostgreSQL + pgvector
```

### Online RAG

```text
User Query
 ↓
RAGPipeline
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

### HTTP Exposure

```text
HTTP Request
 ↓
FastAPI
 ↓
RAGPipeline
 ↓
GeneratedAnswer
 ↓
HTTP Response
```

---

## Architectural Boundaries

The project now exposes:

```text
DocumentLoader
DocumentChunker
ChunkEmbedder
VectorStore
QueryEmbedder
Retriever
PromptAugmenter
LLM
RAGPipeline
HTTP API
```

The core capability implementations remain:

```text
DocumentLoader
    ↑
PdfLoader

DocumentChunker
    ↑
RecursiveDocumentChunker

ChunkEmbedder
    ↑
LocalChunkEmbedder

VectorStore
    ↑
PostgresVectorStore

QueryEmbedder
    ↑
LocalQueryEmbedder

Retriever
    ↑
PostgresRetriever

PromptAugmenter
    ↑
DefaultPromptAugmenter

LLM
    ↑
OllamaLLM

RAGPipeline
    ↑
DefaultRAGPipeline
```

The API is an adapter around the application capability.

---

## Key Learning Outcomes

This sprint established the following concepts:

- a completed application capability can be exposed through a thin inbound adapter
- the HTTP layer should not reimplement application orchestration
- API packages and application pipeline packages represent different responsibilities
- dependency direction should flow from the adapter toward the application capability
- application object construction should have an explicit composition root
- composition should remain separate from HTTP application creation
- a dependency injection framework is not required for explicit object wiring
- expensive shared resources should not be created per request
- FastAPI dependency injection supports clean production wiring and test overrides
- API tests should mock the application capability rather than infrastructure internals
- each public boundary should validate its own contract
- API request models should remain separate from application domain models
- minimal error mapping is preferable to inventing an exception hierarchy without requirements
- real smoke tests validate composition behavior that mocked API tests intentionally do not cover
- an empty retrieval result can successfully travel through the complete HTTP-to-LLM path

---

## Sprint Outcome

Sprint 11 successfully exposed the completed RAG pipeline through an HTTP API.

The application can now:

1. receive an HTTP request
2. validate the request body
3. resolve the application-scoped RAG pipeline
4. pass the query to the pipeline
5. execute the complete online RAG flow
6. receive a `GeneratedAnswer`
7. map the answer to an HTTP response
8. return the response to the client

The public application flow is now:

```text
POST /answers
    ↓
RAGPipeline.answer(query)
    ↓
GeneratedAnswer
    ↓
HTTP 200 Response
```

The project has progressed from:

```text
individual RAG capabilities
```

to:

```text
orchestrated RAG application
```

to:

```text
externally accessible RAG API
```

The next stage should improve production visibility into this complete runtime flow.