# Sprint 13 — Document Ingestion API

## Status

Completed

## Objective

Expose the existing document ingestion application capability through an HTTP API.

Before this sprint, the application already supported:

```text
IngestionPipeline.ingest(path)
```

The complete ingestion operation was:

```text
File Path
    ↓
IngestionPipeline
    ↓
DocumentLoader
    ↓
DocumentChunker
    ↓
ChunkEmbedder
    ↓
VectorStore
    ↓
Document UUID
```

However, no external client could invoke this capability through the application API.

The only possible caller was application code:

```python
pipeline = create_ingestion_pipeline()

document_id = pipeline.ingest(
    "path/to/document.pdf"
)
```

This sprint introduces:

```text
POST /documents
```

The application now supports the complete external flow:

```text
HTTP Client
    ↓
Upload PDF
    ↓
POST /documents
    ↓
IngestionPipeline
    ↓
PostgreSQL + pgvector
    ↓
Document UUID
    ↓
201 Created
```

---

## Scope

This sprint includes:

- multipart PDF upload endpoint
- document upload response model
- ingestion pipeline dependency exposure
- upload-to-filesystem adaptation
- temporary directory lifecycle
- original filename preservation
- uploaded filename sanitization
- PDF media-type validation
- HTTP response mapping
- isolated upload adapter tests
- isolated document endpoint tests
- real HTTP ingestion integration testing

This sprint does not include:

- multiple file uploads
- non-PDF document formats
- asynchronous ingestion
- background jobs
- ingestion progress reporting
- ingestion status endpoints
- file-size limits
- content-based PDF validation
- malware scanning
- object storage
- document listing
- document deletion API
- authentication
- authorization
- observability

These concerns belong to later stages.

---

## Problem Before This Sprint

Sprint 12 introduced the complete ingestion application operation:

```text
IngestionPipeline.ingest(path)
```

The application could perform:

```text
Load
 ↓
Chunk
 ↓
Embed
 ↓
Store
```

through one public boundary.

However, the operation still required a filesystem path.

The architecture was:

```text
Application Code
    ↓
Filesystem Path
    ↓
IngestionPipeline
```

The HTTP API exposed only:

```text
POST /answers
```

Therefore the application could query existing knowledge but could not receive new knowledge from an external client.

The missing flow was:

```text
HTTP Client
    ↓
PDF Upload
    ↓
?
    ↓
Filesystem Path
    ↓
IngestionPipeline
```

---

## Existing Application Boundary

The existing ingestion contract remains:

```text
IngestionPipeline.ingest(path: str) -> UUID
```

This contract is intentionally independent of FastAPI.

The ingestion pipeline knows about:

```text
filesystem path
```

It does not know about:

```text
UploadFile
multipart/form-data
HTTP requests
HTTP responses
FastAPI
```

This separation is preserved.

---

## Selected Architecture

The HTTP layer adapts an uploaded file into the existing application input.

The selected flow is:

```text
POST /documents
    ↓
UploadFile
    ↓
DocumentUploadAdapter
    ↓
Temporary Directory
    ↓
Temporary PDF Path
    ↓
IngestionPipeline.ingest(path)
    ↓
Document UUID
    ↓
DocumentResponse
```

The adapter bridges:

```text
HTTP Representation
```

to:

```text
Application Representation
```

Specifically:

```text
UploadFile
    ↓
filesystem path
```

---

## Why an Upload Adapter Was Introduced

The route could have directly performed:

```text
create temporary file
 ↓
copy uploaded bytes
 ↓
call pipeline
 ↓
delete temporary file
```

This approach was rejected because it would make the route responsible for:

- HTTP handling
- temporary filesystem lifecycle
- byte copying
- cleanup behavior
- application invocation
- response mapping

Instead, the route remains thin.

The selected architecture is:

```text
Route
 ↓
DocumentUploadAdapter
 ↓
IngestionPipeline
```

The adapter owns the translation between the HTTP boundary and the application boundary.

---

## Package Structure

```text
rag_engine/
└── api/
    ├── adapters/
    │   ├── __init__.py
    │   └── document_upload_adapter.py
    │
    ├── models/
    │   └── document_response.py
    │
    ├── routes/
    │   ├── answers.py
    │   └── documents.py
    │
    ├── app.py
    └── dependencies.py
```

Test structure:

```text
tests/
└── api/
    ├── adapters/
    │   ├── __init__.py
    │   └── test_document_upload_adapter.py
    │
    ├── conftest.py
    ├── test_answers.py
    ├── test_documents.py
    ├── test_openapi.py
    └── test_real_document_ingestion.py
```

