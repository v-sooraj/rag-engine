# Sprint 08 — Prompt Augmentation

## Status

Completed

## Objective

Implement the prompt augmentation stage of the RAG pipeline.

The prompt augmentation stage transforms a user query and retrieved chunks into a structured prompt containing:

- grounding instructions
- retrieved context
- the original user question

This sprint extends the retrieval pipeline from:

```text
User Query
 ↓
QueryEmbedder
 ↓
Query Embedding
 ↓
Retriever
 ↓
Top-K Retrieved Chunks
```

to:

```text
User Query
 ↓
QueryEmbedder
 ↓
Query Embedding
 ↓
Retriever
 ↓
Top-K Retrieved Chunks
 ↓
PromptAugmenter
 ↓
AugmentedPrompt
```

The output of this sprint becomes the input to the future LLM generation stage.

---

## Scope

The sprint includes:

- immutable augmented prompt domain model
- prompt augmentation abstraction
- default prompt augmentation implementation
- fixed grounding system instruction
- explicit context block delimiters
- preservation of retrieval ranking order
- context construction from retrieved chunks
- empty retrieval result handling
- query validation
- prompt augmentation domain tests
- prompt augmenter unit tests
- complete retrieval-to-prompt-augmentation pipeline test

The sprint does not include:

- LLM integration
- model provider APIs
- chat message construction
- answer generation
- streaming responses
- prompt templates from external files
- configurable system instructions
- token budgeting
- context truncation
- context compression
- neighboring-chunk expansion
- source citations
- retrieval metadata in prompts
- prompt versioning
- RAG orchestration
- API endpoints

These concerns belong to later pipeline stages.

---

## Pipeline Position

Before this sprint, the retrieval pipeline ended with:

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
```

After this sprint, the pipeline continues into structured prompt augmentation:

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

The RAG engine now has three major pipeline sections:

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
```

---

## Package Structure

```text
rag_engine/
└── prompt_augmentation/
    ├── __init__.py
    ├── augmented_prompt.py
    ├── prompt_augmenter.py
    └── default_prompt_augmenter.py
```

Test structure:

```text
tests/
└── prompt_augmentation/
    ├── __init__.py
    ├── test_augmented_prompt.py
    ├── test_default_prompt_augmenter.py
    └── test_prompt_augmentation_pipeline.py
```

---

## Prompt Augmentation Boundary

The prompt augmentation capability receives:

```text
User Query
        +
list[RetrievedChunk]
```

and returns:

```text
AugmentedPrompt
```

The abstraction is:

```python
class PromptAugmenter(ABC):

    @abstractmethod
    def augment(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> AugmentedPrompt:
        pass
```

The abstraction does not expose:

- sentence-transformers
- PostgreSQL
- pgvector
- LLM providers
- chat completion APIs
- provider-specific message formats

These concerns belong to other pipeline stages.

---

## Why Prompt Augmentation Is a Separate Capability

Retrieval answers:

```text
Which stored chunks are most relevant?
```

Prompt augmentation answers:

```text
How should the retrieved evidence and user question be structured for generation?
```

These are different responsibilities.

The boundary remains:

```text
Retriever
    ↓
list[RetrievedChunk]
    ↓
PromptAugmenter
    ↓
AugmentedPrompt
```

The retriever does not know how retrieved text will be presented to an LLM.

The prompt augmenter does not know how similarity search was performed.

---

## Structured Prompt Output

Two output designs were considered.

### Plain String

```text
instructions
+
context
+
question
    ↓
one string
```

This is simple but collapses several meaningful concepts into one opaque value.

The future LLM layer would receive one string without an explicit distinction between:

- system behavior
- retrieved evidence
- user question

---

### Structured Augmented Prompt

The selected design uses:

```python
class AugmentedPrompt(BaseModel):
    model_config = ConfigDict(frozen=True)

    system_instruction: str
    context: str
    question: str
```

The result preserves the logical structure:

```text
AugmentedPrompt
├── system_instruction
├── context
└── question
```

The future LLM layer can decide how these fields map to a specific provider.

For example:

```text
system_instruction
    ↓
system message

context + question
    ↓
user message
```

Another provider could use a different representation without changing prompt augmentation.

---

## Augmented Prompt Domain Model

The output of prompt augmentation is immutable.

```text
AugmentedPrompt
├── system_instruction
├── context
└── question
```

Immutability is consistent with the existing pipeline domain models.

Once constructed, the prompt represents the exact output of the augmentation stage.

Later pipeline stages should consume it rather than mutate it.

---

## System Instruction

Sprint 8 uses one fixed grounding instruction:

```text
Answer the question using only the provided context. If the context does not contain enough information to answer the question, say that you do not have enough information.
```

The instruction establishes two behaviors:

```text
Relevant context exists
    ↓
answer using that context
```

and:

```text
Context is insufficient
    ↓
state that there is not enough information
```

