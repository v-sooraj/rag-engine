# ADR-014: Adapt HTTP Document Uploads Through a Temporary Filesystem Boundary

## Status

Accepted

## Context

The application already exposes:

```text
IngestionPipeline.ingest(path: str) -> UUID
```

The new document API receives:

```text
FastAPI UploadFile
```

The application therefore needs to bridge:

```text
UploadFile
```

to:

```text
filesystem path
```

The design needed to decide:

- whether `IngestionPipeline` should accept `UploadFile`
- whether the route should manage temporary files directly
- whether temporary-file handling should have its own adapter
- how temporary files should be cleaned up
- whether original filenames should be preserved
- how uploaded filenames should be sanitized
- how failures should propagate

---

## Decision

Introduce:

```text
DocumentUploadAdapter
```

between the HTTP route and `IngestionPipeline`.

The selected flow is:

```text
UploadFile
    ↓
DocumentUploadAdapter
    ↓
Temporary Directory
    ↓
Temporary File Using Sanitized Original Filename
    ↓
IngestionPipeline.ingest(path)
    ↓
UUID
```

The adapter guarantees temporary filesystem cleanup on both success and failure.

The existing `IngestionPipeline` contract remains unchanged.

---

## Decision Drivers

The decision is based on the following requirements:

- keep FastAPI types outside the application layer
- preserve the existing ingestion contract
- keep routes thin
- make temporary-file behavior independently testable
- guarantee cleanup
- preserve original filename metadata
- prevent uploaded filenames from escaping the temporary directory
- support real HTTP integration testing

---

## Considered Option: Change IngestionPipeline to Accept UploadFile

Conceptually:

```text
IngestionPipeline.ingest(file: UploadFile)
```

Advantages:

- no temporary path adapter visible to the route

Disadvantages:

- application layer depends on FastAPI
- ingestion becomes tied to HTTP
- non-HTTP callers must construct HTTP-specific objects
- existing filesystem-based loader contract is weakened

This option was rejected.

---

## Considered Option: Manage Temporary Files in the Route

Conceptually:

```text
Route
 ↓
Create Temporary File
 ↓
Copy Upload
 ↓
Call Pipeline
 ↓
Delete Temporary File
```

Advantages:

- fewer classes

Disadvantages:

- route owns too many responsibilities
- cleanup behavior is harder to test independently
- filesystem adaptation is mixed with HTTP response mapping
- route complexity grows

This option was rejected.

---

## Selected Option: Dedicated Upload Adapter

The selected architecture is:

```text
Route
 ↓
DocumentUploadAdapter
 ↓
IngestionPipeline
```

The route owns:

- request handling
- media-type validation
- dependency resolution
- response mapping

The adapter owns:

- upload byte copying
- temporary directory creation
- temporary path creation
- filename preservation
- filename sanitization
- cleanup

The ingestion pipeline owns:

- loading
- chunking
- embedding
- storage

---

## Initial Temporary File Approach

The first implementation used:

```text
NamedTemporaryFile
```

with a `.pdf` suffix.

The resulting path looked like:

```text
tmp2l9m66ua.pdf
```

The uploaded file:

```text
sample.pdf
```

therefore became:

```text
tmp2l9m66ua.pdf
```

before entering the ingestion pipeline.

The bytes remained correct.

The filename did not.

---

## Problem Discovered

`PdfLoader` derives:

```text
DocumentMetadata.filename
```

from the filesystem path.

Therefore the temporary filename became persisted domain metadata.

The database stored:

```text
tmp2l9m66ua.pdf
```

instead of:

```text
sample.pdf
```

This behavior was incorrect.

---

## Corrected Temporary Directory Approach

The adapter now creates:

```text
TemporaryDirectory
```

and writes the upload using the original filename.

The resulting path is:

```text
<temporary-directory>/sample.pdf
```

The temporary directory remains implementation detail.

The final filename remains domain-significant metadata.

