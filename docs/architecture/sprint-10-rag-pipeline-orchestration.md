# Sprint 10 — RAG Pipeline Orchestration

## Status

Completed

## Objective

Introduce an application-level orchestration capability for the complete online RAG pipeline.

Before this sprint, every online RAG stage existed and worked independently:

```text
User Query
    ↓
QueryEmbedder
    ↓
Query Embedding
    ↓
Retriever
    ↓
Retrieved Chunks
    ↓
PromptAugmenter
    ↓
AugmentedPrompt
    ↓
LLM
    ↓
GeneratedAnswer
```

However, callers were responsible for manually coordinating every stage.

This sprint introduces one public application-level operation:

```text
User Query
    ↓
RAGPipeline
    ↓
GeneratedAnswer
```

The orchestration implementation coordinates:

```text
Embed
    ↓
Retrieve
    ↓
Augment
    ↓
Generate
```

without taking ownership of the responsibilities of the individual stages.

---

## Scope

The sprint includes:

- provider-independent RAG pipeline abstraction
- default RAG pipeline implementation
- application-level `answer(query)` operation
- constructor injection of pipeline capabilities
- configurable retrieval depth using `top_k`
- query validation at the pipeline boundary
- pipeline configuration validation
- orchestration of the complete online RAG flow
- unchanged propagation of stage-specific failures
- zero-result retrieval continuation
- focused orchestration unit tests
- real end-to-end pipeline test through the new orchestration boundary
- removal of an unused speculative `ingest` package

The sprint does not include:

- ingestion orchestration
- FastAPI
- async pipeline execution
- streaming responses
- per-request retrieval overrides
- pipeline-specific exception wrapping
- retry policies
- fallback models
- answer citations
- conversation history
- observability
- evaluation
- caching

These concerns belong to later stages.

---

## Problem Before This Sprint

Before orchestration, the online RAG flow required callers to perform:

```python
query_embedding = query_embedder.embed(query)

retrieved_chunks = retriever.retrieve(
    query_embedding=query_embedding,
    top_k=3,
)

augmented_prompt = prompt_augmenter.augment(
    query=query,
    chunks=retrieved_chunks,
)

answer = llm.generate(
    augmented_prompt
)
```

The individual capabilities were correctly separated, but the application did not yet expose one operation representing the complete online use case.

The caller had to know:

- that the query must first be embedded
- that the embedding must be passed to retrieval
- that retrieval requires `top_k`
- that the original query must be preserved for prompt augmentation
- that retrieved chunks must be passed to the prompt augmenter
- that the augmented prompt must be passed to the LLM

This coordination logic belongs to an application-level orchestration boundary.

---

## Pipeline Position

The complete online flow is now:

```text
User Query
    ↓
RAGPipeline
    ↓
DefaultRAGPipeline
    ↓
QueryEmbedder
    ↓
Query Embedding
    ↓
Retriever
    ↓
Retrieved Chunks
    ↓
PromptAugmenter
    ↓
AugmentedPrompt
    ↓
LLM
    ↓
GeneratedAnswer
```

From the caller's perspective:

```text
query
    ↓
answer
```

From the orchestrator's perspective:

```text
query
    ↓
embed
    ↓
retrieve
    ↓
augment
    ↓
generate
    ↓
answer
```

---

## Package Structure

```text
rag_engine/
└── rag_pipeline/
    ├── __init__.py
    ├── rag_pipeline.py
    └── default_rag_pipeline.py
```

Test structure:

```text
tests/
└── rag_pipeline/
    ├── __init__.py
    └── test_default_rag_pipeline.py
```

The existing complete real RAG integration test was also updated to use:

```text
DefaultRAGPipeline
```

instead of manually coordinating the online stages.

---

## RAG Pipeline Boundary

The application-level capability is:

```python
class RAGPipeline(ABC):

    @abstractmethod
    def answer(
        self,
        query: str,
    ) -> GeneratedAnswer:
        pass
```

The public boundary is:

```text
query
    ↓
RAGPipeline.answer()
    ↓
GeneratedAnswer
```

The caller does not need to know about:

