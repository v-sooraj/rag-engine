# Sprint 07 — Retrieval

## Status

Completed

## Objective

Implement the retrieval stage of the RAG pipeline.

The retrieval stage transforms a user query into an embedding and uses PostgreSQL with pgvector to retrieve the most semantically relevant stored chunks.

This sprint extends the system from an ingestion-only pipeline:

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

to a system containing both ingestion and retrieval paths:

```text
Ingestion

PDF
 ↓
Document
 ↓
Chunks
 ↓
Chunk Embeddings
 ↓
PostgreSQL + pgvector
```

```text
Retrieval

User Query
 ↓
QueryEmbedder
 ↓
Query Embedding
 ↓
Retriever
 ↓
Top-K Retrieved Chunks
```

---

## Scope

The sprint includes:

- query embedding abstraction
- local query embedding implementation
- query validation
- immutable retrieval result domain model
- retrieval abstraction
- PostgreSQL retrieval implementation
- cosine-distance search using pgvector
- configurable top-k retrieval
- raw retrieval distance exposure
- fail-fast retrieval validation
- connection-factory injection
- query embedding unit tests
- real local query embedding test
- retrieval domain model tests
- retriever unit tests
- deterministic real PostgreSQL vector-ranking test
- complete semantic retrieval pipeline test
- shared embedding model instance during pipeline composition

The sprint does not include:

- prompt augmentation
- context construction
- LLM generation
- answer generation
- retrieval thresholds
- metadata filtering
- hybrid search
- keyword search
- reranking
- HNSW indexes
- IVFFlat indexes
- retrieval evaluation frameworks
- RAG orchestration
- API endpoints

These concerns belong to later pipeline stages.

---

## Pipeline Position

Before this sprint, the system could only ingest knowledge:

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

After this sprint, the system can retrieve relevant knowledge:

```text
User Query
 ↓
QueryEmbedder
 ↓
list[float]
 ↓
Retriever
 ↓
list[RetrievedChunk]
```

The complete system now has two complementary flows.

### Ingestion Flow

```text
Source Knowledge
    ↓
Document
    ↓
Chunks
    ↓
Chunk Embeddings
    ↓
Vector Storage
```

### Retrieval Flow

```text
User Query
    ↓
Query Embedding
    ↓
Vector Similarity Search
    ↓
Relevant Chunks
```

The output of retrieval becomes the input to the future prompt augmentation stage.

---

## Package Structure

```text
rag_engine/
├── query_embedding/
│   ├── __init__.py
│   ├── query_embedder.py
│   └── local_query_embedder.py
│
└── retrieval/
    ├── __init__.py
    ├── retrieved_chunk.py
    ├── retriever.py
    └── postgres_retriever.py
```

Test structure:

```text
tests/
├── query_embedding/
│   ├── __init__.py
│   ├── test_local_query_embedder.py
│   └── test_local_query_embedding_integration.py
│
└── retrieval/
    ├── __init__.py
    ├── test_retrieved_chunk.py
    ├── test_postgres_retriever.py
    ├── test_postgres_retriever_integration.py
    └── test_retrieval_pipeline.py
```

---

## Query Embedding Boundary

The retrieval pipeline begins with a user query:

```text
"How can I find similar information using embeddings?"
```

The query must be transformed into the same vector space used by the stored chunk embeddings.

The query embedding capability is represented by:

```python
class QueryEmbedder(ABC):

    @abstractmethod
    def embed(
        self,
        query: str,
    ) -> list[float]:
        pass
```

The contract accepts:

```text
str
```

and returns:

```text
list[float]
```

The abstraction does not expose:

- sentence-transformers
- model loading
- model inference
- embedding dimensions
- batching
- PostgreSQL
- retrieval logic

These concerns belong to concrete implementations or later pipeline stages.

---

## Why Query Embedding Has a Separate Abstraction

The existing ingestion abstraction is:

```text
ChunkEmbedder

list[Chunk]
    ↓
list[EmbeddedChunk]
```

Retrieval requires:

