# ADR-009: Use Structured Prompt Augmentation with Explicit Context Boundaries

## Status

Accepted

## Context

The retrieval pipeline produces:

```text
User Query
        +
list[RetrievedChunk]
```

The future LLM generation stage requires:

- behavioral instructions
- retrieved evidence
- the original user question

The system must decide:

- whether prompt augmentation should return a plain string or structured domain model
- whether context construction requires a separate abstraction
- how retrieved chunks should be represented in the context
- whether retrieval ranking should be preserved
- whether retrieval metadata should be included in the prompt
- how empty retrieval results should be handled
- whether the system instruction should be configurable

These decisions define the boundary between retrieval and generation.

---

## Decision

Introduce a dedicated prompt augmentation capability:

```text
PromptAugmenter

query + list[RetrievedChunk]
        ↓
AugmentedPrompt
```

Represent the output using an immutable structured domain model:

```text
AugmentedPrompt
├── system_instruction
├── context
└── question
```

Use a fixed grounding instruction for the current RAG behavior.

Build context directly inside `DefaultPromptAugmenter`.

Preserve retrieval ranking order.

Represent each retrieved chunk using explicit numbered boundaries:

```text
[CONTEXT 1]
...

[CONTEXT 2]
...
```

Include only retrieved chunk content in the prompt.

Allow empty retrieval results to produce an empty context.

Reject empty or blank queries.

---

## Decision Drivers

The decision is based on the following requirements:

- preserve meaningful prompt structure
- keep prompt augmentation independent of LLM providers
- keep retrieval and generation boundaries separate
- preserve retrieved evidence boundaries
- preserve relevance ranking
- avoid unnecessary prompt noise
- avoid premature abstractions
- support valid empty retrieval outcomes
- keep the future LLM layer free to choose provider-specific message formats

---

## Considered Output Designs

### Option A — Return a Plain String

```text
instructions
+
context
+
question
    ↓
str
```

Advantages:

- simple
- directly usable by text-completion models
- minimal domain modeling

Disadvantages:

- collapses meaningful concepts into one opaque value
- couples augmentation to one prompt representation
- makes provider-specific mapping less flexible
- makes individual prompt components harder to inspect and test

This option was rejected.

---

### Option B — Return a Structured AugmentedPrompt

```text
AugmentedPrompt
├── system_instruction
├── context
└── question
```

Advantages:

- preserves semantic structure
- keeps augmentation provider-independent
- supports independent validation
- supports independent testing
- allows future LLM implementations to choose their own message representation

This option was selected.

---

## Why Prompt Structure Is Preserved

The three prompt components have different meanings.

### System Instruction

Defines how the model should behave.

### Context

Contains retrieved evidence.

### Question

Contains the original user request.

Collapsing them immediately into one string would remove these distinctions from the application domain.

The selected boundary preserves them until the LLM implementation decides how they should be represented.

---

## Provider Independence

The prompt augmentation layer does not know whether the future LLM uses:

- system messages
- user messages
- one text prompt
- a local inference API
- a cloud provider SDK

The output remains:

```text
AugmentedPrompt
```

A future LLM implementation may map:

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

Another implementation may choose a different mapping.

The prompt augmenter remains unchanged.

---

## Considered Context Construction Designs

### Option A — Separate ContextBuilder

```text
list[RetrievedChunk]
    ↓
ContextBuilder
    ↓
context
    ↓
PromptAugmenter
```

Advantages:

- independent context construction capability
- future extensibility

Disadvantages:

- adds another abstraction before context construction is complex
- increases package and dependency structure without a current need

This option was rejected for the current sprint.

---

### Option B — PromptAugmenter Builds Context

```text
query + retrieved chunks
        ↓
PromptAugmenter
        ├── validate query
        ├── format chunks
        ├── join context
        └── create AugmentedPrompt
```

Advantages:

- simple
- cohesive with current requirements
- avoids premature abstraction

This option was selected.

---

## Future ContextBuilder Extraction

A separate context construction capability may become justified if the system introduces:

- token budgets
- context truncation
- neighboring-chunk expansion
- duplicate removal
- document grouping
- source citations
- context compression

The current implementation does not require those capabilities.

---

## Considered Context Formatting Strategies

### Option A — Plain Concatenation

```text
First retrieved chunk.

Second retrieved chunk.

Third retrieved chunk.
```

Advantages:

- minimal formatting
- fewer prompt tokens

Disadvantages:

- evidence boundaries are only implied
- debugging is less explicit
- future source attribution becomes harder to attach cleanly

This option was rejected.

---

### Option B — Explicit Numbered Context Blocks

```text
[CONTEXT 1]
First retrieved chunk.

[CONTEXT 2]
Second retrieved chunk.

[CONTEXT 3]
Third retrieved chunk.
```

Advantages:

