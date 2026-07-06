# Sprint 09 — LLM Integration

## Status

Completed

## Objective

Implement the LLM generation stage of the RAG pipeline.

The LLM integration stage transforms a structured augmented prompt into a generated answer using a local language model.

This sprint extends the pipeline from:

```text
User Query
 ↓
Query Embedding
 ↓
Semantic Retrieval
 ↓
Prompt Augmentation
 ↓
AugmentedPrompt
```

to:

```text
User Query
 ↓
Query Embedding
 ↓
Semantic Retrieval
 ↓
Prompt Augmentation
 ↓
AugmentedPrompt
 ↓
LLM
 ↓
GeneratedAnswer
```

The system now supports the complete RAG flow from stored knowledge and a user question to a locally generated answer.

---

## Scope

The sprint includes:

- immutable generated answer domain model
- provider-independent LLM abstraction
- Ollama-based LLM implementation
- direct HTTP integration using `httpx`
- structured prompt-to-message mapping
- configurable Ollama base URL
- configurable model name
- configurable generation timeout
- synchronous generation
- non-streaming responses
- LLM-specific error boundary
- infrastructure exception translation
- response validation
- mocked HTTP unit tests
- real Ollama integration test
- complete real RAG generation pipeline test

The sprint does not include:

- streaming generation
- asynchronous generation
- cloud LLM providers
- multiple LLM implementations
- token usage tracking
- model metadata in generated answers
- retry logic
- fallback models
- generation caching
- answer citations
- RAG evaluation
- hallucination scoring
- prompt versioning
- RAG orchestration
- FastAPI endpoints
- observability

These concerns belong to later stages.

---

## Pipeline Position

Before this sprint, the online RAG pipeline ended with:

```text
User Query
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
```

After this sprint, the pipeline continues into generation:

```text
User Query
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

The RAG engine now has four major pipeline sections:

```text
INGESTION
    ↓
Stored Knowledge

RETRIEVAL
    ↓
Relevant Knowledge

PROMPT AUGMENTATION
    ↓
Structured LLM Input

GENERATION
    ↓
Generated Answer
```

---

## Package Structure

```text
rag_engine/
└── llm/
    ├── __init__.py
    ├── generated_answer.py
    ├── llm.py
    ├── llm_generation_error.py
    └── ollama_llm.py
```

Test structure:

```text
tests/
└── llm/
    ├── __init__.py
    ├── test_generated_answer.py
    ├── test_ollama_llm.py
    ├── test_ollama_llm_integration.py
    └── test_llm_generation_pipeline.py
```

---

## Generation Boundary

The LLM capability receives:

```text
AugmentedPrompt
```

and returns:

```text
GeneratedAnswer
```

The abstraction is:

```python
class LLM(ABC):

    @abstractmethod
    def generate(
        self,
        prompt: AugmentedPrompt,
    ) -> GeneratedAnswer:
        pass
```

The pipeline boundary is:

```text
PromptAugmenter
    ↓
AugmentedPrompt
    ↓
LLM
    ↓
GeneratedAnswer
```

The abstraction does not expose:

- Ollama
- HTTP
- `httpx`
- model server endpoints
- request payloads
- provider response formats

These concerns belong to concrete LLM implementations.

---

## Why LLM Generation Is a Separate Capability

Prompt augmentation answers:

```text
What structured information should the model receive?
```

LLM generation answers:

```text
How is that structured information sent to a model to generate an answer?
```

These are different responsibilities.

The boundary remains:

```text
DefaultPromptAugmenter
    ↓
AugmentedPrompt
    ↓
LLM
    ↓
GeneratedAnswer
```

The prompt augmenter does not know:

- which model is used
- where the model runs
- which protocol is used
- which provider serves the model

The LLM implementation does not know:

- how retrieval was performed
- how similarity was calculated
- where chunks were stored
- how context was selected

---

## Generated Answer Domain Model

Two output designs were considered.

### Plain String

```text
LLM
 ↓
str
```

This is simple but collapses the generation result into a primitive immediately.

---

### Structured Generated Answer

The selected design uses:

```python
class GeneratedAnswer(BaseModel):
    model_config = ConfigDict(frozen=True)

    content: str = Field(min_length=1)
