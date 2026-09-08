# Backend test suite

`uv run pytest` runs everything below; no live GPU, Docker daemon, or Qdrant
instance is required — `docker`, `httpx`, and the vector DB client are mocked
throughout.

## Covered

- **API contract** (`integration/test_api.py`): request validation, PDF
  magic-byte/size checks, path-traversal sanitization, and the documented
  status codes for every route, including error branches (404, 413, 422,
  500, 503).
- **Ingestion pipeline** (`unit/test_ingestion_service.py`): success path,
  parser failure, empty-text documents, and an embedding failure mid-pipeline
  — each must leave the task `FAILED` with a message, not raise.
- **GPU scheduling** (`unit/test_vram_scheduler.py`):
  - container start/skip-start based on current status
  - idle watcher stopping an idle container and a clean restart on the next
    `schedule_generation()` call
  - the `asyncio.Lock` actually serializing concurrent
    `schedule_embedding()` / `schedule_generation()` calls (no GPU overlap)
  - embedder unload and lock release on both success **and** exception, for
    both the async and sync (`schedule_embedding_sync`) facades
  - typed-error mapping: missing container -> `ContainerUnavailableError`,
    cold-start timeout -> `ModelWarmupTimeoutError`
- **`/health/gpu` observability**: container status, lock-held, and
  seconds-since-last-use are asserted directly against scheduler state.

## Intentionally out of scope

- **Real GPU/VRAM measurement.** Tests assert *behavior* (lock serialization,
  load/unload call counts) via mocks, not actual VRAM usage or wall-clock
  latency — that requires the real `llama-cpp-gpu` container and a GPU, which
  CI does not have. Validate actual VRAM headroom manually with `nvidia-smi`
  against the running stack (`make up`) before a release.
- **Load/performance testing.** No throughput or latency benchmarks run in
  this suite. Repeated ingest/search/chat cycles under real load should be
  driven manually against `make up` (or `make up-cpu`) using a tool like
  `hey`/`locust`, watching `/health/gpu` and `nvidia-smi` for growth in
  container restarts, lock contention, or memory that doesn't return to
  baseline between requests.
- **LlamaParse network calls.** `DocumentParser` is mocked; no test exercises
  a real LlamaParse API round-trip or its rate limits/timeouts.
