# API reference

Written summary of the endpoints in `backend/src/api/routes/`. For full request/response
schemas, use the Swagger UI at `/docs` once the API is running.

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check; also reports the detected GPU/CPU device |
| `POST` | `/ingest` | Upload a PDF (`multipart/form-data`); returns `202` and queues background parsing + embedding + upsert into Qdrant |
| `POST` | `/search` | Hybrid (dense + sparse, RRF-fused) vector search over ingested documents |
| `POST` | `/chat` | Hybrid search + context-grounded completion via the llama.cpp container |
