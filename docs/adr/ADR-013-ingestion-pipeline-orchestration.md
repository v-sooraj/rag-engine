# ADR-013: Introduce an Explicit Ingestion Pipeline Orchestrator

## Status

Accepted

## Context

The application already contained the complete capabilities required to ingest documents:

```text
DocumentLoader
DocumentChunker
ChunkEmbedder
VectorStore
```

However, no application-level abstraction coordinated them.

A caller had to manually execute:

```text
load
 ↓
chunk
 ↓
embed
 ↓
store
```

The online RAG flow already had:

```text
RAGPipeline.answer(query)
```

which hid:

```text
embed query
 ↓
retrieve
 ↓
augment
 ↓
generate
```

The ingestion side needed an equivalent application boundary.

The design also needed to decide:

- whether callers should continue coordinating ingestion stages
- whether ingestion should be part of `RAGPipeline`
- whether the composition root should automatically ingest documents
- where the file path should come from
- what the ingestion operation should return
- whether failures should be wrapped
- whether ingestion and query embedding should share a model instance

---

## Decision

Introduce:

```text
IngestionPipeline
    ↑
DefaultIngestionPipeline
```

with the public operation:

```text
ingest(path: str) -> UUID
```

The pipeline coordinates:

```text
DocumentLoader
 ↓
DocumentChunker
 ↓
ChunkEmbedder
 ↓
VectorStore
```

The caller supplies the file path at runtime.

The composition root constructs the ingestion pipeline but does not execute ingestion.

The ingestion and RAG pipelines remain independent application capabilities.

The chunk embedder and query embedder share one application-scoped `SentenceTransformer` instance.

Stage-specific failures propagate unchanged.

---

## Decision Drivers

The decision is based on the following requirements:

- provide one public application operation for ingestion
- prevent callers from coordinating internal stages
- preserve existing capability boundaries
- keep ingestion separate from question answering
- keep composition separate from business execution
- preserve existing vector-store transaction behavior
- return meaningful persistence identity
- avoid speculative exception architecture
- avoid loading the same embedding model twice
- support a future document upload API

---

## Considered Option: Keep Manual Coordination

The caller would continue performing:

```text
DocumentLoader.load(path)
 ↓
DocumentChunker.chunk(document)
 ↓
ChunkEmbedder.embed(chunks)
 ↓
VectorStore.store(...)
```

Advantages:

- no new abstraction
- fewer files

Disadvantages:

- every caller must know the ingestion sequence
- every caller must connect stage outputs correctly
- orchestration logic can be duplicated
- the application has no single ingestion operation
- the architecture remains asymmetric with `RAGPipeline`

This option was rejected.

---

## Considered Option: Add Ingestion to RAGPipeline

Conceptually:

```text
RAGPipeline
├── ingest(path)
└── answer(query)
```

Advantages:

- one application object

Disadvantages:

- combines write and read/generation workflows
- expands the pipeline into unrelated responsibilities
- couples document processing with question answering
- weakens application boundaries

This option was rejected.

---

## Selected Option: Dedicated IngestionPipeline

The selected architecture is:

```text
IngestionPipeline
└── ingest(path)
```

and separately:

```text
RAGPipeline
└── answer(query)
```

The application therefore exposes two explicit capabilities:

```text
Write Knowledge
    ↓
IngestionPipeline
```

```text
Read and Generate
    ↓
RAGPipeline
```

---

## Ingestion Operation

The selected operation is:

```text
ingest(path: str) -> UUID
```

The sequence is:

```text
validate path
 ↓
load document
 ↓
chunk document
 ↓
embed chunks
 ↓
store document and vectors
 ↓
return persisted document UUID
```

---

## File Path Decision

The file path is supplied by the caller.

The composition root does not configure a document path.

The separation is:

```text
Composition
└── construct capability
```

```text
Caller
└── supply runtime document
```

Example:

```python
pipeline = create_ingestion_pipeline()

document_id = pipeline.ingest(
    "path/to/document.pdf"
)
```

This preserves the distinction between:

```text
application construction
```

and:

```text
application operation execution
```

---

## Why the Composition Root Does Not Ingest Automatically

The composition root owns object construction.

It does not own business operation execution.

The following design was rejected:

```text
Application Startup
 ↓
Automatically Load File
 ↓
Automatically Ingest
 ↓
Create RAG Pipeline
```

Automatic ingestion would incorrectly couple:

- startup lifecycle
- document selection
- ingestion execution
- application availability

It would also require the composition root to answer questions outside its responsibility:

- which file?
- how many files?
- ingest on every restart?
- retry failed ingestion?
- block startup until ingestion completes?

Therefore:

```text
create_ingestion_pipeline()
```

only constructs the capability.

Ingestion happens only when a caller invokes:

```text
ingest(path)
```

---

## Product Ordering Decision

The composition root does not force operation ordering.

However, application usage follows:

```text
Ingest
 ↓
Store Knowledge
 ↓
Ask Question
 ↓
Retrieve Knowledge
 ↓
Generate Grounded Answer
```

If querying happens before relevant knowledge exists:

```text
Retriever
 ↓
No Context
 ↓
Strict Grounding Policy
 ↓
Insufficient-Information Answer
```

This is expected behavior.

---

## Return Type Decision

The ingestion operation returns:

```text
UUID
```

The UUID is the persisted document identity returned by `VectorStore`.

Advantages:

- confirms successful persistence
- exposes a stable document identity
- supports future API responses
- preserves existing idempotency behavior

A future HTTP adapter can map it to:

```json
{
  "document_id": "..."
}
```

---

## Failure Handling Decision

The pipeline does not wrap every stage failure.

The selected behavior is:

```text
Loader Failure
 ↓
propagate unchanged
```

```text
Chunker Failure
 ↓
propagate unchanged
```

```text
Embedder Failure
 ↓
propagate unchanged
```

```text
Vector Store Failure
 ↓
propagate unchanged
```

No new generic ingestion exception hierarchy is introduced.

This preserves stage-specific failure information until concrete error-handling requirements exist.

---

## Transaction Decision

The ingestion pipeline does not create a transaction across all stages.

The vector store continues to own the database transaction.

The sequence is:

```text
Load
 ↓
Chunk
 ↓
Embed
 ↓
VectorStore.store(...)
       ↓
   database transaction
```

This preserves the existing persistence responsibility.

---

## Shared Embedding Model Decision

Both:

```text
LocalChunkEmbedder
```

and:

```text
LocalQueryEmbedder
```

use:

```text
all-MiniLM-L6-v2
```

The composition root creates one shared:

```text
SentenceTransformer
```

instance.

The selected architecture is:

```text
                 Shared Embedding Model
                    /              \
                   ↓                ↓
         LocalChunkEmbedder   LocalQueryEmbedder
                   ↓                ↓
        IngestionPipeline       RAGPipeline
```

---

## Why the Model Is Shared

Separate model instances would cause:

- duplicate memory consumption
- duplicate initialization
- unnecessary resource usage

The ingestion and query flows must also operate in the same vector space.

The shared application-scoped model makes this relationship explicit.

---

## Lifecycle Decision

The composition root caches:

```text
SentenceTransformer
```

```text
IngestionPipeline
```

```text
RAGPipeline
```

Each is created once and reused.

Construction does not trigger:

```text
ingest(path)
```

or:

```text
answer(query)
```

---

## Real Integration Verification

The complete ingestion operation was tested using:

```text
tests/resources/sample.pdf
```

The real flow was:

```text
sample.pdf
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

The test verified persisted:

- document identity
- filename
- page count
- chunk content
- chunk ordering
- 384-dimensional vectors

---

## Testing Decision

Use three testing levels.

### Orchestration Unit Tests

Mock:

```text
DocumentLoader
DocumentChunker
ChunkEmbedder
VectorStore
```

Verify only:

- stage ordering
- argument forwarding
- result forwarding
- validation
- failure propagation

### Real Integration Test

Use real:

```text
PdfLoader
RecursiveDocumentChunker
LocalChunkEmbedder
PostgresVectorStore
PostgreSQL
pgvector
```

Verify the complete application operation.

### Composition Tests

Mock concrete constructors and verify:

- application-scoped reuse
- pipeline construction
- shared embedding model injection

---

## Consequences

### Positive

- callers have one ingestion operation
- ingestion stage coordination is centralized
- ingestion and online RAG have symmetric application boundaries
- existing capabilities remain independently testable
- the composition root can construct both application workflows
- embedding model memory is reused
- real end-to-end ingestion is proven
- a future upload API has a clean application capability to call

### Negative

- ingestion currently accepts only a filesystem path
- no external client can upload a document yet
- ingestion is synchronous
- there is no progress or job status model

### Neutral

The caller must supply a file path because document selection is runtime input.

---

## Future Considerations

A future inbound HTTP adapter should provide:

```text
POST /documents
```

The expected flow is:

```text
HTTP Upload
 ↓
Temporary File
 ↓
IngestionPipeline.ingest(path)
 ↓
Document UUID
 ↓
HTTP Response
```

The adapter should own:

- multipart upload handling
- temporary file creation
- temporary file cleanup
- HTTP request validation
- HTTP response mapping

The ingestion pipeline should remain unaware of:

- FastAPI
- multipart forms
- uploaded-file objects
- HTTP responses

---

## Final Decision

Introduce a dedicated `IngestionPipeline` application boundary.

Accept the document path as runtime input from the caller.

Coordinate loading, chunking, embedding, and storage inside `DefaultIngestionPipeline`.

Return the persisted document UUID.

Keep ingestion separate from `RAGPipeline`.

Keep business operation execution separate from the composition root.

Share one application-scoped embedding model between ingestion and query embedding.