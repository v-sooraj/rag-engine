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

### 🚧 In Progress

- Prompt augmentation

### 📋 Planned

- LLM integration
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
- end-to-end ingestion pipeline tests
- end-to-end semantic retrieval pipeline tests

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
```

The system can now:

```text
store knowledge
```

and:

```text
retrieve semantically relevant knowledge
```

The next phase will transform retrieved chunks into augmented context for an LLM prompt.

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

Current ADRs document the major architectural decisions made while building the RAG engine from scratch.

## Next Phase

Sprint 08 will introduce prompt augmentation:

```text
User Query
 ↓
Query Embedding
 ↓
Top-K Retrieved Chunks
 ↓
Context Construction
 ↓
Augmented Prompt
```

This will prepare the system for LLM integration.