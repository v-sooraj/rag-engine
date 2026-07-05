# ADR-004 — Selection of PyMuPDF as the Initial PDF Parsing Library

## Status

Accepted

---

## Context

The document loading layer requires a reliable PDF parsing library capable of extracting textual content and document metadata.

Several candidate libraries were evaluated.

- PyPDF
- PyMuPDF
- Docling

The project currently focuses on building a production-oriented Retrieval-Augmented Generation (RAG) engine while keeping implementation complexity manageable.

---

## Decision

Use **PyMuPDF** as the initial PDF parsing library.

PyMuPDF will serve as the implementation behind the `PdfLoader` adapter.

The remainder of the application depends only on the `DocumentLoader` abstraction.

---

## Alternatives Considered

### PyPDF

Advantages:

- Simple API
- Pure Python
- Widely adopted

Disadvantages:

- Slower text extraction
- Lower extraction accuracy for complex layouts
- Limited support for advanced document processing

---

### Docling

Advantages:

- Excellent support for production RAG pipelines
- Rich document understanding
- Strong support for structured documents

Disadvantages:

- Larger dependency footprint
- Higher implementation complexity
- Introduces capabilities beyond the current project requirements

---

### PyMuPDF

Advantages:

- Fast text extraction
- High extraction accuracy
- Access to document metadata
- Mature ecosystem
- Suitable for production workloads

Disadvantages:

- Native dependency
- Lower-level API than higher-level document processing frameworks

---

## Consequences

### Positive

- Fast document loading
- Reliable metadata extraction
- Minimal implementation complexity
- Easy replacement through the existing `DocumentLoader` abstraction
- No framework lock-in

### Negative

- OCR support is not provided by default.
- Additional capabilities such as layout understanding may require future enhancements.
- Alternative loaders may still be introduced for specialized document types.

---

## Implementation Notes

The selected library is intentionally isolated inside the `PdfLoader` implementation.

No other component in the application directly depends on PyMuPDF.

This architectural boundary allows future replacement or extension of the parsing implementation without affecting downstream components.

---

## Related Sprint

Sprint 03 — Document Loading