---

## Filename Preservation Decision

Preserve:

```text
original filename
```

because downstream document metadata extraction depends on it.

The adapter therefore treats filename as part of the information being adapted.

The adapted representation must preserve:

```text
bytes
```

and:

```text
filename
```

---

## Filename Sanitization Decision

Do not use the complete client-supplied filename as a path.

Extract only the final filename component.

Conceptually:

```text
../../sample.pdf
```

becomes:

```text
sample.pdf
```

This prevents path traversal outside the temporary directory.

The adapter preserves identity without preserving directory structure.

---

## Cleanup Decision

Use the temporary directory context manager as the resource boundary.

Success:

```text
Create Directory
 ↓
Write File
 ↓
Ingest
 ↓
Return UUID
 ↓
Delete Directory
```

Failure:

```text
Create Directory
 ↓
Write File
 ↓
Ingestion Failure
 ↓
Delete Directory
 ↓
Propagate Failure
```

No explicit cleanup branch is required.

---

## UploadFile Ownership Decision

The adapter does not close:

```text
UploadFile
```

FastAPI owns the request resource.

The adapter owns only resources it creates:

```text
temporary directory
temporary file
```

This follows resource ownership boundaries.

---

## Failure Handling Decision

The adapter does not wrap pipeline failures.

The selected behavior is:

```text
IngestionPipeline Failure
 ↓
Cleanup Temporary Resources
 ↓
Propagate Original Failure
```

No new generic upload exception is introduced.

---

## Media-Type Validation Decision

The route accepts:

```text
application/pdf
```

Unsupported media types return:

```text
415 Unsupported Media Type
```

This validation remains in the HTTP layer because:

```text
content_type
```

is an HTTP upload concern.

The ingestion pipeline remains unaware of HTTP media types.

---

## Testing Decision

Use three levels of testing.

### Adapter Tests

Mock:

```text
IngestionPipeline
```

Verify:

- UUID forwarding
- `.pdf` path
- byte copying
- filename preservation
- cleanup after success
- cleanup after failure
- unchanged failure propagation

### Endpoint Tests

Override:

```text
get_ingestion_pipeline
```

with a mock.

Verify:

- HTTP status
- response body
- missing file validation
- media-type validation
- pipeline invocation
- server error behavior

### Real HTTP Integration Test

Use:

```text
real FastAPI application
real multipart upload
real DocumentUploadAdapter
real IngestionPipeline
real PostgreSQL
real pgvector
```

Verify the complete cross-boundary behavior.

---

## Consequences

### Positive

- application layer remains independent of FastAPI
- routes remain thin
- temporary filesystem logic is isolated
- cleanup is guaranteed
- original filename metadata is preserved
- uploaded paths are sanitized
- adapter behavior is independently testable
- complete HTTP-to-database flow is proven

### Negative

- every upload temporarily touches the local filesystem
- ingestion remains synchronous
- large uploads may hold request workers for significant time
- local temporary storage must be available

### Neutral

The adapter exists specifically because the current ingestion contract is path-based.

A future ingestion source abstraction may change this boundary.

---

## Cross-Boundary Lesson

The initial implementation was locally correct at several levels:

```text
HTTP upload succeeded
```

```text
bytes were copied correctly
```

```text
temporary path ended with .pdf
```

```text
ingestion succeeded
```

Yet the complete system was wrong because:

```text
temporary filename
```

became:

```text
persisted document filename
```

Therefore:

```text
Adapters must preserve all information that is semantically significant downstream.
```

Correct representation conversion is not limited to preserving raw content.

---

## Final Decision

Use a dedicated `DocumentUploadAdapter`.

Keep `IngestionPipeline` path-based and independent of FastAPI.

Create a temporary directory for each upload.

Write the file using the sanitized original filename.

Pass that path to the ingestion pipeline.

Guarantee cleanup through the temporary directory lifecycle.

Preserve pipeline failures unchanged.