- preserves evidence boundaries
- easy to inspect
- easy to debug
- supports future extension with source information

This option was selected.

---

## Retrieval Order

The prompt augmenter preserves the exact order received from the retriever.

```text
RetrievedChunk[0]
    ↓
CONTEXT 1

RetrievedChunk[1]
    ↓
CONTEXT 2
```

The prompt augmenter does not re-rank results.

Retrieval ranking belongs to:

```text
Retriever
```

Prompt formatting belongs to:

```text
PromptAugmenter
```

---

## Why Chunk Index Is Not Used for Ordering

`chunk_index` represents position within one source document.

Retrieval results may contain chunks from multiple documents.

Sorting all retrieved results by `chunk_index` would not represent:

- semantic relevance
- global document order

It could destroy the relevance ranking already produced by vector search.

Therefore:

```text
retriever order
    =
context order
```

---

## Retrieval Metadata

The retrieval result contains:

```text
RetrievedChunk
├── chunk_id
├── document_id
├── content
├── chunk_index
└── distance
```

Only:

```text
content
```

is included in the prompt.

The remaining fields stay within the application domain.

---

## Why Distance Is Excluded

Cosine distance is useful for:

- observability
- evaluation
- debugging
- future thresholding

It is not currently useful to the LLM.

The retrieval stage has already used distance to establish ranking.

Adding:

```text
DISTANCE 0.123456
```

to the prompt would introduce additional content without a generation requirement.

Therefore:

```text
distance
    ↓
application-side signal
```

and:

```text
content
    ↓
LLM evidence
```

---

## Why Persisted Identities Are Excluded

`chunk_id` and `document_id` are useful for:

- tracing
- citations
- source attribution
- feedback

The current system does not yet generate citations.

Including persisted IDs in the prompt would therefore add unnecessary content.

They remain available in the application domain for future use.

---

## Fixed System Instruction

The selected instruction is:

```text
Answer the question using only the provided context. If the context does not contain enough information to answer the question, say that you do not have enough information.
```

The instruction establishes a grounded generation policy.

The model should:

```text
use retrieved evidence
```

and avoid:

```text
inventing an answer when evidence is insufficient
```

---

## Why the Instruction Is Not Configurable Yet

The current system has one RAG behavior.

There is no current requirement for:

- multiple prompt strategies
- per-domain instructions
- runtime prompt selection
- prompt template management

Configuration would add flexibility without a concrete use case.

The fixed instruction remains owned by `DefaultPromptAugmenter`.

---

## Empty Retrieval Results

An empty list of retrieved chunks is considered valid.

```text
query
    ↓
retrieval
    ↓
[]
```

The augmenter produces:

```text
AugmentedPrompt
├── system_instruction = fixed instruction
├── context = ""
└── question = original query
```

This option was selected instead of raising an error.

---

## Why Empty Context Is Valid

No retrieved chunks does not mean the request itself is malformed.

It is a possible retrieval outcome.

The grounding instruction already defines behavior for insufficient evidence.

The prompt augmenter therefore does not convert a valid retrieval outcome into an exception.

---

## Query Validation

The augmenter rejects:

```text
""
```

and:

```text
"   "
```

because prompt augmentation requires a meaningful question.

Whitespace stripping is used only for validation.

Valid query text is preserved exactly.

---

## Immutability

`AugmentedPrompt` is immutable.

Once prompt augmentation completes, the output represents the exact structured input prepared for generation.

Later stages consume the result rather than mutating it.

This is consistent with the project's existing immutable pipeline domain models.

---

## Consequences

### Positive

- prompt structure remains explicit
- augmentation remains independent of LLM providers
- future LLM implementations can choose their own message formats
- retrieved evidence boundaries remain visible
- retrieval relevance order is preserved
- retrieval metadata does not create prompt noise
- empty retrieval outcomes remain valid
- context construction stays simple
- no premature `ContextBuilder` abstraction is introduced

### Negative

- the future LLM layer must map `AugmentedPrompt` into provider-specific input
- explicit context labels consume a small number of additional prompt tokens
- the fixed system instruction cannot yet vary by use case

### Neutral

The current prompt does not include source citations.

Persisted chunk and document identities remain available in `RetrievedChunk` and can support citations later.

---

## Future Considerations

A future version may introduce:

- `ContextBuilder`
- token-budget-aware context construction
- source citations
- document metadata
- neighboring-chunk expansion
- context compression
- prompt versioning
- configurable prompt strategies
- provider-specific message adapters

These changes do not alter the current decision to preserve a structured boundary between prompt augmentation and generation.

---

## Final Decision

Use a dedicated `PromptAugmenter` that returns an immutable structured `AugmentedPrompt`, builds explicitly delimited context blocks directly from retrieved chunk content, preserves retrieval ranking, excludes retrieval metadata from the prompt, uses a fixed grounding instruction, and allows empty retrieval results.