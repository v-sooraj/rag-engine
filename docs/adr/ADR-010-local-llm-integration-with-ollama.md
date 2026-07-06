# ADR-010: Integrate a Local LLM Through Ollama Using Direct HTTP

## Status

Accepted

## Context

The prompt augmentation stage produces:

```text
AugmentedPrompt
├── system_instruction
├── context
└── question
```

The RAG engine requires a generation stage that transforms this structured prompt into an answer.

The system must decide:

- whether generation should return a plain string or domain model
- what the LLM abstraction should accept
- whether to use a cloud or local model
- whether the model should run inside the application process
- which local inference runtime to use
- whether to use a provider SDK or direct HTTP
- how prompt fields should map to model messages
- whether generation should be synchronous or asynchronous
- whether responses should stream
- how infrastructure failures should cross the LLM boundary
- how model configuration should be managed

These decisions define the boundary between the RAG application and model inference infrastructure.

---

## Decision

Introduce a provider-independent LLM capability:

```text
LLM

AugmentedPrompt
    ↓
generate
    ↓
GeneratedAnswer
```

Represent generated output using an immutable domain model:

```text
GeneratedAnswer
└── content
```

Implement the first concrete LLM integration using:

```text
OllamaLLM
```

Communicate with Ollama through direct HTTP using:

```text
httpx
```

Run:

```text
qwen3:4b
```

as the initial local model.

Map:

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

Use:

```text
synchronous generation
+
non-streaming responses
+
configurable timeout
```

Translate infrastructure and response failures into:

```text
LLMGenerationError
```

---

## Decision Drivers

The decision is based on the following requirements:

- preserve a clean application domain
- keep the LLM boundary independent of providers
- compose directly with `AugmentedPrompt`
- avoid cloud API quota and cost dependencies
- keep model runtime concerns outside the application process
- make HTTP integration visible for learning
- support real local end-to-end RAG testing
- keep the initial generation contract simple
- avoid premature streaming and async complexity
- prevent HTTP client exceptions from leaking into application code

---

## Considered Generated Output Designs

### Option A — Plain String

```text
LLM
 ↓
str
```

Advantages:

- simple
- minimal code

Disadvantages:

- reduces a meaningful pipeline result to a primitive
- limits future domain evolution
- is inconsistent with the project's existing pipeline modeling

This option was rejected.

---

### Option B — GeneratedAnswer Domain Model

```text
LLM
 ↓
GeneratedAnswer
└── content
```

Advantages:

- preserves a meaningful domain boundary
- remains extensible
- supports validation
- supports immutability
- remains consistent with existing architecture

This option was selected.

---

## Why GeneratedAnswer Is Minimal

The selected model contains:

```text
content
```

It does not yet contain:

```text
model
input_tokens
output_tokens
duration
provider
```

These fields may become useful later for observability.

The current application requirement is generation of an answer.

Infrastructure metadata should not be added before the application has a concrete use for it.

---

## Considered LLM Interfaces

### Option A — Provider-Shaped Parameters

```python
generate(
    system_instruction,
    context,
    question,
)
```

Advantages:

- simple concrete implementation

Disadvantages:

- forces the caller to dismantle `AugmentedPrompt`
- weakens pipeline composition
- exposes prompt structure as separate method parameters

This option was rejected.

---

### Option B — Domain-Shaped Interface

```python
generate(
    prompt: AugmentedPrompt,
) -> GeneratedAnswer
```

Advantages:

- direct pipeline composition
- preserves the Sprint 8 domain boundary
- keeps provider mapping inside concrete implementations

This option was selected.

---

## LLM Abstraction

The selected abstraction is:

```python
class LLM(ABC):

    @abstractmethod
    def generate(
        self,
        prompt: AugmentedPrompt,
    ) -> GeneratedAnswer:
        pass
```

The application depends on:

```text
LLM
```

rather than:

```text
Ollama
```

The concrete infrastructure implementation is:

```text
OllamaLLM
```

---

## Considered Model Strategies

### Option A — Cloud API Model

```text
RAG Engine
    ↓
Cloud Provider API
    ↓
Hosted Model
```

Advantages:

- no local model hardware requirements
- scalable managed infrastructure
- access to larger models

Disadvantages:

- API quota dependency
- network dependency
- usage cost
- external credentials
- reduced local reproducibility

This option was not selected for the initial implementation.

---

### Option B — Local Model

