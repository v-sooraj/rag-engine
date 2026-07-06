# ADR-011: Introduce a Dedicated RAG Pipeline Orchestration Boundary

## Status

Accepted

## Context

The RAG engine already contains independent capabilities for:

```text
QueryEmbedder
Retriever
PromptAugmenter
LLM
```

The complete online flow is:

```text
User Query
    ↓
Query Embedding
    ↓
Semantic Retrieval
    ↓
Prompt Augmentation
    ↓
LLM Generation
    ↓
GeneratedAnswer
```

Before this decision, callers manually coordinated these capabilities.

The application therefore needed to decide:

- whether orchestration should be represented as a pipeline or service
- what the public orchestration operation should accept and return
- where `top_k` should belong
- who should validate query input
- who should construct pipeline dependencies
- whether orchestration should wrap stage failures
- what should happen when retrieval returns no chunks

---

## Decision

Introduce a provider-independent orchestration capability:

```text
RAGPipeline
```

with the operation:

```python
answer(
    query: str,
) -> GeneratedAnswer
```

Implement the default orchestration using:

```text
DefaultRAGPipeline
```

Inject:

```text
QueryEmbedder
Retriever
PromptAugmenter
LLM
```

through the constructor.

Configure:

```text
top_k
```

at pipeline construction time.

Validate:

- non-empty queries
- non-blank queries
- positive `top_k`

Allow stage-specific failures to propagate unchanged.

When retrieval returns no chunks, continue through:

```text
PromptAugmenter
    ↓
LLM
```

rather than generating a pipeline-level fallback answer.

---

## Decision Drivers

The decision is based on the following requirements:

- expose one application-level online RAG operation
- remove manual stage coordination from callers
- preserve existing capability boundaries
- keep orchestration independent of infrastructure implementations
- hide internal retrieval strategy from ordinary callers
- validate the pipeline's own public contract
- avoid unnecessary exception wrapping
- preserve existing grounding behavior for empty retrieval results
- support focused orchestration unit testing
- support real end-to-end testing through the same public boundary

---

## Considered Orchestration Names

### Option A — RAGService

```text
RAGService
└── answer(query)
```

Advantages:

- familiar application naming
- simple service-style API

Disadvantages:

- generic name
- does not communicate fixed pipeline sequencing
- could become a container for unrelated operations

This option was rejected.

---

### Option B — RAGPipeline

```text
RAGPipeline
└── answer(query)
```

Advantages:

- accurately describes sequential stage coordination
- matches the RAG architecture
- preserves a focused capability boundary
- communicates the data-flow nature of the component

This option was selected.

---

## Public Contract

The selected public contract is:

```python
class RAGPipeline(ABC):

    @abstractmethod
    def answer(
        self,
        query: str,
    ) -> GeneratedAnswer:
        pass
```

The caller sees:

```text
query
    ↓
answer
```

The caller does not coordinate internal stages.

---

## Why GeneratedAnswer Is Returned Directly

The generation stage already returns:

```text
GeneratedAnswer
```

The orchestration layer does not need to introduce another result wrapper.

The pipeline performs:

```text
query
    ↓
orchestration
    ↓
GeneratedAnswer
```

A separate pipeline response model would add structure without a current application requirement.

---

## Default Implementation

The concrete implementation is:

```text
DefaultRAGPipeline
```

The execution sequence is:

```text
answer(query)
    ↓
validate query
    ↓
QueryEmbedder.embed(query)
    ↓
Retriever.retrieve(query_embedding, top_k)
    ↓
PromptAugmenter.augment(query, retrieved_chunks)
    ↓
LLM.generate(augmented_prompt)
    ↓
GeneratedAnswer
```

---

## Considered top_k Designs

### Option A — Request-Level top_k

```python
pipeline.answer(
    query,
    top_k=3,
)
```

Advantages:

- flexible for each request
- caller controls retrieval depth

Disadvantages:

- exposes retrieval strategy in the public use case
- requires ordinary callers to understand vector retrieval
- expands the public operation before a real override requirement exists

This option was rejected.

---

### Option B — Pipeline-Level top_k

```python
pipeline = DefaultRAGPipeline(
    ...,
    top_k=3,
)

answer = pipeline.answer(query)
```

