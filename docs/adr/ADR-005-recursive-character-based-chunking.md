# ADR-005 — Use Recursive Character-Based Chunking as the Initial Chunking Strategy

## Status

Accepted

---

## Context

The RAG pipeline requires documents to be divided into smaller units before embedding and vector storage.

A chunking strategy must balance several competing concerns:

- Preserve related context
- Respect maximum chunk size
- Avoid unnecessary fragmentation
- Maintain contextual continuity across boundaries
- Keep implementation understandable
- Avoid premature model-specific coupling

Several chunking approaches were considered.

---

## Decision

Use recursive character-based chunking as the initial document chunking strategy.

The implementation:

- Measures size in characters
- Attempts stronger textual boundaries before weaker ones
- Recursively processes only oversized pieces
- Preserves separators
- Merges small adjacent pieces
- Applies bounded character overlap

The separator hierarchy is:

```
"\n\n"
"\n"
" "
""
```

This represents:

```
Paragraph
    ↓
Line
    ↓
Word
    ↓
Character fallback
```

---

## Alternatives Considered

### Fixed-Size Chunking

Advantages:

- Simple implementation
- Predictable chunk sizes
- Low computational complexity

Disadvantages:

- Can split words and sentences arbitrarily
- Ignores natural document boundaries
- Can separate related context

Fixed-size chunking was rejected as the initial strategy because it does not sufficiently preserve document structure.

---

### Token-Aware Chunking

Advantages:

- Aligns chunk size with embedding model limits
- Provides more accurate control over model input size

Disadvantages:

- Requires tokenizer integration
- May introduce model-specific coupling
- Adds complexity before an embedding model has been selected

Token-aware chunking was deferred until the embedding stage creates a concrete requirement.

---

### Semantic Chunking

Advantages:

- Can group text based on semantic meaning
- May improve contextual coherence

Disadvantages:

- Higher implementation complexity
- May require additional models or embeddings
- Higher processing cost
- Difficult to evaluate without a retrieval-quality framework

Semantic chunking was deferred until the project has a working retrieval pipeline and can evaluate whether the additional complexity improves results.

---

### Recursive Character-Based Chunking

Advantages:

- Preserves stronger textual boundaries where possible
- Provides deterministic behavior
- Avoids tokenizer dependencies
- Teaches the underlying chunking algorithm directly
- Supports configurable size and overlap
- Can evolve independently behind the chunking abstraction

Disadvantages:

- Character counts do not map directly to model tokens
- Character-based overlap may split words or sentences
- Does not understand document semantics
- Does not preserve page or section structure

This approach provides the best balance between contextual preservation, implementation clarity, and current project requirements.

---

## Consequences

### Positive

The project gains a chunking strategy that:

- Preserves natural text boundaries where possible
- Guarantees maximum chunk size
- Avoids excessive small chunks through merging
- Preserves context using overlap
- Remains independent of embedding providers and tokenizers

The strategy is isolated behind the `DocumentChunker` abstraction.

Future implementations can be introduced without changing callers.

---

### Negative

Chunk sizes are measured in characters rather than tokens.

The configured chunk size therefore does not directly represent the input limits of a future embedding model.

Overlap is based on character tails and may begin inside a word or sentence.

Retrieval quality has not yet been evaluated against alternative chunking strategies.

---

## Implementation Notes

The recursive strategy separates processing into three responsibilities:

```
Split
    ↓
Merge
    ↓
Construct Chunk Models
```

The split phase recursively applies weaker separators only to oversized pieces.

The merge phase combines adjacent pieces toward the configured chunk-size limit.

The final construction phase creates immutable `Chunk` models with sequential indexes and preserved document metadata.

---

## Future Evolution

When the embedding stage introduces a concrete tokenizer and model constraints, the project may evaluate:

- A token-aware chunking strategy
- A pluggable text-length measurement abstraction
- Boundary-aware overlap
- Semantic chunking

No abstraction for these future requirements is introduced yet.

---

## Related Sprint

Sprint 04 — Document Chunking