The goal is to reduce unsupported generation outside the retrieved evidence.

---

## Why the System Instruction Is Fixed

The current RAG engine has one prompt augmentation behavior.

Making the instruction configurable immediately would introduce flexibility without a concrete second prompt strategy.

The selected design is:

```text
DefaultPromptAugmenter
    ↓
owns one fixed system instruction
```

Future requirements may introduce:

- configurable prompt strategies
- prompt versions
- domain-specific instructions
- external prompt templates

Those requirements do not exist yet.

---

## Context Construction Ownership

Two designs were considered.

### Separate ContextBuilder

```text
list[RetrievedChunk]
    ↓
ContextBuilder
    ↓
context string
    ↓
PromptAugmenter
```

This would introduce another abstraction.

---

### PromptAugmenter Builds Context

```text
query
    +
list[RetrievedChunk]
        ↓
PromptAugmenter
        ├── preserve order
        ├── format context blocks
        └── construct AugmentedPrompt
```

This option was selected.

Current context construction is intentionally simple:

```text
RetrievedChunk contents
    ↓
explicit delimiters
    ↓
joined context
```

A separate `ContextBuilder` would be premature.

It may become justified later if context construction introduces:

- token budgets
- deduplication
- neighboring chunks
- source citations
- context compression
- document grouping

---

## Explicit Context Boundaries

Retrieved chunks are not flattened into one uninterrupted block.

Instead, each result receives an explicit delimiter.

Example:

```text
[CONTEXT 1]
Vector databases store embeddings.

[CONTEXT 2]
Cosine distance measures vector closeness.

[CONTEXT 3]
pgvector supports similarity search.
```

This preserves the fact that retrieval produced separate evidence units.

The exact delimiter syntax is an implementation choice.

The important principle is:

```text
preserve evidence boundaries
```

---

## Why Context Boundaries Are Preserved

Without explicit boundaries:

```text
Chunk A

Chunk B

Chunk C
```

the context becomes one loosely structured text block.

With explicit boundaries:

```text
[CONTEXT 1]
Chunk A

[CONTEXT 2]
Chunk B

[CONTEXT 3]
Chunk C
```

the prompt remains easier to:

- inspect
- debug
- reason about
- extend with future source information

The LLM also receives a clearer separation between retrieved evidence units.

---

## Retrieval Ranking Order

The prompt augmenter preserves the exact order returned by the retriever.

```text
RetrievedChunk[0]
    ↓
[CONTEXT 1]

RetrievedChunk[1]
    ↓
[CONTEXT 2]

RetrievedChunk[2]
    ↓
[CONTEXT 3]
```

The augmenter does not sort by:

- `chunk_index`
- `document_id`
- `distance`

The retriever already established relevance ranking.

Reordering results during augmentation would destroy that ranking.

---

## Why Chunk Index Is Not Used for Sorting

Retrieved chunks may come from different documents.

Example:

```text
Result 1
document A
chunk_index = 10

Result 2
document B
chunk_index = 2

Result 3
document A
chunk_index = 0
```

Sorting globally by `chunk_index` would produce:

```text
Result 3
Result 2
Result 1
```

and would destroy retrieval relevance order.

Therefore:

```text
retrieval order
    =
prompt context order
```

---

## Retrieval Metadata Boundary

A `RetrievedChunk` contains:

```text
RetrievedChunk
├── chunk_id
├── document_id
├── content
├── chunk_index
└── distance
```

The prompt context currently includes only:

```text
content
```

The following fields remain application-side metadata:

- `chunk_id`
- `document_id`
- `chunk_index`
- `distance`

---

## Why Distance Is Not Included in the Prompt

Cosine distance is useful for:

- observability
- debugging
- future thresholds
- retrieval evaluation

However, retrieval ranking has already used the distance.

The LLM does not currently need:

```text
[CONTEXT 1 - DISTANCE 0.12]
```

Including the raw distance would add prompt content without a generation requirement.

The boundary is:

```text
RetrievedChunk.distance
    ↓
application observability
```

and:

```text
RetrievedChunk.content
    ↓
LLM context
```

---

## Why Persisted IDs Are Not Included in the Prompt

The current generation stage does not yet support source citations.

Therefore:

- `chunk_id`
- `document_id`

remain outside the prompt.

They may become useful later for:

- citations
- source attribution
- feedback tracking
- traceability

Until then, they remain application metadata.

---

## Empty Retrieval Results

An empty retrieval result is valid.

```text
valid query
    ↓
retrieval finds no relevant chunks
    ↓
[]
```

The prompt augmenter does not reject this outcome.

Instead, it produces:

```text
AugmentedPrompt
├── system_instruction = fixed grounding instruction
├── context = ""
└── question = original query
```

This keeps responsibilities separate.

The augmenter formats the result of retrieval.

It does not decide whether retrieval quality is sufficient.

---

## Why Empty Context Is Allowed

The system instruction already defines behavior for insufficient context:

