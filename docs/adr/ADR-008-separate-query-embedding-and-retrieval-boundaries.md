# ADR-008: Separate Query Embedding and Retrieval Boundaries

## Status

Accepted

## Context

The RAG engine already contains an ingestion embedding capability:

```text
ChunkEmbedder

list[Chunk]
    ↓
list[EmbeddedChunk]
```

The retrieval pipeline requires a different transformation:

```text
User Query
    ↓
Query Embedding
```

The system also needs to decide:

- whether query embedding should reuse `ChunkEmbedder`
- whether the retriever should accept a query string or an embedding
- what a retrieval result should contain
- whether retrieval should expose cosine distance
- whether chunk and query embedders should load separate model instances

These decisions define the retrieval boundary and are therefore recorded together.

---

## Decision

Introduce a dedicated query embedding abstraction:

```text
QueryEmbedder

str
    ↓
list[float]
```

Keep retrieval as a separate capability:

```text
Retriever

query embedding + top_k
    ↓
list[RetrievedChunk]
```

Represent results using a dedicated immutable domain model:

```text
RetrievedChunk
├── chunk_id
├── document_id
├── content
├── chunk_index
└── distance
```

Expose the raw cosine distance returned by pgvector.

Keep `ChunkEmbedder` and `QueryEmbedder` as separate domain capabilities while allowing them to share one underlying sentence-transformer model instance during composition.

---

## Decision Drivers

The decision is based on the following requirements:

- keep ingestion and retrieval responsibilities explicit
- avoid creating artificial chunk objects for user queries
- make the RAG pipeline visible from package and class structure
- keep query embedding independently testable
- keep retrieval independently testable
- preserve retrieval signals for observability
- avoid unnecessary transformation of database results
- avoid loading the same embedding model multiple times
- keep orchestration outside low-level capabilities

---

## Considered Query Embedding Designs

### Option A — Reuse ChunkEmbedder

The query could be wrapped in a temporary `Chunk`:

```text
query string
    ↓
temporary Chunk
    ↓
ChunkEmbedder
    ↓
EmbeddedChunk
    ↓
extract embedding
```

This would avoid introducing another abstraction.

However, a query is not a document chunk.

The approach would require artificial:

- `Chunk`
- `ChunkMetadata`
- `DocumentMetadata`

objects only to satisfy an ingestion-oriented interface.

This option was rejected.

---

### Option B — Introduce QueryEmbedder

```text
query string
    ↓
QueryEmbedder
    ↓
query embedding
```

The abstraction is:

```python
class QueryEmbedder(ABC):

    @abstractmethod
    def embed(
        self,
        query: str,
    ) -> list[float]:
        pass
```

Advantages:

- clear retrieval boundary
- no fake ingestion objects
- visible RAG pipeline structure
- independent testing
- independent replacement of query embedding implementation
- easier debugging

This option was selected.

---

## Separate Domain Capabilities

The ingestion and retrieval embedding capabilities are:

```text
ChunkEmbedder
    ↓
list[Chunk] → list[EmbeddedChunk]
```

and:

```text
QueryEmbedder
    ↓
str → list[float]
```

They remain separate because they represent different domain operations.

The fact that they currently use the same model does not make them the same capability.

---

## Shared Vector Space

Stored chunks and queries must be embedded into the same vector space.

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
```

Comparing vectors from unrelated embedding spaces is not meaningful.

The current system therefore uses:

```text
all-MiniLM-L6-v2
```

for both:

- chunk embedding
- query embedding

Both produce:

```text
384-dimensional vectors
```

---

## Considered Retriever Boundaries

### Option A — Retriever Accepts Query String

```text
query string
    ↓
Retriever
    ├── QueryEmbedder
    └── Vector Search
```

Advantages:

- simpler caller interface
- fewer visible steps

Disadvantages:

- combines embedding and retrieval
- hides pipeline stages
- makes independent testing less direct
- couples retriever composition to an embedder

This option was rejected for the current architecture.

---

### Option B — Retriever Accepts Query Embedding

```text
query string
    ↓
QueryEmbedder
    ↓
query embedding
    ↓
Retriever
```

The abstraction is:

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

Advantages:

- explicit pipeline
- independent capabilities
- independent testing
- easier debugging
- future orchestration remains separate

This option was selected.

---

## Why Orchestration Is Not Inside Retriever

The current architecture intentionally exposes:

```text
QueryEmbedder
    ↓
Retriever
```

rather than hiding both behind one class.

A future orchestration layer can compose:

```text
query
    ↓
query embedding
    ↓
retrieval
    ↓
prompt augmentation
    ↓
LLM generation
```

Low-level capabilities should not prematurely own this orchestration.

---

## Retrieval Result Model

A dedicated immutable model is used:

```python
class RetrievedChunk(BaseModel):
    model_config = ConfigDict(frozen=True)

    chunk_id: UUID
    document_id: UUID
    content: str
    chunk_index: int
    distance: float
