# Sprint 12 — Ingestion Pipeline Orchestration

## Status

Completed

## Objective

Introduce a single application-level capability that orchestrates the complete document ingestion flow.

Before this sprint, the project already contained all ingestion capabilities:

```text
DocumentLoader
DocumentChunker
ChunkEmbedder
VectorStore
```

However, a caller had to coordinate them manually:

```text
Caller
 ↓
DocumentLoader.load(path)
 ↓
DocumentChunker.chunk(document)
 ↓
ChunkEmbedder.embed(chunks)
 ↓
VectorStore.store(document, embedded_chunks)
```

This sprint introduces:

```text
IngestionPipeline.ingest(path)
```

The caller now performs one application-level operation:

```text
File Path
    ↓
IngestionPipeline.ingest(path)
    ↓
Persisted Document UUID
```

---

## Scope

This sprint includes:

- ingestion pipeline abstraction
- default ingestion pipeline implementation
- orchestration of the complete ingestion flow
- ingestion input validation
- unchanged stage-specific failure propagation
- persisted document ID return value
- real end-to-end ingestion integration testing
- ingestion pipeline composition
- shared embedding model composition
- application-scoped ingestion pipeline reuse
- composition tests

This sprint does not include:

- document upload API
- multipart file handling
- temporary file management
- automatic document ingestion at application startup
- directory watching
- asynchronous ingestion
- ingestion job tracking
- ingestion status endpoints
- ingestion progress reporting
- observability
- authentication
- authorization

These concerns belong to later stages.

---

## Problem Before This Sprint

The project had two major flows.

### Online RAG Flow

The online flow already had an application-level orchestrator:

```text
User Query
    ↓
RAGPipeline.answer(query)
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

A caller did not need to coordinate the individual stages.

The caller performed:

```python
answer = pipeline.answer(query)
```

### Ingestion Flow

The ingestion side had no equivalent application-level capability.

The caller had to perform:

```text
File Path
    ↓
DocumentLoader
    ↓
Document
    ↓
DocumentChunker
    ↓
Chunks
    ↓
ChunkEmbedder
    ↓
Embedded Chunks
    ↓
VectorStore
    ↓
Document UUID
```

Conceptually:

```python
document = document_loader.load(path)

chunks = document_chunker.chunk(document)

embedded_chunks = chunk_embedder.embed(chunks)

document_id = vector_store.store(
    document,
    embedded_chunks,
)
```

The architecture was therefore asymmetric:

```text
ONLINE

Caller
 ↓
RAGPipeline
 ↓
Complete Online Flow
```

```text
INGESTION

Caller
 ↓
Manually Coordinate Four Capabilities
```

This sprint removes that asymmetry.

---

## Selected Architecture

The ingestion flow now has a dedicated application boundary:

```text
IngestionPipeline
    ↑
DefaultIngestionPipeline
```

The public operation is:

```text
ingest(path)
```

The complete flow is:

```text
File Path
    ↓
IngestionPipeline.ingest(path)
    ↓
DocumentLoader
    ↓
DocumentChunker
    ↓
ChunkEmbedder
    ↓
VectorStore
    ↓
Persisted Document UUID
```

The caller no longer knows how the ingestion stages are coordinated.

---

## Package Structure

```text
rag_engine/
├── ingestion_pipeline/
│   ├── __init__.py
│   ├── ingestion_pipeline.py
│   └── default_ingestion_pipeline.py
│
├── loader/
├── chunker/
├── embedding/
├── vector_store/
├── rag_pipeline/
└── composition/
```

Test structure:

```text
tests/
├── ingestion_pipeline/
│   ├── __init__.py
│   ├── test_default_ingestion_pipeline.py
│   └── test_real_ingestion_pipeline.py
│
└── composition/
    ├── __init__.py
    └── test_application.py
