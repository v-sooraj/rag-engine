# Design Decision #1: Document Ingestion

## Decision

For the first iteration, documents will be placed manually into a local `documents/` directory. The ingestion process will scan this directory and process every supported document.

## Rationale

- Keeps the project focused on the core Retrieval-Augmented Generation (RAG) pipeline.
- Avoids introducing API design, authentication, and asynchronous processing complexity in the early stages.
- Enables rapid iteration on document parsing, chunking, embedding generation, retrieval, and prompt augmentation.

## Future Improvements

- REST API for document uploads
- Background ingestion pipeline
- Ingestion progress tracking and monitoring
- Cloud object storage integration (Amazon S3, Azure Blob Storage, Google Cloud Storage)

# Design Decision #2: Manual Ingestion Execution

## Decision

Document ingestion will be executed manually using the following command:

```bash
python ingest.py
```

# Design Decision #3: Orchestrator-Driven Ingestion Pipeline

## Decision

The ingestion workflow is orchestrated by `ingest.py`.

- `ingest.py` serves as the central orchestrator for the ingestion pipeline.
- Each component performs **exactly one responsibility** and returns its output to the orchestrator.
- Components do **not** directly invoke downstream components.
- The orchestrator is responsible for coordinating the execution order and passing data between components.

## Rationale

This architecture provides the following benefits:

- **Improved Testability**  
  Each component can be unit tested independently without requiring downstream dependencies.

- **Reduced Coupling**  
  Components remain independent and communicate only through the orchestrator, resulting in a cleaner and more maintainable architecture.

- **Extensibility**  
  Individual implementations (e.g., embedding providers, chunking strategies, or vector stores) can be replaced with minimal impact on the rest of the system.

- **SOLID Compliance**  
  The design adheres to the **Single Responsibility Principle (SRP)** by ensuring each component has a single responsibility, while the orchestrator manages workflow coordination.

- **Common Backend Pattern**  
  Centralized orchestration is a widely adopted pattern in backend systems, improving readability, maintainability, and future scalability.

## Consequences

### Advantages

- Easier unit and integration testing.
- Loose coupling between pipeline components.
- Components are reusable across different workflows.
- Simplifies replacing or extending individual pipeline stages.
- Clear separation of concerns and centralized workflow management.

### Trade-offs

- `ingest.py` assumes responsibility for coordinating the workflow and may grow as the pipeline expands.
- Adding new stages requires updating the orchestrator.