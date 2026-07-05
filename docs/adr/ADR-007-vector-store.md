# ADR-007: Use Normalized, Content-Addressed, Atomic Vector Storage

## Status

Accepted

## Context

The RAG engine produces:

```text
Document
+
list[EmbeddedChunk]
```

The system requires persistent storage for:

- document identity
- document metadata
- chunk content
- embedding vectors

The storage design must support future semantic retrieval while preserving data integrity.

Several decisions are related:

- whether document metadata should be repeated in every chunk row
- how duplicate documents should be detected
- what the storage operation should return
- whether duplicate ingestion should fail or be idempotent
- whether document and chunk writes should be atomic

These decisions form one coherent persistence model and are therefore recorded together.

---

## Decision

Use a normalized PostgreSQL schema with:

```text
documents
    1
    │
    N
  chunks
```

Identify documents using:

```text
SHA-256(Document.content)
```

Enforce uniqueness using:

```text
UNIQUE(content_hash)
```

Make storage idempotent:

```text
same content
    ↓
same persisted document UUID
```

Persist the document and all chunks in one transaction:

```text
Document persisted
        ⇔
all Chunks persisted
```

Use UUIDs as persisted document and chunk identities.

---

## Decision Drivers

The decision is based on the following requirements:

- avoid repeating document metadata for every chunk
- detect duplicate ingestion reliably
- allow changed document content to be stored as a new version
- make ingestion retries safe
- prevent partial document persistence
- preserve document-to-chunk ownership
- expose a stable persisted document identity
- remain compatible with PostgreSQL and pgvector

---

## Considered Storage Models

### Option A — Flat Vector Table

```text
embedded_chunks
├── id
├── filename
├── title
├── author
├── language
├── page_count
├── chunk_index
├── content
└── embedding
```

Advantages:

- simple queries
- fewer joins
- straightforward initial schema

Disadvantages:

- repeats document metadata for every chunk
- weakens the document aggregate boundary
- document-level operations become less explicit
- document identity becomes harder to model cleanly

This option was rejected.

---

### Option B — Normalized Document and Chunk Tables

```text
documents
├── id
├── metadata
└── content_hash

chunks
├── id
├── document_id
├── chunk_index
├── content
└── embedding
```

Advantages:

- document metadata is stored once
- explicit document-to-chunk relationship
- natural document-level identity
- natural cascade deletion
- clear aggregate boundary

Disadvantages:

- retrieval queries may require joins when document metadata is needed

This option was selected.

---

## Considered Document Identity Strategies

### Filename

Rejected because different documents can share the same filename.

```text
report.pdf
report.pdf
```

---

### Metadata Combination

A combination such as:

```text
filename + title + author + language
```

was rejected because document content can change while all metadata remains identical.

---

### Database UUID

A UUID uniquely identifies an already persisted row but cannot detect whether incoming content has been stored before.

It is therefore a persistence identity, not a deduplication identity.

---

### SHA-256 Content Hash

Selected.

```text
Document.content
    ↓
SHA-256
    ↓
content_hash
```

The same content produces the same identity regardless of:

- filename
- chunk size
- chunk overlap
- embedding batch size

Changed content produces a different hash and can be persisted as a new document.

---

## Why Hashing Occurs at the Storage Boundary

The PDF loader is responsible for:

```text
PDF
    ↓
Document
```

It should not know:

- whether persistence will occur
- which database will be used
- how duplicates are detected

Deduplication is a persistence concern.

The storage implementation therefore calculates the content hash.

---

## Why the Original Document Is Passed to Storage

The storage contract is:

```text
store(
    document,
    chunks,
)
```

rather than:

```text
store(chunks)
```

The original document content cannot be reliably reconstructed from chunks because:

- chunks may overlap
- text may be duplicated between chunks
- chunk configuration may change

The original immutable `Document` is therefore required for stable content identity.

---

## Idempotency

Duplicate ingestion does not raise an application error.

Instead:

```text
first store
    ↓
create document
    ↓
return UUID A

second store with same content
    ↓
return UUID A
    ↓
insert nothing
```

This makes retries safe.

The database remains the final authority through:

```text
UNIQUE(content_hash)
```

and:

```text
ON CONFLICT (content_hash) DO NOTHING
```

---

## Concurrency

A prior application-level lookup is insufficient.

Two concurrent transactions could both observe that a hash does not exist.

The selected design relies on the unique database constraint to resolve the race.

The flow is:

```text
INSERT document
ON CONFLICT DO NOTHING
RETURNING id
```

If insertion succeeds, chunks are persisted.

If the content hash already exists, the existing document UUID is queried and returned.

---

## Atomicity

Document and chunk persistence use one transaction.

```text
BEGIN

insert document
insert all chunks

COMMIT
```

If chunk persistence fails:

```text
ROLLBACK
```

Partial ingestion is not accepted.

The invariant is:

```text
Document persisted
        ⇔
all Chunks persisted
```

---

## UUID Persistence Identity

Documents and chunks use UUID primary keys.

Advantages:

- identities can safely flow through APIs and logs
- IDs are not sequentially exposed
- IDs can be generated before insertion
- IDs are suitable for future distributed workflows

The storage operation returns the persisted document UUID.

---

## Aggregate Lifecycle

Chunks belong to one document and do not have an independent lifecycle.

The foreign key therefore uses:

```text
ON DELETE CASCADE
```

Deleting a document removes all associated chunks.

---

## Consequences

### Positive

- document metadata is not repeated for every chunk
- duplicate ingestion is deterministic
- retries are safe
- changed content can be stored separately
- partial ingestion is prevented
- document ownership of chunks is explicit
- the database protects against concurrent duplicate insertion
- callers receive a stable persisted UUID

### Negative

- document metadata retrieval may require a join
- content hashing adds a small amount of CPU work
- changing the content normalization strategy would affect document identity
- duplicate content with different metadata resolves to the first persisted document

### Neutral

The original full document content is not persisted.

The system stores:

- document metadata
- content hash
- chunk content
- chunk embeddings

This is sufficient for the current retrieval architecture.

---

## Future Considerations

Future versions may need explicit document versioning.

If ingestion later requires treating identical extracted content with different source identities as separate records, the content-addressed uniqueness rule will need to evolve.

Future vector storage implementations may also use native pgvector Psycopg adaptation instead of text vector serialization.

These changes do not affect the current decision.

---

## Final Decision

Use normalized `documents` and `chunks` tables, SHA-256 content-addressed deduplication, UUID persistence identities, idempotent duplicate handling, and one atomic transaction for document and chunk persistence.