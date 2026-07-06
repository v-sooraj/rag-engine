# RAG Engine

A production-oriented Retrieval-Augmented Generation (RAG) engine built from scratch to understand every architectural layer behind modern AI applications.

## Goals

- Learn production-grade AI backend engineering
- Build every layer incrementally
- Prioritize architecture over frameworks

## Tech Stack

- Python
- FastAPI
- Uvicorn
- PostgreSQL
- pgvector
- Psycopg
- Docker
- uv
- Pydantic Settings
- PyMuPDF
- sentence-transformers
- httpx
- Ollama
- qwen3:4b
- pytest

## Getting Started

1. Clone the repository.
2. Copy `.env.example` to `.env`.
3. Copy `docker/.env.example` to `docker/.env`.
4. Update the configuration values.
5. Start PostgreSQL using Docker Compose.
6. Install and start Ollama.
7. Pull the configured local LLM.
8. Run the test suite.
9. Start the API.

Example model setup:

```bash
ollama pull qwen3:4b
```

Verify the model is available:

```bash
ollama list
```

Run the test suite:

```bash
uv run pytest -v
```

Start the API:

```bash
uv run uvicorn rag_engine.api.app:app --reload
```

The API runs by default at:

```text
http://127.0.0.1:8000
```

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

The OpenAPI schema is available at:

```text
http://127.0.0.1:8000/openapi.json
```

---

## API Usage

The API currently exposes:

```text
POST /answers
```

Example request:

```json
{
  "query": "What do vector databases store?"
}
```

Example response:

```json
{
  "answer": "Vector databases store embeddings."
}
```

The runtime flow is:

```text
HTTP Request
    ↓
FastAPI
    ↓
RAGPipeline.answer(query)
    ↓
GeneratedAnswer
    ↓
HTTP Response
```

---

## Current Architecture

### Ingestion Pipeline

```text
PDF
 ↓
DocumentLoader
 ↓
PdfLoader
 ↓
Document
 ↓
DocumentChunker
 ↓
RecursiveDocumentChunker
 ↓
list[Chunk]
 ↓
ChunkEmbedder
 ↓
LocalChunkEmbedder
 ↓
all-MiniLM-L6-v2
 ↓
list[EmbeddedChunk]
 ↓
VectorStore
 ↓
PostgresVectorStore
 ↓
PostgreSQL + pgvector
```

### Online RAG Pipeline

```text
User Query
    ↓
RAGPipeline
    ↓
DefaultRAGPipeline
    ↓
QueryEmbedder
    ↓
LocalQueryEmbedder
    ↓
Query Embedding
    ↓
Retriever
    ↓
PostgresRetriever
    ↓
Top-K Retrieved Chunks
    ↓
PromptAugmenter
    ↓
DefaultPromptAugmenter
    ↓
AugmentedPrompt
    ↓
LLM
    ↓
OllamaLLM
    ↓
Ollama
    ↓
qwen3:4b
    ↓
GeneratedAnswer
```

### HTTP API

```text
HTTP Client
    ↓
POST /answers
    ↓
FastAPI
    ↓
AnswerRequest
    ↓
RAGPipeline
    ↓
GeneratedAnswer
    ↓
AnswerResponse
    ↓
HTTP Client
```

From the application caller's perspective:

```text
User Query
    ↓
RAGPipeline.answer()
    ↓
GeneratedAnswer
```

From the HTTP client's perspective:

```text
POST /answers
    ↓
HTTP Response
```

---

## Current Status

### ✅ Completed

- Project bootstrap
- Docker infrastructure
- PostgreSQL + pgvector
- Configuration management
- Environment loading
- Database connectivity
- Document loading
- Document chunking
- Local embedding generation
- Vector storage
- Query embedding
- Vector similarity retrieval
- Prompt augmentation
- Local LLM integration
- RAG pipeline orchestration
- Complete real RAG generation pipeline
- FastAPI exposure
- Application composition root
- HTTP dependency injection
- API request validation
- OpenAPI documentation
- Real API runtime verification

### 🚧 In Progress

- Observability

### 📋 Planned

- Production visibility and diagnostics

---

## Current Capabilities

The project currently supports:

