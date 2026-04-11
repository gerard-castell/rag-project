# VRAM Optimization Design

**Date:** 2026-04-11
**Status:** Approved
**Context:** 6GB VRAM GPU; Ollama LLM (Gemma 4 e4b IT, ~4.6GB) + fastembed embedder (bge-m3, ~570MB) + reranker (bge-reranker-v2-m3, ~570MB)

---

## Problem

Ollama keeps its model resident in VRAM with a default 5-minute `keep_alive`. When the embedder or reranker borrows the GPU during ingestion or chat, combined VRAM usage (~5.7GB peak) risks OOM errors. Both the ingestion and chat flows are affected.

---

## VRAM Budget

| Consumer | VRAM | Notes |
|---|---|---|
| Gemma 4 e4b IT (Ollama) | ~4.6 GB | Resident while keep_alive active |
| bge-m3 (dense embedder) | ~570 MB | GPU borrowed sequentially, released immediately |
| bge-reranker-v2-m3 | ~570 MB | GPU borrowed sequentially after bge-m3 is back on CPU |
| **Peak (Ollama + one model)** | **~5.17 GB** | Technically fits, but fragmentation risk |
| **Total GPU** | **6.0 GB** | ~830 MB safety margin |

The embedder already moves models on/off GPU sequentially via the `_on_gpu` context manager. The problem is solely Ollama's persistent VRAM residency.

---

## Strategy: Combined A+B — VRAM-aware GPU time-sharing

Two rules:

1. **Ollama is evicted before embedding whenever free VRAM drops below `embedder_vram_budget_mb` (1200 MB).** For rapid sequential chats (Ollama loaded, VRAM still available), embedding runs without eviction.
2. **An `asyncio.Lock` serializes all GPU embedding operations.** Only one embedding or reranking operation runs at a time.

Ollama always uses `keep_alive: 60s` — the model unloads automatically after 60 seconds of inactivity.

---

## Architecture

### New files

**`src/core/vram_scheduler.py`** — GPU coordinator singleton

- `asyncio.Lock` for mutual exclusion on GPU embedding operations
- `schedule_embedding(embed_fn)` async context: checks free VRAM, optionally calls `OllamaClient.force_unload()`, then acquires the lock
- `force_evict_ollama()`: always evicts Ollama regardless of VRAM (used by ingestion)

**`src/core/ollama_client.py`** — VRAM-aware Ollama HTTP wrapper

- `get_loaded_models() -> list[str]`: `GET /api/ps` — returns currently loaded model names
- `force_unload(model: str)`: `POST /api/generate` with `keep_alive: 0` and empty prompt — forces immediate VRAM release
- `generate(payload: dict) -> dict`: normal generation, always injects `keep_alive: settings.ollama_keep_alive_seconds`

### Modified files

**`src/core/settings.py`** — two new settings:
- `ollama_keep_alive_seconds: int = 60`
- `embedder_vram_budget_mb: int = 1200`

**`src/services/chat.py`** — uses `VRAMScheduler.schedule_embedding()` around embed+rerank, then calls `OllamaClient.generate()`

**`src/services/ingestion.py`** — uses `VRAMScheduler.force_evict_ollama()` + lock before each embedding batch

**`src/api/dependencies.py`** — exposes `get_vram_scheduler()` and `get_ollama_client()` as cached singletons

---

## Flow

### Chat request (`POST /chat`)

```
1. VRAMScheduler.schedule_embedding():
   a. mem_get_info() → check free VRAM
   b. if free < 1200MB AND Ollama model loaded → OllamaClient.force_unload(model)
   c. acquire asyncio.Lock
2. embedder.generate([query])          ← bge-m3 on GPU, released after
3. embedder.rerank(query, passages)    ← reranker on GPU, released after
4. release asyncio.Lock
5. OllamaClient.generate(payload)      ← Ollama loads (if evicted) and generates
                                          keep_alive=60s set on every request
6. Return ChatResponse
```

### Ingestion batch (`POST /ingest` background task)

```
For each chunk batch:
1. VRAMScheduler.force_evict_ollama()  ← always evict; ingestion not latency-sensitive
2. acquire asyncio.Lock
3. embedder.generate(chunk_batch)
4. release asyncio.Lock
5. db.upsert_points(...)
```

### Idle

After 60s of no chat activity, Ollama's `keep_alive` timer expires and the model unloads automatically. VRAM returns to ~0 in use.

---

## Behavior Summary

| Scenario | Ollama VRAM | Action |
|---|---|---|
| Rapid sequential chats | Loaded, free VRAM > 1200MB | Embed immediately, Ollama stays warm |
| Chat after idle (>60s) | Not loaded | Embed immediately, Ollama reloads on generate |
| Chat during ingestion | Evicted by ingestion | Full reload on next chat generate |
| Ingestion (any state) | Always evicted | Embedding runs clean |

---

## Error handling

- If `GET /api/ps` fails (older Ollama version): skip the VRAM check, always evict before embedding to be safe
- If `force_unload` fails: log warning, proceed anyway — OOM will surface as a 500 from the embedder
- If CUDA OOM occurs during embedding: the exception propagates as a `RAGError`, returning HTTP 500 to the caller

---

## Configuration

All thresholds are in `settings.py` and tunable via environment variables:

| Setting | Default | Purpose |
|---|---|---|
| `OLLAMA_KEEP_ALIVE_SECONDS` | `60` | Seconds Ollama model stays in VRAM after last use |
| `EMBEDDER_VRAM_BUDGET_MB` | `1200` | Min free VRAM required to embed without evicting Ollama |
| `OLLAMA_URL` | `http://localhost:11434` | Already exists |

---

## Out of scope

- CPU or RAM offloading of any model
- Changing embedding model quality or size
- Multi-GPU support
- Concurrent multi-user request handling (single-user assumed)
