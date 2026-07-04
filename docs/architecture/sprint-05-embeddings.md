# Sprint 05 — Embeddings

## Status

Completed

## Objective

Implement the embedding stage of the RAG ingestion pipeline.

The embedding stage transforms immutable text chunks into immutable embedded chunks containing numerical vector representations that can later be persisted and searched using a vector database.

This sprint extends the pipeline from:

PDF → Document → Chunks

to:

PDF → Document → Chunks → Embedded Chunks

---

## Scope

The sprint includes:

- embedding domain model
- embedding abstraction
- local embedding implementation
- configurable batch processing
- local sentence-transformer model integration
- unit tests using model injection
- real local embedding generation test
- complete document loading, chunking, and embedding pipeline test

The sprint does not include:

- vector persistence
- pgvector integration
- vector indexes
- similarity search
- retrieval
- query embedding
- prompt augmentation
- LLM generation

These concerns belong to later pipeline stages.

---

## Pipeline Position

The pipeline before this sprint was:

PDF
↓
DocumentLoader
↓
Document
↓
DocumentChunker
↓
list[Chunk]

The pipeline after this sprint is:

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

The output of this sprint becomes the input to the vector storage stage.

---

## Package Structure

```text
rag_engine/
├── loader/
│   ├── document.py
│   ├── document_loader.py
│   └── pdf_loader.py
│
├── chunker/
│   ├── chunk.py
│   ├── document_chunker.py
│   └── recursive_document_chunker.py
│
└── embedding/
    ├── embedded_chunk.py
    ├── chunk_embedder.py
    └── local_chunk_embedder.py

tests/
└── embedding/
    ├── test_local_chunk_embedder.py
    ├── test_local_embedding_integration.py
    └── test_embedding_pipeline.py