- PDF document loading using PyMuPDF
- immutable document and metadata domain models
- recursive character-based document chunking
- configurable chunk size and overlap
- immutable chunk domain models
- local chunk embedding generation using sentence-transformers
- batched chunk embedding generation
- immutable embedded chunk domain models
- real 384-dimensional embeddings using `all-MiniLM-L6-v2`
- normalized document and chunk persistence
- vector storage using PostgreSQL and pgvector
- SHA-256 content-based document deduplication
- idempotent document ingestion
- atomic document and chunk persistence
- UUID-based persisted document identity
- database-backed chunk and vector integrity constraints
- dedicated query embedding abstraction
- local query embedding using `all-MiniLM-L6-v2`
- shared embedding model instances across embedding capabilities
- immutable retrieval result domain models
- configurable top-k vector retrieval
- cosine-distance search using pgvector
- raw retrieval distance exposure for future observability
- fail-fast query and retrieval validation
- deterministic real PostgreSQL vector-ranking tests
- real semantic retrieval using local embeddings
- dedicated prompt augmentation abstraction
- immutable structured augmented prompt domain model
- fixed grounding system instruction
- explicit numbered context boundaries
- retrieval ranking preservation during prompt augmentation
- empty retrieval result handling
- separation of retrieval metadata from LLM context
- provider-independent LLM abstraction
- immutable generated answer domain model
- local model inference through Ollama
- direct HTTP integration using `httpx`
- configurable Ollama base URL
- configurable local model
- configurable generation timeout
- structured prompt-to-chat-message mapping
- synchronous non-streaming generation
- LLM-specific error translation
- response validation
- dedicated RAG pipeline abstraction
- default online RAG orchestration
- constructor injection of pipeline capabilities
- pipeline-level retrieval depth configuration
- fail-fast pipeline input validation
- fail-fast pipeline configuration validation
- unchanged stage-specific failure propagation
- zero-result retrieval continuation
- dedicated FastAPI inbound adapter
- explicit application composition root
- application-scoped RAG pipeline reuse
- FastAPI dependency injection
- test-time dependency overrides
- dedicated API request and response models
- HTTP request validation
- generated Swagger UI
- generated OpenAPI schema
- real local LLM integration testing
- complete real query-to-answer orchestration testing
- real HTTP-to-RAG runtime verification

---

## Complete Data Flow

```text
                         INGESTION

PDF
 ↓
Document
 ↓
Chunks
 ↓
Chunk Embeddings
 ↓
PostgreSQL + pgvector
 ↑
 │
 │ Cosine-Distance Search
 │
Query Embedding
 ↑
User Query

                         RETRIEVAL
                              ↓
                      Retrieved Chunks
                              ↓
                      Prompt Augmenter

                    PROMPT AUGMENTATION
                              ↓
                       AugmentedPrompt
                              ↓
                             LLM

                         GENERATION
                              ↓
                         OllamaLLM
                              ↓
                            Ollama
                              ↓
                          qwen3:4b
                              ↓
                       GeneratedAnswer

                        HTTP EXPOSURE
                              ↓
                        AnswerResponse
                              ↓
                         HTTP Client
```

The complete online flow is coordinated by:

```text
RAGPipeline
```

The Python caller performs:

```python
answer = pipeline.answer(query)
```

The HTTP caller performs:

```text
POST /answers
```

---

## Domain Flow

The ingestion domain flow is:

```text
Document
    ↓
Chunk
    ↓
EmbeddedChunk
    ↓
Stored Vector
```

The online domain flow is:

```text
User Query
    ↓
Query Embedding
    ↓
RetrievedChunk
    ↓
AugmentedPrompt
    ↓
GeneratedAnswer
```

The application-level flow is:

```text
str
    ↓
RAGPipeline
    ↓
GeneratedAnswer
```

The HTTP flow is:

```text
AnswerRequest
    ↓
RAGPipeline
    ↓
GeneratedAnswer
    ↓
AnswerResponse
```

Each major boundary preserves meaningful structure rather than collapsing application concepts into primitive values too early.

---

## RAG Pipeline Orchestration

The application-level capability is:

```text
RAGPipeline
    ↑
DefaultRAGPipeline
```

The public operation is:

```text
answer(query)
```

The internal sequence is:

```text
validate query
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

The caller does not need to know about:

- query embeddings
- retrieval implementation
- retrieval depth
- retrieved chunk models
- prompt construction
- model invocation

---

## API Architecture

The API is a top-level inbound adapter:

```text
rag_engine/
├── api/
├── composition/
├── rag_pipeline/
└── core capability packages/
```

The dependency direction is:

```text
HTTP Client
    ↓
