# AGENTS.md
Guidance for AI coding agents working in this repo.

## Commands

```bash
make fetch-model              # download the llama.cpp GGUF model into models/
make up                       # docker compose up -d --build (qdrant, llama-cpp, api, frontend)
make down                     # docker compose down
make logs / logs-api / logs-frontend
cd backend && uv run python -m src.main
cd backend && uv run uvicorn src.main:app --reload
cd backend && uv run pytest
cd backend && uv run pytest tests/integration/test_api.py
cd backend && uv run ruff check .
cd backend && uv run ruff format .
cd backend && uv run mypy src/
```

`make up` runs the full Compose stack (`qdrant`, `llama-cpp`, `api`, `frontend`) — don't
run Qdrant manually. See `README.md` for the full quickstart, env vars, and endpoint
reference.

## Architecture

FastAPI backend for PDF ingestion, hybrid vector search, and LLM-backed chat, paired
with a Next.js frontend and a llama.cpp container for generation.

**Request flow:**

1. `POST /ingest` — saves the PDF to `temp_uploads/`, queues a background task
   (`run_ingestion_logic` in `backend/src/services/ingestion.py`) that parses via
   LlamaParse, splits text, generates dense+sparse embeddings, and upserts into Qdrant.
2. `POST /search` — embeds the query and runs hybrid search (dense BGE + sparse SPLADE)
   with RRF fusion via Qdrant.
3. `POST /chat` — same hybrid search, assembles a context-only prompt, sends it to the
   llama.cpp container's `/completion` endpoint (`backend/src/services/chat.py`).
4. `GET /health` — liveness check, reports the detected GPU/CPU device.

**Key layers:**
- `backend/src/core/` — settings, logger, `RAGError` exception hierarchy,
  `LlamaCppClient`, `VRAMScheduler`
- `backend/src/ingestion/` — `DocumentParser` (LlamaParse), `LocalEmbedder` (fastembed /
  sentence-transformers, BAAI/bge-m3 + SPLADE), `VectorDB` (Qdrant client)
- `backend/src/services/` — business logic for ingestion, search, chat
- `backend/src/api/routes/` — FastAPI routers (`health`, `ingest`, `search`, `chat`);
  singletons in `backend/src/api/dependencies.py`
- `backend/src/schemas/` — Pydantic request/response models
- `frontend/` — Next.js UI, proxies `/api/*` to `BACKEND_URL`
  (`frontend/next.config.ts`, `frontend/src/lib/api.ts`)

**Embedding strategy:** hybrid dense (`dense-bge`) + sparse (`sparse-splade`) named
vectors in Qdrant, fused with `Prefetch` + `FusionQuery(RRF)`. A
`BAAI/bge-reranker-v2-m3` cross-encoder is configured (`rerank_model_name`) but **not
wired into** `search.py` or `chat.py` — reserved/planned, unless you're the one adding it.

**GPU / VRAM constraint:** one GPU can't hold the embedding models and the LLM at once.
`VRAMScheduler` (`backend/src/core/vram_scheduler.py`) enforces time-sharing via a single
`asyncio.Lock`: `schedule_embedding()` loads/unloads `LocalEmbedder` in-process per use;
`schedule_generation()` starts the `llama-cpp-gpu` container on demand (Docker Engine
API over `/var/run/docker.sock`), waits for its `/health`, and stops it after
`LLAMA_IDLE_TIMEOUT_SECONDS` (default 300s) idle. Both paths share the lock, so
embedding and generation never run concurrently on the GPU.

**Dependency injection:** `get_embedder()`, `get_vector_db()`, `get_llama_client()`,
`get_vram_scheduler()` in `backend/src/api/dependencies.py` are `lru_cache` singletons.
The embedder is loaded/unloaded per-request via `VRAMScheduler.schedule_embedding()`,
not pre-loaded at startup. The idle watcher starts/stops via the FastAPI lifespan in
`backend/src/main.py`.

## Code Style

- Ruff strict (pydocstring PEP257, isort, bugbear): `ruff check . && ruff format .`
- mypy strict, `disallow_any_explicit = true` — all functions typed
- Double quotes, 88-char lines
- No multiline docstrings/comments unless critical; prefer single-line
- Inline comments only for non-obvious invariants, workarounds, or "why" — never restate
  the code, in any file type
- Address PR review feedback per the specific comment, not a generic fix

## Agent Skills

Skills live in `.agents/skills/` — the single source of truth. Gemini CLI and OpenCode
treat it as an alias natively; `.claude/skills` is a symlink to `../.agents/skills`. Add
new skills only under `.agents/skills/` — don't recreate per-tool skill folders.

## Git Conventions

Run `make hooks` once per clone (commit-msg format, branch name warning).

**Commits & PR titles** — Conventional Commits, no trailing period:
```
<type>(<scope>): <short imperative description>
```
`type`: `feat fix docs chore refactor perf test ci build`. `scope` optional, lowercase
(`api`, `ingestion`, `frontend`). Reference the issue in the body, not the subject:
```
fix(ingestion): handle empty pdf uploads

Closes #34
```
PR titles are checked in CI (`.github/workflows/pr-title.yml`) and become the
squash-merge commit message.

**Branches:**
```
<type>/<issue-number>-<short-slug>
```
e.g. `feat/34-add-health-endpoint`, `fix/47-search-timeout`.

Follow this convention for commits, branches, and PRs without being re-told.