```

---

## Ingestion Pipeline Abstraction

The application-level abstraction is:

```text
IngestionPipeline
```

Its public operation is:

```text
ingest(path: str) -> UUID
```

The input is:

```text
path
```

The output is:

```text
persisted document UUID
```

The abstraction represents one complete application operation:

```text
ingest this document into the knowledge base
```

It does not expose the internal stages to the caller.

---

## Why the Pipeline Accepts a File Path

The current document loader contract is:

```text
DocumentLoader.load(path)
```

Therefore the ingestion pipeline accepts:

```text
path: str
```

and forwards it to the document loader.

The flow is:

```text
Caller
    ↓
chooses file path
    ↓
IngestionPipeline.ingest(path)
    ↓
DocumentLoader.load(path)
```

For example:

```python
pipeline.ingest(
    "tests/resources/sample.pdf"
)
```

or:

```python
pipeline.ingest(
    "C:/documents/knowledge.pdf"
)
```

The path is runtime input.

It is not composition configuration.

---

## Who Supplies the File Path

The composition root does not choose a document.

The caller supplies the path when it wants to perform ingestion.

The separation is:

```text
Composition Root
    ↓
construct IngestionPipeline
```

and later:

```text
Caller
    ↓
select document
    ↓
call ingest(path)
```

The current real integration test acts as the caller:

```text
tests/resources/sample.pdf
    ↓
DefaultIngestionPipeline.ingest(path)
```

A future document upload API will become the real external caller.

---

## Why Composition Does Not Run Ingestion

The composition root constructs application capabilities.

It does not execute application operations.

The correct responsibility is:

```text
Composition Root
├── create_ingestion_pipeline()
└── create_rag_pipeline()
```

The following design is intentionally rejected:

```text
Application Startup
    ↓
Composition Root
    ↓
Automatically Select PDF
    ↓
Automatically Ingest PDF
    ↓
Start Application
```

Automatic startup ingestion would create unresolved questions:

- which document should be ingested?
- where should the document come from?
- should every restart ingest it again?
- what happens when thousands of documents exist?
- what happens when ingestion fails during startup?
- should application availability depend on one document?

Ingestion is a business operation.

Composition is object construction.

These responsibilities remain separate.

---

## Product-Level Ordering

Although composition does not automatically run ingestion, the product-level sequence matters.

For a document-specific grounded answer:

```text
1. Ingest Document
       ↓
   Knowledge Stored

2. Ask Question
       ↓
   Knowledge Retrieved

3. Generate Answer
       ↓
   LLM Receives Context
```

If the knowledge base contains no relevant chunks:

```text
Question
    ↓
Retriever
    ↓
No Relevant Context
    ↓
Strict Grounding Prompt
    ↓
Insufficient-Information Answer
```

Therefore:

```text
Ingestion must happen before querying
```

when the expected answer depends on the ingested document.

This ordering is controlled by application usage, not by the composition root.

---

## Default Ingestion Pipeline

The concrete implementation is:

```text
DefaultIngestionPipeline
```

It depends on:

```text
DocumentLoader
DocumentChunker
ChunkEmbedder
VectorStore
```

The object graph is:

```text
DefaultIngestionPipeline
├── DocumentLoader
├── DocumentChunker
├── ChunkEmbedder
└── VectorStore
```

The pipeline depends on abstractions rather than concrete implementations.

---

## Orchestration Sequence

`DefaultIngestionPipeline.ingest(path)` performs:

```text
validate path
    ↓
document_loader.load(path)
    ↓
document_chunker.chunk(document)
    ↓
chunk_embedder.embed(chunks)
    ↓
vector_store.store(document, embedded_chunks)
    ↓
