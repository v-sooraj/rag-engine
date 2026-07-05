# Sprint 06 — Vector Storage

## Status

Completed

## Objective

Implement the vector persistence stage of the RAG ingestion pipeline.

The vector storage stage persists document identity, document metadata, chunk content, and generated embeddings in PostgreSQL using pgvector.

This sprint extends the pipeline from:

PDF → Document → Chunks → Embedded Chunks

to:

PDF → Document → Chunks → Embedded Chunks → PostgreSQL + pgvector

---

## Scope

The sprint includes:

- vector storage abstraction
- PostgreSQL vector store implementation
- normalized document and chunk schema
- pgvector-backed embedding storage
- UUID-based persisted document identity
- SHA-256 content-based document deduplication
- idempotent document ingestion
- atomic document and chunk persistence
- fail-fast storage validation
- batch chunk insertion
- database-backed integrity constraints
- unit tests with injected connection factories
- real PostgreSQL persistence tests
- real idempotency tests
- real transaction rollback tests
- complete ingestion pipeline test

The sprint does not include:

- query embedding
- similarity search
- top-k retrieval
- vector indexes
- HNSW configuration
- IVFFlat configuration
- metadata filtering
- prompt augmentation
- LLM generation

These concerns belong to later pipeline stages.

---

## Pipeline Position

The pipeline before this sprint was:

```text
PDF
 ↓
DocumentLoader
 ↓
Document
 ↓
DocumentChunker
 ↓
list[Chunk]
 ↓
ChunkEmbedder
 ↓
list[EmbeddedChunk]
```

The pipeline after this sprint is:

```text
PDF
 ↓
DocumentLoader
 ↓
Document
 ↓
DocumentChunker
 ↓
list[Chunk]
 ↓
ChunkEmbedder
 ↓
list[EmbeddedChunk]
 ↓
VectorStore
 ↓
PostgreSQL + pgvector
```

The output of this sprint becomes the persisted knowledge base used by the future retrieval stage.

---

## Package Structure

```text
rag_engine/
├── database/
│   └── connection.py
│
└── vector_store/
    ├── vector_store.py
    └── postgres_vector_store.py
```

Test structure:

```text
tests/
└── vector_store/
    ├── test_postgres_vector_store.py
    ├── test_postgres_vector_store_integration.py
    └── test_ingestion_pipeline.py
```

Database initialization:

```text
docker/
└── postgres/
    └── init.sql
```

---

## Storage Abstraction

The storage capability is represented by:

```python
class VectorStore(ABC):

    @abstractmethod
    def store(
        self,
        document: Document,
        chunks: list[EmbeddedChunk],
    ) -> UUID:
        pass
```

The contract accepts:

- the original immutable `Document`
- the complete collection of `EmbeddedChunk` objects

and returns:

- the UUID of the persisted document

The abstraction does not expose:

- SQL
- PostgreSQL
- pgvector
- transaction handling
- content hashing
- duplicate handling

These concerns belong to the concrete storage implementation.

---

## Why the Original Document Is Required

The storage stage receives both:

```text
Document
+
list[EmbeddedChunk]
```

The original `Document` is required because document identity is derived from the complete original document content.

An `EmbeddedChunk` contains:

```text
EmbeddedChunk
├── Chunk
│   ├── content
│   └── ChunkMetadata
└── embedding
```

The original full document content is no longer available from the chunks.

Reconstructing document identity from chunk content would be incorrect because:

- chunks may overlap
- overlap duplicates text
- chunk configuration may change
- changing chunk size could change the reconstructed representation
- changing overlap could change the reconstructed representation

Therefore:

```text
Document.content
    ↓
SHA-256
    ↓
stable document content identity
```

Chunking configuration does not participate in document identity.

---

## Normalized Storage Model

The database uses separate `documents` and `chunks` tables.

```text
documents
    1
    │
    N
  chunks
```

This design was selected instead of storing all data in one flat vector table.

A flat table would repeat document metadata for every chunk:

```text
chunk 0 → filename, title, author, language, page_count
chunk 1 → filename, title, author, language, page_count
chunk 2 → filename, title, author, language, page_count
```

The normalized design stores document metadata once and associates all chunks through a foreign key.

---

## Documents Table

The document table stores:

```text
documents
├── id
├── filename
├── title
├── author
├── language
├── page_count
└── content_hash
```

Schema:

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    filename TEXT NOT NULL,
    title TEXT,
    author TEXT,
    language TEXT,
    page_count INTEGER NOT NULL CHECK (page_count > 0),
    content_hash TEXT NOT NULL UNIQUE
);
```

The original full document content is not stored.

Once ingestion is complete, retrieval operates on chunks.

Persisting both:

```text
full extracted document content
+
all chunk content
```

would duplicate potentially large text data without a current retrieval use case.

---

## Chunks Table

The chunk table stores:

```text
chunks
├── id
├── document_id
├── chunk_index
├── content
└── embedding
```

Schema:

```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
    content TEXT NOT NULL CHECK (length(content) > 0),
    embedding VECTOR(384) NOT NULL,

    CONSTRAINT fk_chunks_document
        FOREIGN KEY (document_id)
        REFERENCES documents(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_chunks_document_chunk_index
        UNIQUE (document_id, chunk_index)
);
```

---

## UUID Identity

Persisted documents and chunks use UUID primary keys.

```text
Document → UUID
Chunk    → UUID
```

The storage operation returns the document UUID:

```text
VectorStore.store(...)
        ↓