Advantages:

- keeps the public operation focused on question-to-answer
- treats retrieval depth as pipeline strategy
- supports centralized configuration
- avoids premature per-request overrides

This option was selected.

---

## top_k Validation

Because `top_k` is pipeline configuration, it is validated during construction.

The required invariant is:

```text
top_k > 0
```

Invalid configuration fails before the pipeline is used.

This prevents delayed configuration errors during request processing.

---

## Considered Query Validation Ownership

### Option A — Delegate Validation to QueryEmbedder

```text
RAGPipeline
    ↓
QueryEmbedder
    ↓
reject invalid query
```

Advantages:

- avoids repeated validation code

Disadvantages:

- makes the pipeline's public contract depend on one injected implementation
- a future query embedder may validate differently
- invalid pipeline input enters orchestration before rejection

This option was rejected.

---

### Option B — Validate at RAGPipeline Boundary

```text
RAGPipeline.answer(query)
    ↓
validate
    ↓
begin orchestration
```

Advantages:

- pipeline owns its public contract
- invalid input fails before dependencies are called
- behavior remains independent of injected implementations

This option was selected.

---

## Validation Duplication

`QueryEmbedder` may also validate its input.

This is intentional.

The boundaries are:

```text
RAGPipeline
└── validates answer operation input
```

and:

```text
QueryEmbedder
└── validates embedding operation input
```

Each public capability protects its own contract.

---

## Considered Dependency Construction

### Option A — Construct Concrete Dependencies Internally

```text
DefaultRAGPipeline
├── creates LocalQueryEmbedder
├── creates PostgresRetriever
├── creates DefaultPromptAugmenter
└── creates OllamaLLM
```

Advantages:

- simple external construction

Disadvantages:

- couples orchestration to infrastructure
- mixes composition with execution
- makes focused unit testing harder
- forces configuration concerns into the pipeline

This option was rejected.

---

### Option B — Constructor Injection

```text
DefaultRAGPipeline
├── QueryEmbedder
├── Retriever
├── PromptAugmenter
├── LLM
└── top_k
```

Advantages:

- keeps orchestration focused
- depends on abstractions
- supports alternate implementations
- supports isolated unit tests
- separates composition from execution

This option was selected.

---

## Dependency Direction

The pipeline depends on capabilities:

```text
DefaultRAGPipeline
    ↓
QueryEmbedder

DefaultRAGPipeline
    ↓
Retriever

DefaultRAGPipeline
    ↓
PromptAugmenter

DefaultRAGPipeline
    ↓
LLM
```

It does not depend directly on:

```text
sentence-transformers
PostgreSQL
pgvector
httpx
Ollama
qwen3:4b
```

These remain behind concrete capability implementations.

---

## Considered Error Handling

### Option A — Propagate Stage Failures

```text
stage failure
    ↓
caller receives original failure
```

Advantages:

- preserves precise failure information
- avoids unnecessary wrapping
- keeps orchestration simple

This option was selected.

---

### Option B — Wrap Everything in RAGPipelineError

```text
any failure
    ↓
RAGPipelineError
```

Advantages:

- one pipeline-level exception

Disadvantages:

- hides meaningful stage-specific failures
- adds no current recovery behavior
- introduces another exception layer
- reduces debugging precision

This option was rejected.

---

## Exact Exception Preservation

The pipeline does not catch dependency failures.

Therefore the exact exception instance propagates.

Tests verify:

```python
assert exception_info.value is error
```

This proves that failures are not:

- wrapped
- translated
- replaced

---

## Stage Failure Behavior

If query embedding fails:

```text
QueryEmbedder
    ↓
failure
    ↓
stop
```

Retrieval, augmentation, and generation are not called.

If retrieval fails:

```text
Retriever
    ↓
failure
    ↓
stop
```

Augmentation and generation are not called.

If prompt augmentation fails:

```text
PromptAugmenter
    ↓
failure
    ↓
stop
```

Generation is not called.

If generation fails:

```text
LLM
    ↓
failure
    ↓
propagate
```

---

## Considered Empty Retrieval Behavior

### Option A — Pipeline-Level Fallback Answer

```text
No chunks
    ↓
DefaultRAGPipeline
    ↓
GeneratedAnswer with hard-coded fallback
```