```

The generation boundary becomes:

```text
LLM
 ↓
GeneratedAnswer
└── content
```

This follows the architecture established throughout the project:

```text
meaningful pipeline output
    ↓
domain model
```

rather than:

```text
meaningful pipeline output
    ↓
primitive value
```

---

## Why GeneratedAnswer Contains Only Content

The initial domain model contains:

```text
GeneratedAnswer
└── content
```

It does not currently contain:

- model name
- input token count
- output token count
- generation duration
- provider name

These values may become useful for:

- observability
- cost tracking
- performance analysis
- evaluation

However, the current generation capability only requires the generated content.

Adding provider metadata immediately would shape the domain model around infrastructure concerns before the application has a concrete requirement for them.

---

## Immutability

`GeneratedAnswer` is immutable.

Once generation completes:

```text
GeneratedAnswer
```

represents the exact output of the generation stage.

Later stages should consume the answer rather than mutate it.

This remains consistent with the project's immutable pipeline models:

```text
Document
 ↓
Chunk
 ↓
EmbeddedChunk
 ↓
RetrievedChunk
 ↓
AugmentedPrompt
 ↓
GeneratedAnswer
```

---

## Domain-Shaped LLM Interface

Two LLM interface designs were considered.

### Provider-Shaped Interface

```python
def generate(
    system_instruction: str,
    context: str,
    question: str,
) -> GeneratedAnswer:
```

This would require callers to unpack `AugmentedPrompt`.

---

### Domain-Shaped Interface

The selected interface is:

```python
def generate(
    prompt: AugmentedPrompt,
) -> GeneratedAnswer:
```

This preserves direct composition between pipeline stages:

```text
PromptAugmenter
    ↓
AugmentedPrompt
    ↓
LLM
    ↓
GeneratedAnswer
```

The output contract of Sprint 8 becomes the input contract of Sprint 9.

---

## Why AugmentedPrompt Is Passed Directly

Sprint 8 deliberately preserved:

```text
AugmentedPrompt
├── system_instruction
├── context
└── question
```

Immediately unpacking this structure at the next application boundary would weaken the domain model.

Instead:

```text
application pipeline
    ↓
passes AugmentedPrompt
    ↓
concrete LLM implementation
    ↓
maps to provider-specific format
```

The infrastructure implementation owns the translation.

---

## Local Model Strategy

Two model execution strategies were considered.

### Model Loaded Inside the Python Process

```text
RAG Engine
    ↓
Model Runtime
    ↓
Local Model
```

This would make the application process responsible for:

- model loading
- quantization
- GPU configuration
- VRAM management
- inference runtime configuration

---

### Separate Local Inference Server

The selected architecture is:

```text
RAG Engine
    ↓
HTTP
    ↓
Local Inference Server
    ↓
Local Model
```

This separates application concerns from model-serving concerns.

The RAG engine owns:

- prompt mapping
- request construction
- response validation
- error translation

The inference runtime owns:

- model download
- model loading
- GPU utilization
- quantization details
- inference execution

---

## Ollama Runtime

Ollama was selected as the first local inference runtime.

The concrete architecture is:

```text
AugmentedPrompt
    ↓
LLM
    ↓
OllamaLLM
    ↓
HTTP
    ↓
Ollama
    ↓
qwen3:4b
    ↓
GeneratedAnswer
```

The concrete implementation is named:

```text
OllamaLLM
```

rather than:

```text
LocalLLM
```

because the class name should identify the actual infrastructure implementation.

A future local runtime could introduce another implementation without ambiguity.

---

## Model Selection

The selected model is:

```text
qwen3:4b
```

The development machine has:

```text
RAM
└── 16 GB

GPU
└── NVIDIA GTX 1660

CPU
└── AMD Ryzen 5
```

A small instruct model is a practical fit for:

- local development
- grounded question answering
- complete RAG pipeline testing
- avoiding cloud API dependency

The model is served by Ollama rather than loaded directly by the RAG engine.

---

## Configurable Model Infrastructure

The following values are configurable:

```text
OLLAMA_BASE_URL
OLLAMA_MODEL_NAME
OLLAMA_TIMEOUT_SECONDS
```

They map to:

```text
settings.ollama.base_url
settings.ollama.model_name
settings.ollama.timeout_seconds
```

The configuration model is:

```python
class OllamaSettings(BaseModel):
    base_url: str
    model_name: str
    timeout_seconds: float
