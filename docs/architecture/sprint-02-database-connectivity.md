# Sprint 02 – Database Connectivity

## Objective

Establish a robust and maintainable database access layer that the application can depend upon.

Rather than simply connecting to PostgreSQL, the goal of this sprint was to design the database layer with clear ownership, proper separation of responsibilities, and a clean interface that future components can build upon.

---

# Scope

The following areas were completed during this sprint:

- PostgreSQL connectivity using psycopg3
- Connection creation
- Context manager usage
- Database connectivity verification
- pgvector extension verification
- Basic SQL execution

The focus was intentionally limited to establishing a reliable database foundation before implementing higher-level persistence logic.

---

# Responsibilities of the Database Layer

The database layer is responsible for:

- Creating PostgreSQL connections
- Managing connection lifecycle
- Providing a centralized entry point for database access
- Encapsulating psycopg-specific implementation details
- Verifying communication with the database

The database layer is **not** responsible for:

- Business logic
- Vector storage
- Repository operations
- SQL query abstractions
- Transaction orchestration

Those responsibilities will be introduced in future sprints.

---

# Engineering Decisions

## 1. Use psycopg3

### Decision

Use `psycopg3` as the PostgreSQL driver.

### Why?

- Modern PostgreSQL driver for Python
- Active development
- Clean API
- Good support for future async operations
- Suitable for production applications

---

## 2. Centralize Connection Creation

### Decision

Create database connections from a dedicated database module instead of allowing individual components to create their own connections.

### Why?

- Single source of truth
- Reduced duplication
- Easier maintenance
- Better separation of concerns
- Simplifies future enhancements such as connection pooling

---

## 3. Reuse Centralized Configuration

### Decision

Reuse the existing `settings` singleton for database configuration.

### Why?

- Avoid duplicated configuration loading
- Maintain consistency across the application
- Ensure all runtime configuration is validated at startup

---

## 4. Use Context Managers

### Decision

Manage database connections using Python context managers.

### Why?

- Automatic resource cleanup
- Prevent connection leaks
- Simpler lifecycle management
- Equivalent to Java's `try-with-resources`

---

## 5. Verify Infrastructure Early

### Decision

Verify database connectivity and pgvector installation before implementing application-specific features.

### Why?

Detecting infrastructure issues early reduces debugging effort and provides confidence that the environment is correctly configured.

---

# Architecture

The database layer currently has a simple responsibility.

```
Application Modules
        │
        ▼
Database Layer
        │
        ▼
psycopg3
        │
        ▼
PostgreSQL
```

Application components interact with the database through the database layer rather than depending directly on psycopg3.

This keeps implementation details localized and improves maintainability.

---

# Lessons Learned

This sprint focused on understanding the engineering concepts behind database access rather than simply learning a library.

Topics explored included:

- Connection ownership
- Separation of responsibilities
- Resource lifecycle management
- Context managers
- Comparison with Java's try-with-resources
- Centralized configuration reuse
- Infrastructure verification before feature development

---

# Future Considerations

The following topics were intentionally deferred:

- Connection pooling
- Transaction management
- Async database access
- Repository abstraction
- Query builders
- ORM evaluation

These will be introduced only when the project requires them.

---

# Outcome

Sprint 2 established a clean and maintainable database access layer for the project.

The application can now:

- Connect to PostgreSQL
- Execute SQL statements
- Verify pgvector availability
- Reuse centralized configuration
- Manage database resources safely

This foundation enables future development of vector storage, document ingestion, and retrieval without revisiting database connectivity.

---

# Next Sprint

## Sprint 03 – Document Loading

Planned topics include:

- Loader abstraction
- Interface design
- PDF document loading
- Document metadata
- Error handling
- Extensibility for future document formats

The objective of Sprint 3 is to design a flexible document loading layer that can support multiple document sources while keeping higher-level components independent of specific file formats.