Advantages:

- avoids model invocation
- deterministic fallback

Disadvantages:

- introduces answer policy into orchestration
- bypasses existing prompt augmentation behavior
- bypasses the LLM
- creates a second answer-generation path

This option was rejected.

---

### Option B — Continue the Pipeline

```text
No chunks
    ↓
PromptAugmenter
    ↓
AugmentedPrompt with empty context
    ↓
LLM
    ↓
GeneratedAnswer
```

Advantages:

- preserves existing stage responsibilities
- keeps orchestration policy-free
- uses the existing grounding instruction
- maintains one generation path

This option was selected.

---

## Why Empty Retrieval Continues

The existing prompt augmentation and generation design already handles insufficient context.

The system instruction tells the model to state that it lacks enough information when the context cannot answer the question.

Therefore the responsibility chain remains:

```text
Retriever
└── evidence availability

PromptAugmenter
└── prompt construction

LLM
└── grounded answer behavior

RAGPipeline
└── orchestration
```

---

## Original Query Preservation

The original query is required by:

```text
QueryEmbedder
```

and:

```text
PromptAugmenter
```

The pipeline therefore preserves it throughout execution.

The data flow is:

```text
query
├── embed → query embedding
└── augment → original question
```

The embedding is used for retrieval.

The original query remains the question presented to the LLM.

---

## Testing Decision

Use mocked capability abstractions for orchestration unit tests.

The tests verify:

- successful answer return
- query embedding call
- retrieval input
- configured `top_k`
- original query preservation
- retrieved chunk propagation
- augmented prompt propagation
- query validation
- pipeline configuration validation
- zero-result continuation
- exact stage failure propagation
- stopping after stage failures

---

## Real Integration Decision

Update the existing complete real RAG test to call:

```python
pipeline.answer(query)
```

instead of manually performing:

```text
embed
retrieve
augment
generate
```

This ensures the real integration test exercises the same application-level boundary intended for future API callers.

---

## Manual Filtering Removal

The previous real test manually filtered retrieved chunks by test document ID.

That filtering existed outside the real application pipeline.

It was removed when the test moved to:

```text
DefaultRAGPipeline.answer(query)
```

The integration test now proves the actual public behavior without external orchestration.

---

## Empty Speculative Package Decision

An existing package contained only:

```text
rag_engine/
└── ingest/
    └── __init__.py
```

It had no implementation or tests.

The package was deleted.

The project will introduce ingestion orchestration only when a concrete capability is designed and implemented.

---

## Consequences

### Positive

- callers now use one application-level RAG operation
- manual online stage coordination is removed
- orchestration remains independent of infrastructure
- existing capability boundaries are preserved
- retrieval strategy remains hidden from ordinary callers
- invalid pipeline configuration fails early
- invalid query input fails before dependency execution
- stage-specific failures remain precise
- zero-result behavior remains consistent with existing grounding policy
- orchestration can be tested independently
- real integration tests use the true public boundary

### Negative

- the pipeline currently supports only one configured retrieval depth
- callers cannot override `top_k` per request
- execution remains synchronous
- the calling thread remains blocked during model generation

### Neutral

The pipeline does not define a new exception hierarchy.

A unified API error contract may later translate failures at the HTTP boundary.

---

## Future Considerations

Future versions may introduce:

- FastAPI integration
- dependency composition
- per-request retrieval options
- async pipeline execution
- streaming generation
- conversation-aware orchestration
- pipeline metrics
- tracing
- retries
- caching
- evaluation hooks
- ingestion orchestration

These additions should preserve the current responsibility:

```text
RAGPipeline
    ↓
coordinate online RAG stages
```

---

## Final Decision

Introduce a dedicated `RAGPipeline` abstraction with a `DefaultRAGPipeline` implementation.

Expose:

```text
answer(query) → GeneratedAnswer
```

Configure `top_k` at pipeline construction time.

Inject `QueryEmbedder`, `Retriever`, `PromptAugmenter`, and `LLM` abstractions.

Validate the pipeline's own query input and configuration.

Allow stage-specific failures to propagate unchanged.

Continue through prompt augmentation and generation when retrieval returns zero chunks.

Use the new pipeline as the public application-level boundary for the complete online RAG flow.