---

## Document Endpoint

The new endpoint is:

```text
POST /documents
```

The request uses:

```text
multipart/form-data
```

with:

```text
file
```

as the uploaded document field.

The supported media type is:

```text
application/pdf
```

A successful request returns:

```text
201 Created
```

with:

```json
{
  "document_id": "..."
}
```

---

## Endpoint Flow

The route performs:

```text
Receive UploadFile
    ↓
Validate Media Type
    ↓
Resolve IngestionPipeline
    ↓
Create DocumentUploadAdapter
    ↓
Adapt Upload to Path
    ↓
Execute IngestionPipeline
    ↓
Map UUID to HTTP Response
```

The route does not perform:

- PDF parsing
- chunking
- embedding
- vector persistence
- database transaction management

These responsibilities remain behind:

```text
IngestionPipeline
```

---

## HTTP-Level Validation

The route validates:

```text
file.content_type
```

The accepted value is:

```text
application/pdf
```

Unsupported media types return:

```text
415 Unsupported Media Type
```

with:

```json
{
  "detail": "Only PDF files are supported"
}
```

A missing file is rejected by FastAPI request validation with:

```text
422 Unprocessable Entity
```

The ingestion pipeline is not called for either invalid request.

---

## Validation Boundary

The HTTP route owns validation of:

```text
HTTP media type
```

The ingestion pipeline continues to own validation of:

```text
application input path
```

The responsibilities are:

```text
HTTP Route
└── Is this request acceptable to the API?
```

```text
IngestionPipeline
└── Is this path valid application input?
```

This prevents HTTP concerns from leaking into the application layer.

---

## Document Response Model

The endpoint returns:

```text
DocumentResponse
```

with:

```text
document_id: UUID
```

The response maps:

```text
IngestionPipeline UUID
    ↓
DocumentResponse
    ↓
JSON
```

The HTTP representation is:

```json
{
  "document_id": "uuid-value"
}
```

---

## Dependency Injection

The API dependency layer now exposes:

```text
get_ingestion_pipeline()
```

and:

```text
get_rag_pipeline()
```

The mapping is:

```text
get_ingestion_pipeline()
    ↓
create_ingestion_pipeline()
```

and:

```text
get_rag_pipeline()
    ↓
create_rag_pipeline()
```

The two application capabilities remain independent.

The route receives:

```text
IngestionPipeline
```

through FastAPI dependency injection.

---

## Application Routes

The FastAPI application now includes:

```text
/answers
```

and:

```text
/documents
```

The external application capabilities are:

```text
POST /documents
    ↓
Write Knowledge
```

and:

```text
POST /answers
    ↓
Read Knowledge and Generate
```

---

## Upload Adapter

The HTTP adapter is:

```text
DocumentUploadAdapter
```

Its responsibility is:

```text
UploadFile
    ↓
filesystem path
    ↓
IngestionPipeline
```

The adapter receives:

```text
UploadFile
```

and returns:

```text
UUID
```

The UUID is returned unchanged from the ingestion pipeline.

---

## Initial Temporary File Design

The first implementation created:

```text
NamedTemporaryFile
```

with:

```text
suffix=".pdf"
```

The flow was:

```text
sample.pdf
    ↓
Uploaded Bytes
    ↓
tmp2l9m66ua.pdf
    ↓
IngestionPipeline
```

The PDF bytes were correct.

The temporary path was valid.

The ingestion pipeline completed successfully.

However, the document metadata became:

```text
filename = tmp2l9m66ua.pdf
```

instead of:

```text
filename = sample.pdf
```

This was a real cross-boundary metadata bug.

---

## Why the Initial Design Was Incorrect

`PdfLoader` derives document metadata from the filesystem path.

Therefore:

```text
temporary path filename
```

became:

```text
domain document filename
```

The adapter preserved:

```text
file content
```

but corrupted:

```text
file identity metadata
```

The important lesson is:

```text
Correct bytes do not guarantee correct adaptation.
```

An adapter must preserve all downstream-significant information.

---

## Final Temporary File Design

The corrected adapter creates:

```text
TemporaryDirectory
```

and writes the uploaded file inside it using the original filename.

The flow is:

```text
sample.pdf
    ↓
Temporary Directory
    ↓
<temporary-directory>/sample.pdf
    ↓
IngestionPipeline
```

`PdfLoader` now receives a path whose final component remains:

```text
sample.pdf
```

Therefore persisted metadata remains correct.

---