API
    ↓
RAGPipeline
```

The RAG pipeline does not depend on FastAPI.

---

## API Endpoint

The question-answering endpoint is:

```text
POST /answers
```

The endpoint flow is:

```text
AnswerRequest
    ↓
query
    ↓
RAGPipeline.answer(query)
    ↓
GeneratedAnswer
    ↓
AnswerResponse
```

The route does not know about:

- sentence-transformers
- PostgreSQL
- pgvector
- retrieval
- prompt augmentation
- Ollama

The API exposes the capability that already exists.

---

## API Validation

The HTTP boundary rejects:

```text
missing query
empty query
blank query
null query
non-string query
```

Invalid requests return:

```text
422 Unprocessable Entity
```

The pipeline retains its own application-level validation.

The two boundaries protect different contracts:

```text
API
└── HTTP request contract
```

```text
RAGPipeline
└── application operation contract
```

---

## Application Composition

The application composition root constructs:

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

The separation is:

```text
Composition Root
└── choose and construct concrete implementations
```

```text
RAGPipeline
└── orchestrate capabilities
```

```text
API
└── adapt HTTP
```

---

## Pipeline Lifecycle

The real RAG pipeline is created once and reused.

The lifecycle is:

```text
First Dependency Resolution
    ↓
Construct Application Object Graph
    ↓
Cache RAGPipeline
```

Later requests perform:

```text
Dependency Resolution
    ↓
Reuse Existing RAGPipeline
```

The local embedding model is not loaded for every request.

---

## FastAPI Dependency Injection

The route receives:

```text
RAGPipeline
```

through FastAPI dependency injection.

Production:

```text
Endpoint
    ↓
get_rag_pipeline()
    ↓
Composition Root
    ↓
Real RAGPipeline
```

Tests:

```text
TestClient
    ↓
Dependency Override
    ↓
Mock RAGPipeline
```

This keeps API tests independent of real infrastructure.

---

## API Error Behavior

The current API behavior is intentionally minimal.

Invalid request:

```text
HTTP validation failure
    ↓
422
```

Unexpected pipeline failure:

```text
Application failure
    ↓
500
```

Detailed exception-to-HTTP mapping is deferred until the application has a concrete operational error contract.

---

## Prompt Augmentation Output

The prompt augmentation stage produces:

```text
AugmentedPrompt
├── system_instruction
├── context
└── question
```

Retrieved chunks are represented as explicit evidence blocks:

```text
[CONTEXT 1]
Most relevant retrieved evidence

[CONTEXT 2]
Second most relevant retrieved evidence

[CONTEXT 3]
Third most relevant retrieved evidence
```

Retrieval ranking is preserved.

Application metadata such as:

- cosine distance
- chunk ID
- document ID
- chunk index

remains outside the LLM context.

---

## LLM Message Mapping

The structured prompt maps to the local LLM as:

```text
system_instruction
    ↓
system message
```

and:

```text
context + question
    ↓
user message
```

The user message is formatted as:

```text
Context:
{retrieved context}

Question:
{user question}
```

Retrieved evidence remains separate from trusted system instructions.

---

## Local LLM Infrastructure

The generation architecture is:

```text
RAG Engine
    ↓
OllamaLLM
    ↓
httpx
    ↓
Ollama HTTP API
    ↓
qwen3:4b
```

The RAG engine owns:

- prompt-to-message mapping
- request construction
- response validation
- error translation

Ollama owns:

- model download
- model loading
- local inference
- GPU utilization
- runtime details

---

## Configuration

PostgreSQL configuration uses:

```text
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_DATABASE
POSTGRES_USER
POSTGRES_PASSWORD
```

Ollama configuration uses:

```text
OLLAMA_BASE_URL
OLLAMA_MODEL_NAME
OLLAMA_TIMEOUT_SECONDS
```

Example Ollama configuration:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_NAME=qwen3:4b
OLLAMA_TIMEOUT_SECONDS=300
```

---

## Testing

The project currently has:

```text
106 tests passing
```

The test suite includes:

