# CLAUDE.md
This file provides guidance to Claude Code.

## Commands

```bash
make fetch-model              # download the llama.cpp GGUF model into models/
make up                       # docker compose up -d --build (qdrant, llama-cpp, api, frontend)
make down                     # docker compose down
make logs / logs-api / logs-frontend
uv run python -m src.main
uv run uvicorn src.main:app --reload
uv run pytest
uv run pytest tests/integration/test_api.py
uv run ruff check .
uv run ruff format .
uv run mypy src/
```

`docker compose` (via `make up`) runs the full stack: `qdrant`, `llama-cpp`, `api`,
`frontend`. Do not run Qdrant manually — `make up` starts it as part of Compose. See
`README.md` for the full quickstart, env vars, and endpoint reference.

## Architecture

This is a FastAPI-based RAG system for PDF ingestion, hybrid vector search, and
LLM-backed chat, paired with a Next.js frontend and a llama.cpp container for
generation.

**Request flow:**

1. `POST /ingest` — accepts a PDF, saves it to `temp_uploads/`, and queues a background
   task (`run_ingestion_logic` in `src/services/ingestion.py`)
2. The background task: parses PDF via LlamaParse → splits text → generates dense+sparse
   embeddings → upserts into Qdrant
3. `POST /search` — embeds the query, runs a hybrid search (dense BGE + sparse SPLADE)
   with RRF fusion via Qdrant
4. `POST /chat` — runs the same hybrid search, assembles a context-only prompt, and
   sends it to the llama.cpp container's `/completion` endpoint (`src/services/chat.py`)
5. `GET /health` — liveness check, also reports the detected GPU/CPU device

**Key layers:**
- `src/core/` — settings (Pydantic), logger, custom exceptions (`RAGError` hierarchy),
  `LlamaCppClient` (HTTP client for the llama.cpp container), `VRAMScheduler`
  (GPU time-sharing, see below)
- `src/ingestion/` — `DocumentParser` (LlamaParse), `LocalEmbedder` (fastembed /
  sentence-transformers, BAAI/bge-m3 + SPLADE), `VectorDB` (Qdrant client)
- `src/services/` — business logic for ingestion, search, and chat (called from routes)
- `src/api/routes/` — FastAPI routers (`health`, `ingest`, `search`, `chat`);
  dependencies (embedder/db/llama client/scheduler singletons) in
  `src/api/dependencies.py`
- `src/schemas/` — Pydantic request/response models
- `frontend/` — Next.js (App Router) UI; calls the backend through a `/api/*` rewrite
  proxy to `BACKEND_URL` (see `frontend/next.config.ts`, `frontend/src/lib/api.ts`)

**Embedding strategy:** Hybrid — dense vectors (`dense-bge`) + sparse vectors
(`sparse-splade`) stored as named vectors in Qdrant. Search uses `Prefetch` +
`FusionQuery(RRF)`. A `BAAI/bge-reranker-v2-m3` cross-encoder is configured
(`rerank_model_name` setting) but is **not currently invoked** in `search.py` or
`chat.py` — treat it as reserved/planned, not part of the live request path, unless
you are the one wiring it in.

**GPU / VRAM constraint:** the project targets a single GPU that cannot hold the
embedding models and the LLM in VRAM simultaneously. `VRAMScheduler`
(`src/core/vram_scheduler.py`) enforces strict time-sharing via one `asyncio.Lock`:
- `schedule_embedding()` loads/unloads `LocalEmbedder` in-process around each use.
- `schedule_generation()` starts the `llama-cpp-gpu` Docker container on demand
  (via the Docker Engine API, over the `/var/run/docker.sock` mount in
  `docker-compose.yml`), waits for its `/health` endpoint, and lets a background idle
  watcher stop the container after `LLAMA_IDLE_TIMEOUT_SECONDS` (default 300s) of
  inactivity.
Both code paths go through the same lock, so embedding and LLM generation never run
concurrently on the GPU.

**Dependency injection:** `get_embedder()`, `get_vector_db()`, `get_llama_client()`,
and `get_vram_scheduler()` in `src/api/dependencies.py` are `lru_cache`-backed
singletons. The embedder is **not** pre-loaded at startup — it is loaded and unloaded
per-request through `VRAMScheduler.schedule_embedding()`. The `VRAMScheduler`'s idle
watcher is started/stopped via the FastAPI lifespan in `src/main.py`.

## Code Style

- Ruff with strict rules (pydocstring PEP257, isort, bugbear); `ruff check . && ruff format .`
- mypy strict mode — all functions must be typed; `disallow_any_explicit = true`
- Double quotes, 88-char line length
- No multiline docstrings/comments unless critical (e.g. explaining a non-obvious invariant or bug workaround); prefer a single-line docstring
- Inline comments only when strictly necessary (e.g. a non-obvious invariant, workaround, or "why" that isn't clear from the code itself) — do not restate what the code already says, in any file type (code, YAML, config, etc.)
- When addressing PR review feedback, follow the specific guidance left in each comment rather than a generic fix

## Agent Skills

Skills live in `.agents/skills/` — the single source of truth. Gemini CLI and
OpenCode both natively treat `.agents/skills/` as an alias, so they need no
copy of their own. Claude Code only scans `.claude/skills/`, so `.claude/skills`
is a symlink to `../.agents/skills`. Add new skills under `.agents/skills/`
only; do not recreate `.agent/`, `.gemini/`, or other per-tool skill folders.

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