- query embeddings
- vector retrieval
- `top_k`
- retrieved chunks
- prompt augmentation
- augmented prompts
- model invocation

These remain internal pipeline stages.

---

## Why RAGPipeline Was Selected

Two names were considered:

```text
RAGPipeline
```

and:

```text
RAGService
```

`RAGPipeline` was selected because the component has one specific responsibility:

```text
coordinate a fixed sequence of RAG stages
```

The sequence is:

```text
Query Embedding
    ↓
Retrieval
    ↓
Prompt Augmentation
    ↓
Generation
```

The component is not a general service containing unrelated application operations.

The architecture remains capability-oriented:

```text
QueryEmbedder
    ↑
LocalQueryEmbedder

Retriever
    ↑
PostgresRetriever

PromptAugmenter
    ↑
DefaultPromptAugmenter

LLM
    ↑
OllamaLLM

RAGPipeline
    ↑
DefaultRAGPipeline
```

---

## Default RAG Pipeline

The concrete implementation is:

```text
DefaultRAGPipeline
```

It receives:

```text
QueryEmbedder
Retriever
PromptAugmenter
LLM
top_k
```

Its execution flow is:

```text
answer(query)
    ↓
validate query
    ↓
query_embedder.embed(query)
    ↓
retriever.retrieve(query_embedding, top_k)
    ↓
prompt_augmenter.augment(query, retrieved_chunks)
    ↓
llm.generate(augmented_prompt)
    ↓
GeneratedAnswer
```

The implementation contains no infrastructure-specific logic.

---

## Dependency Injection

`DefaultRAGPipeline` receives capability abstractions through constructor injection:

```python
DefaultRAGPipeline(
    query_embedder=query_embedder,
    retriever=retriever,
    prompt_augmenter=prompt_augmenter,
    llm=llm,
    top_k=3,
)
```

The pipeline does not construct:

```text
LocalQueryEmbedder
PostgresRetriever
DefaultPromptAugmenter
OllamaLLM
```

internally.

---

## Why Dependencies Are Injected

The pipeline's responsibility is:

```text
orchestration
```

It should not also decide:

- which embedding model to use
- which vector database implementation to use
- which prompt augmentation strategy to use
- which LLM provider to use
- where configuration comes from

The separation is:

```text
Composition
├── choose implementations
├── configure implementations
└── create pipeline
        ↓
DefaultRAGPipeline
└── coordinate capabilities
```

This keeps orchestration independent of infrastructure.

---

## Capability Dependencies

The orchestrator depends on:

```text
QueryEmbedder
Retriever
PromptAugmenter
LLM
```

rather than:

```text
LocalQueryEmbedder
PostgresRetriever
DefaultPromptAugmenter
OllamaLLM
```

Therefore the orchestration layer remains compatible with future implementations.

For example:

```text
QueryEmbedder
    ↑
AnotherQueryEmbedder
```

or:

```text
Retriever
    ↑
AnotherRetriever
```

or:

```text
LLM
    ↑
CloudLLM
```

can be composed without changing `DefaultRAGPipeline`.

---

## Retrieval Depth Configuration

The retriever requires:

```text
top_k
```

Two designs were considered.

### Per-Request top_k

```python
pipeline.answer(
    query="What is a vector database?",
    top_k=3,
)
```

This would expose retrieval strategy to every caller.

---

### Pipeline-Level top_k

The selected design is:

```python
pipeline = DefaultRAGPipeline(
    query_embedder=query_embedder,
    retriever=retriever,
    prompt_augmenter=prompt_augmenter,
    llm=llm,
    top_k=3,
)

answer = pipeline.answer(
    "What is a vector database?"
)
```

The caller's concern remains:

```text
question
    ↓
answer
```

The retrieval depth remains pipeline configuration.

---

## Why top_k Is Not a Query Parameter

`top_k` currently represents:

```text
retrieval strategy
```

rather than:

```text
user question data
```

The user asks:

```text
What do vector databases store?
```

The user does not need to know:

```text
retrieve exactly three vector matches
```

Therefore:

```text
top_k
    ↓
pipeline configuration
```

If a future requirement needs per-request retrieval overrides, that capability can be introduced deliberately.