```text
QueryEmbedder

str
    ↓
list[float]
```

Reusing `ChunkEmbedder` would require creating artificial ingestion objects:

```text
query string
    ↓
fake Chunk
    ↓
fake ChunkMetadata
    ↓
fake DocumentMetadata
    ↓
ChunkEmbedder
```

This would force a retrieval concern through an ingestion-oriented interface.

The selected design keeps the boundaries explicit:

```text
Ingestion

ChunkEmbedder
    ↓
list[Chunk] → list[EmbeddedChunk]
```

```text
Retrieval

QueryEmbedder
    ↓
str → list[float]
```

The two abstractions represent different domain capabilities even though they currently use the same underlying embedding model.

---

## Local Query Embedding

The concrete implementation is:

```text
QueryEmbedder
      ▲
      │
LocalQueryEmbedder
      ↓
SentenceTransformer
      ↓
all-MiniLM-L6-v2
```

The local implementation transforms:

```text
User Query
    ↓
all-MiniLM-L6-v2
    ↓
384-dimensional embedding
```

The result is converted to:

```text
list[float]
```

before leaving the embedding boundary.

---

## Query Validation

Empty and blank queries are rejected before model inference.

Invalid examples:

```text
""
```

and:

```text
"   "
```

The validation flow is:

```text
query
 ↓
strip whitespace
 ↓
empty?
 ├── yes → raise ValueError
 └── no  → call embedding model
```

This prevents unnecessary model execution for invalid input.

---

## Shared Vector Space Requirement

Vector similarity is meaningful only when stored chunk embeddings and query embeddings belong to the same vector space.

Invalid architecture:

```text
Chunks
    ↓
Model A
    ↓
Vector Space A

Query
    ↓
Model B
    ↓
Vector Space B

Comparison
    ↓
meaningless
```

The current system therefore uses:

```text
all-MiniLM-L6-v2
```

for both:

```text
Chunk Embeddings
        and
Query Embeddings
```

Both sides produce:

```text
384-dimensional vectors
```

The compatibility requirement is:

```text
Stored Chunk Embedding Space
            =
Query Embedding Space
```

---

## Separate Capabilities, Shared Model Instance

`ChunkEmbedder` and `QueryEmbedder` remain separate domain capabilities.

However, loading the same sentence-transformer model twice during pipeline composition would be wasteful:

```text
LocalChunkEmbedder
    ↓
load all-MiniLM-L6-v2

LocalQueryEmbedder
    ↓
load all-MiniLM-L6-v2 again
```

The selected composition creates one model instance:

```python
model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)
```

and injects it into both capabilities:

```text
ChunkEmbedder       QueryEmbedder
      ↑                    ↑
      └──── shared model ──┘
```

This preserves:

- separate domain boundaries
- clear pipeline responsibilities
- independent testing

while avoiding:

- duplicate model loading
- unnecessary memory usage
- unnecessary initialization time

The principle is:

```text
Separate capabilities
        +
Shared infrastructure instance
```

---

## Retrieved Chunk Domain Model

Retrieval results are represented by a dedicated immutable domain model:

```python
class RetrievedChunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunk_id: UUID
    document_id: UUID
    content: str
    chunk_index: int
    distance: float
```

A retrieved chunk is different from an ingestion `Chunk`.

An ingestion chunk represents:

```text
text prepared for embedding
```

A retrieved chunk represents:

```text
persisted knowledge
    +
retrieval relevance information
```

Using a separate domain model keeps ingestion and retrieval concepts distinct.

---

## Retrieved Chunk Fields

### `chunk_id`

The persisted identity of the retrieved chunk.

Useful for:

- tracing
- logging
- debugging
- future citations
- future feedback collection

---

### `document_id`

The persisted identity of the source document.

Useful for:

- tracing results back to documents
- future document metadata lookup
- future filtering
- future citations

---

### `content`

The actual retrieved text.

This is the primary output required by the future prompt augmentation stage.

```text
RetrievedChunk.content
    ↓
Prompt Context
```

---

### `chunk_index`

