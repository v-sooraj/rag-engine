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

## Document Ingestion API

The application exposes:

```text
POST /documents
```

The endpoint accepts:

```text
multipart/form-data
```

with a PDF in the:

```text
file
```

field.

The complete flow is:

```text
HTTP Client
    ↓
POST /documents
    ↓
UploadFile
    ↓
DocumentUploadAdapter
    ↓
Temporary Directory
    ↓
Temporary PDF Using Original Filename
    ↓
IngestionPipeline
    ↓
PostgreSQL + pgvector
    ↓
Document UUID
    ↓
201 Created
```

A successful response is:

```json
{
  "document_id": "..."
}
```

The route accepts:

```text
application/pdf
```

Unsupported media types return:

```text
415 Unsupported Media Type
```

A missing file returns:

```text
422 Unprocessable Entity
```

---

## Observability

The application includes a first observability layer for:

```text
HTTP Requests
```

and:

```text
Application Operations
```

The runtime architecture is:

```text
HTTP Request
    ↓
RequestObservabilityMiddleware
    ↓
Observed Pipeline
    ↓
Default Pipeline
    ↓
Structured JSON Logs
```

The observability layer answers:

```text
What happened?
```

```text
How long did it take?
```

```text
Which request did it belong to?
```

---

## HTTP Request Observability

Every HTTP request is observed by:

```text
RequestObservabilityMiddleware
```

The middleware emits:

```text
http.request.started
```

```text
http.request.completed
```

or:

```text
http.request.failed
```

A completed request includes:

```text
request_id
method
path
status_code
duration_ms
```

---

## Request Correlation

The application uses:

```text
X-Request-ID
```

for request correlation.

If the client sends:

```text
X-Request-ID
```

the application reuses it.

Otherwise:

```text
UUID
```

is generated.

The resolved request ID is returned in the response:

```text
X-Request-ID
```

The request ID is propagated internally through:

```text
ContextVar
```

This allows pipeline events to include request correlation without changing application method signatures.

---

## Observed Application Pipelines

The composed ingestion capability is:

```text
ObservedIngestionPipeline
    ↓
DefaultIngestionPipeline
```

The composed RAG capability is:

```text
ObservedRAGPipeline
    ↓
DefaultRAGPipeline
```

The decorators preserve:

```text
same input
same output
same exception
```

and add:

```text
start event
completion event
failure event
duration
request correlation
```

---

## Ingestion Events

The ingestion operation emits:

```text
ingestion.started
```

```text
ingestion.completed
```

or:

```text
ingestion.failed
```

Operational fields may include:

```text
request_id
document_filename
document_id
duration_ms
exception_type
```

The full document path and document contents are not logged.

---

## RAG Events

The RAG operation emits:

```text
rag.started
```

```text
rag.completed
```

or:

```text
rag.failed
```

Operational fields may include:

```text
request_id
duration_ms
exception_type
```

The application does not log:

```text
user query
retrieved context
augmented prompt
generated answer
```

by default.

---

## JSON Logs

Logs are emitted as newline-delimited JSON to:

```text
stdout
```

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

The application is not coupled to a monitoring vendor.

Deployment infrastructure can later collect stdout and forward it to a centralized logging system.

---

## Observability Privacy

The application deliberately avoids logging:

- document contents
- chunk contents
- embeddings
- full document paths
- user questions
- retrieved context
- augmented prompts
- generated answers

The current observability layer records operational metadata only.

---

## Observability Architecture

The complete request flow is:

```text
HTTP Request
    ↓
http.request.started
    ↓
Application Operation
    ↓
ingestion.started / rag.started
    ↓
Default Pipeline
    ↓
ingestion.completed / rag.completed
    ↓
http.request.completed
    ↓
HTTP Response
```

All events belonging to the same HTTP request can be correlated using:

```text
request_id
```

---

## Upload Adaptation

The ingestion pipeline accepts:

```text
filesystem path
```

while the HTTP API receives:

```text
UploadFile
```