```

A retrieved chunk is not the same domain concept as an ingestion chunk.

An ingestion chunk represents:

```text
text prepared for embedding
```

A retrieved chunk represents:

```text
persisted text selected by similarity search
```

with additional retrieval information.

---

## Why Persisted Identities Are Returned

`chunk_id` identifies the exact retrieved database row.

`document_id` identifies the source document.

These identities support future:

- observability
- tracing
- citations
- filtering
- evaluation
- user feedback

---

## Why Chunk Index Is Returned

`chunk_index` preserves the chunk's position within the source document.

This supports future:

- neighboring-chunk retrieval
- context expansion
- document-order reconstruction
- debugging

---

## Why Embeddings Are Not Returned

The stored vector is required to perform similarity search.

After retrieval completes, the next pipeline stage needs text context.

Returning the embedding would expose:

```text
384 float values per result
```

without a current use case.

Embeddings therefore remain internal to the vector search boundary.

---

## Why Document Metadata Is Not Returned

The current retrieval stage does not require:

- filename
- title
- author
- language

Including these values would require document joins for every retrieval query.

They will be added only when a concrete requirement exists, such as:

- source attribution
- citations
- metadata filtering

This keeps the retrieval contract minimal.

---

## Distance Versus Similarity

pgvector's cosine operator returns cosine distance.

The database can directly perform:

```text
calculate distance
    ↓
sort ascending
    ↓
limit top_k
```

Top-k retrieval does not require converting distance into a similarity score.

Two application representations were considered.

### Option A — Convert to Similarity

```text
similarity = 1 - cosine distance
```

Advantages:

- larger values may feel more intuitive

Disadvantages:

- adds a transformation with no current requirement
- hides the direct database value

---

### Option B — Expose Raw Distance

```text
pgvector distance
    ↓
RetrievedChunk.distance
```

Advantages:

- transparent database boundary
- no hidden transformation
- useful for debugging
- useful for future observability
- useful for future thresholds
- useful for future evaluation

This option was selected.

---

## Why Distance Is Returned At All

The database does not need to return distance for basic top-k retrieval.

It can already perform:

```text
ORDER BY distance
LIMIT top_k
```

However, retaining the distance provides a useful retrieval signal.

Potential future uses include:

- retrieval quality dashboards
- relevance thresholding
- debugging irrelevant results
- comparing retrieval strategies
- evaluation
- reranking

The field is therefore retained even though it is not required for ranking itself.

---

## Shared Model Instance

Separate query and chunk embedding capabilities could independently load:

```text
all-MiniLM-L6-v2
```

This would result in:

```text
LocalChunkEmbedder
    ↓
Model Instance A

LocalQueryEmbedder
    ↓
Model Instance B
```

Loading the same model twice adds unnecessary:

- initialization time
- memory usage

The selected composition is:

```text
SentenceTransformer Instance
        ↓
        ├── LocalChunkEmbedder
        └── LocalQueryEmbedder
```

The principle is:

```text
Separate domain capabilities
        +
Shared infrastructure instance
```

Model injection already exists, so no new abstraction is required.

---

## Query Validation

Empty and blank queries are rejected before model execution.

This prevents unnecessary inference for invalid input.

The query embedding boundary owns this validation because it receives the raw user query.

---

## Retrieval Validation

The concrete PostgreSQL retriever validates:

```text
query embedding dimension = 384
```

and:

```text
top_k > 0
```

before opening a database connection.

This preserves the existing project principle:

```text
validate in memory first
    ↓
acquire expensive resources only for valid input
```

---

## Consequences

### Positive

- ingestion and retrieval remain clearly separated
- package structure communicates the RAG pipeline
- no artificial chunk objects are created for queries
- query embedding is independently testable
- retrieval is independently testable
- future orchestration can compose explicit stages
- raw retrieval distance remains available
- embedding model loading can be shared efficiently
- retrieval results contain only currently useful fields

### Negative

- callers must explicitly compose query embedding and retrieval
- compatible embedding models must be configured correctly
- model compatibility is currently an architectural convention rather than a centralized configuration guarantee
- raw cosine distance may be less intuitive than a similarity score for some consumers

### Neutral

The current retrieval result does not include document metadata.

This can be added later when citations or metadata filtering create a concrete requirement.

---

## Future Considerations

A future composition root or dependency-injection layer may centralize:

- embedding model name
- embedding model instance
- embedding dimension

A future RAG orchestrator may expose a simpler operation:

```text
query
    ↓
retrieve relevant context
```

while internally composing:

```text
QueryEmbedder
    ↓
Retriever
```

Future retrieval improvements may include:

- distance thresholds
- metadata filters
- neighboring-chunk expansion
- hybrid retrieval
- reranking
- HNSW indexing
- retrieval evaluation

These changes do not alter the current decision.

---

## Final Decision

Use separate `QueryEmbedder` and `Retriever` abstractions, keep query embedding and vector retrieval as visible pipeline stages, return dedicated immutable `RetrievedChunk` results with raw cosine distance, and share the underlying embedding model instance when composing chunk and query embedding capabilities.