```text
If the context does not contain enough information to answer the question, say that you do not have enough information.
```

Therefore an empty context remains a valid prompt state.

The future generation layer can process it according to the system instruction.

---

## Query Validation

Empty and blank queries are invalid.

Rejected examples:

```text
""
```

and:

```text
"   "
```

The validation flow is:

```text
query
 ↓
strip for validation
 ↓
empty?
 ├── yes → raise ValueError
 └── no  → continue
```

Validation occurs before context construction.

---

## Original Query Preservation

Whitespace stripping is used only to determine whether the query is invalid.

A valid query is not silently modified.

Example:

```text
"  What is retrieval augmented generation?  "
```

remains:

```text
"  What is retrieval augmented generation?  "
```

inside:

```text
AugmentedPrompt.question
```

The principle is:

```text
validate input
    ≠
silently rewrite input
```

---

## Default Prompt Augmenter

The concrete implementation is:

```text
PromptAugmenter
       ▲
       │
DefaultPromptAugmenter
```

Its responsibilities are:

1. validate the query
2. preserve retrieved chunk order
3. format each chunk as an explicit context block
4. join context blocks
5. construct an immutable `AugmentedPrompt`

The implementation does not:

- perform retrieval
- calculate similarity
- sort retrieved chunks
- call an LLM
- create provider-specific messages

---

## Context Formatting

Each retrieved chunk becomes:

```text
[CONTEXT N]
<chunk content>
```

Multiple blocks are separated by two newline characters.

Conceptually:

```text
[CONTEXT 1]
First chunk

[CONTEXT 2]
Second chunk

[CONTEXT 3]
Third chunk
```

The numbering begins at:

```text
1
```

rather than:

```text
0
```

because the labels are intended for human-readable prompt structure.

---

## Testing Strategy

### Augmented Prompt Domain Tests

Domain model tests verify:

- valid prompts can be created
- empty context is allowed
- empty system instructions are rejected
- empty questions are rejected
- prompts are immutable

---

### Default Prompt Augmenter Tests

Unit tests verify:

- structured prompts are returned
- the fixed system instruction is used
- retrieval order is preserved
- explicit chunk boundaries are created
- retrieval metadata is excluded from context
- empty retrieved chunk lists are allowed
- empty queries are rejected
- blank queries are rejected
- original valid query text is preserved

---

## Complete Prompt Augmentation Pipeline Test

The Sprint 8 integration test proves:

```text
Real Query
    ↓
LocalQueryEmbedder
    ↓
384-dimensional Query Embedding
    ↓
PostgresRetriever
    ↓
list[RetrievedChunk]
    ↓
DefaultPromptAugmenter
    ↓
AugmentedPrompt
```

The test uses:

- real local query embeddings
- real PostgreSQL
- real pgvector retrieval
- real prompt augmentation

The test verifies:

- retrieved evidence reaches the prompt
- the system instruction is preserved
- the original question is preserved
- context delimiters are created
- retrieval order becomes context order
- the generated context exactly matches the retrieved results

The test boundary ends at:

```text
AugmentedPrompt
```

No LLM is involved.

This ensures Sprint 8 tests only the responsibility introduced by Sprint 8.

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

The retrieval and augmentation pipeline is:

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
                         ↓
                  Augmented Prompt

                PROMPT AUGMENTATION
```

---

## Key Learning Outcomes

This sprint established the following concepts:

- prompt augmentation is a separate RAG pipeline capability
- retrieved evidence should remain separate from provider-specific LLM APIs
- meaningful prompt structure should not be collapsed into one primitive too early
- structured prompt models preserve system instructions, context, and questions independently
- context construction can remain inside the augmenter while it is simple
- separate context-builder abstractions should be introduced only when complexity justifies them
- retrieved evidence boundaries should remain visible
- retrieval ranking should be preserved during augmentation
- chunk indexes should not be used to reorder globally ranked retrieval results
- retrieval metadata and LLM context serve different purposes
- raw vector distance belongs to application observability rather than prompt content
- empty retrieval results are valid RAG outcomes
- input validation should not silently rewrite valid input
- prompt augmentation should remain independent of LLM providers
- integration tests should stop at the architectural boundary introduced by the sprint

---

## Sprint Outcome

Sprint 08 successfully completed the prompt augmentation stage.

The system can now:

1. accept a valid user query
2. retrieve semantically relevant chunks
3. preserve retrieval ranking
4. preserve retrieved evidence boundaries
5. construct explicit numbered context blocks
6. exclude unnecessary retrieval metadata from the prompt
7. handle empty retrieval results
8. apply a fixed grounding instruction
9. preserve the original user question
10. return an immutable structured `AugmentedPrompt`

The RAG engine can now:

```text
store knowledge
    ↓
retrieve relevant knowledge
    ↓
construct grounded LLM input
```

The next sprint will introduce LLM generation and transform the structured augmented prompt into a generated answer.