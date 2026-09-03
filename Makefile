COMPOSE_FILE=docker-compose.yml
MODEL_DIR=models
MODEL_FILE=$(MODEL_DIR)/gemma-4-E4B-it-Q4_K_M.gguf
MODEL_REPO=unsloth/gemma-4-E4B-it-GGUF
MODEL_REPO_FILE=gemma-4-E4B-it-Q4_K_M.gguf

.PHONY: help up run down restart logs logs-api logs-frontend status clean \
	frontend-dev frontend-build frontend-install frontend-type-check frontend-lint \
	fetch-model lint test hooks

help:
	@echo "Available commands:"
	@echo "  make up              - Build and start all containers (requires make fetch-model first)"
	@echo "  make run             - Start containers in foreground with live logs"
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

up:
	@if [ ! -f "$(MODEL_FILE)" ]; then \
		echo "Error: model file $(MODEL_FILE) not found."; \
		echo "Run 'make fetch-model' first."; \
		exit 1; \
	fi
	docker compose -f $(COMPOSE_FILE) up -d --build

run:
	docker compose -f $(COMPOSE_FILE) up --build

down:
	docker compose -f $(COMPOSE_FILE) down

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
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src/

test:
	uv run pytest

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