```

The selected defaults are:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_NAME=qwen3:4b
OLLAMA_TIMEOUT_SECONDS=300
```

---

## Why Model Configuration Is External

The model name is infrastructure configuration.

The application should be able to change:

```text
qwen3:4b
```

to another compatible model without changing application code.

The same principle applies to:

- Ollama server location
- generation timeout

Therefore:

```text
infrastructure values
    ↓
configuration
```

rather than:

```text
infrastructure values
    ↓
hard-coded application logic
```

---

## Structured Prompt Mapping

The `AugmentedPrompt` contains:

```text
AugmentedPrompt
├── system_instruction
├── context
└── question
```

`OllamaLLM` maps this to chat messages.

The mapping is:

```text
system_instruction
    ↓
system message
```

and:

```text
context + question
    ↓
user message
```

The request conceptually becomes:

```text
messages
├── system
│   └── system_instruction
│
└── user
    ├── context
    └── question
```

---

## System Message Mapping

The system instruction becomes:

```text
role = system
content = prompt.system_instruction
```

This represents trusted application behavior.

For example:

```text
Answer the question using only the provided context.
If the context does not contain enough information to answer the question,
say that you do not have enough information.
```

---

## User Message Mapping

Retrieved context and the original question become one user message:

```text
Context:
{context}

Question:
{question}
```

Example:

```text
Context:
[CONTEXT 1]
Vector databases store numerical embeddings.

Question:
What do vector databases store?
```

---

## Why Retrieved Context Is Not a System Message

Retrieved content is evidence.

It is not trusted application instruction.

The boundary is:

```text
Application behavior
    ↓
system message
```

and:

```text
Retrieved evidence
    ↓
user message
```

This preserves the distinction created by the structured `AugmentedPrompt`.

---

## Direct HTTP Integration

Two integration approaches were considered.

### Ollama Python SDK

```text
OllamaLLM
    ↓
Ollama SDK
    ↓
Ollama
```

This would reduce direct protocol visibility.

---

### Direct HTTP

The selected design is:

```text
OllamaLLM
    ↓
httpx
    ↓
Ollama HTTP API
```

The request path is:

```text
POST /api/chat
```

This keeps the complete infrastructure boundary visible:

```text
AugmentedPrompt
    ↓
request payload
    ↓
HTTP request
    ↓
response validation
    ↓
GeneratedAnswer
```

---

## Why httpx Is Used

`httpx` provides the HTTP client capability required by `OllamaLLM`.

The RAG engine does not introduce a custom abstraction such as:

```text
HttpClient
```

because no application requirement currently needs one.

The concrete infrastructure implementation depends directly on the HTTP client library.

---

## HTTP Client Injection

`OllamaLLM` supports an injected `httpx.Client`.

Conceptually:

```text
Production
    ↓
real HTTP client
```

and:

```text
Unit Tests
    ↓
mock HTTP client
```

This makes request construction and response handling independently testable without calling the real model.

The application does not introduce a separate mock LLM implementation merely to test HTTP mapping.

---

## Synchronous Generation

Generation is synchronous.

The interface remains:

```python
def generate(
    self,
    prompt: AugmentedPrompt,
) -> GeneratedAnswer:
```

The execution flow is:

```text
generate()
    ↓
HTTP request
    ↓
model inference
    ↓
complete response
    ↓
GeneratedAnswer
```

---

## Why Async Was Not Introduced

The current pipeline is synchronous:

```text
load()
 ↓
chunk()
 ↓
embed()
 ↓
store()
 ↓
retrieve()
 ↓
augment()
 ↓
generate()
```

The project does not yet have:

- FastAPI endpoints
- concurrent request handling
- async orchestration

Introducing async now would make the entire generation boundary asynchronous before a concrete consumer requires it.

The concurrency model can be revisited when the API layer is introduced.

---

## Explicit Timeout

Local model inference may take significantly longer than a normal REST call.

Therefore the implementation uses an explicit configurable timeout:

```text
OLLAMA_TIMEOUT_SECONDS
```

The current value is:

