COMPOSE_FILE=docker-compose.yml
OLLAMA_MODEL=hf.co/unsloth/gemma-4-E4B-it-GGUF:Q4_K_M

.PHONY: help up run down restart logs logs-api status clean pull-model

help:
	@echo "Available commands:"
	@echo "  make up              - Build and start all containers, then pull the Ollama model"
	@echo "  make run             - Start containers in foreground with live logs"
	@echo "  make down            - Stop and remove containers"
	@echo "  make restart         - Restart all services"
	@echo "  make logs            - View real-time logs for all services"
	@echo "  make logs-api        - View real-time logs for the API only"
	@echo "  make logs-frontend   - View real-time logs for the frontend only"
	@echo "  make status          - Show container status"
	@echo "  make pull-model      - Pull the Ollama model into the running container"
	@echo "  make clean           - Stop containers and remove volumes (WARNING: deletes data)"
	@echo ""
	@echo "Frontend development:"
	@echo "  make frontend-dev    - Run frontend dev server (requires backend running)"
	@echo "  make frontend-build  - Build frontend for production"
	@echo "  make frontend-install- Install frontend dependencies"

up:
	docker compose -f $(COMPOSE_FILE) up -d --build
	$(MAKE) pull-model

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

pull-model:
	docker exec ollama-gpu ollama pull $(OLLAMA_MODEL)

logs-frontend:
	docker compose -f $(COMPOSE_FILE) logs -f frontend

clean:
	docker compose -f $(COMPOSE_FILE) down -v

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