The original position of the chunk within its source document.

Useful for:

- preserving document order
- debugging
- future neighboring-chunk retrieval
- future context expansion

---

### `distance`

The raw cosine distance returned by pgvector.

Useful for:

- observability
- debugging
- future retrieval thresholds
- evaluation
- reranking

The distance is not required to perform top-k retrieval.

The database already performs ranking.

It is retained because the retrieval signal may become useful to later system capabilities.

---

## Why Embeddings Are Not Returned

`RetrievedChunk` does not contain the stored embedding.

After similarity search:

```text
query embedding
        +
stored embeddings
        ↓
similarity search complete
```

The next pipeline stage needs:

```text
retrieved text
```

not:

```text
384-dimensional vectors
```

Returning embeddings would:

- increase memory usage
- increase data transfer
- expose storage details unnecessarily
- provide no current value to prompt augmentation

Therefore embeddings remain internal to vector search.

---

## Why Document Metadata Is Not Returned Yet

The retrieval result does not currently include:

- filename
- title
- author
- language

Adding these fields would require every retrieval query to join:

```text
chunks
    +
documents
```

The current next-stage requirement is only:

```text
retrieved chunk content
```

Document metadata will be added only when a concrete requirement exists, such as:

- source citations
- document filtering
- answer attribution

This avoids speculative expansion of the retrieval contract.

---

## Retrieval Abstraction

The retrieval capability is represented by:

```python
class Retriever(ABC):

    @abstractmethod
    def retrieve(
        self,
        query_embedding: list[float],
        top_k: int,
    ) -> list[RetrievedChunk]:
        pass
```

The contract accepts:

```text
query embedding
+
top_k
```

and returns:

```text
list[RetrievedChunk]
```

The abstraction does not expose:

- SQL
- PostgreSQL
- pgvector operators
- vector serialization
- connection handling

These concerns belong to the concrete retrieval implementation.

---

## Why Retriever Accepts an Embedding Instead of a Query String

Two designs were considered.

### Combined Design

```text
query string
    ↓
Retriever
    ├── QueryEmbedder
    └── Vector Search
```

### Separated Design

```text
query string
    ↓
QueryEmbedder
    ↓
query embedding
    ↓
Retriever
    ↓
retrieved chunks
```

The separated design was selected.

This keeps the retrieval pipeline explicit:

```text
Query
 ↓
QueryEmbedder
 ↓
Embedding
 ↓
Retriever
 ↓
RetrievedChunk
```

It also keeps both capabilities independently:

- testable
- replaceable
- observable

A later orchestration layer can compose them.

---

## PostgreSQL Retriever

The concrete retrieval implementation is:

```text
Retriever
    ▲
    │
PostgresRetriever
    ↓
PostgreSQL + pgvector
```

The implementation:

1. validates the query embedding
2. validates `top_k`
3. converts the embedding to pgvector representation
4. opens a database connection
5. performs cosine-distance search
6. returns ranked immutable `RetrievedChunk` objects

---

## Cosine Distance Search

The current retrieval query uses pgvector's cosine-distance operator:

```sql
embedding <=> query_vector
```

The retrieval query conceptually performs:

```sql
SELECT
    id,
    document_id,
    content,
    chunk_index,
    embedding <=> query_vector AS distance
FROM chunks
ORDER BY embedding <=> query_vector
LIMIT top_k;
```

The flow is:

```text
Query Embedding
    ↓
compare against stored embeddings
    ↓
calculate cosine distance
    ↓
sort ascending
    ↓
LIMIT top_k
```

For cosine distance:

```text
smaller distance
    =
closer vector
    =
better match
```

Example:

```text
Chunk A → 0.08
Chunk B → 0.21
Chunk C → 0.64
```

Ranking:

```text
1. Chunk A
2. Chunk B
3. Chunk C
```

---

## Distance Versus Similarity Score

The database already performs top-k ranking.

No similarity-score conversion is required for retrieval.

The system could transform:

```text
similarity = 1 - cosine distance
```