UUID
```

UUIDs were selected because persisted identities may later flow through:

- APIs
- ingestion jobs
- logs
- asynchronous workflows
- distributed components

The application generates UUIDs before insertion.

---

## Document Identity

Filename is not a reliable document identity.

Different documents can share the same filename:

```text
report.pdf
report.pdf
```

Metadata combinations are also insufficient.

Two versions of a document can share:

- filename
- title
- author
- language

while containing different content.

The storage implementation therefore calculates:

```text
SHA-256(Document.content)
```

and persists the result as:

```text
content_hash UNIQUE
```

This gives the following behavior:

```text
same content
    ↓
same hash
    ↓
same persisted document
```

and:

```text
same metadata + changed content
    ↓
different hash
    ↓
new persisted document
```

---

## Separation of Responsibilities

Document hashing belongs to the storage stage.

It does not belong to `PdfLoader`.

The loader boundary remains:

```text
PdfLoader
    ↓
load document content and metadata
    ↓
Document
```

The loader does not know:

- whether the document will be persisted
- which database will be used
- how duplicates are detected

The storage boundary owns persistence identity and deduplication.

---

## Idempotent Ingestion

Storing the same document content multiple times is idempotent.

```text
First store
    ↓
new document
    ↓
new UUID
    ↓
insert all chunks
```

```text
Second store with same content
    ↓
same SHA-256
    ↓
existing document
    ↓
return existing UUID
    ↓
insert no chunks
```

The implementation uses:

```sql
INSERT INTO documents (...)
ON CONFLICT (content_hash)
DO NOTHING
RETURNING id
```

If an ID is returned:

```text
this transaction created the document
    ↓
insert all chunks
```

If no ID is returned:

```text
document already exists
    ↓
query existing UUID
    ↓
return existing UUID
    ↓
do not insert chunks
```

---

## Database Authority for Deduplication

An application-level lookup alone is insufficient for concurrent ingestion.

Two concurrent transactions could both observe:

```text
content hash does not exist
```

and both attempt insertion.

The database therefore remains the final authority through:

```text
UNIQUE(content_hash)
```

and:

```text
ON CONFLICT (content_hash) DO NOTHING
```

This prevents duplicate document rows even under concurrent insertion attempts.

---

## Atomic Persistence

Document and chunk persistence form one logical operation.

```text
BEGIN

insert document
insert all chunks

COMMIT
```

If any chunk insertion fails:

```text
ROLLBACK
```

The invariant is:

```text
Document persisted
        ⇔
all of its chunks persisted
```

Partial states are not accepted.

The transaction boundary is owned by `PostgresVectorStore`.

The caller sees one operation:

```text
store(document, chunks)
```

---

## Psycopg Transaction Boundary

The implementation uses the Psycopg connection context manager:

```python
with self.connection_factory() as connection:
```

Successful context exit commits the transaction.

Exceptional context exit rolls back the transaction.

The storage implementation does not expose transaction management to callers.

---

## Fail-Fast Validation

All validation that can be performed in memory occurs before opening a database connection.

The validation flow is:

```text
store(document, chunks)
    ↓
chunks must not be empty
    ↓
chunk document metadata must match document metadata
    ↓
embedding dimension must equal 384
    ↓
chunk indexes must be unique
    ↓
only then open database connection
```

Invalid input therefore does not:

- acquire a database connection
- begin a transaction
- execute SQL

---

## Empty Chunk Validation

The storage operation rejects:

```text
chunks = []
```

A persisted document without retrievable chunks has no purpose in the current RAG ingestion pipeline.

---

## Metadata Consistency

Every embedded chunk must belong to the supplied document.

The implementation validates:

```text
EmbeddedChunk
    ↓
Chunk
    ↓
ChunkMetadata.document_metadata

must equal

Document.metadata
```

This prevents chunks associated with one document from being persisted under another document row.

The full document content hash remains the authoritative document deduplication identity.

---

## Embedding Dimension Boundary

The generic domain model remains model-independent:

```text
EmbeddedChunk.embedding
    ↓
any non-empty list[float]
```

The concrete PostgreSQL storage implementation is model-specific:

```text
PostgresVectorStore
    ↓
exactly 384 dimensions
```

The database provides the final constraint:

```text
VECTOR(384)
```

This creates three validation layers:

```text
Domain
    → embedding must be non-empty

Concrete storage implementation
    → embedding must contain 384 values

Database
    → column type is VECTOR(384)
