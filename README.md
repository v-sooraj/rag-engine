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

### Retrieval Pipeline

```text
User Query
 ↓
QueryEmbedder
 ↓
LocalQueryEmbedder
 ↓
all-MiniLM-L6-v2
 ↓
Query Embedding
 ↓
Retriever
 ↓
PostgresRetriever
 ↓
pgvector Cosine-Distance Search
 ↓
Top-K Retrieved Chunks
```

### Prompt Augmentation Pipeline

```text
User Query
        +
Top-K Retrieved Chunks
        ↓
PromptAugmenter
        ↓
DefaultPromptAugmenter
        ↓
AugmentedPrompt
├── system_instruction
├── context
└── question
```

### LLM Generation Pipeline

```text
AugmentedPrompt
    ↓
LLM
    ↓
OllamaLLM
    ↓
HTTP
    ↓
Ollama
    ↓
qwen3:4b
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
- Complete real RAG generation pipeline

### 🚧 In Progress

- RAG pipeline orchestration

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
- real local LLM integration testing
- complete real query-to-answer RAG pipeline testing

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

The system can now:

```text
store knowledge
```

then:

```text
retrieve semantically relevant knowledge
```

then:

```text
construct structured grounded model input
```

then:

```text
generate an answer using a local LLM
```

---

## Domain Flow

The core domain models now form the following pipeline:

```text
Document
    ↓
Chunk
    ↓
EmbeddedChunk
    ↓
Stored Vector
```

and:

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

Each major pipeline boundary preserves meaningful structure rather than collapsing application concepts into primitive values too early.

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

## Error Handling

LLM generation exposes one application-level failure:

```text
LLMGenerationError
```

Infrastructure failures such as:

- connection errors
- timeouts
- non-success HTTP responses
- malformed model responses
- empty generated content

are translated into the LLM-specific application exception.

The original failure is preserved as the exception cause for debugging.

---

## Testing

The project currently has:

```text
82 tests passing
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
- real Ollama integration tests
- complete pipeline integration tests

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

The retrieval and augmentation coverage proves:

```text
Real Query
 ↓
Query Embedding
 ↓
Semantic Retrieval
 ↓
Retrieved Chunks
 ↓
Prompt Augmentation
 ↓
AugmentedPrompt
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

The complete real RAG test proves:

```text
Stored Knowledge
    ↓
Local Embeddings
    ↓
PostgreSQL + pgvector

User Query
    ↓
Query Embedding
    ↓
Semantic Retrieval
    ↓
Prompt Augmentation
    ↓
Local LLM Generation
    ↓
GeneratedAnswer
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
```

This keeps the RAG pipeline organized around capabilities rather than framework-specific components.

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

ADRs document the major architectural decisions made while building the RAG engine from scratch.

---

## Core RAG Pipeline Status

The core RAG capabilities are now complete:

```text
Load
 ↓
Chunk
 ↓
Embed
 ↓
Store
 ↓
Retrieve
 ↓
Augment
 ↓
Generate
```

However, the complete online flow is currently composed manually in integration tests.

The application does not yet expose one capability such as:

```text
answer(query)
```

that coordinates:

```text
QueryEmbedder
 ↓
Retriever
 ↓
PromptAugmenter
 ↓
LLM
```

---

## Next Phase

The next sprint will introduce RAG pipeline orchestration:

```text
User Query
    ↓
RAG Pipeline
    ├── QueryEmbedder
    ├── Retriever
    ├── PromptAugmenter
    └── LLM
    ↓
GeneratedAnswer
```

The next stage will decide:

- the orchestration abstraction boundary
- whether orchestration returns `GeneratedAnswer` directly
- how `top_k` enters the pipeline
- how pipeline dependencies are composed
- how the current manually assembled integration flow becomes one application-level operation

After orchestration, the complete online RAG pipeline will be ready to expose through FastAPI.