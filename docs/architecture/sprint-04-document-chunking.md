# Sprint 04 – Document Chunking

## Objective

Design and implement a document chunking layer that transforms validated documents into retrieval-ready chunks while preserving source provenance and contextual continuity.

The objective of this sprint was not simply to split text into smaller strings.

The primary goal was to establish a clean architectural boundary between document loading and future embedding generation while designing chunking as an extensible domain capability.

The implementation emphasizes:

- Strongly typed domain models
- Immutable pipeline objects
- Strategy abstraction
- Recursive boundary-aware splitting
- Chunk-size guarantees
- Context preservation through overlap
- Source metadata preservation

---

# Scope

The following areas were completed during this sprint:

- Chunk domain modelling
- Chunk metadata modelling
- Document and chunk immutability
- Document chunking abstraction
- Recursive chunking strategy
- Character-based chunk sizing
- Recursive separator fallback
- Separator preservation
- Small-piece merging
- Configurable chunk overlap
- Chunk configuration validation
- Unit testing
- End-to-end PDF loading and chunking integration testing

The following areas were intentionally excluded:

- Token-aware chunking
- Semantic chunking
- Embedding generation
- Vector persistence
- Retrieval quality evaluation
- Page-aware chunk metadata
- Section-aware chunk metadata

These capabilities will be introduced only when later pipeline stages create a concrete requirement for them.

---

# Responsibilities of the Chunking Layer

The chunking layer is responsible for:

- Accepting a validated `Document`
- Splitting document content into bounded pieces
- Preserving natural text boundaries where possible
- Merging small adjacent pieces
- Applying configurable overlap
- Preserving source document metadata
- Assigning sequential chunk indexes
- Returning validated `Chunk` domain models

The chunking layer is **not** responsible for:

- Loading source documents
- Generating embeddings
- Counting model-specific tokens
- Persisting vectors
- Detecting duplicate documents
- Retrieval
- Prompt augmentation

These responsibilities belong to other stages of the RAG pipeline.

---

# Domain Model

Sprint 4 introduced a dedicated chunk domain model.

```
Chunk
├── content
└── metadata
    ├── chunk_index
    └── document_metadata
```

The complete relationship between document and chunk models is:

```
Document
├── content
└── DocumentMetadata
    ├── filename
    ├── page_count
    ├── title
    ├── author
    └── language

                ↓

              Chunker

                ↓

list[Chunk]

Chunk
├── content
└── ChunkMetadata
    ├── chunk_index
    └── document_metadata ──► DocumentMetadata
```

Each chunk preserves provenance by referencing the metadata of its source document.

---

# Engineering Decisions

## 1. Introduce a Strongly Typed Chunk Model

### Decision

Represent chunks using dedicated `Chunk` and `ChunkMetadata` domain models instead of returning `list[str]`.

### Why?

A string contains only text.

Future pipeline stages also require information about:

- Chunk ordering
- Source document provenance
- Retrieval context

A strongly typed model ensures that chunk content and metadata travel together through the pipeline.

---

## 2. Preserve Complete Document Metadata

### Decision

Each `ChunkMetadata` references the original `DocumentMetadata`.

### Why?

Reducing provenance to only a filename would discard useful information such as:

- Title
- Author
- Language
- Page count

Preserving the complete document metadata keeps chunks self-describing when they later move through embedding, vector storage, and retrieval.

---

## 3. Make Pipeline Domain Models Immutable

### Decision

The following domain models are immutable after construction:

```
Document
DocumentMetadata
Chunk
ChunkMetadata
```

### Why?

These models represent the validated output of completed pipeline stages.

The lifecycle is:

```
Construct
    ↓
Validate
    ↓
Freeze
    ↓
Consume
```

Downstream components should consume the output of previous stages rather than mutate it.

Immutability prevents:

- Accidental modification of loaded document content
- Inconsistent source metadata between chunks
- Modification of chunk content after embedding
- Shared-reference mutation bugs

---

## 4. Share Immutable Document Metadata

### Decision

Chunks reference the same immutable `DocumentMetadata` instance rather than creating a metadata copy for every chunk.

### Why?

All chunks produced from one document share the same source facts.

Because `DocumentMetadata` is immutable, sharing the reference is safe.