```text
300
```

This allows:

- model cold starts
- local hardware variability
- slower generation

while still preventing indefinite waiting.

---

## Non-Streaming Generation

The Ollama request explicitly uses:

```text
stream = false
```

The current capability is:

```text
AugmentedPrompt
    ↓
generate
    ↓
complete GeneratedAnswer
```

It is not:

```text
AugmentedPrompt
    ↓
stream of tokens
```

---

## Why Streaming Is Deferred

Streaming would change the abstraction.

The current contract is:

```python
generate(...) -> GeneratedAnswer
```

A streaming contract would require something closer to:

```text
generate(...)
    ↓
Iterator[str]
```

or:

```text
AsyncIterator[str]
```

That is a different capability.

Streaming will become meaningful when an API or UI exists to consume incremental output.

---

## Ollama Request Payload

The generated request contains:

```text
model
messages
stream
```

Conceptually:

```python
{
    "model": configured_model,
    "messages": [
        {
            "role": "system",
            "content": system_instruction,
        },
        {
            "role": "user",
            "content": formatted_context_and_question,
        },
    ],
    "stream": False,
}
```

The payload construction belongs entirely to `OllamaLLM`.

---

## Response Mapping

The Ollama response is expected to contain:

```text
message
└── content
```

The mapping is:

```text
Ollama response
    ↓
message.content
    ↓
validation
    ↓
GeneratedAnswer.content
```

The application domain does not expose the raw Ollama response.

---

## Response Validation

The implementation rejects:

- missing `message`
- missing `content`
- non-string content
- empty content
- blank content

Valid content becomes:

```text
GeneratedAnswer
└── content
```

This prevents malformed infrastructure responses from crossing into the application domain.

---

## LLM Error Boundary

A dedicated exception is introduced:

```python
class LLMGenerationError(Exception):
    pass
```

The public generation boundary is:

```text
LLM.generate()
├── success → GeneratedAnswer
└── failure → LLMGenerationError
```

---

## Why HTTP Exceptions Do Not Leak

Without translation, callers could receive:

- `httpx.ConnectError`
- `httpx.ReadTimeout`
- `httpx.HTTPStatusError`

These are implementation details of the concrete HTTP integration.

Instead:

```text
HTTP failure
Timeout
Non-success response
Malformed response
Invalid generated content
        ↓
LLMGenerationError
```

The application depends on the LLM capability rather than the HTTP client library.

---

## Preserving Original Failure Causes

Infrastructure failures are translated using exception chaining:

```python
raise LLMGenerationError(
    "failed to generate answer"
) from error
```

The caller receives a stable application-level exception.

Debugging still retains the original infrastructure cause.

This provides:

```text
clean boundary
    +
root-cause visibility
```

---

## Why One Exception Type Is Enough

Sprint 9 introduces only:

```text
LLMGenerationError
```

It does not introduce:

```text
LLMConnectionError
LLMTimeoutError
LLMResponseError
LLMEmptyAnswerError
```

The application currently has no different recovery behavior for these failures.

More specific exception types should be introduced only when callers need different handling strategies.

---

## Unit Testing Strategy

The mocked HTTP tests verify:

- a generated answer is returned
- system instruction maps to the system message
- context and question map to the user message
- configured model name is used
- streaming is disabled
- the correct Ollama endpoint is called
- configured timeout is used
- trailing base URL slashes are handled
- connection failures are translated
- timeouts are translated
- HTTP status failures are translated
- missing messages are rejected
- missing content is rejected
- non-string content is rejected
- empty content is rejected
- blank content is rejected

These tests do not require:

- Ollama
- a downloaded model
- GPU availability

---

## Generated Answer Domain Tests

Domain model tests verify:

- valid answers can be created
- empty answers are rejected
- answers are immutable

---

## Real Ollama Integration Test

The real infrastructure test proves:

```text
AugmentedPrompt
    ↓
OllamaLLM
    ↓
Real HTTP Request
    ↓
Ollama
    ↓
qwen3:4b
    ↓
GeneratedAnswer
```

The test uses:

- a real running Ollama server
- the real configured model
- real local inference
- real response mapping

The test verifies that a non-empty generated answer is returned.

---

## Why Exact Generated Text Is Not Asserted

