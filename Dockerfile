# Stage 1 — builder: install dependencies with uv into an isolated venv
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml .
RUN uv sync --no-dev --no-cache

# Stage 2 — runtime: slim Python image
# PyTorch >=2.6 and onnxruntime-gpu >=1.24 bundle their own CUDA runtime libraries.
# GPU access is provided by the NVIDIA Container Toolkit on the host — no CUDA base image needed.
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY src/ src/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