```
Chunk 0 ──┐
Chunk 1 ──┼──► immutable DocumentMetadata
Chunk 2 ──┘
```

This avoids unnecessary copying while guaranteeing consistent provenance.

---

## 5. Introduce a Document Chunking Abstraction

### Decision

Define a `DocumentChunker` abstraction.

Its contract is:

```
Document
    ↓
chunk()
    ↓
list[Chunk]
```

### Why?

Different chunking strategies may be introduced in the future.

Examples include:

- Recursive chunking
- Token-aware chunking
- Semantic chunking
- Structure-aware chunking

Callers should depend on the chunking capability rather than a specific implementation.

---

## 6. Pass the Complete Document to the Chunker

### Decision

The chunking contract accepts a `Document` rather than only a text string.

### Why?

Chunk construction requires both:

- Document content
- Document metadata

Accepting only a string would force callers to reattach provenance after chunking.

That responsibility belongs inside the chunking layer.

---

## 7. Configure the Strategy at Construction Time

### Decision

Provide `chunk_size` and `chunk_overlap` when constructing `RecursiveDocumentChunker`.

Example:

```
RecursiveDocumentChunker(
    chunk_size=500,
    chunk_overlap=50,
)
```

### Why?

These values define how the strategy behaves.

The configured strategy can then be reused across multiple documents.

```
Configured Chunker
        │
        ├── chunk(document_a)
        ├── chunk(document_b)
        └── chunk(document_c)
```

---

## 8. Validate Configuration Immediately

### Decision

Reject invalid chunking configuration during construction.

The following invariants are enforced:

```
chunk_size > 0

chunk_overlap >= 0

chunk_overlap < chunk_size
```

### Why?

Invalid strategy configuration should fail immediately rather than causing incorrect behavior during document processing.

---

## 9. Use Character-Based Measurement Initially

### Decision

Measure chunk size and overlap using characters.

### Why?

Character-based measurement allows the project to focus on understanding the chunking algorithm without introducing:

- Model-specific tokenizers
- Tokenizer dependencies
- Embedding-model coupling

Token-aware chunking will be introduced only when the embedding stage creates a concrete requirement for it.

---

## 10. Preserve Natural Boundaries Recursively

### Decision

Use the following separator hierarchy:

```
"\n\n"   paragraph boundary
"\n"     line boundary
" "      word boundary
""       character fallback
```

### Why?

The algorithm attempts to preserve the strongest available textual boundary.

Only oversized pieces move to weaker separators.

```
Paragraph
    ↓ oversized

Line
    ↓ oversized

Word
    ↓ oversized

Character fallback
```

This avoids unnecessarily breaking text at weaker boundaries.

---

## 11. Preserve Separators During Splitting

### Decision

Retain separators as part of the preceding piece.

Example:

```
Paragraph A\n\nParagraph B
```

becomes:

```
[
    "Paragraph A\n\n",
    "Paragraph B"
]
```

### Why?

The splitting phase should not destroy document structure.

The following invariant is preserved before overlap is introduced:

```
"".join(pieces) == original_text
```

The merge phase should combine pieces, not reconstruct information lost during splitting.

---

## 12. Merge Small Adjacent Pieces

### Decision

Do not treat every recursively produced piece as a final chunk.

Instead:

```
Recursive Split
        ↓
Natural Pieces
        ↓
Merge Adjacent Pieces
        ↓
Final Chunks
```

### Why?

Without merging, natural boundaries could produce many unnecessarily small chunks.

This would increase:

- Embedding operations
- Vector count
- Index size
- Storage requirements

Merging packs adjacent pieces toward the configured chunk-size limit while preserving their order.

---

## 13. Apply Bounded Overlap

### Decision

Carry text from the end of the previous chunk into the beginning of the next chunk.

The configured overlap is treated as a maximum desired overlap.

### Why?

Overlap helps preserve context across chunk boundaries.

However:

```
overlap + next piece <= chunk_size
```

must always remain true.

Therefore, overlap is reduced when necessary to preserve the hard chunk-size guarantee.

---

# Recursive Chunking Algorithm

The strategy operates in three stages.

```
Document
    ↓
Recursive Split
    ↓
Natural Pieces
    ↓
Merge + Overlap
    ↓
Final Text Chunks
    ↓
Construct Chunk Models
```

---

## Stage 1 – Recursive Split

