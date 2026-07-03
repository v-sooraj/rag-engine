# RAG Engine

A production-oriented Retrieval-Augmented Generation (RAG) engine built from scratch to understand every architectural layer behind modern AI applications.

## Goals

- Learn production-grade AI backend engineering
- Build every layer incrementally
- Prioritize architecture over frameworks

## Tech Stack

- Python
- PostgreSQL
- pgvector
- Docker
- uv
- Pydantic Settings
- pytest

## Getting Started

1. Clone the repository.
2. Copy `.env.example` to `.env`.
3. Copy `docker/.env.example` to `docker/.env`.
4. Update the configuration values.
5. Start PostgreSQL using Docker Compose.
6. Run the test suite.

## Current Status

### ✅ Completed

- Project bootstrap
- Docker infrastructure
- PostgreSQL + pgvector
- Configuration management
- Environment loading
- Unit tests
- Database connectivity
- Document loading
- Document chunking

### 🚧 In Progress

- Embeddings

### 📋 Planned

- Vector storage
- Retrieval
- Prompt augmentation
- LLM integration
- FastAPI
- Observability

## Documentation

Detailed architectural discussions and engineering decisions can be found under the `docs/architecture` directory.