- domain model tests
- configuration tests
- database connectivity tests
- document loading tests
- document chunking tests
- local embedding tests
- vector storage tests
- transaction rollback tests
- idempotency tests
- query embedding tests
- deterministic vector-ranking tests
- semantic retrieval tests
- prompt augmentation tests
- generated answer tests
- mocked Ollama HTTP tests
- RAG pipeline orchestration tests
- API application tests
- API request validation tests
- API dependency override tests
- API failure behavior tests
- real Ollama integration tests
- complete pipeline integration tests

---

## API Test Coverage

The API tests prove:

```text
Application
├── Swagger UI available
└── OpenAPI schema available
```

```text
Successful Request
├── accepts query
├── calls RAGPipeline exactly once
├── passes original query
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

The API test suite contains:

```text
10 tests
```

The complete suite contains:

```text
106 tests
```

---

## Integration Coverage

The ingestion integration coverage proves:

```text
PDF
 ↓
Document
 ↓
Chunks
 ↓
Embeddings
 ↓
PostgreSQL + pgvector
```

The generation coverage proves:

```text
AugmentedPrompt
 ↓
OllamaLLM
 ↓
Real HTTP Request
 ↓
Ollama
 ↓
qwen3:4b
 ↓
GeneratedAnswer
```

The complete RAG integration coverage proves:

```text
Stored Knowledge
    ↓
PostgreSQL + pgvector

User Query
    ↓
DefaultRAGPipeline.answer(query)
    ↓
LocalQueryEmbedder
    ↓
PostgresRetriever
    ↓
DefaultPromptAugmenter
    ↓
OllamaLLM
    ↓
qwen3:4b
    ↓
GeneratedAnswer
```

The real API smoke test proves:

```text
HTTP Request
    ↓
FastAPI
    ↓
Real Composition Root
    ↓
Real RAGPipeline
    ↓
PostgreSQL + pgvector
    ↓
Ollama
    ↓
HTTP Response
```

---

## Real API Verification

The API was started using:

```bash
uv run uvicorn rag_engine.api.app:app --reload
```

A real request was sent to:

```text
POST /answers
```

using:

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

The result proved:

```text
HTTP
 ↓
FastAPI
 ↓
Composition
 ↓
RAGPipeline
 ↓
Query Embedding
 ↓
Retrieval
 ↓
Empty Context
 ↓
Prompt Augmentation
 ↓
Ollama
 ↓
Grounded Insufficient-Information Answer
 ↓
HTTP Response
```

---

## Current Architectural Boundaries

The project currently exposes the following major capabilities:

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

Their concrete implementations are:

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

The HTTP API is an inbound adapter around the application capability.

The composition root owns concrete object construction.

---

## Documentation

Detailed architectural discussions and engineering decisions can be found under:

- `docs/architecture`
- `docs/adr`

Architecture documents cover the incremental implementation of:

- project foundation
- database connectivity
- document loading
- document chunking
- embedding generation
- vector storage
- retrieval
- prompt augmentation
- LLM integration
- RAG pipeline orchestration
- API exposure

ADRs document the major architectural decisions made while building the RAG engine from scratch.

---

## Core RAG Application Status

The core RAG application is now complete and externally accessible.

The ingestion path is:

```text
Document
 ↓
Load
 ↓
Chunk
 ↓
Embed
 ↓
Store
```

The online path is:

```text
Query
 ↓
Embed
 ↓
Retrieve
 ↓
Augment
 ↓
Generate
 ↓
Answer
```

The application operation is:

```text
RAGPipeline.answer(query)
```

The external operation is:

```text
POST /answers
```

The system can now:

```text
store knowledge
```

then:

```text
receive a question over HTTP
```

then:

```text
retrieve semantically relevant knowledge
```

then:

```text
construct grounded model input
```

then:

```text
generate an answer using a local LLM
```

then:

```text
return the answer as an HTTP response
```

---

## Next Phase

The next sprint will focus on observability.

The next stage should decide how to make the runtime pipeline visible without coupling core capabilities to one monitoring backend.

The target is to gain visibility into:

```text
HTTP Request
    ↓
RAG Pipeline
    ↓
Embedding
    ↓
Retrieval
    ↓
Prompt Augmentation
    ↓
LLM Generation
    ↓
HTTP Response
```

Potential observability concerns include:

- structured logging
- request correlation
- pipeline timing
- stage timing
- retrieval result counts
- retrieval distances
- LLM latency
- failure visibility

The next sprint should introduce only the observability signals that provide real value and preserve the current architectural boundaries.