but no current requirement needs that transformation.

The selected design exposes the raw database signal:

```text
pgvector cosine distance
        ↓
RetrievedChunk.distance
```

This avoids a hidden transformation.

The boundary remains transparent:

```text
database calculates distance
        ↓
retriever returns distance
```

---

## Why Distance Is Retained

Top-k retrieval would still work without returning the distance.

The database already provides:

```text
ORDER BY distance
LIMIT top_k
```

However, retaining the distance supports future capabilities.

### Observability

```text
What distances are commonly returned?
```

### Debugging

```text
Why was this chunk retrieved?
```

### Thresholding

```text
Ignore results beyond an acceptable distance.
```

### Evaluation

```text
How does retrieval quality change across queries?
```

### Reranking

```text
Preserve the first-stage retrieval signal.
```

Therefore the distance is retained as part of the retrieval result.

---

## Top-K Retrieval

The caller controls the maximum number of results:

```text
top_k = 3
```

The database performs:

```text
ORDER BY nearest vector
LIMIT 3
```

The retriever therefore returns at most:

```text
3 RetrievedChunk objects
```

The retrieval abstraction does not currently define a default value.

The caller must explicitly choose `top_k`.

This keeps retrieval behavior visible at the call site.

---

## Fail-Fast Validation

All validation that can be performed in memory occurs before opening a database connection.

The validation flow is:

```text
retrieve(query_embedding, top_k)
    ↓
query embedding dimension must equal 384
    ↓
top_k must be greater than 0
    ↓
only then open database connection
```

Invalid input therefore does not:

- acquire a database connection
- execute SQL
- perform vector search

---

## Query Embedding Dimension Validation

The current storage schema requires:

```text
VECTOR(384)
```

The retriever therefore requires:

```text
len(query_embedding) == 384
```

Invalid example:

```text
query embedding dimension = 3
stored embedding dimension = 384
```

The request is rejected before database access.

The validation layers are:

```text
QueryEmbedder
    ↓
produces embedding

PostgresRetriever
    ↓
requires 384 dimensions

PostgreSQL
    ↓
stored vectors are VECTOR(384)
```

---

## Top-K Validation

The retriever rejects:

```text
top_k = 0
```

and:

```text
top_k < 0
```

Valid input requires:

```text
top_k > 0
```

This prevents meaningless database queries.

---

## Vector Serialization

The current retriever converts the query embedding into pgvector text representation:

```text
[0.1,0.2,0.3,...]
```

and uses:

```sql
%s::vector
```

This matches the vector serialization approach already used by `PostgresVectorStore`.

A future implementation may use native pgvector Psycopg adaptation if required.

No additional dependency was introduced during this sprint.

---

## Connection Factory Injection

Production usage:

```text
PostgresRetriever
    ↓
create_connection
    ↓
real PostgreSQL
```

Unit-test usage:

```text
PostgresRetriever
    ↓
injected connection_factory
    ↓
mock connection
```

This keeps database orchestration testable without requiring PostgreSQL for every test.

The retriever reuses the existing database connection boundary.

---

## Testing Strategy

### Query Embedding Unit Tests

Unit tests verify:

- valid queries are passed to the model
- model output is returned as `list[float]`
- empty queries are rejected before model execution
- blank queries are rejected before model execution

---

### Real Query Embedding Test

The real local embedding test verifies:

```text
real query
    ↓
all-MiniLM-L6-v2
    ↓
384-dimensional embedding
```

It confirms:

- the real model loads
- query embedding succeeds
- the result contains 384 values
- values are returned as floats

---

### Retrieved Chunk Domain Tests

Domain model tests verify:

- valid retrieval results can be created
- empty content is rejected
- negative chunk indexes are rejected
- negative distances are rejected
- retrieval results are immutable

---

### Retriever Unit Tests

Unit tests verify:

- invalid query embedding dimensions are rejected before connection creation
- zero `top_k` is rejected before connection creation
- negative `top_k` is rejected before connection creation
- database rows are mapped to `RetrievedChunk`
- ranked results preserve database order
- distance is preserved
- empty database results return an empty list

