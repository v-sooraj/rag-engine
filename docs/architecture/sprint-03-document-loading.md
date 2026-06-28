# Sprint 03 – Document Loading

## Objective

Design and implement a flexible and extensible document loading layer capable of transforming external documents into a validated internal domain model.

Rather than focusing solely on PDF parsing, the primary objective of this sprint was to establish a clean architectural boundary between external document sources and the application's internal processing pipeline.

The implementation intentionally emphasizes abstraction, separation of responsibilities, and domain modelling to support future document formats with minimal changes.

---

# Scope

The following areas were completed during this sprint:

- Document domain modelling
- Metadata modelling
- Loader abstraction
- PDF loader implementation
- PDF parsing using PyMuPDF
- Domain validation
- Integration testing

The scope intentionally excluded document chunking, embedding generation, and ingestion orchestration, which will be introduced in subsequent sprints.

---

# Responsibilities of the Document Loading Layer

The document loading layer is responsible for:

- Reading documents from an external source
- Extracting textual content
- Extracting document metadata
- Constructing validated domain models
- Isolating third-party parsing libraries from the rest of the application

The document loading layer is **not** responsible for:

- Chunking
- Duplicate detection
- Idempotency
- Embedding generation
- Vector persistence
- Ingestion orchestration
- Retry handling

Those responsibilities belong to higher-level components introduced in future sprints.

---

# Engineering Decisions

## 1. Introduce a Loader Abstraction

### Decision

Define an abstract `DocumentLoader` interface responsible for transforming a document source into a `Document` domain object.

### Why?

- Enables future support for additional document formats.
- Decouples callers from implementation details.
- Encourages programming against abstractions rather than concrete implementations.

---

## 2. Strongly Typed Domain Models

### Decision

Represent loaded documents using dedicated domain models.

```
Document
├── content
└── metadata

DocumentMetadata
├── filename
├── page_count
├── title
├── author
└── language
```

### Why?

- Provides compile-time clarity.
- Enforces domain invariants.
- Prevents loosely structured dictionaries from propagating through the application.

---

## 3. Fail-fast Validation

### Decision

Validate loaded documents during model construction using Pydantic.

### Why?

Invalid documents should fail immediately rather than propagating incomplete state through later pipeline stages.

---

## 4. Isolate External Libraries

### Decision

Confine PyMuPDF usage exclusively to the PDF loader implementation.

### Why?

The remainder of the application should remain independent of third-party parsing libraries.

Replacing the parsing implementation in the future should only affect a single component.

---

## 5. Decompose the Loading Algorithm

### Decision

Separate document loading into distinct internal operations.

```
load()
    │
    ├── extract_content()
    ├── extract_metadata()
    └── construct Document
```

### Why?

Each private method performs a single well-defined responsibility while preserving a highly readable orchestration method.

---

# Architecture

The document loading architecture currently consists of the following layers.

```
Application
        │
        ▼
DocumentLoader (Abstraction)
        │
        ▼
PdfLoader
        │
        ▼
PyMuPDF
        │
        ▼
PDF Document
```

The remainder of the application interacts exclusively with the `DocumentLoader` abstraction.

Implementation details remain localized inside the adapter layer.

---

# Testing Strategy

Integration testing was introduced for the document loading layer.

The implemented test validates:

- PDF parsing
- Metadata extraction
- Domain model construction
- Content extraction

Testing the complete loading pipeline provides greater confidence than isolated unit tests of third-party library interactions.

---

# Lessons Learned

This sprint focused primarily on architectural modelling rather than framework usage.

Topics explored included:

- Domain modelling
- Separation of concerns
- Adapter pattern
- Abstract base classes
- Dependency inversion
- Fail-fast validation
- Strongly typed metadata
- Integration testing
- External library isolation

---

# Future Considerations

The following topics were intentionally deferred:

- Document chunking
- OCR support
- Additional document formats
- Streaming large documents
- Remote document sources
- Ingestion orchestration
- Idempotent ingestion

These capabilities will be introduced incrementally as the project evolves.

---

# Outcome

Sprint 3 successfully established a clean document loading layer.

The application can now:

- Load PDF documents
- Extract textual content
- Extract document metadata
- Validate domain models
- Isolate parsing implementation details
- Support future document formats through a common abstraction

This completes the first stage of the Retrieval-Augmented Generation (RAG) pipeline.

---

# Architectural Decisions

During this sprint the following ADR was introduced:

- ADR-004 — Selection of PyMuPDF as the initial PDF parsing library.

---

# Next Sprint

## Sprint 04 – Document Chunking

Planned topics include:

- Chunk domain model
- Chunking abstraction
- Fixed-size chunking
- Recursive chunking
- Chunk metadata
- Overlapping windows
- Token-aware chunking
- Chunk quality evaluation

The objective of Sprint 4 is to transform loaded documents into retrieval-optimized chunks that will later be embedded and stored in the vector database.