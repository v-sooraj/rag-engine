# ADR-002: Centralize Application Configuration using Pydantic Settings

## Status

Accepted

---

## Context

The application requires centralized runtime configuration for database connectivity and future integrations such as OpenAI, retrieval settings, logging, and chunking.

Scattered environment variable access would increase coupling and reduce maintainability.

---

## Decision

Use `pydantic-settings` to load configuration into a singleton `Settings` object.

Configuration is grouped by responsibility using nested models.

Example:

```
Settings
├── postgres
├── openai
├── retrieval
├── logging
```

---

## Alternatives Considered

### os.getenv()

**Pros**

- Minimal dependencies

**Cons**

- No validation
- No type safety
- Configuration scattered throughout the application

Rejected.

---

### python-dotenv

**Pros**

- Simple environment loading

**Cons**

- Does not provide structured configuration models
- Validation must be implemented manually

Rejected.

---

## Consequences

### Positive

- Single source of truth
- Strong typing
- Startup validation
- High cohesion
- Easy extensibility

### Negative

- Additional dependency
- Requires understanding of Pydantic models

---

## Related Documents

- sprint-01-foundation.md