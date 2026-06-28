# ADR-004: Use psycopg3 as PostgreSQL Driver

## Status

Accepted

---

## Context

The application requires direct PostgreSQL connectivity while maintaining a clear understanding of SQL, transactions, and connection lifecycle.

Introducing an ORM at this stage would hide concepts that are important for learning.

---

## Decision

Use `psycopg3` as the PostgreSQL driver.

Database connectivity is centralized within the database module.

Connections are managed using Python context managers.

---

## Alternatives Considered

### psycopg2

**Pros**

- Mature
- Large community

**Cons**

- Older API
- psycopg3 is the recommended successor

Rejected.

---

### SQLAlchemy

**Pros**

- ORM support
- Rich abstractions

**Cons**

- Hides SQL execution
- Additional abstraction layer
- Outside current project scope

Rejected.

---

### asyncpg

**Pros**

- High performance
- Async-first

**Cons**

- Introduces async complexity before it is required

Rejected.

---

## Consequences

### Positive

- Modern PostgreSQL driver
- Clear understanding of SQL
- Future async compatibility
- Minimal abstraction

### Negative

- Manual SQL management
- Connection pooling deferred to future iterations

---

## Related Documents

- sprint-02-database-connectivity.md