```text
RAG Engine
    ↓
Local Inference
    ↓
Local Model
```

Advantages:

- no API quota
- no per-request cost
- local experimentation
- complete end-to-end control
- offline model inference after installation

This option was selected.

---

## Considered Local Execution Strategies

### Option A — Load Model Inside Python

```text
RAG Engine Process
    ↓
Model Library
    ↓
Model
```

Advantages:

- direct model control
- no HTTP boundary

Disadvantages:

- application owns model loading
- application owns GPU configuration
- application owns quantization concerns
- application process becomes tightly coupled to inference runtime

This option was rejected.

---

### Option B — Separate Inference Server

```text
RAG Engine
    ↓
HTTP
    ↓
Inference Server
    ↓
Model
```

Advantages:

- separates application and inference concerns
- isolates model runtime configuration
- resembles production model-serving architecture
- allows model changes without embedding runtime logic in the application

This option was selected.

---

## Why Ollama Was Selected

Ollama provides:

- local model management
- local model serving
- HTTP API access
- GPU-backed inference support
- simple local development workflow

The architecture becomes:

```text
RAG Engine
    ↓
OllamaLLM
    ↓
HTTP
    ↓
Ollama
    ↓
qwen3:4b
```

The RAG application does not manage:

- model files
- quantization format
- GPU layers
- model loading
- inference runtime internals

---

## Why the Concrete Class Is Named OllamaLLM

The implementation is named:

```text
OllamaLLM
```

rather than:

```text
LocalLLM
```

`LocalLLM` describes deployment location.

`OllamaLLM` identifies the actual infrastructure implementation.

A future implementation could introduce:

```text
LlamaCppLLM
```

or another local runtime without naming ambiguity.

---

## Model Selection

The initial model is:

```text
qwen3:4b
```

The development environment has:

```text
16 GB RAM
NVIDIA GTX 1660
AMD Ryzen 5
```

A small instruct model provides a practical balance for:

- local inference
- RAG question answering
- complete integration testing

Larger models are not required to prove the architecture.

---

## Configurable Infrastructure

The following values are external configuration:

```text
OLLAMA_BASE_URL
OLLAMA_MODEL_NAME
OLLAMA_TIMEOUT_SECONDS
```

The application receives:

```text
settings.ollama.base_url
settings.ollama.model_name
settings.ollama.timeout_seconds
```

This allows infrastructure changes without application code changes.

---

## Considered Integration Approaches

### Option A — Ollama Python SDK

```text
OllamaLLM
    ↓
Ollama SDK
    ↓
Ollama
```

Advantages:

- less manual request construction
- provider convenience methods

Disadvantages:

- hides the HTTP boundary
- introduces provider-specific client dependency
- reduces visibility into request and response mapping

This option was rejected.

---

### Option B — Direct HTTP with httpx

```text
OllamaLLM
    ↓
httpx
    ↓
Ollama API
```

Advantages:

- explicit request mapping
- explicit response mapping
- direct visibility into the infrastructure boundary
- no provider-specific Python SDK
- straightforward client mocking

This option was selected.

---

## Prompt-to-Message Mapping

The structured prompt is:

```text
AugmentedPrompt
├── system_instruction
├── context
└── question
```

The selected mapping is:

```text
system_instruction
    ↓
system role
```

and:

```text
context + question
    ↓
user role
```

---

## Why Context Is Not a System Message

The system instruction represents trusted application behavior.

Retrieved context represents external evidence.

Therefore:

```text
trusted application instruction
    ↓
system message
```

while:

```text
retrieved evidence
    ↓
user message
```

The application does not elevate retrieved content to the trusted instruction boundary.

---

## User Message Format

The selected user message format is:

```text
Context:
{prompt.context}

Question:
{prompt.question}
```

This preserves:

- explicit context
- explicit question
- the context boundaries created during prompt augmentation

---

## Considered Execution Models

### Option A — Synchronous

```text
generate()
    ↓
wait
    ↓
GeneratedAnswer
```

Advantages:

- matches the existing pipeline
- simple abstraction
- simple tests
- no current async consumer required

This option was selected.

---

### Option B — Asynchronous

```text
async generate()
    ↓
await
    ↓
GeneratedAnswer
```

Advantages:

- useful for future concurrent APIs

Disadvantages:

- introduces async before FastAPI exists
- changes the pipeline programming model without a current requirement

This option was deferred.

---

