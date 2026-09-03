# RAG Project

A self-hosted, hybrid-search RAG (Retrieval-Augmented Generation) system: upload PDFs,
search them with dense + sparse vector retrieval, and chat over them with a locally
served LLM — all on a single GPU.

Backend is FastAPI + Qdrant + fastembed. The LLM runs in a llama.cpp container. A
`VRAMScheduler` time-shares the one available GPU between the embedding models and the
LLM so both fit on modest hardware. Frontend is Next.js.

## Architecture

```
┌────────────┐      /api/*        ┌──────────────┐
│  Next.js   │ ─────────────────► │   FastAPI    │
│  frontend  │  (rewrite proxy)   │   backend    │
│ (port 3000)│                    │  (port 8000) │
└────────────┘                    └──────┬───────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
                    ▼                     ▼                     ▼
             ┌─────────────┐      ┌──────────────┐      ┌───────────────┐
             │   Qdrant    │      │  LlamaParse   │      │  llama.cpp    │
             │ (port 6333) │      │ (external API,│      │  container    │
             │ hybrid      │      │  PDF parsing) │      │ (port 8080)   │
             │ vector store│      └──────────────┘      │  gemma-4-E4B  │
             └─────────────┘                             └───────────────┘
                    ▲
                    │  dense (BAAI/bge-m3) + sparse (SPLADE) embeddings,
                    │  generated in-process by the FastAPI container
                    └────────────────── GPU ──────────────────┘
                         time-shared by VRAMScheduler
```

- **Ingest**: `POST /ingest` saves the uploaded PDF, then a background task parses it
  with LlamaParse, splits the text, generates dense (`BAAI/bge-m3`) and sparse
  (`prithivida/Splade_PP_en_v1`, SPLADE) embeddings locally via `fastembed` /
  `sentence-transformers`, and upserts everything into Qdrant as named vectors
  (`dense-bge`, `sparse-splade`).
- **Search**: `POST /search` embeds the query and runs a hybrid Qdrant query
  (`Prefetch` on both vectors + `FusionQuery(RRF)`).
- **Chat**: `POST /chat` runs the same hybrid search, stuffs the retrieved chunks into a
  context-only system prompt, and sends it to the llama.cpp container's
  `/completion` endpoint.