---

## Deterministic PostgreSQL Ranking Test

A real PostgreSQL integration test inserts controlled vectors.

The query vector is:

```text
[1.0, 0.0, 0.0, ...]
```

Stored vectors represent:

```text
exact direction
close direction
far direction
```

The test then retrieves:

```text
top_k = 2
```

and verifies:

```text
1. Exact vector match
2. Close vector match
```

This test proves:

- real pgvector cosine-distance calculation
- real database ordering
- real top-k limiting
- real distance return values

The test uses controlled vectors rather than a language model so vector ranking can be verified deterministically.

---

## Complete Semantic Retrieval Pipeline Test

The final Sprint 7 integration test uses real semantic text.

Stored chunks contain unrelated topics:

```text
Chunk 0 → vector databases and similarity search
Chunk 1 → biryani
Chunk 2 → cricket
```

The chunks are embedded using:

```text
LocalChunkEmbedder
    ↓
all-MiniLM-L6-v2
```

and persisted using:

```text
PostgresVectorStore
    ↓
PostgreSQL + pgvector
```

A real query is then embedded:

```text
"How can I find similar information using embeddings?"
```

using:

```text
LocalQueryEmbedder
    ↓
all-MiniLM-L6-v2
```

The query embedding is passed to:

```text
PostgresRetriever
```

The test verifies that the vector-database chunk is ranked as the relevant result.

This proves the complete retrieval path:

```text
Real Text
    ↓
Real Chunk Embeddings
    ↓
Real Vector Storage
    ↓
Real Query
    ↓
Real Query Embedding
    ↓
Real pgvector Search
    ↓
Semantically Relevant Result
```

---

## Current Complete Architecture

The system now contains a complete ingestion pipeline:

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
list[EmbeddedChunk]
    ↓
VectorStore
    ↓
PostgresVectorStore
    ↓
PostgreSQL + pgvector
```

and a complete retrieval pipeline:

```text
User Query
    ↓
QueryEmbedder
    ↓
LocalQueryEmbedder
    ↓
list[float]
    ↓
Retriever
    ↓
PostgresRetriever
    ↓
pgvector cosine-distance search
    ↓
list[RetrievedChunk]
```

Together:

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
 │ cosine-distance search
 │
Query Embedding
 ↑
User Query

                    RETRIEVAL
```

---

## Key Learning Outcomes

This sprint established the following concepts:

- ingestion and retrieval are separate halves of a RAG system
- query embedding deserves a separate domain boundary
- retrieval should not create fake ingestion objects
- query and document embeddings must exist in the same vector space
- separate domain capabilities can share one infrastructure instance
- query embedding and chunk embedding can use one shared model instance
- retrieval results are different domain concepts from ingestion chunks
- retrieved vectors do not need to leave the similarity-search boundary
- document metadata should not be added to retrieval results without a requirement
- pgvector can rank vectors using cosine distance
- top-k retrieval does not require converting distance into similarity
- raw distance is useful for future observability and evaluation
- smaller cosine distance means a closer vector match
- retrieval input should be validated before database access
- deterministic vector tests and semantic pipeline tests prove different guarantees
- controlled vectors prove database ranking
- real text embeddings prove semantic retrieval
- orchestration should be added later rather than hidden inside low-level capabilities

---

## Sprint Outcome

Sprint 07 successfully completed the retrieval pipeline.

The system can now:

1. accept a user query
2. reject invalid empty queries
3. generate a real 384-dimensional query embedding
4. search stored chunk embeddings using pgvector cosine distance
5. retrieve configurable top-k results
6. preserve persisted chunk and document identities
7. return chunk content and original chunk position
8. expose raw cosine distance for observability
9. rank controlled vectors correctly in real PostgreSQL
10. retrieve semantically relevant text using real local embeddings

The RAG engine can now both:

```text
store knowledge
```

and:

```text
retrieve relevant knowledge
```

The next sprint will use retrieved chunks to construct augmented context for an LLM prompt.