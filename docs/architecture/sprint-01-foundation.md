# Sprint 01 – Foundation

## Objective

Establish a solid engineering foundation for the RAG Engine before implementing any application logic.

The objective of this sprint was **not** to build Retrieval-Augmented Generation (RAG) functionality. Instead, the focus was on preparing the project with a clean, maintainable, and production-oriented architecture that future components can build upon.

---

# Scope

The following areas were intentionally completed during this sprint:

- Project bootstrap
- Development environment
- Containerized database
- Dependency management
- Application configuration
- Testing setup
- Development workflow

No application-specific RAG functionality was implemented during this sprint.

---

# Architecture Principles Established

The following principles will guide the development of this project:

- Architecture before implementation
- Concepts before framework syntax
- Single Responsibility Principle (SRP)
- High cohesion and low coupling
- Incremental development
- Fail-fast configuration validation
- Testable and maintainable code
- Small feature branches and pull requests

These principles will continue to influence architectural decisions throughout the project.

---

# Engineering Decisions

## 1. Containerized PostgreSQL

### Decision

Use Docker Compose with the official `pgvector/pgvector:pg17` image.

### Why?

- Avoid local PostgreSQL installation
- Ensure reproducible development environments
- Enable pgvector support from the beginning
- Keep development environment isolated from the host machine

---

## 2. Separate Infrastructure and Application Configuration

### Decision

Maintain two independent `.env` files.

```
docker/.env
```

Contains infrastructure configuration.

```
project-root/.env
```

Contains application runtime configuration.

### Why?

Infrastructure and application have different responsibilities and lifecycles.

Keeping them separate improves maintainability and prevents accidental coupling.

---

## 3. Application Configuration

### Decision

Centralize runtime configuration using Pydantic Settings.

Configuration is exposed through a singleton `settings` object.

### Why?

- Single source of truth
- Fail-fast validation
- Simplified dependency management
- Similar lifecycle to Spring Boot singleton beans

---

## 4. Nested Configuration

### Decision

Group configuration by responsibility.

Example:

```
Settings
├── postgres
├── openai
├── retrieval
├── logging
```

Instead of maintaining a flat list of unrelated configuration properties.

### Why?

- Higher cohesion
- Easier navigation
- Better scalability as new configuration groups are introduced

---

## 5. Environment Variable Mapping

### Decision

Use nested environment variable mapping.

Example:

```
POSTGRES_HOST
POSTGRES_PORT
```

Maps to:

```
settings.postgres.host
settings.postgres.port
```

### Why?

- Improves readability
- Maintains concise environment variable names
- Provides a clean mapping between runtime configuration and application objects

---

## 6. Testing

### Decision

Introduce pytest from the beginning of the project.

### Why?

Configuration is production code and should be validated automatically.

Early testing also establishes the testing culture for future development.

---

## 7. Git Workflow

### Decision

Develop one feature per branch.

```
feature
    ↓

small commits
    ↓

merge
    ↓

next feature
```

### Why?

- Easier code reviews
- Smaller pull requests
- Simpler rollback if necessary
- Cleaner project history

---

# Lessons Learned

This sprint focused on understanding engineering concepts rather than framework syntax.

Topics explored included:

- Docker volumes
- PostgreSQL initialization scripts
- Dependency management using `uv`
- Configuration ownership
- Object lifecycle
- Singleton pattern
- Environment management
- Systematic debugging through reasoning instead of trial and error

---

# Outcome

Sprint 1 successfully established the engineering foundation for the project.

The repository now includes:

- Dockerized PostgreSQL
- pgvector integration
- Python project bootstrap
- Centralized configuration management
- Unit testing setup
- Clean Git workflow

With the platform foundation complete, future sprints can focus entirely on implementing application functionality.

---

# Next Sprint

## Sprint 02 – Database Connectivity

Planned topics:

- psycopg3
- Connection management
- Context managers
- Database lifecycle
- Verifying pgvector installation
- Basic SQL execution
- Integration testing

The goal of Sprint 2 is to build a robust database access layer that future components can depend upon.