```

The generic domain model is therefore not coupled to the active embedding model.

---

## Chunk Index Integrity

Chunk indexes must be unique within a document.

The application validates duplicate indexes before opening a connection.

The database also enforces:

```text
UNIQUE(document_id, chunk_index)
```

This prevents states such as:

```text
document A → chunk index 0
document A → chunk index 0
```

while allowing:

```text
document A → chunk index 0
document B → chunk index 0
```

---

## Aggregate Lifecycle

A chunk has no independent lifecycle outside its document.

The foreign key therefore uses:

```sql
ON DELETE CASCADE
```

Deleting a document automatically deletes all associated chunks.

```text
delete Document
    ↓
delete all Chunks
```

This preserves the document aggregate boundary.

---

## Batch Chunk Insertion

All chunk rows are prepared and inserted using one batch operation:

```text
list[EmbeddedChunk]
    ↓
build chunk rows
    ↓
executemany(...)
```

The caller does not manage chunk-level database operations.

The storage implementation owns persistence batching.

---

## Vector Serialization

The current implementation converts each embedding to pgvector text representation:

```text
[0.1,0.2,0.3,...]
```

and inserts it using:

```sql
%s::vector
```

This avoids introducing another Python dependency during the current sprint.

A future implementation may use native pgvector Psycopg adaptation if that becomes beneficial.

---

## Connection Factory Injection

Production usage:

```text
PostgresVectorStore
    ↓
create_connection
    ↓
real PostgreSQL
```

Unit-test usage:

```text
PostgresVectorStore
    ↓
injected connection_factory
    ↓
mock connection
```

This allows storage orchestration to be unit-tested without requiring PostgreSQL.

The existing Sprint 2 database connection boundary is reused rather than introducing a second connection mechanism.

---

## Testing Strategy

### Unit Tests

Unit tests verify:

- empty chunks are rejected before connection creation
- mismatched document metadata is rejected before connection creation
- invalid embedding dimensions are rejected before connection creation
- duplicate chunk indexes are rejected before connection creation
- new documents are inserted
- all chunks are batch inserted
- the persisted document UUID is returned
- duplicate documents return the existing UUID
- duplicate documents do not reinsert chunks
- chunk insertion failures propagate

### Real PostgreSQL Persistence Test

The real database test verifies:

```text
Document + EmbeddedChunks
        ↓
PostgresVectorStore
        ↓
PostgreSQL
```

It confirms:

- a document row is persisted
- document metadata is preserved
- all chunk rows are persisted
- chunk order is preserved through `chunk_index`
- embeddings are stored as 384-dimensional pgvector values

### Real Idempotency Test

The real database idempotency test performs:

```text
store(document, chunks)
store(same document, chunks)
```

and verifies:

```text
same UUID returned
1 document row
1 set of chunk rows
```

This proves idempotency at both the application contract and database-state levels.

### Real Transaction Rollback Test

A real Psycopg connection is wrapped with a test cursor that:

```text
allows document INSERT
        ↓
fails during chunk INSERT
```

The exception leaves the real Psycopg transaction context.

The test then queries PostgreSQL and verifies:

```text
document row count = 0
```

This proves actual transaction rollback rather than merely mocking rollback behavior.

### Complete Ingestion Pipeline Test

The complete integration test verifies:

```text
sample.pdf
    ↓
PdfLoader
    ↓
Document
    ↓
RecursiveDocumentChunker
    ↓
list[Chunk]
    ↓
LocalChunkEmbedder
    ↓
all-MiniLM-L6-v2
    ↓
list[EmbeddedChunk]
    ↓
PostgresVectorStore
    ↓
PostgreSQL + pgvector
```

The test confirms:

- the PDF is loaded
- the document is chunked
- all chunks receive real embeddings
- the document is persisted
- every embedded chunk is persisted
- persisted chunk indexes match generated chunk indexes
- every stored vector contains 384 dimensions

---

## Final Architecture

```text
PDF File
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
PostgreSQL
    ↓
pgvector VECTOR(384)
```

---

## Key Learning Outcomes

This sprint established the following concepts:

- vector storage is a separate pipeline capability
- storage abstractions should hide database-specific behavior
- document identity should be based on content rather than filenames
- content hashing enables deterministic deduplication
- idempotent ingestion makes retries safe
- database constraints remain the final integrity authority
- document and chunk persistence should be atomic
- validation should happen before acquiring expensive resources
- generic domain models should remain independent of concrete vector dimensions
- concrete storage implementations may enforce model-specific dimensions
- normalized storage avoids repeating document metadata
- chunks belong to a document aggregate
- foreign-key cascades can enforce aggregate lifecycle
- connection-factory injection keeps database code unit-testable
- mocked tests cannot prove real database rollback
- transaction guarantees should be verified against the real database
- end-to-end tests prove that independently designed pipeline stages compose correctly

---

## Sprint Outcome

Sprint 06 successfully completed the RAG ingestion pipeline.

The system can now:

1. load a PDF
2. extract an immutable document
3. recursively split the document into immutable chunks
4. generate real local embeddings in batches
5. persist document metadata
6. persist chunk content and vectors in PostgreSQL with pgvector
7. prevent duplicate ingestion using SHA-256 content identity
8. atomically roll back incomplete ingestion
9. return the persisted document UUID

The next sprint will introduce query embedding and similarity-based retrieval from the stored vectors.