LLM generation is non-deterministic.

The integration test does not assert:

```text
generated answer
    =
one exact sentence
```

Instead, it verifies the infrastructure contract:

```text
valid structured prompt
    ↓
real model generation
    ↓
valid non-empty GeneratedAnswer
```

Exact answer quality belongs to RAG evaluation rather than infrastructure integration testing.

---

## Complete Real RAG Generation Test

The final Sprint 9 pipeline test proves:

```text
Test Knowledge
    ↓
Chunk
    ↓
LocalChunkEmbedder
    ↓
384-dimensional Embedding
    ↓
PostgresVectorStore
    ↓
PostgreSQL + pgvector

User Query
    ↓
LocalQueryEmbedder
    ↓
384-dimensional Query Embedding
    ↓
PostgresRetriever
    ↓
Top-K Retrieved Chunks
    ↓
DefaultPromptAugmenter
    ↓
AugmentedPrompt
    ↓
OllamaLLM
    ↓
Ollama
    ↓
qwen3:4b
    ↓
GeneratedAnswer
```

The test uses real:

- sentence-transformer embeddings
- PostgreSQL persistence
- pgvector similarity search
- prompt augmentation
- HTTP communication
- Ollama inference
- local LLM generation

---

## Integration Test Cleanup

The complete pipeline test creates temporary test knowledge.

The test uses:

```text
try
    ↓
retrieve
    ↓
augment
    ↓
generate

finally
    ↓
delete test document
```

Because chunks reference documents with:

```text
ON DELETE CASCADE
```

deleting the test document also removes its test chunks.

This keeps the real database clean after the integration test.

---

## Current Complete Architecture

The ingestion pipeline is:

```text
PDF File
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

The online RAG pipeline is:

```text
User Query
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

Together:

```text
                         INGESTION

PDF
 ↓
Document
 ↓
Chunks
 ↓
Chunk Embeddings
 ↓
PostgreSQL + pgvector
 ↑
 │
 │ Cosine-Distance Search
 │
Query Embedding
 ↑
User Query

                         RETRIEVAL
                              ↓
                      Retrieved Chunks
                              ↓
                      Prompt Augmenter

                    PROMPT AUGMENTATION
                              ↓
                       AugmentedPrompt
                              ↓
                             LLM

                         GENERATION
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

## Key Learning Outcomes

This sprint established the following concepts:

- LLM generation is a separate RAG pipeline capability
- meaningful generation output should use a domain model rather than a primitive
- prompt augmentation output should compose directly with the LLM input boundary
- provider-specific mapping belongs inside concrete LLM implementations
- local model serving should remain separate from the application process
- inference runtime concerns should not leak into the RAG engine
- infrastructure configuration should remain external
- trusted system instructions and retrieved evidence belong to different message boundaries
- retrieved context should not be promoted to system instructions
- direct HTTP integration makes provider boundaries explicit
- HTTP clients can be injected for focused infrastructure unit testing
- synchronous generation is sufficient until a concrete async consumer exists
- streaming should not be added before the application has a streaming boundary
- model inference requires explicit timeout handling
- infrastructure-specific exceptions should not leak through application capabilities
- exception chaining preserves root-cause visibility
- malformed provider responses must be validated before entering the application domain
- real integration tests should verify infrastructure contracts without asserting exact non-deterministic model wording
- complete pipeline tests prove architectural composition across real components

---

## Sprint Outcome

Sprint 09 successfully completed the LLM integration stage.

The system can now:

1. receive an immutable `AugmentedPrompt`
2. map the system instruction to a system message
3. map retrieved context and the user question to a user message
4. construct an Ollama chat request
5. call a local model through HTTP
6. wait for a complete non-streaming response
7. validate the model response
8. translate infrastructure failures into `LLMGenerationError`
9. return an immutable `GeneratedAnswer`
10. execute the complete real RAG pipeline from stored knowledge to generated answer

The RAG engine can now:

```text
store knowledge
    ↓
retrieve relevant knowledge
    ↓
construct grounded model input
    ↓
generate an answer locally
```

The core RAG pipeline is now complete.

The next stage should introduce orchestration so the complete online pipeline can be invoked through one application-level capability instead of manually composing each stage.