## Original Filename Preservation

The adapter uses the original uploaded filename for the temporary file.

The architecture is:

```text
UploadFile.filename
    ↓
Sanitize Filename
    ↓
Temporary Directory
    ↓
Sanitized Original Filename
```

For example:

```text
sample.pdf
```

becomes:

```text
<temporary-directory>/sample.pdf
```

This preserves the filename used by downstream metadata extraction.

---

## Filename Sanitization

The adapter does not use the uploaded filename as an unrestricted path.

It extracts only the final filename component.

Conceptually:

```text
../../sample.pdf
    ↓
sample.pdf
```

This prevents the uploaded filename from escaping the temporary directory.

The adapter therefore preserves:

```text
filename identity
```

without preserving:

```text
client-supplied directory structure
```

---

## Temporary Directory Lifecycle

The adapter uses a scoped temporary directory.

The success flow is:

```text
Create Temporary Directory
    ↓
Write Uploaded PDF
    ↓
Call IngestionPipeline
    ↓
Receive Document UUID
    ↓
Exit Temporary Directory Scope
    ↓
Delete Temporary File and Directory
```

The failure flow is:

```text
Create Temporary Directory
    ↓
Write Uploaded PDF
    ↓
Call IngestionPipeline
    ↓
Pipeline Failure
    ↓
Exit Temporary Directory Scope
    ↓
Delete Temporary File and Directory
    ↓
Propagate Failure
```

Cleanup is guaranteed by the temporary directory context manager.

---

## Why the Adapter Does Not Close UploadFile

The uploaded file belongs to the HTTP request lifecycle.

The adapter reads from:

```text
UploadFile.file
```

but does not own the uploaded request resource.

Therefore the adapter does not close it.

Resource ownership remains:

```text
FastAPI
└── request upload lifecycle
```

```text
DocumentUploadAdapter
└── temporary filesystem lifecycle
```

---

## Failure Semantics

The adapter does not wrap ingestion pipeline failures.

If:

```text
IngestionPipeline
```

raises:

```text
RuntimeError
```

the same exception propagates unchanged.

The adapter still guarantees temporary filesystem cleanup.

The flow is:

```text
Pipeline Failure
    ↓
Cleanup Temporary Directory
    ↓
Propagate Original Failure
```

No speculative upload-specific exception hierarchy is introduced.

---

## HTTP Failure Mapping

The current API behavior is:

```text
Unhandled Pipeline Failure
    ↓
HTTP 500 Internal Server Error
```

This matches the existing `/answers` endpoint behavior.

No application-specific error mapping is introduced in this sprint.

Future error taxonomy work may map known failures to more specific HTTP responses.

---

## Isolated Upload Adapter Tests

The upload adapter tests use:

```text
Mock IngestionPipeline
```

They prove:

```text
Adapter
├── returns document UUID
├── passes a .pdf path to pipeline
├── copies uploaded bytes correctly
├── preserves original filename
├── deletes temporary data after success
├── deletes temporary data after failure
└── propagates pipeline failure unchanged
```

The adapter suite contains:

```text
7 tests
```

---

## Isolated Endpoint Tests

The document endpoint tests use:

```text
Mock IngestionPipeline
```

through FastAPI dependency overrides.

They prove:

```text
POST /documents
├── returns 201 Created
├── returns document UUID
├── invokes ingestion pipeline
├── passes temporary PDF path
├── rejects missing file
├── rejects non-PDF media type
└── returns 500 when ingestion fails
```

The endpoint suite contains:

```text
6 tests
```

---

## API Test Dependency Overrides

The shared API test fixture overrides:

```text
get_ingestion_pipeline
```

and:

```text
get_rag_pipeline
```

with mocks.

The isolated API tests therefore do not:

- load the embedding model
- connect to PostgreSQL
- execute real PDF parsing
- execute real chunking
- execute real embeddings

This keeps route tests focused on HTTP behavior.

---

## Real HTTP Integration Test

One real integration test proves the complete external boundary.

Unlike the isolated endpoint tests, it does not override:

```text
get_ingestion_pipeline
```

The test creates the real application:

```text
create_app()
```

and sends:

```text
tests/resources/sample.pdf
```

through a real multipart HTTP request.

---

## Complete Real Integration Flow

The test proves:

