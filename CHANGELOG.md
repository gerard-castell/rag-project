# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/) (`vMAJOR.MINOR.PATCH`).
See the [Release process](./README.md#release-process) section of the README for what
each version segment means and when a release gets cut.

## [Unreleased]

## [0.1.0] - 2026-09-08

Phase 0: the project boots and runs end-to-end for the first time — ingest a PDF,
search it, chat over it, on a single consumer GPU.

### Added

- FastAPI backend with `POST /ingest`, `POST /search`, `POST /chat`, `GET /health`.
- Hybrid retrieval: dense (`BAAI/bge-m3`) + sparse (SPLADE) embeddings fused with RRF
  in Qdrant.
- LLM generation via a llama.cpp container, called from `/chat`.
- `VRAMScheduler`: time-shares the single GPU between the embedding models and the
  LLM, starting/stopping the llama.cpp container on demand via the Docker Engine API.
- Ingestion status endpoint and per-document progress tracking.
- Document persistence, deletion, and per-document search/chat scoping.
- Next.js frontend with a unified UI redesign, restructured by feature with a typed
  API layer.
- Docker Compose stack (`qdrant`, `llama-cpp`, `api`, `frontend`) and `Makefile`
  targets (`make up`, `make down`, `make fetch-model`, `make logs`, `make lint`,
  `make test`).
- CI: backend/frontend lint + test workflows, PR title convention checks, commit
  hooks, Dependabot.
- `LICENSE` and package metadata.
- README and `AGENTS.md`/`CLAUDE.md` documentation for contributors and AI agents.

### Fixed

- `POST /search` 500 caused by the embedder never loading.
- VRAM thrashing and unhandled scheduler failures under load.
- Docker socket exposure: the `api` container no longer mounts `/var/run/docker.sock`
  directly — a `docker-socket-proxy` scopes it to `CONTAINERS`/`START`/`STOP` only.
- `/ingest` hardening: filename sanitized against path traversal, magic-byte PDF
  check, enforced upload size cap.
- Reproducible Docker builds, correct proxy target, GPU sparse embeddings.
- Leftover Ollama references removed from the Makefile after the move to llama.cpp.

### Changed

- Backend moved into `backend/` for symmetry with `frontend/`.
- Consistent `RAGError` → HTTP status mapping; dead code removed; test coverage
  raised.
- `AGENTS.md` established as the primary instructions file for AI coding agents.

[Unreleased]: https://github.com/gerard-castell/rag-project/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/gerard-castell/rag-project/releases/tag/v0.1.0