return document UUID
```

Each stage receives the exact output of the previous stage.

---

## Thin Orchestration

The ingestion pipeline owns:

- input validation
- stage ordering
- passing outputs between stages
- returning the final persistence result

It does not own:

- PDF parsing
- metadata extraction
- chunking strategy
- chunk overlap logic
- embedding model inference
- database connections
- transaction handling
- document deduplication
- idempotency
- vector persistence

Those responsibilities remain in their existing capabilities.

---

## Input Validation

The ingestion pipeline rejects:

```text
empty path
blank path
```

before any downstream capability is called.

Invalid examples include:

```text
""
" "
"   "
"\t"
"\n"
```

The pipeline raises:

```text
ValueError
```

with:

```text
path must not be empty or blank
```

This protects the public application operation.

---

## Failure Semantics

The ingestion pipeline does not wrap stage-specific failures.

If:

```text
DocumentLoader
```

fails, the loader failure propagates unchanged.

If:

```text
DocumentChunker
```

fails, the chunker failure propagates unchanged.

If:

```text
ChunkEmbedder
```

fails, the embedding failure propagates unchanged.

If:

```text
VectorStore
```

fails, the storage failure propagates unchanged.

The pipeline does not introduce a speculative:

```text
IngestionPipelineError
```

hierarchy.

---

## Fail-Fast Stage Ordering

If one stage fails, later stages do not execute.

### Loader Failure

```text
DocumentLoader
    ↓
failure
    ↓
STOP
```

The following are not called:

```text
DocumentChunker
ChunkEmbedder
VectorStore
```

### Chunker Failure

```text
DocumentLoader
    ↓
DocumentChunker
    ↓
failure
    ↓
STOP
```

The following are not called:

```text
ChunkEmbedder
VectorStore
```

### Embedder Failure

```text
DocumentLoader
    ↓
DocumentChunker
    ↓
ChunkEmbedder
    ↓
failure
    ↓
STOP
```

The vector store is not called.

---

## Persistence Responsibility

The ingestion pipeline does not manage database transactions.

The flow is:

```text
IngestionPipeline
    ↓
VectorStore.store(...)
```

The vector store remains responsible for:

- database connection behavior
- persistence transaction
- document persistence
- chunk persistence
- vector persistence
- rollback
- deduplication
- idempotency

This preserves the existing persistence boundary.

---

## Return Value

The pipeline returns:

```text
UUID
```

representing the persisted document.

The flow is:

```text
VectorStore.store(...)
    ↓
Document UUID
    ↓
IngestionPipeline
    ↓
Caller
```

This allows a future external adapter to return the persisted document identity.

For example:

```text
POST /documents
    ↓
IngestionPipeline.ingest(path)
    ↓
document_id
    ↓
HTTP Response
```

---

## Real Ingestion Pipeline Integration Test

A real integration test proves the complete application operation.

The test uses:

```text
tests/resources/sample.pdf
```

and executes:

```text
Real PDF
    ↓
DefaultIngestionPipeline
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

The concrete configuration is:

```text
PdfLoader
```

```text
RecursiveDocumentChunker
├── chunk_size = 500
└── chunk_overlap = 50
```

```text
LocalChunkEmbedder
├── model = all-MiniLM-L6-v2
└── batch_size = 2
```

```text
PostgresVectorStore
```

---

## What the Real Integration Test Proves

The real test proves:

```text
Real PDF Path
    ↓
real file loading
    ↓
real text extraction
    ↓
real recursive chunking
    ↓
real local embedding generation
    ↓
real PostgreSQL persistence
    ↓
real pgvector storage
```

The persisted document is verified directly in PostgreSQL.

The test verifies:

```text
Document
├── persisted
├── filename preserved
└── page count preserved
```

The test also verifies:

```text
Chunks
├── multiple chunks persisted
├── chunk indexes ordered
├── content persisted
└── embeddings have 384 dimensions
```

The test returns and verifies a real:

```text
UUID
```

---

## Application Composition

The composition root now constructs two application-level capabilities:

```text
Composition Root
├── create_ingestion_pipeline()
└── create_rag_pipeline()
```

These capabilities are independent.

Construction does not execute either operation.

---

## Ingestion Composition

The real ingestion object graph is:

```text
PdfLoader
        \
         \
RecursiveDocumentChunker
           \
            \
LocalChunkEmbedder
              \
               \
PostgresVectorStore
                 \
                  ↓
         DefaultIngestionPipeline
```

The composition root selects the concrete implementations.

The pipeline coordinates them through their abstractions.

---

## RAG Composition

The online RAG object graph remains:

```text
LocalQueryEmbedder
        \
         \
PostgresRetriever
           \
            \
DefaultPromptAugmenter
              \
               \
OllamaLLM
                 \
                  ↓
          DefaultRAGPipeline
```

