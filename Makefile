SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

COMPOSE ?= docker compose
APP ?= django

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available commands
	@echo "Smart Home Energy Management - Technical Interview"
	@echo "============================================================"
	@echo "Usage: make [command]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

#-------------------------------------------------------
# DOCKER / COMPOSE
#-------------------------------------------------------

.PHONY: build
build: ## Build containers
	$(COMPOSE) build

.PHONY: up
up: ## Start containers (foreground)
	$(COMPOSE) up

.PHONY: up-d
up-d: ## Start containers (detached)
	$(COMPOSE) up -d

.PHONY: down
down: ## Stop containers
	$(COMPOSE) down

.PHONY: reset
reset: ## Stop containers and remove volumes (fresh DB)
	$(COMPOSE) down -v

.PHONY: logs
logs: ## Tail logs for all services
	$(COMPOSE) logs -f --tail=200

.PHONY: ps
ps: ## List running services
	$(COMPOSE) ps

#-------------------------------------------------------
# APP COMMANDS
#-------------------------------------------------------

.PHONY: shell
shell: ## Exec into the app container
	$(COMPOSE) exec $(APP) bash

.PHONY: django-shell
django-shell: ## Django shell inside container
	$(COMPOSE) exec $(APP) python manage.py shell

.PHONY: migrate
migrate: ## Apply database migrations
	$(COMPOSE) exec $(APP) python manage.py migrate

.PHONY: makemigrations
makemigrations: ## Create new migrations
	$(COMPOSE) exec $(APP) python manage.py makemigrations

.PHONY: seed
seed: ## Seed the database with sample devices
	$(COMPOSE) exec $(APP) python manage.py seed