```text
sample.pdf
    ↓
multipart/form-data
    ↓
POST /documents
    ↓
FastAPI UploadFile
    ↓
DocumentUploadAdapter
    ↓
Temporary Directory
    ↓
<temporary-directory>/sample.pdf
    ↓
DefaultIngestionPipeline
    ↓
PdfLoader
    ↓
RecursiveDocumentChunker
    ↓
LocalChunkEmbedder
    ↓
PostgresVectorStore
    ↓
PostgreSQL + pgvector
    ↓
201 Created
    ↓
document_id
```

---

## What the Real HTTP Test Verifies

The HTTP response is verified:

```text
status = 201
```

and:

```text
document_id is a valid UUID
```

The persisted document is verified directly in PostgreSQL:

```text
Document
├── exists
├── filename = sample.pdf
└── page_count > 1
```

The persisted chunks are also verified:

```text
Chunks
├── multiple chunks exist
├── indexes are ordered
├── content is non-empty
└── embeddings have 384 dimensions
```

---

## Why the Real HTTP Test Was Necessary

The isolated tests all passed with the first adapter implementation.

They proved:

```text
uploaded bytes copied correctly
```

and:

```text
pipeline called with temporary .pdf path
```

However, they did not prove:

```text
the original filename survives the complete system
```

Only the real HTTP test connected:

```text
UploadFile.filename
```

to:

```text
PdfLoader metadata extraction
```

to:

```text
database persistence
```

The first real test failed because the database contained:

```text
tmp2l9m66ua.pdf
```

instead of:

```text
sample.pdf
```

This failure exposed a bug that no isolated test could detect.

---

## Cross-Boundary Testing Lesson

Different test levels prove different properties.

### Adapter Test

Proves:

```text
UploadFile
    ↓
temporary path
```

### Pipeline Integration Test

Proves:

```text
filesystem path
    ↓
database
```

### Real HTTP Integration Test

Proves:

```text
UploadFile
    ↓
temporary path
    ↓
metadata extraction
    ↓
database
```

The bug existed in the interaction between boundaries.

Therefore:

```text
All components can be correct in isolation
while their composition still loses information.
```

---

## Complete External Product Flow

The application now supports the full write/read lifecycle.

### Write Knowledge

```text
Client
    ↓
POST /documents
    ↓
Upload PDF
    ↓
IngestionPipeline
    ↓
PostgreSQL + pgvector
```

### Read Knowledge

```text
Client
    ↓
POST /answers
    ↓
RAGPipeline
    ↓
Retrieve Stored Chunks
    ↓
Augment Prompt
    ↓
LLM
    ↓
Grounded Answer
```

The intended usage sequence is:

```text
1. POST /documents
       ↓
   Knowledge Stored

2. POST /answers
       ↓
   Knowledge Retrieved

3. LLM Generates
       ↓
   Grounded Answer
```

---

## Architecture Before and After

### Before Sprint 13

```text
External Client
    ↓
POST /answers
```

but ingestion required:

```text
Application Code
    ↓
pipeline.ingest(path)
```

### After Sprint 13

```text
External Client
    ├── POST /documents
    └── POST /answers
```

The application is now externally usable as a complete RAG system.

---

## Test Count

Before Sprint 13:

```text
129 tests
```

Sprint 13 added:

```text
7 upload adapter tests
```

```text
6 document endpoint tests
```

```text
1 real HTTP ingestion integration test
```

The complete suite now contains:

```text
143 tests passing
```

---

## Key Learning Outcomes

This sprint established that:

- external adapters should translate representations without changing application contracts
- `UploadFile` should not leak into the application layer
- temporary filesystem concerns belong outside the ingestion pipeline
- routes should remain focused on HTTP concerns
- runtime file adaptation deserves its own testable boundary
- cleanup must work on both success and failure paths
- original filename can be domain-significant metadata
- preserving bytes is not enough if metadata is lost
- temporary filenames can accidentally become persisted domain data
- client-supplied filenames must be sanitized before filesystem use
- isolated tests cannot prove all cross-boundary properties
- real integration tests should target the new boundary introduced by a sprint
- a failing integration test can reveal a design flaw rather than a test flaw

---

## Sprint Outcome

Sprint 13 successfully exposed document ingestion through:

```text
POST /documents
```

The complete external flow is now:

```text
PDF Upload
    ↓
HTTP Adapter
    ↓
Temporary Filesystem Representation
    ↓
IngestionPipeline
    ↓
PostgreSQL + pgvector
    ↓
Document UUID
```

The adapter preserves:

- uploaded bytes
- original filename
- temporary resource cleanup

The API now exposes both primary application capabilities:

```text
POST /documents
```

for knowledge ingestion and:

```text
POST /answers
```

for grounded question answering.

The complete suite passes:

```text
143 tests
```