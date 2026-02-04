COMPOSE_FILE=docker-compose.yml

.PHONY: help up down restart logs status clean

help:
	@echo "Available commands:"
	@echo "  make up      - Start containers in background and pull images"
	@echo "  make run     - Start containers and show logs"
	@echo "  make down    - Stop and remove containers"
	@echo "  make restart - Restart all services"
	@echo "  make logs    - View real-time logs"
	@echo "  make clean   - Stop and remove volumes (WARNING: deletes data)"

up:
	docker compose -f $(COMPOSE_FILE) up -d --build

run:
	docker compose -f $(COMPOSE_FILE) up --build

down:
	docker compose -f $(COMPOSE_FILE) down

restart:
	docker compose -f $(COMPOSE_FILE) restart

logs:
	docker compose -f $(COMPOSE_FILE) logs -f

status:
	docker compose -f $(COMPOSE_FILE) ps

clean:
	docker compose -f $(COMPOSE_FILE) down -v