# ADR-003: Use uv for Python Dependency Management

## Status

Accepted

---

## Context

The project requires reproducible dependency management, isolated virtual environments, and fast package installation.

Traditional Python tooling often relies on multiple utilities for dependency management and virtual environments.

---

## Decision

Use `uv` as the project's package manager and virtual environment manager.

Project metadata is maintained through `pyproject.toml`.

---

## Alternatives Considered

### pip + venv

**Pros**

- Standard Python tooling

**Cons**

- Multiple commands
- Slower dependency resolution
- Separate environment management

Rejected.

---

### Poetry

**Pros**

- Rich dependency management

**Cons**

- Larger toolchain
- Additional concepts
- More than required for this project

Rejected.

---

## Consequences

### Positive

- Fast dependency installation
- Integrated virtual environment management
- Lockfile support
- Modern Python workflow

### Negative

- Newer ecosystem
- Smaller community than pip

---

## Related Documents

- sprint-01-foundation.md