---

## Pipeline Configuration Validation

Because `top_k` belongs to the pipeline configuration, the pipeline validates it during construction.

Invalid values are:

```text
0
negative numbers
```

The rule is:

```text
top_k > 0
```

An invalid pipeline configuration fails immediately:

```text
construct pipeline
    ↓
validate top_k
    ├── valid → pipeline created
    └── invalid → ValueError
```

The pipeline does not wait until a query is answered before discovering that its own configuration is invalid.

---

## Query Validation

The public operation is:

```text
answer(query)
```

Therefore `DefaultRAGPipeline` validates its own input contract.

The pipeline rejects:

```text
empty query
blank query
```

before calling any dependency.

The flow is:

```text
answer(query)
    ↓
validate query
    ├── empty → reject
    ├── blank → reject
    └── valid → begin orchestration
```

---

## Why Pipeline Validation Is Not Delegated

`LocalQueryEmbedder` already validates query input.

However, the pipeline does not rely on that behavior.

The responsibility is:

```text
RAGPipeline
└── validates pipeline input

QueryEmbedder
└── validates embedding input
```

These are separate public boundaries.

A future `QueryEmbedder` implementation should not determine whether `RAGPipeline.answer()` has a valid input contract.

---

## Fail-Fast Validation

Invalid queries are rejected before:

- query embedding
- retrieval
- prompt augmentation
- LLM generation

The tests verify that no dependency is called for invalid input.

The behavior is:

```text
invalid query
    ↓
pipeline validation failure
    ↓
stop
```

rather than:

```text
invalid query
    ↓
partial pipeline execution
```

---

## Error Propagation

`DefaultRAGPipeline` does not introduce a pipeline-specific exception.

Stage-specific failures propagate unchanged.

The behavior is:

```text
QueryEmbedder failure
    ↓
propagate unchanged
```

```text
Retriever failure
    ↓
propagate unchanged
```

```text
PromptAugmenter failure
    ↓
propagate unchanged
```

```text
LLM failure
    ↓
propagate unchanged
```

---

## Why RAGPipelineError Was Not Introduced

An alternative design was:

```text
Any stage failure
    ↓
RAGPipelineError
```

This was rejected for Sprint 10.

The orchestrator does not currently provide:

- retries
- recovery
- fallback behavior
- unified error handling

Wrapping every failure would erase useful stage-specific information without adding application behavior.

For example:

```text
Ollama unavailable
    ↓
LLMGenerationError
```

remains:

```text
LLMGenerationError
```

rather than:

```text
LLMGenerationError
    ↓
RAGPipelineError
```

---

## Exact Failure Preservation

The unit tests verify:

```python
assert exception_info.value is error
```

This proves that `DefaultRAGPipeline` does not:

- catch the exception
- wrap the exception
- replace the exception
- create another exception of the same type

The exact dependency failure escapes unchanged.

---

## Zero Retrieval Results

The pipeline does not stop when the retriever returns:

```text
[]
```

Instead:

```text
No Retrieved Chunks
    ↓
PromptAugmenter
    ↓
AugmentedPrompt with empty context
    ↓
LLM
    ↓
GeneratedAnswer
```

---

## Why the Pipeline Does Not Create a Fallback Answer

A possible alternative was:

```text
No retrieved chunks
    ↓
DefaultRAGPipeline
    ↓
hard-coded GeneratedAnswer
```

This was rejected.

The pipeline is an orchestrator.

It should not introduce a second answer-generation policy.

The existing responsibility chain is:

```text
Retriever
└── returns available evidence

PromptAugmenter
└── constructs the prompt

LLM
└── generates according to the grounding instruction

RAGPipeline
└── coordinates the stages
```

The grounding system instruction already tells the model how to behave when context is insufficient.

---

## Original Query Preservation

The original query is used twice:

```text
query
    ↓
QueryEmbedder
```

and:

```text
query
    ↓
PromptAugmenter
```

The pipeline preserves the original query throughout orchestration.

The flow is:

```text
Original Query
├── embed → Query Embedding
└── augment → Question in AugmentedPrompt
```

The query embedding does not replace the original question.

