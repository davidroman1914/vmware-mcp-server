# VMware vSphere VM List Makefile

# Help
.PHONY: help
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

# Local development with uv
.PHONY: setup-uv
setup-uv: ## Sync dependencies from pyproject.toml (first time or anytime)
	uv sync

.PHONY: install
install: ## Sync dependencies from pyproject.toml
	uv sync

.PHONY: run-local
run-local: ## Run the MCP server locally using uv
	uv run python server.py

.PHONY: shell
shell: ## Start a Python shell with dependencies
	uv run python

# Docker workflow
.PHONY: setup
setup: ## Create .env file from template if needed
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "Created .env file. Please edit it with your vCenter credentials."; \
	else \
		echo ".env file already exists."; \
	fi

.PHONY: build
build: ## Build Docker image
	docker-compose build

.PHONY: run
run: ## Run the MCP server in Docker
	docker-compose up

.PHONY: run-detached
run-detached: ## Run the MCP server in Docker (detached)
	docker-compose up -d

.PHONY: stop
stop: ## Stop Docker containers
	docker-compose down

.PHONY: clean
clean: ## Clean up Docker resources
	docker-compose down --rmi all --volumes

.PHONY: logs
logs: ## View Docker logs
	docker-compose logs -f

.PHONY: all
all: setup build run ## Setup, build, and run Docker workflow 