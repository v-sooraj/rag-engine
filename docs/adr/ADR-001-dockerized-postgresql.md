# ADR-001: Use Dockerized PostgreSQL with pgvector

## Status

Accepted

---

## Context

The RAG Engine requires a relational database capable of storing vector embeddings while providing a reproducible development environment across different machines.

Installing PostgreSQL directly on every development machine introduces operating system dependencies, manual configuration, and environment drift.

The project also requires native support for vector operations.

---

## Decision

Use Docker Compose to provision PostgreSQL using the official `pgvector/pgvector:pg17` image.

The database is started as part of the project infrastructure and initialized automatically through Docker initialization scripts.

---

## Alternatives Considered

### Local PostgreSQL Installation

**Pros**

- No Docker dependency

**Cons**

- Environment inconsistency
- Manual installation
- Manual extension management
- Difficult onboarding

Rejected.

---

### Build a Custom PostgreSQL Image

**Pros**

- Full control over the image

**Cons**

- Unnecessary maintenance
- Duplicates official images
- No additional value for this project

Rejected.

---

## Consequences

### Positive

- Reproducible development environment
- Native pgvector support
- Minimal setup for new developers
- Isolated infrastructure
- Consistent behavior across machines

### Negative

- Requires Docker Desktop
- Slight startup overhead

---

## Related Documents

- sprint-01-foundation.md