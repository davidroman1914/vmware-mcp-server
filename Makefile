# VMware MCP Server Makefile

.PHONY: help build run test install clean

help: ## Show available commands
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

setup: ## Create .env file from template
	@if [ ! -f .env ]; then cp env.example .env; echo "Created .env file"; else echo ".env file exists"; fi

install: ## Install dependencies
	pip install -r requirements.txt

run: ## Run server locally
	cd mcp-server && python server.py

test: ## Test server locally
	python tests/test_maintenance.py

test-all: ## Run all tests
	python -m pytest tests/ -v

build: ## Build Docker image
	docker build -t vmware-mcp-server .

run-docker: ## Run in Docker
	docker-compose up vmware-mcp-server

test-docker: ## Test in Docker
	docker run --rm --env-file .env vmware-mcp-server python tests/test_maintenance.py

clean: ## Clean up
	docker-compose down --rmi all --volumes
	rm -rf __pycache__ mcp-server/__pycache__ tests/__pycache__
	find . -name "*.pyc" -delete
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true 