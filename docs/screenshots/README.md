# Screenshots

Real captures for the top-level `README.md` "Screenshots & demo" section go here.
Nothing in this folder is auto-generated — no headless browser was available in the
environment that scaffolded this repo pass, so these are placeholders until captured
manually.

## What to capture

1. `upload.png` — the upload/ingest view mid- or post-upload, showing ingestion status.
2. `chat.png` — a chat turn with the answer and its retrieved-source citations visible.
3. `demo.gif` (optional) — a short end-to-end loop: drag a PDF in, ask a question, get a
   grounded answer. Keep it under ~15s / ~5MB (tools like
   [Peek](https://github.com/phw666/peek) or `ffmpeg` from a `.mov` work well).

## How

```bash
make up        # or `make up-cpu` if you don't have an NVIDIA GPU
# open http://localhost:3000, upload a PDF, ask it a question
```

Crop to the app viewport only (no browser chrome/tabs), PNG format, roughly
1200–1600px wide, each file under ~1MB. Save into this folder using the filenames
above, then update the table in the root `README.md`'s "Screenshots & demo" section to
point at them instead of the "screenshot pending" placeholders.