The two application operations are:

```text
IngestionPipeline.ingest(path)
```

and:

```text
RAGPipeline.answer(query)
```

---

## Shared Embedding Model

Both ingestion and retrieval queries use:

```text
all-MiniLM-L6-v2
```

The ingestion side uses it through:

```text
LocalChunkEmbedder
```

The online side uses it through:

```text
LocalQueryEmbedder
```

The composition root now creates one shared:

```text
SentenceTransformer
```

instance.

The architecture is:

```text
                    SentenceTransformer
                         /        \
                        ↓          ↓
             LocalChunkEmbedder   LocalQueryEmbedder
                        ↓          ↓
              IngestionPipeline   RAGPipeline
```

---

## Why the Embedding Model Is Shared

Loading two independent copies of the same model would cause:

- unnecessary memory usage
- duplicate model initialization
- slower application initialization
- redundant CPU or GPU resources

The same embedding space must also be used for:

```text
stored chunk embeddings
```

and:

```text
query embeddings
```

The shared model makes this relationship explicit.

---

## Embedding Model Lifecycle

The composition root exposes cached model construction.

The lifecycle is:

```text
First Model Resolution
    ↓
Create SentenceTransformer
    ↓
Cache Instance
```

Later:

```text
Ingestion Pipeline Construction
    ↓
Reuse Shared Model
```

and:

```text
RAG Pipeline Construction
    ↓
Reuse Shared Model
```

The model is not loaded separately for each pipeline.

---

## Application-Scoped Pipeline Reuse

The composition root also caches:

```text
IngestionPipeline
```

and:

```text
RAGPipeline
```

The lifecycle is:

```text
First create_ingestion_pipeline()
    ↓
construct ingestion object graph
    ↓
cache
```

Later calls reuse the same ingestion pipeline.

Similarly:

```text
First create_rag_pipeline()
    ↓
construct online RAG object graph
    ↓
cache
```

Later calls reuse the same RAG pipeline.

---

## Composition Does Not Imply Execution

This distinction is essential:

```text
create_ingestion_pipeline()
```

means:

```text
construct and return an ingestion capability
```

It does not mean:

```text
find a file and ingest it
```

Similarly:

```text
create_rag_pipeline()
```

means:

```text
construct and return a question-answering capability
```

It does not mean:

```text
ask a question
```

Execution happens only when a caller invokes:

```text
ingestion_pipeline.ingest(path)
```

or:

```text
rag_pipeline.answer(query)
```

---

## Unit Testing Strategy

The ingestion pipeline unit tests replace all four capabilities with mocks:

```text
Mock DocumentLoader
Mock DocumentChunker
Mock ChunkEmbedder
Mock VectorStore
```

The tests focus only on orchestration.

They do not:

- read a real PDF
- load an embedding model
- connect to PostgreSQL

---

## Ingestion Pipeline Unit Tests

The tests prove:

```text
Happy Path
├── returns persisted document UUID
├── passes path to loader
├── passes Document to chunker
├── passes chunks to embedder
└── passes Document + EmbeddedChunks to VectorStore
```

They also prove:

```text
Boundary Validation
└── empty and blank paths are rejected
```

And:

```text
Failure Semantics
├── loader failure propagates unchanged
├── chunker failure propagates unchanged
├── embedder failure propagates unchanged
└── vector store failure propagates unchanged
```

The unit test suite contains:

```text
14 tests
```

---

## Composition Testing Strategy

Composition tests mock concrete infrastructure constructors.

The tests prove:

```text
Embedding Model
├── created once
└── reused
```

```text
Ingestion Pipeline
├── composition returns IngestionPipeline
├── pipeline instance is reused
└── receives shared embedding model
```

```text
RAG Pipeline
├── composition returns RAGPipeline
├── pipeline instance is reused
└── receives shared embedding model
```

```text
Cross-Pipeline Composition
└── chunk and query embedders receive the same model instance
```

The composition test suite contains:

```text
8 tests
```