## Timeout Decision

Model inference is slower than typical service-to-service HTTP calls.

The request therefore uses a configurable timeout.

The current configuration is:

```text
OLLAMA_TIMEOUT_SECONDS=300
```

This accommodates:

- model cold starts
- local hardware variability
- generation latency

while preventing indefinite waiting.

---

## Considered Response Modes

### Option A — Non-Streaming

```text
request
    ↓
complete generation
    ↓
one response
    ↓
GeneratedAnswer
```

This option was selected.

---

### Option B — Streaming

```text
request
    ↓
token chunks
    ↓
incremental consumer
```

Streaming would require a different abstraction such as:

```text
Iterator[str]
```

or:

```text
AsyncIterator[str]
```

The application does not yet have a streaming consumer.

This option was deferred.

---

## Error Boundary

The selected application-level exception is:

```text
LLMGenerationError
```

The generation contract is:

```text
generate()
├── GeneratedAnswer
└── LLMGenerationError
```

---

## Why Infrastructure Exceptions Are Translated

The concrete implementation may encounter:

```text
httpx.ConnectError
httpx.ReadTimeout
httpx.HTTPStatusError
```

These exceptions belong to the HTTP implementation.

Allowing them to escape would couple callers to:

```text
httpx
```

Instead:

```text
infrastructure failure
    ↓
LLMGenerationError
```

The application depends on the LLM capability rather than the transport library.

---

## Why One Exception Type Is Used

The current caller does not have different recovery strategies for:

- connection failures
- timeouts
- server failures
- malformed responses

Therefore one exception type is sufficient.

More specific exceptions should be introduced only when application behavior requires different handling.

---

## Exception Chaining

The original exception is preserved:

```python
raise LLMGenerationError(
    "failed to generate answer"
) from error
```

This provides:

```text
stable application exception
    +
original debugging cause
```

---

## Response Validation

The Ollama response must contain:

```text
message.content
```

The content must be:

```text
string
+
non-empty
+
non-blank
```

Invalid responses are translated into:

```text
LLMGenerationError
```

Malformed infrastructure responses do not enter the application domain.

---

## Testing Decision

The implementation uses two levels of testing.

### Mocked HTTP Tests

These verify:

- request construction
- message mapping
- model configuration
- timeout configuration
- endpoint construction
- non-streaming mode
- response mapping
- error translation

---

### Real Integration Tests

These verify:

```text
OllamaLLM
    ↓
real Ollama
    ↓
real qwen3:4b
    ↓
GeneratedAnswer
```

and:

```text
stored knowledge
    ↓
retrieval
    ↓
prompt augmentation
    ↓
real local generation
    ↓
GeneratedAnswer
```

---

## Why Exact LLM Output Is Not Asserted

Generated wording may vary.

The real integration tests verify:

```text
valid input
    ↓
successful real inference
    ↓
valid non-empty output
```

They do not verify one exact answer string.

Answer correctness and grounding quality belong to a future evaluation capability.

---

## Consequences

### Positive

- complete RAG pipeline runs locally
- no cloud API quota is required
- application remains provider-independent
- model runtime concerns remain outside the Python process
- prompt structure composes directly across pipeline stages
- HTTP integration remains explicit
- infrastructure failures do not leak through the application boundary
- real end-to-end testing is possible

### Negative

- local inference requires Ollama installation
- the configured model must be downloaded
- real integration tests depend on local infrastructure
- generation latency depends on development hardware
- synchronous generation blocks the calling thread

### Neutral

The current implementation does not support streaming.

Streaming can be introduced later as a separate capability when an API or UI requires incremental output.

---

## Future Considerations

Future versions may introduce:

- additional LLM implementations
- cloud providers
- async generation
- streaming generation
- token usage metadata
- model metadata
- retry policies
- fallback models
- generation metrics
- answer evaluation
- source citations

These changes do not alter the current provider-independent LLM boundary.

---

## Final Decision

Use a provider-independent `LLM` abstraction that accepts `AugmentedPrompt` and returns an immutable `GeneratedAnswer`.

Implement the first concrete provider as `OllamaLLM`.

Run `qwen3:4b` through a separate local Ollama inference server.

Integrate through direct synchronous HTTP using `httpx`, use non-streaming responses with a configurable timeout, map trusted instructions to the system role and retrieved evidence plus the question to the user role, and translate infrastructure failures into `LLMGenerationError`.