The application bridges these representations through:

```text
DocumentUploadAdapter
```

The adapter owns:

- temporary directory creation
- uploaded byte copying
- original filename preservation
- filename sanitization
- temporary resource cleanup

The adapter does not own:

- PDF parsing
- chunking
- embedding
- vector storage

Those responsibilities remain behind:

```text
IngestionPipeline
```

---

## Temporary File Lifecycle

Each upload creates a scoped temporary directory.

For:

```text
sample.pdf
```

the temporary path is conceptually:

```text
<temporary-directory>/sample.pdf
```

The ingestion pipeline receives this path.

After ingestion succeeds or fails:

```text
temporary file
```

and:

```text
temporary directory
```

are deleted automatically.

---

## Filename Preservation

The original upload adapter design used a generated temporary filename.

This caused:

```text
sample.pdf
```

to become:

```text
tmp2l9m66ua.pdf
```

inside persisted document metadata.

The final design preserves the original filename:

```text
sample.pdf
    ↓
<temporary-directory>/sample.pdf
    ↓
PdfLoader
    ↓
DocumentMetadata.filename = sample.pdf
```

The filename is sanitized before filesystem use so client-supplied directory components are not preserved.

---

## Complete External RAG Flow

The application now exposes both sides of the RAG lifecycle.

### Ingest Knowledge

```text
POST /documents
    ↓
Upload PDF
    ↓
Load
    ↓
Chunk
    ↓
Embed
    ↓
Store
```

### Ask Questions

```text
POST /answers
    ↓
Embed Query
    ↓
Retrieve Relevant Chunks
    ↓
Augment Prompt
    ↓
Generate Answer
```

The intended usage is:

```text
1. POST /documents
       ↓
   Knowledge Stored

2. POST /answers
       ↓
   Relevant Knowledge Retrieved

3. LLM
       ↓
   Grounded Answer
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
- FastAPI answer exposure
- Application composition root
- Ingestion pipeline orchestration
- Shared embedding model composition
- Document ingestion API
- HTTP upload adaptation
- Original filename preservation
- Real HTTP-to-pgvector ingestion verification
- Application observability
- HTTP request correlation
- Structured JSON logging
- Pipeline operation timing

### 🚧 In Progress

- None

### 📋 Planned

- Production hardening
- Advanced observability

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

## Ingestion Pipeline Orchestration

The application-level ingestion capability is:

```text
IngestionPipeline
    ↑
DefaultIngestionPipeline
```

The public operation is:

```text
ingest(path)
```

The internal sequence is:

```text
validate path
    ↓
DocumentLoader
    ↓
DocumentChunker
    ↓
ChunkEmbedder
    ↓
VectorStore
    ↓
Document UUID
```

The caller no longer manually coordinates the ingestion stages.

The caller performs:

```python
document_id = ingestion_pipeline.ingest(
    "path/to/document.pdf"
)
```

The pipeline owns:

- stage ordering
- passing outputs between stages
- input validation
- returning the persisted document ID

The pipeline does not own:

- PDF parsing
- chunking strategy
- embedding implementation
- database transactions
- deduplication
- idempotency

These responsibilities remain inside the existing capabilities.

---

## Application Operations

The application now exposes two primary operations.

### Ingest Knowledge

```text
IngestionPipeline.ingest(path)
```

Flow:

```text
File Path
 ↓
Load
 ↓
Chunk
 ↓
Embed
 ↓
Store
 ↓
Document UUID
```

### Answer Questions

```text
RAGPipeline.answer(query)
```

Flow:

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
GeneratedAnswer
```

The complete usage sequence is:

```text
Ingest Document
    ↓
Knowledge Stored in pgvector
    ↓
Ask Question
    ↓
Relevant Chunks Retrieved
    ↓
LLM Receives Context
    ↓
Grounded Answer
```

The composition root constructs both application capabilities independently.

It does not automatically run ingestion before question answering.

---

## Shared Embedding Model

The ingestion and online query flows use the same embedding model:

```text
all-MiniLM-L6-v2
```

The composition architecture is:

```text
                 Shared SentenceTransformer
                      /              \
                     ↓                ↓
           LocalChunkEmbedder   LocalQueryEmbedder
                     ↓                ↓
          IngestionPipeline       RAGPipeline
```

The model is created once and reused.

This avoids:

- duplicate model loading
- unnecessary memory usage
- duplicate initialization

It also ensures stored chunk embeddings and query embeddings use the same vector space.

---

## Application Composition

The composition root now provides:

```text
create_embedding_model()
```

```text
create_ingestion_pipeline()
```

```text
create_rag_pipeline()
```

The responsibilities are:

```text
Composition Root
└── construct application capabilities
```

```text
IngestionPipeline
└── execute document ingestion
```

```text
RAGPipeline
└── execute question answering
```

The composition root does not:

- select a document
- ingest a document
- ask a question

Runtime callers execute those operations.

---

## Current Ingestion Usage

The ingestion capability currently accepts a filesystem path.

Example:

```python
pipeline = create_ingestion_pipeline()

document_id = pipeline.ingest(
    "path/to/document.pdf"
)
```

The path is supplied by the caller.

The flow is:

```text
Caller
 ↓
File Path
 ↓
IngestionPipeline
 ↓
PdfLoader
 ↓
DocumentChunker
 ↓
ChunkEmbedder
 ↓
VectorStore
 ↓
PostgreSQL + pgvector
```

The ingestion pipeline is fully functional, but it does not yet have an external HTTP entry point.

The next sprint will expose it through a document upload API.

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
143 tests passing
```

Sprint 13 added:

```text
7 upload adapter tests
```

```text
6 document endpoint tests
```

```text
1 real HTTP ingestion integration test
```

The upload adapter tests prove:

```text
DocumentUploadAdapter
├── returns document UUID
├── passes PDF path to pipeline
├── copies uploaded bytes
├── preserves original filename
├── cleans temporary data after success
├── cleans temporary data after failure
└── propagates pipeline failure unchanged
```

The endpoint tests prove:

```text
POST /documents
├── returns 201 Created
├── returns document UUID
├── invokes ingestion pipeline
├── rejects missing file
├── rejects unsupported media type
└── returns 500 for unhandled pipeline failure
```

The real HTTP integration test proves:

```text
sample.pdf
    ↓
multipart HTTP upload
    ↓
FastAPI
    ↓
DocumentUploadAdapter
    ↓
IngestionPipeline
    ↓
PdfLoader
    ↓
RecursiveDocumentChunker
    ↓
LocalChunkEmbedder
    ↓
PostgresVectorStore
    ↓
PostgreSQL + pgvector
```

It verifies:

```text
HTTP
├── 201 Created
└── valid document UUID
```

```text
Document
├── persisted
├── original filename preserved
└── page count preserved
```

```text
Chunks
├── multiple chunks persisted
├── indexes ordered
├── content non-empty
└── embeddings have 384 dimensions
```

The real integration test also exposed a cross-boundary metadata bug that isolated tests did not detect.

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

The RAG engine now has a complete first product loop:

```text
Upload Knowledge
    ↓
Store Embeddings
    ↓
Ask Questions
    ↓
Retrieve Context
    ↓
Generate Grounded Answers
    ↓
Observe Runtime Execution
```

The application now supports:

```text
POST /documents
```

```text
POST /answers
```

and:

```text
structured runtime observability
```

The next phase should focus on production hardening rather than adding more pipeline features immediately.

Potential areas include:

- centralized error handling
- API error contracts
- configuration validation
- file-size limits
- content-based PDF validation
- health and readiness endpoints
- graceful application startup
- graceful shutdown
- ingestion idempotency behavior
- document management APIs
- deployment packaging

Advanced observability can later introduce:

```text
metrics
```

```text
stage-level timing
```

```text
distributed tracing
```

```text
dashboards
```

only when the application has a concrete operational need for them.