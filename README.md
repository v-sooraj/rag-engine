# RAG Engine

A production-oriented Retrieval-Augmented Generation (RAG) engine built from scratch to understand every architectural layer behind modern AI applications.

## Goals

- Learn production-grade AI backend engineering
- Build every layer incrementally
- Prioritize architecture over frameworks

## Tech Stack

- Python
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

From the application caller's perspective:

```text
User Query
    ↓
RAGPipeline.answer()
    ↓
GeneratedAnswer
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

### 🚧 In Progress

- API exposure

### 📋 Planned

- FastAPI
- Observability

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
- shared embedding model instances across chunk and query embedding capabilities
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
- real local LLM integration testing
- complete real query-to-answer orchestration testing

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
```

The complete online flow is coordinated by:

```text
RAGPipeline
```

The caller now performs:

```python
answer = pipeline.answer(query)
```

rather than manually coordinating every stage.

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

Each major pipeline boundary preserves meaningful structure rather than collapsing application concepts into primitive values too early.

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

## Pipeline Dependencies

`DefaultRAGPipeline` receives:

```text
QueryEmbedder
Retriever
PromptAugmenter
LLM
top_k
```

through constructor injection.

The pipeline depends on capability abstractions rather than concrete infrastructure implementations.

The current composition is:

```text
DefaultRAGPipeline
├── LocalQueryEmbedder
├── PostgresRetriever
├── DefaultPromptAugmenter
├── OllamaLLM
└── top_k
```

---

## Retrieval Configuration

The retrieval depth is configured when the pipeline is created:

```python
pipeline = DefaultRAGPipeline(
    query_embedder=query_embedder,
    retriever=retriever,
    prompt_augmenter=prompt_augmenter,
    llm=llm,
    top_k=3,
)
```

The caller then uses:

```python
answer = pipeline.answer(query)
```

The ordinary query operation does not expose vector retrieval strategy.

---

## Pipeline Validation

The pipeline rejects:

```text
empty query
blank query
```

before calling any dependency.

The pipeline also rejects invalid configuration:

```text
top_k <= 0
```

The rule is:

```text
top_k > 0
```

This keeps invalid input and invalid configuration from entering pipeline execution.

---

## Pipeline Failure Behavior

`DefaultRAGPipeline` does not wrap stage-specific failures.

Failures from:

```text
QueryEmbedder
Retriever
PromptAugmenter
LLM
```

propagate unchanged.

For example:

```text
Ollama unavailable
    ↓
OllamaLLM
    ↓
LLMGenerationError
    ↓
RAGPipeline
    ↓
caller receives LLMGenerationError
```

The orchestration layer does not introduce a generic `RAGPipelineError`.

---

## Empty Retrieval Behavior

If retrieval returns no chunks:

```text
Retriever
    ↓
[]
```

the pipeline continues:

```text
[]
    ↓
PromptAugmenter
    ↓
AugmentedPrompt with empty context
    ↓
LLM
    ↓
GeneratedAnswer
```

The orchestrator does not create a separate hard-coded fallback answer.

Grounding behavior remains owned by the prompt and generation stages.

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
96 tests passing
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
- real Ollama integration tests
- complete pipeline integration tests

---

## Orchestration Test Coverage

The RAG pipeline unit tests prove:

```text
Happy Path
├── query is embedded
├── configured top_k is used
├── retrieved chunks are passed forward
├── original query is preserved
├── augmented prompt is passed to the LLM
└── GeneratedAnswer is returned unchanged
```

```text
Boundary Validation
├── empty query rejected
├── blank query rejected
├── zero top_k rejected
└── negative top_k rejected
```

```text
Behavior
└── zero retrieved chunks continue through the pipeline
```

```text
Failure Semantics
├── QueryEmbedder failure propagates unchanged
├── Retriever failure propagates unchanged
├── PromptAugmenter failure propagates unchanged
└── LLM failure propagates unchanged
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

The complete real RAG test now proves the application-level operation:

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

The online stages are no longer manually coordinated inside the integration test.

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

This keeps the RAG engine organized around capabilities rather than framework-specific components.

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

ADRs document the major architectural decisions made while building the RAG engine from scratch.

---

## Core RAG Pipeline Status

The core online RAG pipeline is now complete and orchestrated:

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

The public application operation is:

```text
RAGPipeline.answer(query)
```

The system can now:

```text
store knowledge
```

then:

```text
receive a user question
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

through one application-level pipeline boundary.

---

## Next Phase

The next sprint will expose the completed RAG pipeline through an HTTP API.

The next stage will decide:

- the FastAPI application boundary
- request and response API models
- how application dependencies are composed
- where pipeline configuration is created
- how `RAGPipeline` is injected into the API layer
- how application failures map to HTTP responses
- which endpoint exposes question answering

The target flow is:

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