---

## Data Flow Through the Pipeline

The complete orchestration data flow is:

```text
str
 ↓
QueryEmbedder
 ↓
list[float]
 ↓
Retriever
 ↓
list[RetrievedChunk]
 ↓
PromptAugmenter
 ↓
AugmentedPrompt
 ↓
LLM
 ↓
GeneratedAnswer
```

Each stage receives the output contract of the previous stage.

The original query is also preserved for prompt augmentation.

---

## Orchestration Responsibility

`DefaultRAGPipeline` owns:

- stage ordering
- passing outputs between stages
- preserving the original query
- applying configured `top_k`
- validating pipeline input
- validating pipeline configuration

It does not own:

- embedding generation
- vector similarity search
- context formatting
- model inference
- provider communication
- stage-specific error translation

---

## Unit Testing Strategy

The orchestration tests inject mocked capability abstractions.

The tests do not require:

- sentence-transformer model loading
- PostgreSQL
- pgvector
- Ollama
- GPU access

The unit tests focus only on orchestration behavior.

---

## Happy Path Tests

The tests prove:

```text
query
    ↓
QueryEmbedder receives original query
```

```text
query embedding + configured top_k
    ↓
Retriever
```

```text
original query + retrieved chunks
    ↓
PromptAugmenter
```

```text
AugmentedPrompt
    ↓
LLM
```

```text
GeneratedAnswer
    ↓
returned unchanged
```

---

## Boundary Validation Tests

The tests prove:

- empty queries are rejected
- blank queries are rejected
- dependencies are not called after invalid query input
- zero `top_k` is rejected
- negative `top_k` is rejected

---

## Zero Retrieval Test

The tests prove that:

```text
Retriever
    ↓
[]
```

still continues to:

```text
PromptAugmenter
    ↓
LLM
    ↓
GeneratedAnswer
```

The orchestrator does not create its own fallback path.

---

## Failure Propagation Tests

The tests prove unchanged propagation for failures from:

- `QueryEmbedder`
- `Retriever`
- `PromptAugmenter`
- `LLM`

They also verify that later stages are not called after an earlier stage fails.

For example:

```text
QueryEmbedder failure
    ↓
stop
```

The pipeline does not continue to:

- retrieval
- prompt augmentation
- generation

---

## Real Pipeline Integration Test

Before Sprint 10, the complete real RAG test manually performed:

```text
embed
    ↓
retrieve
    ↓
filter
    ↓
augment
    ↓
generate
```

After Sprint 10, the online path is:

```python
answer = pipeline.answer(query)
```

The real test now proves:

```text
Real Stored Knowledge
    ↓
DefaultRAGPipeline.answer(query)
    ↓
LocalQueryEmbedder
    ↓
PostgresRetriever
    ↓
DefaultPromptAugmenter
    ↓
OllamaLLM
    ↓
qwen3:4b
    ↓
GeneratedAnswer
```

---

## Why Manual Retrieval Filtering Was Removed

The earlier integration test manually filtered retrieval results by test document ID.

That behavior existed outside the real application pipeline.

Once `DefaultRAGPipeline` became the public orchestration boundary, the test was changed to exercise the exact public behavior:

```text
pipeline.answer(query)
```

The integration test no longer performs partial orchestration outside the pipeline.

This ensures the test proves the actual application-level operation.

---

## Test Count

After Sprint 10:

```text
96 tests passing
```

The sprint added:

```text
14 focused orchestration tests
```

The existing complete real RAG test was updated rather than duplicated.

Therefore the final suite proves both:

```text
isolated orchestration semantics
```

and:

```text
real end-to-end orchestration
```

---

## Removal of Empty ingest Package

An existing package was reviewed:

```text
rag_engine/
└── ingest/
    └── __init__.py
```

The package contained:

- no implementation
- no abstraction
- no tests

It was an unused speculative placeholder.

The package was deleted.

---

## Why the Empty Package Was Deleted

The project should create architectural packages when a real capability exists.

The deletion does not mean ingestion orchestration is rejected.

The current ingestion stages remain:

```text
DocumentLoader
    ↓
DocumentChunker
    ↓
ChunkEmbedder
    ↓
VectorStore
```