- **VRAM scheduler**: see [GPU / VRAM constraint](#gpu--vram-constraint-and-the-vramscheduler) below.

Note: `BAAI/bge-reranker-v2-m3` is present as a configured setting
(`rerank_model_name`) but is **not currently wired into the search or chat path** —
no reranking step runs today. Treat it as reserved/planned, not active.

## Quickstart

Requires Docker, Docker Compose, an NVIDIA GPU + drivers (for the `llama-cpp` and
`api` containers, both request a GPU via Compose), and a
[LlamaParse API key](https://cloud.llamaindex.ai/).

```bash
git clone <this-repo>
cd rag-project

# 1. Download the LLM weights used by the llama.cpp container
make fetch-model

# 2. Set required env vars (see below), then build and start the full stack
make up
```

`make up` runs `docker compose up -d --build`, which starts four services: `qdrant`,
`llama-cpp`, `api`, and `frontend`.

- Frontend: http://localhost:3000
- API: http://localhost:8000 (docs at http://localhost:8000/docs)
- Qdrant: http://localhost:6333
- llama.cpp server: http://localhost:8080

Other useful targets: `make down`, `make restart`, `make logs` / `make logs-api` /
`make logs-frontend`, `make status`, `make clean` (also removes volumes), `make lint`,
`make test`. For local (non-Docker) dev: `make frontend-dev`,
`make frontend-install`, `uv run uvicorn src.main:app --reload`.

## Environment variables

Set in a `.env` file at the repo root (loaded by both `uv run` and the `api` service
via `env_file: .env` in `docker-compose.yml`). No `.env.example` currently ships in
the repo — the table below is the full set of settings from `src/core/settings.py`.

| Variable | Required | Default | Notes |
|---|---|---|---|
| `LLAMA_PARSE_API_KEY` | **Yes** | — | LlamaParse API key, used for PDF parsing |
| `QDRANT_URL` | No | `http://localhost:6333` | Overridden to `http://qdrant:6333` inside Docker Compose |
| `COLLECTION_NAME` | No | `knowledge_base` | Qdrant collection name |
| `UPLOAD_DIR` | No | `temp_uploads` | Where uploaded PDFs are staged |
| `MODELS_CACHE_DIR` | No | `models_cache` | fastembed/sentence-transformers cache |
| `CHUNK_SIZE` | No | `800` | Text splitter chunk size |
| `CHUNK_OVERLAP` | No | `100` | Text splitter chunk overlap |
| `DENSE_MODEL_NAME` | No | `BAAI/bge-m3` | Dense embedding model |
| `SPARSE_MODEL_NAME` | No | `prithivida/Splade_PP_en_v1` | Sparse (SPLADE) embedding model |
| `EMBEDDING_BATCH_SIZE` | No | `8` | Batch size for embedding generation |
| `INGESTION_BATCH_SIZE` | No | `32` | Batch size for Qdrant upserts |
| `SPARSE_MODEL_THREADS` | No | `4` | ONNX runtime threads for the sparse model |
| `RERANK_MODEL_NAME` | No | `BAAI/bge-reranker-v2-m3` | Configured but not yet used (see note above) |
| `LLAMA_CPP_URL` | No | `http://localhost:8080` | Overridden to `http://llama-cpp:8080` inside Docker Compose |
| `LLAMA_CPP_MODEL_NAME` | No | `gemma-4-E4B-it-Q4_K_M` | Reported back in `/chat` responses |
| `LLAMA_CONTAINER_NAME` | No | `llama-cpp-gpu` | Docker container name the VRAMScheduler starts/stops |
| `LLAMA_IDLE_TIMEOUT_SECONDS` | No | `300` | Seconds of chat inactivity before the llama.cpp container is stopped |
| `DEFAULT_SEARCH_LIMIT` | No | `5` | Default `/search` result count |
| `RETRIEVAL_LIMIT` | No | `15` | Chunks retrieved for `/chat` context |
| `PREFETCH_MULTIPLIER` | No | `2` | Multiplier applied to each hybrid-search prefetch leg |

## Endpoint reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check; also reports the detected GPU/CPU device |
| `POST` | `/ingest` | Upload a PDF (`multipart/form-data`); returns `202` and queues background parsing + embedding + upsert into Qdrant |
| `POST` | `/search` | Hybrid (dense + sparse, RRF-fused) vector search over ingested documents |
| `POST` | `/chat` | Hybrid search + context-grounded completion via the llama.cpp container |

Full request/response schemas are available at `/docs` (Swagger UI) once the API is
running.

## GPU / VRAM constraint (and the VRAMScheduler)

This project is built to run entirely on a single consumer GPU, which is not big
enough to keep the embedding models and the LLM resident in VRAM at the same time.
Rather than run everything simultaneously and risk an out-of-memory crash, the
`api` container includes a `VRAMScheduler` (`src/core/vram_scheduler.py`) that
strictly time-shares the GPU:

- A single `asyncio.Lock` serializes all GPU work, so embedding generation and LLM
  generation never run concurrently.
- **Embedding models** (dense BGE + sparse SPLADE) are loaded/unloaded in-process
  around each use (`schedule_embedding`), releasing CUDA memory (`torch.cuda.empty_cache()`)
  when idle.
- **The LLM** runs in its own Docker container (`llama-cpp-gpu`, built from
  `ghcr.io/ggml-org/llama.cpp:full-cuda`). The scheduler controls its lifecycle
  directly through the Docker Engine API (the `api` container mounts
  `/var/run/docker.sock` for this), starting it on demand for `/chat`
  (`schedule_generation`, which polls the llama.cpp `/health` endpoint until ready)
  and stopping it automatically after `LLAMA_IDLE_TIMEOUT_SECONDS` (default 300s) of
  inactivity via a background idle watcher.
- This means the first chat request after a period of inactivity pays a container
  start + model load latency cost, in exchange for embedding and ingestion work
  never being starved of VRAM by an LLM sitting loaded but idle.

The project originally targeted an Ollama-based setup on a 6GB-class GPU, where the
combined footprint of the LLM (~4.6GB) plus the embedding and reranking models
(~0.5–0.6GB each) would have exceeded available VRAM if all were resident at once.
The LLM serving layer was later moved from Ollama to a llama.cpp container, but the
same underlying constraint — one GPU, more model memory than it can hold at once —
is why the scheduler exists.

## Learning roadmap

[`steps.md`](./steps.md) is the running log of the sprint-by-sprint plan this project
was built against (in Spanish), from initial ingestion/search through hybrid
retrieval, reranking, an agentic layer, and evaluation.

## Evaluation results

_Not yet available._ A RAGAS-based evaluation of retrieval and answer quality is
planned but not implemented in this repo yet — results will be added to this section
once that work lands.

## Development

```bash
uv run uvicorn src.main:app --reload   # run the API locally (needs Qdrant/llama.cpp reachable)
uv run pytest                          # run tests
uv run ruff check . && uv run ruff format . && uv run mypy src/   # lint/type-check
```

See [`CLAUDE.md`](./CLAUDE.md) for a more detailed architecture/code-style guide aimed
at contributors and AI coding agents.