---

## Test Count

Before Sprint 12:

```text
106 tests
```

Sprint 12 added:

```text
14 ingestion pipeline unit tests
```

```text
1 real ingestion pipeline integration test
```

```text
8 composition tests
```

The complete suite now contains:

```text
129 tests passing
```

---

## Architecture Before and After

### Before

```text
INGESTION

Caller
 ↓
DocumentLoader
 ↓
DocumentChunker
 ↓
ChunkEmbedder
 ↓
VectorStore
```

```text
ONLINE RAG

Caller
 ↓
RAGPipeline
 ↓
Complete Online Flow
```

### After

```text
INGESTION

Caller
 ↓
IngestionPipeline
 ↓
Complete Ingestion Flow
```

```text
ONLINE RAG

Caller
 ↓
RAGPipeline
 ↓
Complete Online Flow
```

The architecture is now symmetric.

---

## Complete Application Operations

The application now exposes two primary operations.

### Write Knowledge

```text
IngestionPipeline.ingest(path)
```

Flow:

```text
Path
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

### Read and Generate

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

---

## Complete Knowledge Lifecycle

The complete lifecycle is now:

```text
                    WRITE SIDE

PDF Path
    ↓
IngestionPipeline
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


                    READ SIDE

User Query
    ↓
RAGPipeline
    ↓
QueryEmbedder
    ↓
PostgresRetriever
    ↓
PostgreSQL + pgvector
    ↓
Retrieved Chunks
    ↓
PromptAugmenter
    ↓
LLM
    ↓
GeneratedAnswer
```

---

## Current External Accessibility

The online operation already has an HTTP adapter:

```text
POST /answers
    ↓
RAGPipeline.answer(query)
```

The ingestion operation currently does not.

Current usage is:

```python
pipeline = create_ingestion_pipeline()

document_id = pipeline.ingest(
    "path/to/document.pdf"
)
```

Therefore the application capability exists and works, but there is not yet an external document-upload entry point.

---

## Next Architectural Gap

The missing external flow is:

```text
HTTP Client
    ↓
Upload PDF
    ↓
IngestionPipeline.ingest(path)
```

The next sprint should introduce:

```text
POST /documents
```

The expected flow is:

```text
Client
    ↓
POST /documents
    ↓
PDF Upload
    ↓
Temporary File
    ↓
IngestionPipeline.ingest(path)
    ↓
Document UUID
    ↓
HTTP Response
```

After that, the complete external product flow becomes:

```text
POST /documents
    ↓
Knowledge Stored

POST /answers
    ↓
Knowledge Retrieved
    ↓
Grounded Answer
```

---

## Key Learning Outcomes

This sprint established that:

- having individual capabilities does not create an application workflow
- multi-stage workflows need explicit orchestration boundaries
- ingestion and online RAG are separate application operations
- callers should not manually coordinate internal pipeline stages
- orchestration should remain thin
- orchestration should depend on capability abstractions
- persistence transactions remain inside the persistence boundary
- stage-specific failures can propagate unchanged until a real error taxonomy is required
- runtime input such as a file path comes from the caller
- the composition root constructs capabilities but does not execute business operations
- ingestion must occur before document-grounded querying at the product usage level
- expensive embedding models should be shared across ingestion and query flows
- unit tests should prove orchestration independently of infrastructure
- real integration tests should prove the complete public application operation
- application composition deserves focused tests when resource sharing is architecturally important

---

## Sprint Outcome

Sprint 12 successfully introduced the missing ingestion application boundary.

The application now supports:

```text
IngestionPipeline.ingest(path)
```

which coordinates:

```text
Load
 ↓
Chunk
 ↓
Embed
 ↓
Store
```

The real pipeline has been proven using:

```text
sample.pdf
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

The composition root now provides:

```text
create_ingestion_pipeline()
```

and:

```text
create_rag_pipeline()
```

using one shared embedding model.

The complete application now has both:

```text
Write Knowledge
```

and:

```text
Read Knowledge and Generate
```

capabilities.

The next sprint should expose document ingestion through an HTTP API.