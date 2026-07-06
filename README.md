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
- pytest

## Getting Started

1. Clone the repository.
2. Copy `.env.example` to `.env`.
3. Copy `docker/.env.example` to `docker/.env`.
4. Update the configuration values.
5. Start PostgreSQL using Docker Compose.
6. Run the test suite.

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

### 🚧 In Progress

- LLM integration

### 📋 Planned

- RAG pipeline orchestration
- FastAPI
- Observability

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
- end-to-end ingestion pipeline tests
- end-to-end semantic retrieval pipeline tests
- end-to-end retrieval-to-prompt-augmentation pipeline tests

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
                              ↓
                       AugmentedPrompt
                    ┌─────────┼─────────┐
                    ↓         ↓         ↓
                 System    Context   Question

                    PROMPT AUGMENTATION
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
construct structured grounded input for an LLM
```

## Prompt Augmentation Output

The current prompt augmentation stage produces:

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

## Testing

The project currently has:

```text
61 tests passing
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
- complete pipeline integration tests

The integration coverage proves:

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

and:

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

## Documentation

Detailed architectural discussions and engineering decisions can be found under:

- `docs/architecture`
- `docs/adr`

Current architecture documents cover:

- project foundation
- database connectivity
- document loading
- document chunking
- embedding generation
- vector storage
- retrieval
- prompt augmentation

Current ADRs document the major architectural decisions made while building the RAG engine from scratch.

## Next Phase

Sprint 09 will introduce LLM generation:

```text
AugmentedPrompt
    ↓
LLM
    ↓
Generated Answer
```

The next stage will decide:

- the LLM abstraction boundary
- the generated answer domain model
- how structured prompts map to model input
- which model implementation to use
- how insufficient-context behavior is tested
- how generation remains independent of the rest of the RAG pipeline

After Sprint 09, the system will be able to transform retrieved knowledge into a generated answer.