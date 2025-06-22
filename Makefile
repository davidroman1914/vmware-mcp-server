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
	uv run python main.py

.PHONY: run-server
run-server: ## Run the MCP server directly
	uv run python mcp-server/server.py

.PHONY: shell
shell: ## Start a Python shell with dependencies
	uv run python

# Clean vmware-vcenter server targets
.PHONY: run-vmware-server
run-vmware-server: ## Run the clean vmware-vcenter MCP server locally
	cd mcp-server-vmware && python server.py

.PHONY: test-vmware-server
test-vmware-server: ## Test the clean vmware-vcenter MCP server
	cd mcp-server-vmware && python test_server.py

.PHONY: install-vmware
install-vmware: ## Install dependencies for clean vmware-vcenter server
	cd mcp-server-vmware && pip install -r requirements.txt

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

.PHONY: build-vmware
build-vmware: ## Build only the clean vmware-vcenter Docker image
	docker-compose build vmware-vcenter-server

.PHONY: run
run: ## Run the MCP server in Docker
	docker-compose up

.PHONY: run-vmware
run-vmware: ## Run the clean vmware-vcenter server in Docker
	docker-compose up vmware-vcenter-server

.PHONY: run-detached
run-detached: ## Run the MCP server in Docker (detached)
	docker-compose up -d

.PHONY: run-vmware-detached
run-vmware-detached: ## Run the clean vmware-vcenter server in Docker (detached)
	docker-compose up -d vmware-vcenter-server

.PHONY: stop
stop: ## Stop Docker containers
	docker-compose down

.PHONY: clean
clean: ## Clean up Docker resources
	docker-compose down --rmi all --volumes

.PHONY: logs
logs: ## View Docker logs
	docker-compose logs -f

.PHONY: logs-vmware
logs-vmware: ## View clean vmware-vcenter server logs
	docker-compose logs -f vmware-vcenter-server

.PHONY: all
all: setup build run ## Setup, build, and run Docker workflow

.PHONY: all-vmware
all-vmware: setup build-vmware run-vmware ## Setup, build, and run clean vmware-vcenter server 