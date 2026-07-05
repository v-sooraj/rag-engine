# ADR-006: Use a Local Sentence-Transformer Model for Embedding Generation

## Status

Accepted

## Context

The RAG engine requires an embedding stage that transforms text chunks into numerical vectors.

The embedding implementation must satisfy the existing abstraction:

```text
list[Chunk]
    ↓
ChunkEmbedder
    ↓
list[EmbeddedChunk]