COMPOSE_FILE=docker-compose.yml
COMPOSE_FILE_CPU=docker-compose.yml -f docker-compose.cpu.yml
MODEL_DIR=models
MODEL_FILE=$(MODEL_DIR)/gemma-4-E4B-it-Q4_K_M.gguf
MODEL_REPO=unsloth/gemma-4-E4B-it-GGUF
MODEL_REPO_FILE=gemma-4-E4B-it-Q4_K_M.gguf

.PHONY: help up up-cpu run run-cpu down restart logs logs-api logs-frontend status clean \
	check-gpu check-model \
	frontend-dev frontend-build frontend-install frontend-type-check frontend-lint \
	fetch-model lint test hooks

help:
	@echo "Available commands:"
	@echo "  make up              - Build and start all containers (requires an NVIDIA GPU; make fetch-model first)"
	@echo "  make up-cpu          - Same as 'make up', but CPU-only (no GPU required, slower)"
	@echo "  make run             - Start containers in foreground with live logs"
	@echo "  make run-cpu         - Same as 'make run', but CPU-only"
	@echo "  make down            - Stop and remove containers"
	@echo "  make restart         - Restart all services"
	@echo "  make logs            - View real-time logs for all services"
	@echo "  make logs-api        - View real-time logs for the API only"
	@echo "  make logs-frontend   - View real-time logs for the frontend only"
	@echo "  make status          - Show container status"
	@echo "  make fetch-model     - Download the llama.cpp GGUF model into ./models/"
	@echo "  make clean           - Stop containers and remove volumes (WARNING: deletes data)"
	@echo "  make lint            - Run ruff and mypy checks"
	@echo "  make test            - Run the test suite"
	@echo "  make hooks           - Install commit-msg/pre-push git hooks (commit convention)"
	@echo ""
	@echo "Frontend development:"
	@echo "  make frontend-dev    - Run frontend dev server (requires backend running)"
	@echo "  make frontend-build  - Build frontend for production"
	@echo "  make frontend-install- Install frontend dependencies"

up: check-gpu check-model
	docker compose -f $(COMPOSE_FILE) up -d --build

up-cpu: check-model
	docker compose -f $(COMPOSE_FILE_CPU) up -d --build

run: check-gpu check-model
	docker compose -f $(COMPOSE_FILE) up --build

run-cpu: check-model
	docker compose -f $(COMPOSE_FILE_CPU) up --build

down:
	docker compose -f $(COMPOSE_FILE) down

check-gpu:
	@if ! command -v nvidia-smi >/dev/null 2>&1 || ! nvidia-smi >/dev/null 2>&1; then \
		echo "Error: no NVIDIA GPU detected (nvidia-smi not found or failed)."; \
		echo "'make up' requires an NVIDIA GPU + drivers + the NVIDIA Container Toolkit"; \
		echo "(see 'Hardware requirements' in README.md)."; \
		echo "Run 'make up-cpu' instead for a slower, GPU-free demo."; \
		exit 1; \
	fi

check-model:
	@if [ ! -f "$(MODEL_FILE)" ]; then \
		echo "Error: model file $(MODEL_FILE) not found."; \
		echo "Run 'make fetch-model' first."; \
		exit 1; \
	fi

restart:
	docker compose -f $(COMPOSE_FILE) restart

logs:
	docker compose -f $(COMPOSE_FILE) logs -f

logs-api:
	docker compose -f $(COMPOSE_FILE) logs -f api

status:
	docker compose -f $(COMPOSE_FILE) ps

logs-frontend:
	docker compose -f $(COMPOSE_FILE) logs -f frontend

clean:
	docker compose -f $(COMPOSE_FILE) down -v

fetch-model:
	@if [ -f "$(MODEL_FILE)" ]; then \
		echo "Model already present at $(MODEL_FILE), skipping download."; \
	else \
		mkdir -p $(MODEL_DIR); \
		huggingface-cli download $(MODEL_REPO) $(MODEL_REPO_FILE) \
			--local-dir $(MODEL_DIR) --local-dir-use-symlinks False; \
	fi

lint:
	cd backend && uv run ruff check .
	cd backend && uv run ruff format --check .
	cd backend && uv run mypy src/

test:
	cd backend && uv run pytest

hooks:
	git config core.hooksPath .githooks
	@echo "Git hooks enabled (.githooks) — commit messages and branch names are now checked."

frontend-dev:
	cd frontend && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev

frontend-build:
	cd frontend && npm run build

frontend-install:
	cd frontend && npm install

frontend-type-check:
	cd frontend && npx tsc --noEmit

frontend-lint:
	cd frontend && npx next lint