If ingestion orchestration becomes a real requirement, the boundary should be designed deliberately at that time.

A future capability may become:

```text
IngestionPipeline
    ↑
DefaultIngestionPipeline
```

The project does not keep empty packages in anticipation of possible future architecture.

---

## Current Complete Architecture

The ingestion flow is:

```text
PDF
    ↓
DocumentLoader
    ↓
PdfLoader
    ↓
Document
    ↓
DocumentChunker
    ↓
RecursiveDocumentChunker
    ↓
list[Chunk]
    ↓
ChunkEmbedder
    ↓
LocalChunkEmbedder
    ↓
list[EmbeddedChunk]
    ↓
VectorStore
    ↓
PostgresVectorStore
    ↓
PostgreSQL + pgvector
```

The online RAG flow is now:

```text
User Query
    ↓
RAGPipeline
    ↓
DefaultRAGPipeline
    ↓
QueryEmbedder
    ↓
LocalQueryEmbedder
    ↓
Query Embedding
    ↓
Retriever
    ↓
PostgresRetriever
    ↓
list[RetrievedChunk]
    ↓
PromptAugmenter
    ↓
DefaultPromptAugmenter
    ↓
AugmentedPrompt
    ↓
LLM
    ↓
OllamaLLM
    ↓
Ollama
    ↓
qwen3:4b
    ↓
GeneratedAnswer
```

---

## Public Online Application Flow

Before Sprint 10:

```text
Caller
├── embed query
├── retrieve chunks
├── augment prompt
├── generate answer
└── coordinate data flow
```

After Sprint 10:

```text
Caller
    ↓
RAGPipeline.answer(query)
    ↓
GeneratedAnswer
```

The application now has one complete online RAG capability.

---

## Architectural Boundaries

The project now exposes:

```text
DocumentLoader
DocumentChunker
ChunkEmbedder
VectorStore
QueryEmbedder
Retriever
PromptAugmenter
LLM
RAGPipeline
```

The concrete implementations are:

```text
DocumentLoader
    ↑
PdfLoader

DocumentChunker
    ↑
RecursiveDocumentChunker

ChunkEmbedder
    ↑
LocalChunkEmbedder

VectorStore
    ↑
PostgresVectorStore

QueryEmbedder
    ↑
LocalQueryEmbedder

Retriever
    ↑
PostgresRetriever

PromptAugmenter
    ↑
DefaultPromptAugmenter

LLM
    ↑
OllamaLLM

RAGPipeline
    ↑
DefaultRAGPipeline
```

---

## Key Learning Outcomes

This sprint established the following concepts:

- working pipeline stages still require an application-level orchestration boundary
- orchestration should coordinate capabilities without taking over their responsibilities
- a RAG pipeline is a more precise abstraction than a generic service for a fixed RAG sequence
- application callers should not manually coordinate internal pipeline stages
- retrieval strategy configuration does not automatically belong in the public query operation
- pipeline configuration should be validated at construction time
- public pipeline input should be validated at the pipeline boundary
- validation at multiple public boundaries can be intentional rather than accidental duplication
- orchestration dependencies should be injected as capability abstractions
- orchestrators should not construct infrastructure implementations
- stage-specific failures should not be wrapped without a concrete recovery requirement
- exact exception preservation can be tested explicitly
- zero retrieval results should continue through existing domain policies rather than create orchestration-specific answer behavior
- real integration tests should exercise the same public boundary used by application callers
- speculative empty packages should be removed until a real capability exists

---

## Sprint Outcome

Sprint 10 successfully introduced the application-level RAG orchestration boundary.

The system can now:

1. receive a user query
2. validate the query
3. generate a query embedding
4. retrieve the configured number of relevant chunks
5. preserve the original question
6. construct an augmented prompt
7. generate an answer through the configured LLM
8. return the final `GeneratedAnswer`

The public online flow is now:

```text
User Query
    ↓
RAGPipeline.answer()
    ↓
GeneratedAnswer
```

The core RAG engine no longer requires callers to manually coordinate the online stages.

The next stage should expose this completed application capability through an API boundary.