# Screenshots

Captures used by the "Screenshots & demo" section of the root [`README.md`](../../README.md).

| File | Shows |
| --- | --- |
| `chat.png` | A chat turn: question, and an answer generated locally from retrieved chunks |
| `search.png` | Hybrid search results with source file, page, and relevance score |
| `documents.png` | The indexed-documents view (page and chunk counts) |
| `upload.png` | The upload dialog's drag-and-drop zone |

All four are real captures of the running stack against an ingested copy of NVIDIA's
public FY2024 Corporate Sustainability Report — no mockups, no edited text.

## Recapturing

Start the stack (`make up`, or `make up-cpu` without an NVIDIA GPU) and open
http://localhost:3000. These were captured from the production frontend container at a
1360x800 viewport at 2x device scale, cropped to the app viewport only (no browser
chrome). Keep each PNG under ~1MB.

Warm the stack before shooting: the first `/search` after startup loads the embedding
models (~1 min) and the first `/chat` starts the llama.cpp container, which can exceed
the scheduler's readiness budget and render a warm-up notice instead of an answer.

If you capture from `next dev` instead, set `devIndicators: false` in
`frontend/next.config.ts` first so the dev badge stays out of the shot, and revert it
afterwards. `next dev` also re-appends a Next.js agent-rules block to
`frontend/AGENTS.md`; that block was removed deliberately (#67), so discard it before
committing.
