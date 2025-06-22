# VMware MCP Server Makefile

# Help
.PHONY: help
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

# Local development with uv
.PHONY: setup-uv
setup-uv: ## Sync dependencies from pyproject.toml (first time or anytime)
	cd mcp-server && uv sync

.PHONY: install
install: ## Sync dependencies from pyproject.toml
	cd mcp-server && uv sync

.PHONY: run-local
run-local: ## Run the MCP server locally using uv
	cd mcp-server && uv run python server.py

.PHONY: test
test: ## Test the power management functionality
	cd mcp-server && uv run python test_power_management.py

.PHONY: shell
shell: ## Start a Python shell with dependencies
	cd mcp-server && uv run python

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
	docker build -t vmware-mcp-server-clean .

.PHONY: run
run: ## Run the MCP server in Docker
	docker-compose up vmware-mcp-server-clean

.PHONY: run-detached
run-detached: ## Run the MCP server in Docker (detached)
	docker-compose up -d vmware-mcp-server-clean

.PHONY: docker-run
docker-run: ## Run the server directly in Docker (without docker-compose)
	docker run --rm -it \
		-e VCENTER_SERVER=$(VCENTER_SERVER) \
		-e VCENTER_USERNAME=$(VCENTER_USERNAME) \
		-e VCENTER_PASSWORD=$(VCENTER_PASSWORD) \
		-e VCENTER_INSECURE=$(VCENTER_INSECURE) \
		vmware-mcp-server-clean

.PHONY: stop
stop: ## Stop Docker containers
	docker-compose down

.PHONY: clean
clean: ## Clean up Docker resources
	docker-compose down --rmi all --volumes

.PHONY: logs
logs: ## View Docker logs
	docker-compose logs -f vmware-mcp-server-clean

.PHONY: all
all: setup build run ## Setup, build, and run Docker workflow

# Development helpers
.PHONY: lint
lint: ## Run linting (if configured)
	cd mcp-server && uv run python -m flake8 . || echo "Linting not configured"

.PHONY: format
format: ## Format code (if configured)
	cd mcp-server && uv run python -m black . || echo "Formatting not configured"

.PHONY: clean-files
clean-files: ## Clean up generated files
	cd mcp-server && rm -rf __pycache__ *.pyc .pytest_cache 