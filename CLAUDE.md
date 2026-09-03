# CLAUDE.md
This file provides guidance to Claude Code.

## Commands

```bash
uv run python -m src.main
uv run uvicorn src.main:app --reload
uv run pytest
uv run pytest tests/integration/test_api.py
uv run ruff check .
uv run ruff format .
uv run mypy src/
```

Qdrant must be running locally at `http://localhost:6333`.

## Architecture

This is a FastAPI-based RAG API for PDF ingestion and hybrid vector search.

**Request flow:**

1. `POST /ingest` — accepts a PDF, saves it to `temp_uploads/`, and queues a background task (`run_ingestion_logic` in `src/services/ingestion.py`)
2. The background task: parses PDF via LlamaParse → splits text → generates dense+sparse embeddings → upserts into Qdrant
3. `POST /search` — embeds the query, runs a hybrid search (dense BGE + sparse SPLADE) with RRF fusion via Qdrant

**Key layers:**
- `src/core/` — settings (Pydantic), logger, custom exceptions (`RAGError` hierarchy)
- `src/ingestion/` — `DocumentParser` (LlamaParse), `LocalEmbedder` (fastembed, BAAI/bge-m3 + SPLADE), `VectorDB` (Qdrant client)
- `src/services/` — business logic for ingestion and search (called from routes)
- `src/api/routes/` — FastAPI routers; dependencies (embedder/db singletons) in `src/api/dependencies.py`
- `src/schemas/` — Pydantic request/response models

**Embedding strategy:** Hybrid — dense vectors (`dense-bge`) + sparse vectors (`sparse-splade`) stored as named vectors in Qdrant. Search uses `Prefetch` + `FusionQuery(RRF)`.

**Dependency injection:** `get_embedder()` and `get_vector_db()` in `src/api/dependencies.py` are cached singletons. The embedder is pre-loaded at startup via the FastAPI lifespan.

## Code Style

- Ruff with strict rules (pydocstring PEP257, isort, bugbear); `ruff check . && ruff format .`
- mypy strict mode — all functions must be typed; `disallow_any_explicit = true`
- Double quotes, 88-char line length
- No multiline docstrings/comments unless critical (e.g. explaining a non-obvious invariant or bug workaround); prefer a single-line docstring
- When addressing PR review feedback, follow the specific guidance left in each comment rather than a generic fix

## Git Conventions

Run `make hooks` once per clone to enable local checks (commit-msg format, branch name warning).

**Commits & PR titles** — Conventional Commits, no period at the end:
```
<type>(<scope>): <short imperative description>
```
`type` is one of `feat fix docs chore refactor perf test ci build`. `scope` is optional, lowercase, names the affected area (e.g. `api`, `ingestion`, `frontend`). Reference the issue in the body, not the subject:
```
fix(ingestion): handle empty pdf uploads

Closes #34
```
A PR title must match this same format — it's checked in CI (`.github/workflows/pr-title.yml`) and becomes the squash-merge commit message.

**Branches**:
```
<type>/<issue-number>-<short-slug>
```
e.g. `feat/34-add-health-endpoint`, `fix/47-search-timeout`. Same `type` list as commits.

When asked to create a commit, branch, or PR, follow this convention without being re-told.