The algorithm first checks whether the text already fits within the configured chunk size.

If it fits:

```
return [text]
```

If it is oversized, the strongest available separator is attempted.

```
Paragraph
    ↓
Line
    ↓
Word
    ↓
Character
```

Only oversized pieces recurse to the next weaker separator.

---

## Stage 2 – Character Fallback

If no stronger boundary can reduce the text sufficiently, the algorithm falls back to direct character slicing.

Example:

```
1200 characters
chunk_size = 500
```

becomes:

```
Piece 0 → 500 characters
Piece 1 → 500 characters
Piece 2 → 200 characters
```

This guarantees that every piece respects the configured maximum size.

---

## Stage 3 – Merge and Overlap

Small adjacent pieces are combined while the result remains within `chunk_size`.

When the next piece cannot fit:

- The current chunk is finalized.
- A bounded tail from the previous chunk is retained.
- The next chunk begins with the overlap followed by the next piece.

This preserves contextual continuity without violating the maximum chunk-size constraint.

---

# Architecture

The application pipeline now consists of:

```
PDF
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
```

The dependency structure is:

```
Application
        │
        ▼
DocumentChunker
        ▲
        │
RecursiveDocumentChunker
```

Callers depend on the abstraction rather than the concrete recursive implementation.

---

# Testing Strategy

The chunking layer is tested at multiple behavioral boundaries.

The test suite verifies:

- Documents smaller than `chunk_size`
- Preservation of original content
- Sequential chunk indexing
- Shared immutable document metadata
- Recursive fallback to weaker separators
- Maximum chunk-size enforcement
- Merging of small adjacent pieces
- Configured overlap behavior
- Invalid constructor configuration
- End-to-end PDF loading and chunking

The integration test verifies the complete pipeline:

```
sample.pdf
    ↓
PdfLoader
    ↓
Document
    ↓
RecursiveDocumentChunker
    ↓
list[Chunk]
```

---

# Lessons Learned

This sprint focused on algorithm design and domain modelling rather than framework usage.

Topics explored included:

- Recursive algorithms
- Base cases
- Progressive fallback strategies
- Semantic text boundaries
- Domain invariants
- Immutable object graphs
- Shared object references
- Strategy abstraction
- Constructor validation
- Character-based chunk sizing
- Context overlap
- Split and merge phases
- Behavioral testing
- Pipeline integration testing

---

# Known Limitations

The current implementation intentionally accepts several limitations.

Chunk size is measured in characters rather than model tokens.

Overlap is character-tail based and may begin in the middle of a word or sentence.

The current `Document` model does not preserve:

- Page boundaries
- Section headings
- Paragraph identifiers

Therefore, the chunker cannot currently produce page-aware or section-aware chunk metadata.

These limitations are documented rather than prematurely abstracted.

---

# Future Considerations

Potential future enhancements include:

- Token-aware chunk sizing
- Token-aware overlap
- Semantic chunking
- Boundary-aware overlap
- Page-aware chunk metadata
- Section-aware chunk metadata
- Configurable separator hierarchies
- Retrieval quality evaluation
- Chunk-size experimentation

These enhancements should be introduced only when supported by concrete requirements or retrieval evaluation.

---

# Outcome

Sprint 4 successfully established the document chunking layer.

The application can now:

- Accept validated documents
- Recursively split oversized content
- Preserve natural text boundaries where possible
- Merge small adjacent pieces
- Apply bounded overlap
- Preserve source document provenance
- Produce validated immutable chunks
- Compose document loading and chunking into a working pipeline

The RAG pipeline now supports:

```
PDF
    ↓
Load
    ↓
Document
    ↓
Chunk
    ↓
list[Chunk]
```

This prepares the project for the next major stage: converting chunk content into vector embeddings.

---

# Architectural Decisions

During this sprint the following ADR was introduced:

- ADR-005 — Use Recursive Character-Based Chunking as the Initial Chunking Strategy

---

# Next Sprint

## Sprint 05 – Embeddings

Planned topics include:

- Embedding concepts
- Embedding model selection
- Embedding abstraction
- API configuration
- Batch embedding
- Embedding domain modelling
- Token limits
- Error handling
- Testing strategy

The objective of Sprint 5 is to transform document chunks into numerical vector representations while keeping the application independent of a specific embedding provider.